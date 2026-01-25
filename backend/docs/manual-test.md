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

测试上传接口（/api/jobs）需要额外安装 `python-multipart`：

```bash
uv pip install python-multipart
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

## 8. 验证 /api/jobs 创建与查询

创建任务（注意：`source` 使用自定义渠道，值可为示例 dummy）：

**单行写法（推荐）：**

```bash
curl -sSf -X POST http://127.0.0.1:8000/api/jobs -F "file=@/home/ifzzh/Project/PDF-Babel/test-pdf/Kua.pdf" -F 'options={"lang_in":"en","lang_out":"zh"}' -F 'source={"mode":"custom","channel_id":"openai","credentials":{"api_key":"dummy","model":"gpt-4o-mini"}}'
```

**多行写法（注意每行末尾使用单个反斜杠 `\\` 作为续行）：**

```bash
curl -sSf -X POST http://127.0.0.1:8000/api/jobs \\
  -F "file=@/home/ifzzh/Project/PDF-Babel/test-pdf/Kua.pdf" \\
  -F 'options={"lang_in":"en","lang_out":"zh"}' \\
  -F 'source={"mode":"custom","channel_id":"openai","credentials":{"api_key":"dummy","model":"gpt-4o-mini"}}'
```

期望：返回 `job_id` / `status` / `created_at`。\n

查询任务：\n

```bash
curl -sSf http://127.0.0.1:8000/api/jobs/{job_id} | jq .
```

期望：能看到 `folder_name` 与 `original_filename`。

## 9. 验证 /api/jobs 历史列表

```bash
curl -sSf \"http://127.0.0.1:8000/api/jobs?limit=10&offset=0\" | jq .
```

可选：按时间筛选（北京时间 ISO 8601）：\n

```bash
curl -sSf \"http://127.0.0.1:8000/api/jobs?created_from=2026-01-25T00:00:00%2B08:00\" | jq .
```

期望：返回 `items` 和 `total`，items 按 `created_at` 降序。

## 10. 验证重命名（PATCH /api/jobs/{id}）

前置：需要一个 `status` 为 `finished/failed/canceled` 的任务。

获取最新任务的 `job_id`（也可使用 /api/jobs 列表查询）：\n

```bash
curl -sSf "http://127.0.0.1:8000/api/jobs?limit=1&offset=0" | jq -r '.items[0].job_id'
```

可以手动在数据库里将状态改为 `finished`（仅用于测试）：\n

```bash
sqlite3 /mnt/raid1/babeldoc-data/db/db.sqlite3 \\
  "update jobs set status='finished' where id='YOUR_JOB_ID';"
```

重命名测试（folder + original 文件名）：\n

```bash
curl -sSf -X PATCH http://127.0.0.1:8000/api/jobs/YOUR_JOB_ID \\
  -H 'Content-Type: application/json' \\
  -d '{"folder_name":"KuaRenamed","original_filename":"KuaRenamed.pdf","confirm":false}' | jq .
```

若命名冲突，将返回 409，并给出建议名；用户确认后再提交：\n

```bash
curl -sSf -X PATCH http://127.0.0.1:8000/api/jobs/YOUR_JOB_ID \\
  -H 'Content-Type: application/json' \\
  -d '{"folder_name":"KuaRenamed_20260125-011500","original_filename":"KuaRenamed_20260125-011500.pdf","confirm":true}' | jq .
```

期望：\n
- `folder_name` / `original_filename` 更新\n
- `renamed_at` 为当前时间\n

## 11. 常见问题

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
