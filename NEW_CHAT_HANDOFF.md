# Ceramic watermark service maintenance

## Service identity

Maintain the complete `step114750` service under `deployment_artifacts/wechat_cloudrun/`.

- API: `2.3.0`
- Release: `robustness-20261016`
- Protocol: `57bit-crc4-bch5`
- Checkpoint SHA-256: `6dd2b1e14f79f0ce3c02c1eafb48e1da8bfe2cfcd664564ecd39c69678275674`

The package includes the adapted checkpoint, official Q initialization models, TrustMark source, decoder API, private gateway entry point, storage-job transport, Dockerfile, pinned requirements, license, and 36-file hash manifest.

## Maintenance entry points

1. Fetch Git LFS objects and run `python deployment_artifacts/wechat_cloudrun/verify_package.py`.
2. Read [current service state](57BIT_RETAINED_STATE.md) for exact file identities.
3. Follow [deployment instructions](deployment_artifacts/README.md) for container startup and API checks.

The corresponding server 249 source package is `/data0/liyanlei/ceramic_watermark/incoming/wechat_cloudrun_build3/`.

`serve.py` installs trusted WeChat gateway checks and asynchronous storage routes. Use it as the CloudRun entry point. Keep public and VPC ingress disabled for this gateway-based authentication model.

Production availability and endpoint configuration must be checked in the live deployment environment. Model training or a live endpoint change requires a separate user instruction.
