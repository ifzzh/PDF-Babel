# Options 覆盖对照表

> 版本：v0.7
> 说明：仅统计“翻译 options（/api/jobs 的 options 字段）”相关能力，不含渠道/凭据与服务端运行参数。
> 标记：`✓` 表示已支持，`—` 表示未支持。
> 默认值：以当前系统默认值为准，前后端应保持一致。

## 基础

| 能力（options key） | 说明 | 默认值 | Babeldoc | 后端 | 前端 |
|---|---|---|---|---|---|
| `lang_in` | 源语言代码（如 en） | `en` | ✓ | ✓ | ✓ |
| `lang_out` | 目标语言代码（如 zh） | `zh` | ✓ | ✓ | ✓ |
| `pages` | 指定翻译页码范围，格式如 `1,2,1-,-3,3-5` | 全部（空/不传） | ✓ | ✓ | ✓ |
| `min_text_length` | 最小翻译文本长度，低于该长度不翻译 | `5` | ✓ | — | — |

## 输出与水印

| 能力（options key） | 说明 | 默认值 | Babeldoc | 后端 | 前端 |
|---|---|---|---|---|---|
| `no_dual` | 不输出双语 PDF | `false` | ✓ | ✓ | ✓ |
| `no_mono` | 不输出单语 PDF | `false` | ✓ | ✓ | ✓ |
| `use_alternating_pages_dual` | 双语 PDF 使用“原文/译文交替页”模式 | `false` | ✓ | — | — |
| `watermark_output_mode` | 水印输出模式：`watermarked` / `no_watermark` / `both` | `no_watermark` | ✓ | ✓ | ✓ |
| `only_include_translated_page` | 仅输出翻译页（仅在指定 `pages` 时生效） | `false` | ✓ | ✓ | ✓ |
| `dual_translate_first` | 双语模式下译文页在前 | `false` | ✓ | — | — |

## 性能与分片

| 能力（options key） | 说明 | 默认值 | Babeldoc | 后端 | 前端 |
|---|---|---|---|---|---|
| `qps` | 翻译服务 QPS 限制（速率） | `4` | ✓ | ✓ | — |
| `max_pages_per_part` | 分片翻译时每片最大页数（不设则不分片） | 不分片（空/不传） | ✓ | ✓ | — |
| `pool_max_workers` | 内部任务池最大线程数（默认随 QPS） | 自动（跟随 `qps`） | ✓ | ✓ | ✓ |
| `term_pool_max_workers` | 术语抽取线程池最大线程数（默认随 pool_max_workers） | 自动（跟随 `pool_max_workers`） | ✓ | ✓ | ✓ |
| `report_interval` | 进度回报间隔（秒） | `0.1` | ✓ | — | — |

## 版式/兼容与渲染

| 能力（options key） | 说明 | 默认值 | Babeldoc | 后端 | 前端 |
|---|---|---|---|---|---|
| `split_short_lines` | 强制拆分短行（可能影响排版/稳定性） | `false` | ✓ | ✓ | ✓ |
| `short_line_split_factor` | 短行拆分阈值系数（页内行长中位数 × 系数） | `0.8` | ✓ | ✓ | ✓ |
| `skip_clean` | 跳过 PDF 清理步骤 | `false` | ✓ | ✓ | ✓ |
| `enhance_compatibility` | 兼容性增强（等同 `skip_clean` + `dual_translate_first` + `disable_rich_text_translate`） | `false` | ✓ | ✓ | ✓ |
| `disable_rich_text_translate` | 禁用富文本翻译（提高兼容性） | `false` | ✓ | ✓ | — |
| `disable_same_text_fallback` | 禁用“译文等于原文时回退”逻辑 | `false` | ✓ | ✓ | — |
| `translate_table_text` | 翻译表格文字（实验性） | `false` | ✓ | — | — |
| `show_char_box` | 显示字符框（调试） | `false` | ✓ | — | — |
| `disable_graphic_element_process` | 禁用图形元素处理 | `false` | ✓ | — | — |
| `merge_alternating_line_numbers` | 合并交替行号布局（默认开启） | `true` | ✓ | — | — |
| `skip_translation` | 跳过翻译步骤 | `false` | ✓ | — | — |
| `skip_form_render` | 跳过表单渲染 | `false` | ✓ | — | — |
| `skip_curve_render` | 跳过曲线渲染 | `false` | ✓ | — | — |
| `only_parse_generate_pdf` | 只解析并生成 PDF，不做翻译 | `false` | ✓ | — | — |
| `remove_non_formula_lines` | 移除非公式线条（保护图表线） | `false` | ✓ | — | — |
| `non_formula_line_iou_threshold` | 非公式线条判定 IoU 阈值（越高越保守） | `0.9` | ✓ | — | — |
| `figure_table_protection_threshold` | 图表区域保护 IoU 阈值 | `0.9` | ✓ | — | — |
| `skip_formula_offset_calculation` | 跳过公式偏移计算 | `false` | ✓ | — | — |

## 扫描/OCR

| 能力（options key） | 说明 | 默认值 | Babeldoc | 后端 | 前端 |
|---|---|---|---|---|---|
| `skip_scanned_detection` | 跳过扫描检测（非扫描文档更快） | `false` | ✓ | ✓ | ✓ |
| `ocr_workaround` | OCR workaround（实验性，给文本加背景） | `false` | ✓ | ✓ | ✓ |
| `auto_enable_ocr_workaround` | 自动启用 OCR workaround（重扫描文档） | `false` | ✓ | ✓ | ✓ |

## 术语与提示词

| 能力（options key） | 说明 | 默认值 | Babeldoc | 后端 | 前端 |
|---|---|---|---|---|---|
| `custom_system_prompt` | 自定义系统提示词 | 空（不传） | ✓ | ✓ | ✓ |
| `auto_extract_glossary` | 自动抽取术语 | `true` | ✓ | ✓ | ✓ |
| `save_auto_extracted_glossary` | 保存自动术语 CSV 到输出目录 | `true` | ✓ | ✓ | ✓ |

## 公式与字体

| 能力（options key） | 说明 | 默认值 | Babeldoc | 后端 | 前端 |
|---|---|---|---|---|---|
| `add_formula_placehold_hint` | 添加公式占位提示（不推荐，可能影响质量） | `false` | ✓ | ✓ | — |
| `primary_font_family` | 覆盖译文主字体族（`serif` / `sans-serif` / `script`） | 空（自动） | ✓ | ✓ | — |
| `formular_font_pattern` | 公式字体匹配模式 | 空（不传） | ✓ | — | — |
| `formular_char_pattern` | 公式字符匹配模式 | 空（不传） | ✓ | — | — |

## 备注

- 前端已发送但未开放配置：`pool_max_workers`、`term_pool_max_workers`
- 后端支持但前端未露出：`qps`、`disable_rich_text_translate`、`add_formula_placehold_hint`、`disable_same_text_fallback`、`primary_font_family`、`max_pages_per_part`
- babeldoc 支持但后端未接入：见“版式/兼容与渲染”与“公式与字体”中标记为 `—` 的条目
