# 陶瓷 57-bit 水印服务

面向陶瓷图案与手机拍摄图像的 TrustMark-Q 业务标识解码服务。

## 服务版本

| 项目 | 版本 |
| --- | --- |
| API | `2.3.0` |
| 发布标识 | `robustness-20261016` |
| 业务检查点 | `step114750` |
| 模型 | `trustmark-q-57bit-robust-step114750-locator5-perspective-rotation` |
| 协议 | `57bit-crc4-bch5` |

检查点 SHA-256：

```text
6dd2b1e14f79f0ce3c02c1eafb48e1da8bfe2cfcd664564ecd39c69678275674
```

完整服务位于 [`deployment_artifacts/wechat_cloudrun/`](deployment_artifacts/wechat_cloudrun/)，包括 API、CloudRun 入口、异步图片任务、TrustMark 源码、固定依赖、Dockerfile、校验清单及模型文件。业务检查点和启动所需的官方 encoder/decoder 基础模型均通过 Git LFS 管理。

## 获取与校验

```bash
git lfs install
git clone https://github.com/lylei5/ceramic-project.git
cd ceramic-project
git lfs pull
python deployment_artifacts/wechat_cloudrun/verify_package.py
```

校验通过后输出 `Package verified: step 114750, 57-bit protocol`。GitHub 的 ZIP 下载通常包含 LFS 指针；获取可运行权重请使用 Git LFS。

## 运行与接口

```bash
docker build -t ceramic-decoder:step114750 deployment_artifacts/wechat_cloudrun
```

CloudRun 使用可信的微信私有网关接入，并保持公网及 VPC 入口关闭。网关注入的身份头只在该信任边界内具有鉴权意义。

- `GET /healthz`：检查模型、step、SHA-256、协议与候选策略。
- `POST /decode`：multipart 图片解码，字段为 `image` 和 `payload_bits=57`。
- `POST /decode-jobs`：提交受限存储 URL 与原始图片 SHA-256，返回任务 ID。
- `GET /decode-jobs/{job_id}`：查询当前用户的任务状态与结果。

成功以 `detected`、`ecc_valid` 和 `crc_valid` 为准，`payload_bits` 为恢复的 57-bit 字符串，`business_id` 为解析后的业务编号。

详细部署与异步任务约束见 [部署说明](deployment_artifacts/README.md)。当前文件身份与验证口径见 [服务状态](57BIT_RETAINED_STATE.md)。

## 目录

- `deployment_artifacts/wechat_cloudrun/`：step114750 完整服务。
- `cloudfunctions/`：CloudBase 解码及配置相关源码。
- `comparison_exports/`、`.planning/`：既有实验报告和规划资料。
- `NEW_CHAT_HANDOFF.md`：服务维护入口。

TrustMark 许可随服务保存在 `TRUSTMARK_LICENSE.txt`。凭据、私钥、环境变量文件和用户图片保存在部署环境中。
