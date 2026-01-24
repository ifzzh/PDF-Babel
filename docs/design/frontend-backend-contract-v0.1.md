# 前后端契约 v0.1

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

7) **平台提供渠道 v0.1 固定**  
   - 仅 **DeepSeek**，且 `enabled=false`（灰显不可选）

8) **时间与时区固定**  
   - 所有时间字段（`created_at` / `updated_at` / `ts`）使用北京时间（UTC+08:00）  
   - 格式统一为 ISO 8601（示例：`2026-01-24T12:00:00+08:00`）

9) **持久化存储根目录固定**  
   - 根目录固定为：`/mnt/raid1/babeldoc-data`  
   - 结果文件夹均创建在该目录下

如需调整上述任一条，必须升级版本号（例如 v0.2）并同步前后端变更。

## 1. 能力来源（翻译渠道）

前端提供两种模式：

- **平台提供**：仅显示渠道名称，隐藏 URL/Key/Model 等字段（当前仅展示 DeepSeek，置灰不可选）
- **自定义**：选择渠道后，显示该渠道所需字段

### 1.0 平台提供策略 v0.1

- 仅预置 **DeepSeek**，但 **不可选**（前端灰显）
- `GET /api/channels` 会返回 `enabled=false` 与 `disabled_reason`
- 前端需据此禁用点击，并显示原因提示（例如“暂未开放”）

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
- `GET /api/jobs/{id}`：查询任务状态/进度
- `GET /api/jobs/{id}/events`：SSE 实时进度事件
- `GET /api/jobs/{id}/files`：获取输出文件列表
- `GET /api/files/{file_id}`：下载/预览 PDF（支持 Range）
- `POST /api/jobs/{id}/cancel`：取消任务
- `GET /api/channels`：获取渠道定义（平台/自定义/不支持）
 
### 2.2 可选扩展接口（v0.1 推荐）

- `GET /api/jobs`：查询历史任务列表（用于“历史/文件夹”页面）

响应示例：

```json
{
  "items": [
    {
      "job_id": "uuid",
      "folder_name": "paper",
      "created_at": "2026-01-24T12:00:00+08:00",
      "status": "finished",
      "has_mono": true,
      "has_dual": true
    }
  ],
  "total": 1
}
```

说明：
- `folder_name` 为后端生成的展示字符串，规则：`{原文件名stem}`  
- 若同名冲突，后端可追加短后缀，例如 `paper_a1b2`  
- 前端只展示，不做解析与改写

### 2.1 渠道定义（/api/channels）

响应示例：

```json
{
  "platform": [
    {
      "id": "deepseek",
      "label": "DeepSeek",
      "enabled": false,
      "disabled_reason": "暂未开放",
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
  "custom_system_prompt": "",
  "add_formula_placehold_hint": false,
  "pool_max_workers": 4,
  "term_pool_max_workers": 4,
  "disable_same_text_fallback": false,
  "primary_font_family": null,
  "only_include_translated_page": false
}
```

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

## 5. 文件列表

`GET /api/jobs/{id}/files`

```json
[
  {
    "file_id": "uuid",
    "type": "mono|dual|glossary",
    "watermark": "watermarked|no_watermark|none",
    "filename": "paper.zh.mono.pdf",
    "size": 12345678,
    "url": "/api/files/uuid"
  }
]
```

## 6. 预览/下载

- `GET /api/files/{file_id}` 支持 `Range`
- 前端可直接用该 URL 预览（PDF.js）

## 7. 性能约定

- SSE 推送频率：<= 10 次/秒
- 前端使用 rAF 合并更新
- PDF 预览必须支持 HTTP Range
