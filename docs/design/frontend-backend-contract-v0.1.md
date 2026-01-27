# 前后端契约 v0.4

> 适用范围：BabelDOC 后端（FastAPI）+ Vue 前端（SSE 实时进度）。
> 备注：BabelDOC 当前仅支持 OpenAI 兼容接口。非兼容渠道可展示但需标注“暂不支持”。

## 0. 不可变约定（双方必须遵守）

以下内容作为**前后端稳定契约**，在未升级版本号前不得改动：

1) **接口路径与方法固定**  
   - `POST /api/jobs`  
   - `GET /api/jobs/{id}`  
   - `GET /api/jobs/{id}/events`  
   - `GET /api/jobs/{id}/files`  
   - `GET /api/files/{file_id}`  
   - `POST /api/jobs/{id}/cancel`  
   - `GET /api/channels`
   - `PATCH /api/jobs/{id}`  
   - 可新增扩展接口，但不得修改上述接口语义

2) **SSE 事件结构固定**  
   - 必须包含：`type`、`job_id`、`ts`、`data`  
   - `type` 只能是：`stage_summary|progress_start|progress_update|progress_end|finish|error|heartbeat`

3) **创建任务请求体字段固定**  
   - multipart 中字段名固定为：`file`、`options`、`source`、`glossary_files`  
   - `source.mode` 只允许：`platform|custom`

4) **渠道定义结构固定**  
   - `GET /api/channels` 返回 `platform/custom/unsupported` 三类  
   - 任一渠道可带 `enabled`、`disabled_reason`、`visible`  
   - `enabled=false` 需在前端灰显且不可选  
   - `visible=false` 不显示到前端

5) **文件列表结构固定**  
   - `GET /api/jobs/{id}/files` 返回数组对象：必须包含  
     `file_id|type|watermark|filename|size|url`

6) **PDF 预览与下载固定**  
   - `GET /api/files/{file_id}` 必须支持 HTTP Range

7) **平台提供渠道 v0.4 固定**  
   - 仅 **DeepSeek**  
   - `enabled` 由后端平台配置决定（未配置时为 `false` 并灰显）

8) **时间与时区固定**  
   - 所有时间字段（`created_at` / `updated_at` / `ts`）使用北京时间（UTC+08:00）  
   - 格式统一为 ISO 8601（示例：`2026-01-24T12:00:00+08:00`）

9) **持久化存储根目录固定**  
   - 根目录固定为：`/mnt/raid1/babeldoc-data`  
   - 结果文件夹均创建在该目录下

10) **命名与重命名规则固定**  
   - 文件夹名默认使用 PDF 文件名的 stem  
   - 仅允许对 `finished/failed/canceled` 状态的任务进行重命名  
   - 重命名冲突时：后端生成带时间后缀的建议名并返回  
   - 前端需让用户确认后再提交  
   - 后端记录 `renamed_at`（北京时间）
   - `original_filename` 不允许为 `mono.pdf` 或 `dual.pdf`（保留名）
11) **展示名称固定**  
   - `display_name` 仅用于展示，不影响文件或文件夹  
   - 初始化为原文件名的 stem，之后不会自动跟随文件名变化

如需调整上述任一条，必须升级版本号（例如 v0.5）并同步前后端变更。

## 1. 能力来源（翻译渠道）

前端提供两种模式：

- **平台提供**：仅显示渠道名称，隐藏 URL/Key/Model 等字段（DeepSeek 是否可选取决于 `enabled`）
- **自定义**：选择渠道后，显示该渠道所需字段

### 1.0 平台提供策略 v0.4

- 仅预置 **DeepSeek**
- `GET /api/channels` 会返回 `enabled` 与 `disabled_reason`
- 若 `enabled=false`，前端需禁用点击并显示原因提示（例如“缺少平台配置”）

### 1.1 OpenAI 兼容（后端可直接支持）

- OpenAI：`base_url` / `api_key` / `model`
- AzureOpenAI：`base_url` / `api_key` / `model` / `api_version`
- ModelScope：`base_url` / `api_key` / `model`
- Zhipu：`api_key` / `model`（base_url 固定）
- Silicon：`api_key` / `model`（base_url 固定）
- Gemini：`api_key` / `model`（base_url 固定）
- Grok：`api_key` / `model`（base_url 固定）
- Groq：`api_key` / `model`（base_url 固定）
- DeepSeek：`api_key` / `model`（base_url 固定）
- OpenAI-liked：`base_url` / `api_key` / `model`
- Ali Qwen-Translation：`api_key` / `model` / `domains`（base_url 固定）

### 1.2 非 OpenAI 兼容（仅展示，暂不支持）

- Google / Bing（网页接口）
- DeepL / DeepLX
- Azure（Translator） / Tencent
- Argos Translate（本地模型）
- Ollama / Xinference
- Dify / AnythingLLM

## 2. 接口清单

