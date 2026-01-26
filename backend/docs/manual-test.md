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

## 6.1 平台渠道配置（可选）

平台 DeepSeek 的配置通过 JSON 文件读取，默认路径：

```
/mnt/raid1/babeldoc-data/config/platform.json
```

可通过环境变量覆盖配置文件路径：

```bash
export BABELDOC_PLATFORM_CONFIG="/mnt/raid1/babeldoc-data/config/platform.json"
```

示例内容（请替换为你自己的 key）：

```json
{
  "platform": {
    "deepseek": {
      "base_url": "https://api.deepseek.com/v1",
      "api_key": "YOUR_KEY",
      "model": "deepseek-chat"
    }
  }
}
```

如需覆盖配置文件，可用环境变量：

```bash
export BABELDOC_PLATFORM_DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"
export BABELDOC_PLATFORM_DEEPSEEK_API_KEY="YOUR_KEY"
export BABELDOC_PLATFORM_DEEPSEEK_MODEL="deepseek-chat"
```

## 7. 验证渠道定义接口

```bash
curl -sSf http://127.0.0.1:8000/api/channels | jq .
```

期望：返回 `platform/custom/unsupported` 三个字段；`platform` 中只有 DeepSeek；每个条目包含 `visible`。

说明：
- 平台 DeepSeek 是否可用取决于平台配置文件
- 未配置时 `enabled=false` 且 `disabled_reason` 提示“缺少平台配置”

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
JOB_ID=$(curl -sSf "http://127.0.0.1:8000/api/jobs?limit=1&offset=0" | jq -r '.items[0].job_id')
curl -sSf http://127.0.0.1:8000/api/jobs/$JOB_ID | jq .
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
JOB_ID=$(curl -sSf "http://127.0.0.1:8000/api/jobs?limit=1&offset=0" | jq -r '.items[0].job_id')
```

可以手动在数据库里将状态改为 `finished`（仅用于测试）：

**单行写法（推荐）：**

```bash
sqlite3 /mnt/raid1/babeldoc-data/db/db.sqlite3 "update jobs set status='finished' where id='${JOB_ID}';"
```

**多行写法（注意每行末尾使用单个反斜杠 `\\` 作为续行）：**

```bash
sqlite3 /mnt/raid1/babeldoc-data/db/db.sqlite3 \\
  "update jobs set status='finished' where id='${JOB_ID}';"
```

重命名测试（folder + original 文件名）：

注意：`original_filename` 不允许为 `mono.pdf` 或 `dual.pdf`。
说明：`display_name` 仅用于展示，不影响文件或文件夹。

```bash
curl -sSf -X PATCH http://127.0.0.1:8000/api/jobs/$JOB_ID \
  -H 'Content-Type: application/json' \
  -d '{"folder_name":"KuaRenamed","original_filename":"KuaRenamed.pdf","confirm":false}' | jq .
