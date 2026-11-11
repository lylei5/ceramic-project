# Ceramic 57-bit service state

Verified: 2026-11-11, Asia/Shanghai.

## Accepted service

- API version: `2.3.0`
- Release: `robustness-20261016`
- Business checkpoint: `step114750`
- Model: `trustmark-q-57bit-robust-step114750-locator5-perspective-rotation`
- Protocol: `57bit-crc4-bch5`
- SHA-256: `6dd2b1e14f79f0ce3c02c1eafb48e1da8bfe2cfcd664564ecd39c69678275674`

Repository package: `deployment_artifacts/wechat_cloudrun/`.

Server 249 package: `/data0/liyanlei/ceramic_watermark/incoming/wechat_cloudrun_build3/`.

## Preserved model files

The current repository contains one adapted business checkpoint plus the two official base models required for initialization:

| File within the package | SHA-256 |
| --- | --- |
| `weights/checkpoint-step114750.pt` | `6dd2b1e14f79f0ce3c02c1eafb48e1da8bfe2cfcd664564ecd39c69678275674` |
| `src/trustmark/models/encoder_Q.ckpt` | `dc382c3f6b4fd568b27d6fbb763d6ffc2d2587126d84afe9d5ee95b4c5d99826` |
| `src/trustmark/models/decoder_Q.ckpt` | `e3d9cea5406a26590735719f8f15cb10802b11852ae69047eaf4cf17214df781` |

All three files use Git LFS. `package-manifest.json` covers 36 runtime and model files.

## Verification and operation

The package passes manifest verification and temporary CPU startup; `/healthz` identifies step114750 and the checksum above. Storage transport checks pass, and all seven supplied regression samples recover their expected identifiers through asynchronous storage jobs. These checks establish package identity, loadability, and results on those samples. Live ingress availability is determined by the deployed environment's health endpoint.

The service accepts 57-bit business identifiers with BCH-5 and CRC-4 validation, supports multipart decoding and asynchronous storage jobs, and runs behind a trusted private WeChat gateway. See [deployment instructions](deployment_artifacts/README.md) for the entry point, limits, and isolation requirements.

Keep the checkpoint, runtime source, dependencies, and manifest consistent when maintaining this package. Training or a change to the deployed Mini Program endpoint requires its own user instruction.