- `POST /api/jobs`：上传 PDF + 选项，创建任务
- `GET /api/jobs/{id}`：查询任务状态/进度（包含 `display_name`）
- `GET /api/jobs/{id}/events`：SSE 实时进度事件
- `GET /api/jobs/{id}/files`：获取输出文件列表
- `GET /api/files/{file_id}`：下载/预览 PDF（支持 Range）
- `POST /api/jobs/{id}/cancel`：取消任务
- `GET /api/channels`：获取渠道定义（平台/自定义/不支持）
- `PATCH /api/jobs/{id}`：修改文件夹名 / 原始文件名
 
### 2.2 可选扩展接口（v0.4 推荐）

- `GET /api/jobs`：查询历史任务列表（用于“历史/文件夹”页面）
- `DELETE /api/jobs/{id}`：删除单条任务（需 `confirm=true`）
- `POST /api/jobs/delete`：批量删除任务（需 `confirm=true`）
- `GET /api/queue`：查询当前队列快照（运行中/排队中）
- `POST /api/queue/resume`：手动恢复队列执行（用于重启后/手动启动）

响应示例：

```json
{
  "items": [
    {
      "job_id": "uuid",
      "folder_name": "paper",
      "display_name": "paper",
      "created_at": "2026-01-24T12:00:00+08:00",
      "renamed_at": null,
      "status": "finished",
      "has_mono": true,
      "has_dual": true,
      "has_glossary": true
    }
  ],
  "total": 1
}
```

说明：
- `folder_name` 为后端生成的存储文件夹名  
- `display_name` 为前端展示名，初始化为原文件名的 stem  
- 若同名冲突，后端可追加短后缀，例如 `paper_a1b2`  

### 2.3 队列快照（/api/queue）

响应示例：

```json
{
  "max_running": 1,
  "running": ["uuid-1"],
  "queued": ["uuid-2", "uuid-3"]
}
```

说明：
- `running` / `queued` 仅包含任务 ID
- `queued` 包含所有 `status=queued` 的任务（按创建时间入队），但不会自动执行
- 需要调用 `POST /api/jobs/{id}/run` 或 `POST /api/queue/resume` 才会开始执行
- `max_running` 为并发上限

### 2.4 恢复队列（/api/queue/resume）

请求体（二选一）：

```json
{ "mode": "all" }
```

```json
{ "job_ids": ["uuid-1", "uuid-2"] }
```

响应示例：

```json
{
  "accepted": ["uuid-2"],
  "skipped": [
    { "job_id": "uuid-1", "reason": "running" },
    { "job_id": "uuid-x", "reason": "not_queued" }
  ]
}
```

说明：
- 只会接受 `queued` 状态的任务
- `skipped.reason` 可能为 `running` / `not_queued`
- 该接口用于**手动启动**队列（服务重启后不会自动执行）

### 2.1 渠道定义（/api/channels）

响应示例：

```json
{
  "platform": [
    {
      "id": "deepseek",
      "label": "DeepSeek",
      "enabled": true,
      "disabled_reason": "",
      "visible": true
    }
  ],
  "custom": [
    {
      "id": "deepseek",
      "label": "DeepSeek",
      "openai_compatible": true,
      "enabled": true,
      "visible": true,
      "fields": [
        { "key": "api_key", "label": "API Key", "required": true, "secret": true },
        { "key": "model", "label": "Model", "required": true, "secret": false }
      ]
    }
  ],
  "unsupported": [
    {
      "id": "google",
      "label": "Google",
      "reason": "非OpenAI兼容",
      "visible": true
    }
  ]
}
```

说明：
- `platform` / `custom` 中均可带 `enabled`、`disabled_reason`、`visible`
- `enabled=false` 的渠道前端必须灰显且不可选择
- `visible=false` 的渠道前端不可展示
- 若前端仍提交 `enabled=false` 的 `channel_id`，后端应返回 400

## 3. 创建任务

请求（multipart/form-data）：

- `file`：PDF 文件
- `options`：JSON 字符串
- `source`：JSON 字符串
- `glossary_files`：可选 CSV，可多文件

`source` 示例（平台提供）：

```json
{
  "mode": "platform",
  "channel_id": "deepseek"
}
```

`source` 示例（自定义）：

```json
{
  "mode": "custom",
  "channel_id": "openai",
  "credentials": {
    "base_url": "https://api.openai.com/v1",
    "api_key": "xxxx",
    "model": "gpt-4o-mini"
  }
}
```

`options` 示例（节选，后端会映射到 BabelDOC 参数）：

```json
{
  "lang_in": "en",
  "lang_out": "zh",
  "pages": "1,2,5-10",
  "qps": 4,
  "no_dual": false,
  "no_mono": false,
  "watermark_output_mode": "watermarked",
  "max_pages_per_part": 0,
  "skip_clean": false,
  "enhance_compatibility": false,
  "disable_rich_text_translate": false,
  "split_short_lines": false,
  "short_line_split_factor": 0.8,
  "skip_scanned_detection": false,
  "ocr_workaround": false,
  "auto_enable_ocr_workaround": false,
  "auto_extract_glossary": true,
  "save_auto_extracted_glossary": false,
  "custom_system_prompt": "",
  "add_formula_placehold_hint": false,
  "pool_max_workers": 4,
  "term_pool_max_workers": 4,
  "disable_same_text_fallback": false,
  "primary_font_family": null,
  "only_include_translated_page": false
}
```

