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

