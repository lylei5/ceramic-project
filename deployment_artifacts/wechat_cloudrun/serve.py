"""CloudRun entry point. Public and VPC access must remain disabled."""
import os
from pathlib import Path

from verify_package import verify

ROOT = Path(__file__).resolve().parent
os.environ.setdefault('CERAMIC_ROOT', str(ROOT))
os.environ.setdefault('CERAMIC_CHECKPOINT', str(ROOT / 'weights/checkpoint-step114750.pt'))
os.environ.setdefault('CERAMIC_CHECKPOINT_SHA256', '6dd2b1e14f79f0ce3c02c1eafb48e1da8bfe2cfcd664564ecd39c69678275674')
os.environ['CERAMIC_DEVICE'] = 'cpu'
verify()

import cv2
import torch
from starlette.responses import JSONResponse
from decoder_api.app import app, decode
from storage_jobs import install_storage_jobs

torch.set_num_threads(4)
torch.set_num_interop_threads(1)
cv2.setNumThreads(1)
APP_ID = 'wxe79a18d344821272'


@app.middleware('http')
async def require_wechat_gateway(request, call_next):
    # These headers are identity signals only inside WeChat's private gateway.
    # Never enable a public ingress for this service: a public caller can forge them.
    if request.url.path != '/healthz':
        if request.headers.get('x-wx-appid') != APP_ID or not request.headers.get('x-wx-openid'):
            return JSONResponse({'detail': 'WeChat Mini Program identity required'}, status_code=403)
    return await call_next(request)


install_storage_jobs(app, decode)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', '8080')), workers=1)
