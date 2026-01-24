# 前端功能需求 v0.1（给 Gemini）

> 目标：Vue 3 前端对接 FastAPI 后端，完成 PDF 翻译任务创建、实时进度、结果预览。
> 约束：遵循 `docs/design/frontend-backend-contract-v0.1.md` 中“不可变约定”。

## 1. 页面与功能清单（必须实现）

1) **文件上传**
- 支持拖拽与点击上传 PDF
- 限制文件类型：`.pdf`
- 单文件优先（MVP），可扩展多文件

2) **翻译选项表单**
- 语言：`lang_in` / `lang_out`
- 页码：`pages`（文本输入，留空表示全部）
- 输出选项：单语/双语/水印模式
- 高级选项（折叠区）：
  - `skip_clean` / `enhance_compatibility` / `split_short_lines` / `short_line_split_factor`
  - `skip_scanned_detection` / `ocr_workaround` / `auto_enable_ocr_workaround`
  - `auto_extract_glossary` / `custom_system_prompt`
  - `pool_max_workers` / `term_pool_max_workers`

3) **翻译能力来源（渠道选择）**
- 采用两页签或双按钮：**平台提供** / **自定义**
- 渠道数据来自 `GET /api/channels`
- **平台提供**：仅展示渠道名称，不显示 URL/Key/Model
- **自定义**：选择渠道后显示字段（由后端返回 `fields` 定义）
- 必须遵守：
  - `enabled=false`：灰显且不可选
  - `visible=false`：不展示

4) **任务控制**
- “开始翻译”按钮：调用 `POST /api/jobs`
- “取消”按钮：调用 `POST /api/jobs/{id}/cancel`

5) **实时进度（SSE）**
- 连接 `GET /api/jobs/{id}/events`
- 显示：当前阶段、阶段进度、总进度
- 事件类型必须兼容：`progress_start/progress_update/progress_end/finish/error`
- 建议前端做 UI 节流（rAF 合并更新）

6) **结果列表与预览**
- `GET /api/jobs/{id}/files` 获取结果列表
- 展示：文件名、类型、大小、下载按钮
- 预览：选中文件后用 PDF.js 预览
- 预览 URL 使用 `/api/files/{file_id}`（必须支持 Range）

7) **错误处理与状态反馈**
- 上传失败、翻译失败、SSE 中断等必须提示
- 任务状态展示：`queued | running | finished | failed | canceled`

8) **历史文件夹页面（持久化结果）**
- 通过按钮从首页跳转到“历史/文件夹”页面
- 调用 `GET /api/jobs` 获取历史任务
- 每条任务展示：文件夹名（由“时间 + 文件名”组成）、状态、创建时间、是否有 mono/dual
- 点击条目进入详情或直接加载 `/api/jobs/{id}/files` 展示与预览

---

## 2. 前端状态模型（建议）

```ts
interface JobState {
  jobId?: string;
  status: 'idle' | 'queued' | 'running' | 'finished' | 'failed' | 'canceled';
  overallProgress: number; // 0-100
  currentStage?: string;
  error?: string;
}

interface ChannelDef {
  id: string;
  label: string;
  enabled?: boolean;
  disabled_reason?: string;
  visible?: boolean;
  openai_compatible?: boolean;
  fields?: Array<{ key: string; label: string; required: boolean; secret: boolean }>;
}
```

---

## 3. UI 结构建议（组件）

- `UploadCard`
- `OptionsForm`
- `SourceSelector`（平台/自定义 + 渠道字段动态渲染）
- `ProgressPanel`
- `ResultList`
- `PdfPreview`

---

## 4. 性能要求（必须）

- SSE 更新频率控制在 **<=10 次/秒**
- 进度 UI 使用 rAF 合并更新
- PDF 预览使用 pdf.js worker，避免主线程卡顿
- 仅渲染可视页或单页（避免长文档一次性渲染）

---

## 5. 调用流程（简化版）

1) 启动页面 -> `GET /api/channels`
2) 选择渠道 + 填表 -> 上传 PDF -> `POST /api/jobs`
3) SSE 监听 `/api/jobs/{id}/events`
4) `finish` 后拉取 `/api/jobs/{id}/files`
5) 选择结果 -> `/api/files/{file_id}` 预览
6) 首页按钮 -> 历史页面 -> `GET /api/jobs` -> 列表 -> 进入详情

---

## 6. 不可变约定（必须遵循）

详见：`docs/design/frontend-backend-contract-v0.1.md` -> **0. 不可变约定**