```

若命名冲突，将返回 409，并给出建议名；用户确认后再提交：

```bash
curl -sSf -X PATCH http://127.0.0.1:8000/api/jobs/$JOB_ID \
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
JOB_ID=$(curl -sSf "http://127.0.0.1:8000/api/jobs?limit=1&offset=0" | jq -r '.items[0].job_id')
curl -sSf http://127.0.0.1:8000/api/jobs/$JOB_ID/files | jq .
```

期望：返回数组，至少包含 `type=original` 的记录。

若返回空数组，说明该 job 可能创建于旧版本（未写入 files 记录）。
可再次调用该接口，它会尝试自动补建 `original` 记录（前提是原文件仍在目录内）。

## 12. 验证 /api/files/{file_id}（Range）

先从上一步返回中取一个 `file_id`，测试 Range 下载：

```bash
JOB_ID=$(curl -sSf "http://127.0.0.1:8000/api/jobs?limit=1&offset=0" | jq -r '.items[0].job_id')
FILE_ID=$(curl -sSf http://127.0.0.1:8000/api/jobs/$JOB_ID/files | jq -r '.[0].file_id')
curl -sSf -H "Range: bytes=0-99" -D - http://127.0.0.1:8000/api/files/$FILE_ID -o /tmp/sample.pdf
```

期望：
- 返回 206（Partial Content）
- `/tmp/sample.pdf` 存在且大小约 100 字节

## 13. 验证翻译执行（/api/jobs/{id}/run）

前置：
- 创建任务时需提供真实可用的 `source.credentials`（API Key / Model / Base URL）。
- `/api/jobs/{id}/run` 为**异步执行**，会立即返回 `status=running`，真正完成需要等待 SSE 或轮询状态。
- 仅允许 `status=queued` 的任务执行，若已完成需重新创建任务。
- 可通过环境变量 `BABELDOC_MAX_RUNNING` 控制并发上限（默认 1）。
- 当并发已满时，本接口会返回 `status=queued`，任务进入队列等待执行。
- 队列状态已持久化到数据库，服务重启后会恢复队列，并把 `running` 任务重置为 `queued`（需调用 `/api/queue/resume` 才会继续执行）。

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
JOB_ID=$(curl -sSf "http://127.0.0.1:8000/api/jobs?limit=1&offset=0" | jq -r '.items[0].job_id')
curl -sSf -X POST http://127.0.0.1:8000/api/jobs/$JOB_ID/run | jq .
```

期望：
- 立即返回 `status: "running"`。
- 任务目录中存在 `mono.pdf` / `dual.pdf`（若未禁用对应输出）。

可用下面方式等待完成（任选其一）：

```bash
JOB_ID=$(curl -sSf "http://127.0.0.1:8000/api/jobs?limit=1&offset=0" | jq -r '.items[0].job_id')
curl -sSf http://127.0.0.1:8000/api/jobs/$JOB_ID | jq .
```

可选检查（查看文件列表）：

```bash
JOB_ID=$(curl -sSf "http://127.0.0.1:8000/api/jobs?limit=1&offset=0" | jq -r '.items[0].job_id')
curl -sSf http://127.0.0.1:8000/api/jobs/$JOB_ID/files | jq .
```

失败排查：
- 若返回 500，可在数据库中查看 `jobs.error` 字段。

## 14. 验证 SSE 事件流（/api/jobs/{id}/events）

在一个终端保持监听：

```bash
JOB_ID=$(curl -sSf "http://127.0.0.1:8000/api/jobs?limit=1&offset=0" | jq -r '.items[0].job_id')
curl -N http://127.0.0.1:8000/api/jobs/$JOB_ID/events
```

在另一个终端执行翻译：

```bash
JOB_ID=$(curl -sSf "http://127.0.0.1:8000/api/jobs?limit=1&offset=0" | jq -r '.items[0].job_id')
curl -sSf -X POST http://127.0.0.1:8000/api/jobs/$JOB_ID/run | jq .
```

期望：
- SSE 输出包含 `stage_summary` / `progress_update` / `finish`（或 `error`）

## 15. 验证取消任务（/api/jobs/{id}/cancel）

在一个终端执行翻译（会阻塞）：

```bash
JOB_ID=$(curl -sSf "http://127.0.0.1:8000/api/jobs?limit=1&offset=0" | jq -r '.items[0].job_id')
curl -sSf -X POST http://127.0.0.1:8000/api/jobs/$JOB_ID/run | jq .
```

翻译过程中在另一个终端发送取消请求：

```bash
JOB_ID=$(curl -sSf "http://127.0.0.1:8000/api/jobs?limit=1&offset=0" | jq -r '.items[0].job_id')
curl -sSf -X POST http://127.0.0.1:8000/api/jobs/$JOB_ID/cancel | jq .
```

期望：
- 返回 `status: canceling` 或 `status: canceled`
- `/api/jobs/{id}` 最终状态为 `canceled`
- SSE 最终收到 `error`（内容包含 canceled）

## 16. 验证并发上限（BABELDOC_MAX_RUNNING）

重启服务前设置并发上限（示例：1）：

```bash
export BABELDOC_MAX_RUNNING=1
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

创建两个任务并尝试同时执行：

```bash
JOB_ID_1=$(curl -sSf -X POST http://127.0.0.1:8000/api/jobs \
  -F "file=@/home/ifzzh/Project/PDF-Babel/test-pdf/Kua.pdf" \
  -F 'options={"lang_in":"en","lang_out":"zh"}' \
  -F 'source={"mode":"custom","channel_id":"deepseek","credentials":{"base_url":"https://api.deepseek.com/v1","api_key":"YOUR_KEY","model":"deepseek-chat"}}' \
  | jq -r '.job_id')

JOB_ID_2=$(curl -sSf -X POST http://127.0.0.1:8000/api/jobs \
  -F "file=@/home/ifzzh/Project/PDF-Babel/test-pdf/Kua.pdf" \
  -F 'options={"lang_in":"en","lang_out":"zh"}' \
  -F 'source={"mode":"custom","channel_id":"deepseek","credentials":{"base_url":"https://api.deepseek.com/v1","api_key":"YOUR_KEY","model":"deepseek-chat"}}' \
  | jq -r '.job_id')

curl -sSf -X POST http://127.0.0.1:8000/api/jobs/$JOB_ID_1/run | jq .
curl -sSf -X POST http://127.0.0.1:8000/api/jobs/$JOB_ID_2/run | jq .
```

期望：
- 第一个返回 `status: running`
- 第二个返回 `status: queued`（进入等待队列）

可用轮询确认第二个任务会在第一个完成后自动进入 `running`：

```bash
curl -sSf http://127.0.0.1:8000/api/jobs/$JOB_ID_2 | jq .
```

## 17. 验证队列快照（/api/queue）

```bash
curl -sSf http://127.0.0.1:8000/api/queue | jq .
```

期望：
- 返回 `max_running`、`running`、`queued`

## 18. 恢复队列执行（/api/queue/resume）

全量恢复（将队列中的任务重新触发执行）：

```bash
curl -sSf -X POST http://127.0.0.1:8000/api/queue/resume \
  -H 'Content-Type: application/json' \
  -d '{"mode":"all"}' | jq .
```

仅恢复部分任务（先从队列快照中取一个 `job_id`）：

```bash
JOB_ID=$(curl -sSf http://127.0.0.1:8000/api/queue | jq -r '.queued[0]')
curl -sSf -X POST http://127.0.0.1:8000/api/queue/resume \
  -H 'Content-Type: application/json' \
  -d "{\"job_ids\":[\"$JOB_ID\"]}" | jq .
```

期望：
- 返回 `accepted` 与 `skipped` 列表
- 只有 `queued` 的任务会进入 `accepted`

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
