# 后端手动测试说明（v0.1）

本说明用于你本地手动验证后端最小功能（目前仅 /healthz）。

## 1. 创建虚拟环境

```bash
cd /home/ifzzh/Project/PDF-Babel
uv venv .venv
source .venv/bin/activate
```

## 2. 安装依赖（最小）

仅测试 /healthz 时，安装 FastAPI 与 Uvicorn 即可：

```bash
uv pip install fastapi uvicorn
```

如果你更倾向于跟随项目依赖（可能较慢）：

```bash
uv pip install -e .
```

## 3. 启动服务

```bash
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

> 如果端口 8000 被占用，可换成 8010/8020 等端口。

## 4. 请求健康检查

```bash
curl -sSf http://127.0.0.1:8000/healthz
```

期望输出：

```json
{"status": "ok"}
```

## 5. 验证持久化目录创建

服务启动后，会自动创建持久化目录结构：

```bash
ls -la /mnt/raid1/babeldoc-data
ls -la /mnt/raid1/babeldoc-data/jobs
ls -la /mnt/raid1/babeldoc-data/db
```

期望：目录存在且当前用户有写权限。

## 6. 验证数据库初始化

服务启动后，会自动创建数据库文件：

```bash
ls -la /mnt/raid1/babeldoc-data/db
```

期望：存在 `db.sqlite3` 文件。

可选验证（若已安装 sqlite3）：\n

```bash
sqlite3 /mnt/raid1/babeldoc-data/db/db.sqlite3 \".tables\"\n
```

期望输出包含：`jobs` 与 `files`。

## 7. 验证渠道定义接口

```bash
curl -sSf http://127.0.0.1:8000/api/channels | jq .
```

期望：返回 `platform/custom/unsupported` 三个字段；`platform` 中只有 DeepSeek 且 `enabled=false`；每个条目包含 `visible`。

## 8. 常见问题

- **端口无法绑定**：
  - 换用其他端口，例如 `--port 8010`
  - 或使用 `--host 0.0.0.0`

- **模块找不到**：
  - 确认已激活虚拟环境：`source .venv/bin/activate`

## 8. 验证第六步（create_job）

使用本地测试文件夹 `/home/ifzzh/Project/PDF-Babel/test-pdf` 中的 PDF：

```bash
source .venv/bin/activate
python - <<'PY'
from pathlib import Path
from backend.config import settings
from backend.storage import ensure_storage
from backend.db import init_db
from backend.jobs import create_job

storage = ensure_storage(settings)
init_db(settings.db_path)

pdf_path = Path("/home/ifzzh/Project/PDF-Babel/test-pdf/Kua.pdf")
record = create_job(
    settings,
    storage["jobs"],
    pdf_path.name,
    pdf_path.read_bytes(),
)

print("job_id:", record.id)
print("folder:", record.folder_name)
print("file exists:", (storage["jobs"]/record.folder_name/pdf_path.name).exists())
PY
```

然后检查数据库记录：

```bash
sqlite3 /mnt/raid1/babeldoc-data/db/db.sqlite3 \
  "select id, folder_name, status from jobs order by created_at desc limit 1;"
```

期望：
- `file exists: True`
- 最后一条 job 状态为 `queued`

