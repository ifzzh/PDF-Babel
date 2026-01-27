# Options 覆盖对照表

> 版本：v0.4
> 说明：仅统计“翻译 options（/api/jobs 的 options 字段）”相关能力，不含渠道/凭据与服务端运行参数。
> 标记：`✓` 表示已支持，`—` 表示未支持。

## 基础

| 能力（options key） | Babeldoc | 后端 | 前端 |
|---|---|---|---|
| `lang_in` | ✓ | ✓ | ✓ |
| `lang_out` | ✓ | ✓ | ✓ |
| `pages` | ✓ | ✓ | ✓ |
| `min_text_length` | ✓ | — | — |

## 输出与水印

| 能力（options key） | Babeldoc | 后端 | 前端 |
|---|---|---|---|
| `no_dual` | ✓ | ✓ | — |
| `no_mono` | ✓ | ✓ | — |
| `use_alternating_pages_dual` | ✓ | — | — |
| `watermark_output_mode` | ✓ | ✓ | — |
| `only_include_translated_page` | ✓ | ✓ | — |
| `dual_translate_first` | ✓ | — | — |

## 性能与分片

| 能力（options key） | Babeldoc | 后端 | 前端 |
|---|---|---|---|
| `qps` | ✓ | ✓ | — |
| `max_pages_per_part` | ✓ | ✓ | — |
| `pool_max_workers` | ✓ | ✓ | ✓ |
| `term_pool_max_workers` | ✓ | ✓ | ✓ |
| `report_interval` | ✓ | — | — |

## 版式/兼容与渲染

| 能力（options key） | Babeldoc | 后端 | 前端 |
|---|---|---|---|
| `split_short_lines` | ✓ | ✓ | ✓ |
| `short_line_split_factor` | ✓ | ✓ | ✓ |
| `skip_clean` | ✓ | ✓ | ✓ |
| `enhance_compatibility` | ✓ | ✓ | ✓ |
| `disable_rich_text_translate` | ✓ | ✓ | — |
| `disable_same_text_fallback` | ✓ | ✓ | — |
| `translate_table_text` | ✓ | — | — |
| `show_char_box` | ✓ | — | — |
| `disable_graphic_element_process` | ✓ | — | — |
| `merge_alternating_line_numbers` | ✓ | — | — |
| `skip_translation` | ✓ | — | — |
| `skip_form_render` | ✓ | — | — |
| `skip_curve_render` | ✓ | — | — |
| `only_parse_generate_pdf` | ✓ | — | — |
| `remove_non_formula_lines` | ✓ | — | — |
| `non_formula_line_iou_threshold` | ✓ | — | — |
| `figure_table_protection_threshold` | ✓ | — | — |
| `skip_formula_offset_calculation` | ✓ | — | — |

## 扫描/OCR

| 能力（options key） | Babeldoc | 后端 | 前端 |
|---|---|---|---|
| `skip_scanned_detection` | ✓ | ✓ | ✓ |
| `ocr_workaround` | ✓ | ✓ | ✓ |
| `auto_enable_ocr_workaround` | ✓ | ✓ | ✓ |

## 术语与提示词

| 能力（options key） | Babeldoc | 后端 | 前端 |
|---|---|---|---|
| `custom_system_prompt` | ✓ | ✓ | ✓ |
| `auto_extract_glossary` | ✓ | — | ✓ |
| `save_auto_extracted_glossary` | ✓ | — | — |

## 公式与字体

| 能力（options key） | Babeldoc | 后端 | 前端 |
|---|---|---|---|
| `add_formula_placehold_hint` | ✓ | ✓ | — |
| `primary_font_family` | ✓ | ✓ | — |
| `formular_font_pattern` | ✓ | — | — |
| `formular_char_pattern` | ✓ | — | — |

## 备注

- 前端有但后端未接入：`auto_extract_glossary`
- 后端支持但前端未露出：`qps`、`no_dual`、`no_mono`、`disable_rich_text_translate`、`add_formula_placehold_hint`、`disable_same_text_fallback`、`primary_font_family`、`only_include_translated_page`、`watermark_output_mode`、`max_pages_per_part`
- babeldoc 支持但后端未接入：见“版式/兼容与渲染”与“术语/提示词”中标记为 `—` 的条目
