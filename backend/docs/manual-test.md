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

翻译执行（/api/jobs/{id}/run）需要完整依赖（包含 onnxruntime / openai / pymupdf 等）：

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
curl -sSf "http://127.0.0.1:8000/api/jobs?limit=1&offset=0" | jq -r '.items[0].job_id'
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

获取最新任务的 `job_id`（也可使用 /api/jobs 列表查询）：

```bash
curl -sSf "http://127.0.0.1:8000/api/jobs?limit=1&offset=0" | jq -r '.items[0].job_id'
```

可以手动在数据库里将状态改为 `finished`（仅用于测试）：

**单行写法（推荐）：**

```bash
sqlite3 /mnt/raid1/babeldoc-data/db/db.sqlite3 "update jobs set status='finished' where id='YOUR_JOB_ID';"
```

**多行写法（注意每行末尾使用单个反斜杠 `\\` 作为续行）：**

```bash
sqlite3 /mnt/raid1/babeldoc-data/db/db.sqlite3 \\
  "update jobs set status='finished' where id='YOUR_JOB_ID';"
```

重命名测试（folder + original 文件名）：

```bash
curl -sSf -X PATCH http://127.0.0.1:8000/api/jobs/02757bac-6856-4af6-a4e9-401a46c98ecd \
  -H 'Content-Type: application/json' \
  -d '{"folder_name":"KuaRenamed","original_filename":"KuaRenamed.pdf","confirm":false}' | jq .
```

若命名冲突，将返回 409，并给出建议名；用户确认后再提交：

```bash
curl -sSf -X PATCH http://127.0.0.1:8000/api/jobs/02757bac-6856-4af6-a4e9-401a46c98ecd \
  -H 'Content-Type: application/json' \
  -d '{"folder_name":"KuaRenamed_20260125-011500","original_filename":"KuaRenamed_20260125-011500.pdf","confirm":true}' | jq .
```

期望：
- `folder_name` / `original_filename` 更新
- `renamed_at` 为当前时间

可选检查（目录与文件是否真实改名）：

```bash
ls -la /mnt/raid1/babeldoc-data/jobs/KuaRenamed
```

## 11. 验证 /api/jobs/{id}/files

```bash
curl -sSf http://127.0.0.1:8000/api/jobs/02757bac-6856-4af6-a4e9-401a46c98ecd/files | jq .
```

期望：返回数组，至少包含 `type=original` 的记录。

若返回空数组，说明该 job 可能创建于旧版本（未写入 files 记录）。
可再次调用该接口，它会尝试自动补建 `original` 记录（前提是原文件仍在目录内）。

## 12. 验证 /api/files/{file_id}（Range）

先从上一步返回中取一个 `file_id`，测试 Range 下载：

```bash
curl -sSf -H "Range: bytes=0-99" -D - http://127.0.0.1:8000/api/files/5b483390-6465-4473-a2fd-17deddcebf8c -o /tmp/sample.pdf
```

期望：
- 返回 206（Partial Content）
- `/tmp/sample.pdf` 存在且大小约 100 字节

## 13. 验证翻译执行（/api/jobs/{id}/run）

前置：
- 创建任务时需提供真实可用的 `source.credentials`（API Key / Model / Base URL）。
- 本步骤为**同步执行**，会阻塞请求直到翻译结束。

示例（DeepSeek 自定义渠道）：

```bash
curl -sSf -X POST http://127.0.0.1:8000/api/jobs \
  -F "file=@/home/ifzzh/Project/PDF-Babel/test-pdf/Kua.pdf" \
  -F 'options={"lang_in":"en","lang_out":"zh"}' \
  -F 'source={"mode":"custom","channel_id":"deepseek","credentials":{"base_url":"https://api.deepseek.com/v1","api_key":"YOUR_KEY","model":"deepseek-chat"}}'
```

> 请将 `YOUR_KEY` 替换为你自己的真实 API Key（不要提交到仓库）。

执行：

```bash
curl -sSf "http://127.0.0.1:8000/api/jobs?limit=1&offset=0" | jq -r '.items[0].job_id'
curl -sSf -X POST http://127.0.0.1:8000/api/jobs/{job_id}/run | jq .
```

期望：
- 返回 `status: "finished"`，并包含 `files` 列表。
- 任务目录中存在 `mono.pdf` / `dual.pdf`（若未禁用对应输出）。

可选检查（查看文件列表）：

```bash
curl -sSf "http://127.0.0.1:8000/api/jobs?limit=1&offset=0" | jq -r '.items[0].job_id'
curl -sSf http://127.0.0.1:8000/api/jobs/{job_id}/files | jq .
```

失败排查：
- 若返回 500，可在数据库中查看 `jobs.error` 字段。

## 14. 验证 SSE 事件流（/api/jobs/{id}/events）

在一个终端保持监听：

```bash
curl -sSf "http://127.0.0.1:8000/api/jobs?limit=1&offset=0" | jq -r '.items[0].job_id'
curl -N http://127.0.0.1:8000/api/jobs/{job_id}/events
```

在另一个终端执行翻译：

```bash
curl -sSf "http://127.0.0.1:8000/api/jobs?limit=1&offset=0" | jq -r '.items[0].job_id'
curl -sSf -X POST http://127.0.0.1:8000/api/jobs/{job_id}/run | jq .
```

期望：
- SSE 输出包含 `stage_summary` / `progress_update` / `finish`（或 `error`）

## 15. 验证取消任务（/api/jobs/{id}/cancel）

在一个终端执行翻译（会阻塞）：

```bash
curl -sSf "http://127.0.0.1:8000/api/jobs?limit=1&offset=0" | jq -r '.items[0].job_id'
curl -sSf -X POST http://127.0.0.1:8000/api/jobs/{job_id}/run | jq .
```

翻译过程中在另一个终端发送取消请求：

```bash
curl -sSf "http://127.0.0.1:8000/api/jobs?limit=1&offset=0" | jq -r '.items[0].job_id'
curl -sSf -X POST http://127.0.0.1:8000/api/jobs/{job_id}/cancel | jq .
```

期望：
- 返回 `status: canceling` 或 `status: canceled`
- `/api/jobs/{id}` 最终状态为 `canceled`
- SSE 最终收到 `error`（内容包含 canceled）

## 13. 常见问题

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