校验与约束（Phase 1）：
- `no_dual` 与 `no_mono` 不能同时为 `true`
- `qps` 必须为 `>= 1` 的整数
- `max_pages_per_part` 必须为 `>= 0` 的整数（0 表示不分片）
- `watermark_output_mode` 仅支持 `"watermarked"` / `"no_watermark"`（暂不支持 `"both"`）
- `primary_font_family` 仅支持 `"serif"` / `"sans-serif"` / `"script"`

响应：

```json
{ "job_id": "uuid", "status": "queued", "created_at": "2026-01-24T12:00:00+08:00" }
```

## 4. 进度与事件（SSE）

`GET /api/jobs/{id}/events`

统一事件结构：

```json
{
  "type": "stage_summary|progress_start|progress_update|progress_end|finish|error|heartbeat",
  "job_id": "uuid",
  "ts": "2026-01-24T12:00:00+08:00",
  "data": { ... }
}
```

`progress_update` 示例：

```json
{
  "stage": "LayoutParser",
  "stage_current": 12,
  "stage_total": 100,
  "stage_progress": 12.0,
  "overall_progress": 45.3,
  "part_index": 1,
  "total_parts": 3
}
```

`finish` 示例：

```json
{ "result_id": "uuid" }
```

`error` 示例：

```json
{ "message": "error text" }
```

### 4.1 前端队列与进度展示（约定）

- 前端需展示**当前运行任务**与**队列中的任务**
- 队列数据来自 `GET /api/queue`
- 任务进度来自 SSE（`/api/jobs/{id}/events`）
- 提供“**恢复队列**”按钮（调用 `POST /api/queue/resume` 的 `mode=all`）
- 列表项可提供“恢复此任务”入口（调用 `POST /api/queue/resume` 的 `job_ids`）

## 5. 文件列表

`GET /api/jobs/{id}/files`

```json
[
  {
    "file_id": "uuid",
    "type": "mono|dual|glossary",
    "watermark": "watermarked|no_watermark|none",
    "filename": "mono.pdf",
    "size": 12345678,
    "url": "/api/files/uuid"
  }
]
```

说明：
- 原文件保留原始文件名（如 `Kua.pdf`）  
- mono/dual 输出文件命名为 `mono.pdf` / `dual.pdf`
- glossary 输出文件命名为 `glossary.csv`（当自动术语抽取有结果且 `save_auto_extracted_glossary=true` 时生成）

## 6. 预览/下载

- `GET /api/files/{file_id}` 支持 `Range`
- 前端可直接用该 URL 预览（PDF.js）
- glossary 文件为 `text/csv`，下载名为 `{原名stem}.glossary.csv`

## 7. 重命名接口（PATCH /api/jobs/{id}）

请求体（JSON）：

```json
{
  "folder_name": "paper",
  "display_name": "Paper Title",
  "original_filename": "paper.pdf",
  "confirm": false
}
```

规则：
- 仅允许 `finished/failed/canceled` 状态
- `folder_name` / `display_name` / `original_filename` 可单独或同时修改
- 命名限制：禁止包含 `/ \\ : * ? \" < > |` 与控制字符
- `original_filename` 不能为 `mono.pdf` 或 `dual.pdf`（保留名）
- `display_name` 仅用于展示，不影响文件或文件夹
- 冲突时返回 409，并提供 `suggested_*` 名称

冲突响应示例：

```json
{
  "error": "name_conflict",
  "suggested_folder_name": "paper_20260125-011500",
  "suggested_original_filename": "paper_20260125-011500.pdf"
}
```

用户确认后再提交（`confirm=true`）。

## 8. 删除任务（DELETE /api/jobs/{id}）

说明：
- 必须提供 `confirm=true`（用于二次确认）
- `running` 任务会先触发取消并返回 `status=canceling`，需要后续再次删除
- `queued` / `finished` / `failed` / `canceled` 可直接删除（会清理 DB 与文件夹）

请求示例（带 confirm）：

```bash
curl -sSf -X DELETE "http://127.0.0.1:8000/api/jobs/{job_id}?confirm=true" | jq .
```

响应示例：

```json
{ "job_id": "uuid", "status": "deleted" }
```

若在运行中：

```json
{ "job_id": "uuid", "status": "canceling" }
```

## 9. 批量删除（POST /api/jobs/delete）

请求体：

```json
{
  "job_ids": ["uuid-1", "uuid-2"],
  "confirm": true
}
```

响应示例：

```json
{
  "deleted": ["uuid-2"],
  "skipped": [
    { "job_id": "uuid-1", "reason": "canceling" }
  ]
}
```

## 10. 性能约定

- SSE 推送频率：<= 10 次/秒
- 前端使用 rAF 合并更新
- PDF 预览必须支持 HTTP Range
