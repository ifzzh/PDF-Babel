# 版本号与发布约定（前后端协作）

本文件用于前后端开发协作时的版本号约定与发布顺序，避免口头约定遗漏。

## 语义化版本（SemVer）

- PATCH（x.y.z）：修 bug、小改动，不影响接口/数据结构
- MINOR（x.y.z）：新增功能，保持兼容
- MAJOR（x.y.z）：破坏性变更（接口/配置/数据结构不兼容）

## 三套版本独立维护

- backend-base：仅当 uv.lock 或系统依赖变更时升版本
- backend：后端逻辑或 API 变化时升版本
- frontend：前端功能或样式变化时升版本

## 必要同步动作

- backend-base 升级时：
  - 更新 docker.version.backend.base
  - 更新 Dockerfile.backend 的 BASE_IMAGE tag
- 对外运行使用具体版本号（不要使用 latest）

## 发布顺序

1) backend-base
2) backend
3) frontend

## 离线资产包（GitHub Release）

用途：无外网环境或网络不稳定时，避免运行时下载字体/模型资源导致失败。

### 生成

在有外网的机器上执行：

```bash
docker run --rm -v $PWD/data/assets:/out ifzzh520/pdf-babel-backend:<backend_version> \
  python -m babeldoc.main --generate-offline-assets /out
```

生成文件：`data/assets/offline_assets_<hash>.zip`

### 发布

- 使用 GitHub Release 发布离线包（避免提交到仓库）
- Tag 命名：`assets-YYYY-MM-DD`（例如 `assets-2026-01-29`）
- Release 标题：`Offline assets YYYY-MM-DD`
- 附件：`offline_assets_<hash>.zip`

### 使用

1) 放到部署机器：`./data/assets/offline_assets_<hash>.zip`
2) 后端容器内恢复：

```bash
python -m babeldoc.main --restore-offline-assets /data/assets/offline_assets_<hash>.zip
```

### 更新时机

- 仅在 **Babeldoc 资产清单变化** 或 **版本升级** 时重新生成并发布
- 资产包是版本绑定的，旧包可能校验失败
