# Ceramic step114750 deployment

## Package identity

The complete service is in `wechat_cloudrun/`.

- API version: `2.3.0`
- Release: `robustness-20261016`
- Checkpoint step: `114750`
- Model: `trustmark-q-57bit-robust-step114750-locator5-perspective-rotation`
- Protocol: `57bit-crc4-bch5`
- Checkpoint SHA-256: `6dd2b1e14f79f0ce3c02c1eafb48e1da8bfe2cfcd664564ecd39c69678275674`

`package-manifest.json` verifies 36 runtime and model files. The service uses its bundled `src/trustmark/` source and two official Q base models to initialize the network, then loads `weights/checkpoint-step114750.pt` into the decoder.

## Fetch and verify

From the repository root:

```bash
git lfs install
git lfs pull
python deployment_artifacts/wechat_cloudrun/verify_package.py
```

All three model binaries are stored through Git LFS. A missing LFS object or an unexpanded pointer fails package verification.

## CPU container

```bash
docker build -t ceramic-decoder:step114750 deployment_artifacts/wechat_cloudrun
```

The image starts `python serve.py` with one worker on port `8080` (or `PORT`) and CPU inference. It installs the pinned runtime dependencies and validates the package during the build and at startup.

For a local health check, bind the container to loopback:

```bash
docker run --rm --name ceramic-step114750 \
  -p 127.0.0.1:8080:8080 ceramic-decoder:step114750
curl --fail http://127.0.0.1:8080/healthz
```

## WeChat CloudRun access

Deploy behind the trusted private WeChat gateway with public and VPC ingress disabled. The gateway supplies `x-wx-appid` and `x-wx-openid`; the service requires the configured Mini Program app ID and a nonempty open ID for all routes except `/healthz`. These headers can be forged on an unrestricted public endpoint.

`serve.py` is the service entry point: it installs gateway checks and the asynchronous storage routes around `decoder_api.app`.

The storage allowlist is configured in `storage_jobs.py` and matches the supplied CloudBase environment. Changing the deployment environment requires configuring the app ID and exact storage hosts and then updating the corresponding hashes in `package-manifest.json`.

## API

### Health

`GET /healthz` returns `status`, `model`, `checkpoint_step`, `checkpoint_sha256`, `payload_bits`, `protocol`, `release`, `device`, and search-policy fields.

Expected identity: step `114750`, payload `57`, release `robustness-20261016`, and the SHA-256 above.

### Multipart decode

`POST /decode` accepts multipart field `image` and form field `payload_bits=57`. `X-Image-SHA256` supplies the digest of the exact uploaded bytes; it is mandatory when `CERAMIC_REQUIRE_IMAGE_SHA256=1`.

Recovery succeeds when `detected`, `ecc_valid`, and `crc_valid` are all true. `payload_bits` is the recovered binary payload and `business_id` is its parsed decimal representation.

### Storage jobs

Submit `POST /decode-jobs`:

```json
{
  "url": "https://<allowed-storage-host>/ceramic-tests/image.png?<temporary-signature>",
  "sha256": "<lowercase-sha256-of-original-image>",
  "payload_bits": 57,
  "content_type": "image/png"
}
```

The response is HTTP `202` with `job_id`. Query `GET /decode-jobs/{job_id}` with the same gateway user identity. States are `queued`, `running`, `done`, and `failed`; completed jobs include `result` or `error`.

Source URLs require HTTPS, an exact configured host, and the `/ceramic-tests/` path prefix. Downloads reject redirects and verify the original byte hash. The service allows images up to 50 MiB and 50 million pixels, serializes model inference, accepts at most 8 pending jobs, retains at most 32 results, and expires completed results after 600 seconds. Jobs reside in the memory of one replica; use one replica or sticky routing for submit/poll continuity.

## Decoder policy

The decoder first tries OpenCV cubic 2x interpolation with a bounded search and falls back to the original image. It combines a ranked direct crop, luminance correction, scale alternatives, 12 perspective candidates, and 36 quarter-turn rotation candidates. The health contract reports a maximum of 72 attempts.

## Validation

The service is checked through its 36-file hash manifest, CPU startup, health identity, storage transport checks, and the supplied regression sample set. Sample-set results describe those inputs; independent production images need their own evaluation.
