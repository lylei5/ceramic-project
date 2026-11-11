"""Bounded, owner-scoped image jobs for a single private CloudRun replica."""
import asyncio
import hashlib
import io
import re
import secrets
import time
from urllib.parse import unquote, urlsplit

import requests
from fastapi import HTTPException, Request, UploadFile
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import Headers
from starlette.responses import JSONResponse

BUCKET = '6365-ceramic-test-d8g02lrcebca4cefa-1509912646'
HOSTS = frozenset((BUCKET + '.tcb.qcloud.la', BUCKET + '.cos.ap-shanghai.myqcloud.com'))
PREFIX = '/ceramic-tests/'
MAX_BYTES = 50 * 1024 * 1024
MAX_PENDING = 8
MAX_RETAINED = 32
RESULT_TTL = 600


def validate_source(url, digest):
    if not isinstance(url, str) or len(url) > 8192:
        raise HTTPException(422, 'Invalid storage URL')
    try:
        parsed = urlsplit(url)
        valid = (parsed.scheme == 'https' and parsed.hostname in HOSTS
                 and parsed.port in (None, 443) and not parsed.username
                 and not parsed.password and not parsed.fragment
                 and unquote(parsed.path).startswith(PREFIX))
    except ValueError:
        valid = False
    if not valid:
        raise HTTPException(422, 'Only this test environment storage is accepted')
    if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
        raise HTTPException(422, 'A lowercase SHA-256 digest is required')


def download_image(url, digest):
    validate_source(url, digest)
    # Never follow redirects or log signed URLs. The hostname is an exact allowlist.
    try:
        with requests.get(url, stream=True, timeout=(5, 20), allow_redirects=False) as response:
            if response.status_code != 200:
                raise HTTPException(502, 'Storage download failed; refresh the temporary URL')
            length = response.headers.get('Content-Length')
            if length and int(length) > MAX_BYTES:
                raise HTTPException(413, 'Image exceeds upload limit')
            data = bytearray()
            started = time.monotonic()
            for block in response.iter_content(64 * 1024):
                if time.monotonic() - started > 60:
                    raise HTTPException(504, 'Storage download timed out')
                data.extend(block)
                if len(data) > MAX_BYTES:
                    raise HTTPException(413, 'Image exceeds upload limit')
    except (requests.RequestException, ValueError):
        raise HTTPException(502, 'Storage download failed') from None
    if not secrets.compare_digest(hashlib.sha256(data).hexdigest(), digest):
        raise HTTPException(422, 'Image SHA-256 mismatch')
    return bytes(data)


def install_storage_jobs(app, decode):
    jobs = {}
    tasks = set()
    serial = asyncio.Semaphore(1)

    def prune():
        now = time.monotonic()
        for key in list(jobs):
            job = jobs[key]
            if job['state'] in ('done', 'failed') and now - job['finished'] > RESULT_TTL:
                del jobs[key]

    async def execute(job, request, url, digest, content_type):
        try:
            async with serial:
                job['state'] = 'running'
                raw = await run_in_threadpool(download_image, url, digest)
                upload = UploadFile(io.BytesIO(raw), filename='photo', headers=Headers({'content-type': content_type}))
                try:
                    job['result'] = await decode(request, image=upload, payload_bits=57)
                finally:
                    await upload.close()
                job['state'] = 'done'
        except HTTPException as exc:
            job.update(state='failed', error={'status': exc.status_code, 'message': str(exc.detail)})
        except Exception:
            job.update(state='failed', error={'status': 500, 'message': 'Image processing failed'})
        finally:
            job['finished'] = time.monotonic()

    @app.post('/decode-jobs')
    async def submit(request: Request):
        body = await request.body()
        if len(body) > 16 * 1024:
            raise HTTPException(413, 'Job request too large')
        try:
            import json
            values = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            raise HTTPException(422, 'Expected JSON job request') from None
        if not isinstance(values, dict) or values.get('payload_bits') != 57:
            raise HTTPException(422, 'payload_bits must be 57')
        url, digest = values.get('url'), values.get('sha256')
        validate_source(url, digest)
        content_type = values.get('content_type', 'image/png')
        if content_type not in ('image/png', 'image/jpeg', 'image/webp'):
            raise HTTPException(415, 'Unsupported image content type')
        prune()
        if sum(j['state'] in ('queued', 'running') for j in jobs.values()) >= MAX_PENDING:
            raise HTTPException(429, 'Decoder queue is full; retry later')
        while len(jobs) >= MAX_RETAINED:
            completed = [key for key, job in jobs.items() if job['state'] in ('done', 'failed')]
            if not completed:
                raise HTTPException(429, 'Decoder queue is full; retry later')
            del jobs[min(completed, key=lambda key: jobs[key]['finished'])]
        key = secrets.token_urlsafe(24)
        job = {'owner': request.headers['x-wx-openid'], 'state': 'queued'}
        jobs[key] = job
        task = asyncio.create_task(execute(job, request, url, digest, content_type))
        tasks.add(task)
        task.add_done_callback(tasks.discard)
        return JSONResponse({'job_id': key, 'state': 'queued'}, status_code=202)

    @app.get('/decode-jobs/{key}')
    async def status(key: str, request: Request):
        prune()
        job = jobs.get(key)
        if not job or not secrets.compare_digest(job['owner'], request.headers['x-wx-openid']):
            raise HTTPException(404, 'Job unavailable; submit again if the service restarted')
        result = {'state': job['state']}
        if job['state'] == 'done':
            result['result'] = job['result']
        elif job['state'] == 'failed':
            result['error'] = job['error']
        return result
