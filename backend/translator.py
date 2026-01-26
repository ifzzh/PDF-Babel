import json
from asyncio import CancelledError
import threading
from pathlib import Path
from typing import Any

from babeldoc.docvision.base_doclayout import DocLayoutModel
from babeldoc.format.pdf.high_level import do_translate
from babeldoc.format.pdf.high_level import get_translation_stage
from babeldoc.format.pdf.high_level import init as babeldoc_init
from babeldoc.format.pdf.translation_config import TranslationConfig
from babeldoc.format.pdf.translation_config import WatermarkOutputMode
from babeldoc.progress_monitor import ProgressMonitor
from babeldoc.translator.translator import OpenAITranslator
from babeldoc.translator.translator import set_translate_rate_limiter

from backend.config import Settings
from backend.events import EVENT_STORE
from backend.files import create_file_record
from backend.jobs import get_job_by_id
from backend.jobs import update_job_status

_OPENAI_COMPATIBLE_CHANNELS = {
    "openai",
    "azure-openai",
    "modelscope",
    "zhipu",
    "silicon",
    "gemini",
    "grok",
    "groq",
    "deepseek",
    "openai-liked",
    "ali-qwen-translation",
}

_DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "modelscope": "https://api-inference.modelscope.cn/v1",
    "zhipu": "https://open.bigmodel.cn/api/paas/v4",
    "silicon": "https://api.siliconflow.cn/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "grok": "https://api.x.ai/v1",
    "groq": "https://api.groq.com/openai/v1",
    "deepseek": "https://api.deepseek.com/v1",
    "ali-qwen-translation": "https://dashscope.aliyuncs.com/compatible-mode/v1",
}

_QWEN_LANG_MAP = {
    "zh": "Chinese",
    "zh-cn": "Chinese",
    "zh-hans": "Chinese",
    "zh-tw": "Chinese",
    "zh-hant": "Chinese",
    "en": "English",
    "fr": "French",
    "de": "German",
    "ja": "Japanese",
    "ko": "Korean",
    "ru": "Russian",
    "es": "Spanish",
    "it": "Italian",
}


class TranslationError(RuntimeError):
    pass


def _parse_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}


def _require_value(payload: dict[str, Any], key: str) -> Any:
    value = payload.get(key)
    if value is None or value == "":
        raise ValueError(f"missing {key}")
    return value


def _parse_watermark_mode(value: str | None) -> WatermarkOutputMode:
    if not value:
        return WatermarkOutputMode.Watermarked
    if value == WatermarkOutputMode.NoWatermark.value:
        return WatermarkOutputMode.NoWatermark
    if value == WatermarkOutputMode.Both.value:
        return WatermarkOutputMode.Both
    return WatermarkOutputMode.Watermarked


def _bool_value(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    return bool(value)


def _int_value(value: Any, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _float_value(value: Any, default: float) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _resolve_base_url(channel_id: str, credentials: dict[str, Any]) -> str | None:
    base_url = credentials.get("base_url")
    if base_url:
        return base_url
    return _DEFAULT_BASE_URLS.get(channel_id)


def _map_qwen_lang(lang: str) -> str:
    if not lang:
        return ""
    return _QWEN_LANG_MAP.get(lang.lower(), lang)


def _build_translator(
    *,
    channel_id: str,
    lang_in: str,
    lang_out: str,
    credentials: dict[str, Any],
) -> OpenAITranslator:
    if channel_id not in _OPENAI_COMPATIBLE_CHANNELS:
        raise ValueError("unsupported channel")

    api_key = _require_value(credentials, "api_key")
    model = _require_value(credentials, "model")
    base_url = _resolve_base_url(channel_id, credentials)
    if not base_url:
        raise ValueError("missing base_url")

    translator = OpenAITranslator(
        lang_in=lang_in,
        lang_out=lang_out,
        model=model,
        base_url=base_url,
        api_key=api_key,
        ignore_cache=False,
    )

    if channel_id == "ali-qwen-translation":
        domains = credentials.get("domains")
        translator.send_dashscope_header = True
        translator.extra_body["translation_options"] = {
            "source_lang": _map_qwen_lang(lang_in),
            "target_lang": _map_qwen_lang(lang_out),
            "domains": domains or "",
        }

    return translator


def _prepare_config(
    *,
    job_dir: Path,
    input_path: Path,
    lang_in: str,
    lang_out: str,
    options: dict[str, Any],
    translator: OpenAITranslator,
) -> TranslationConfig:
    pages = options.get("pages")
    qps = _int_value(options.get("qps"), 1)
    no_dual = _bool_value(options.get("no_dual"), False)
    no_mono = _bool_value(options.get("no_mono"), False)
    split_short_lines = _bool_value(options.get("split_short_lines"), False)
    short_line_split_factor = _float_value(
        options.get("short_line_split_factor"), 0.8
    )
    skip_clean = _bool_value(options.get("skip_clean"), False)
    enhance_compatibility = _bool_value(options.get("enhance_compatibility"), False)
    disable_rich_text_translate = _bool_value(
        options.get("disable_rich_text_translate"), False
    )
    skip_scanned_detection = _bool_value(
        options.get("skip_scanned_detection"), False
    )
    ocr_workaround = _bool_value(options.get("ocr_workaround"), False)
    auto_enable_ocr_workaround = _bool_value(
        options.get("auto_enable_ocr_workaround"), False
    )
    custom_system_prompt = options.get("custom_system_prompt")
    add_formula_placehold_hint = _bool_value(
        options.get("add_formula_placehold_hint"), False
    )
    disable_same_text_fallback = _bool_value(
        options.get("disable_same_text_fallback"), False
    )
    primary_font_family = options.get("primary_font_family")
    only_include_translated_page = _bool_value(
        options.get("only_include_translated_page"), False
    )
    watermark_output_mode = _parse_watermark_mode(
        options.get("watermark_output_mode")
    )

    max_pages_per_part = _int_value(options.get("max_pages_per_part"), 0)
    split_strategy = None
    if max_pages_per_part > 0:
        split_strategy = (
            TranslationConfig.create_max_pages_per_part_split_strategy(
                max_pages_per_part
            )
        )

    pool_max_workers = options.get("pool_max_workers")
    if pool_max_workers is not None:
        pool_max_workers = _int_value(pool_max_workers, 1)
    term_pool_max_workers = options.get("term_pool_max_workers")
    if term_pool_max_workers is not None:
        term_pool_max_workers = _int_value(term_pool_max_workers, 1)

    doc_layout_model = DocLayoutModel.load_onnx()

    working_dir = job_dir / "_working"
    working_dir.mkdir(parents=True, exist_ok=True)

    set_translate_rate_limiter(max(qps, 1))

    config = TranslationConfig(
        input_file=str(input_path),
        lang_in=lang_in,
        lang_out=lang_out,
        doc_layout_model=doc_layout_model,
        translator=translator,
        term_extraction_translator=translator,
        pages=pages,
        output_dir=str(job_dir),
        working_dir=str(working_dir),
        no_dual=no_dual,
        no_mono=no_mono,
        qps=max(qps, 1),
        split_short_lines=split_short_lines,
        short_line_split_factor=short_line_split_factor,
        skip_clean=skip_clean,
        enhance_compatibility=enhance_compatibility,
        disable_rich_text_translate=disable_rich_text_translate,
        skip_scanned_detection=skip_scanned_detection,
        ocr_workaround=ocr_workaround,
        auto_enable_ocr_workaround=auto_enable_ocr_workaround,
        custom_system_prompt=custom_system_prompt,
        add_formula_placehold_hint=add_formula_placehold_hint,
        split_strategy=split_strategy,
        pool_max_workers=pool_max_workers,
        term_pool_max_workers=term_pool_max_workers,
        disable_same_text_fallback=disable_same_text_fallback,
        primary_font_family=primary_font_family,
        only_include_translated_page=only_include_translated_page,
        watermark_output_mode=watermark_output_mode,
    )

    getattr(doc_layout_model, "init_font_mapper", lambda _config: None)(config)
    return config


def _move_result(path: Path | None, target: Path) -> Path | None:
    if path is None:
        return None
    src = Path(path)
    if not src.exists():
        return None
    if src.resolve() == target.resolve():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    src.replace(target)
    return target


def run_translation_job(
    settings: Settings,
    storage: dict[str, Path],
    job_id: str,
) -> dict[str, Any]:
    record = get_job_by_id(settings, job_id)
    if record is None:
        raise LookupError("job not found")
    if record.status != "queued":
        raise ValueError("job not in queued status")

    update_job_status(settings, record.id, "running")
    cancel_event = threading.Event()
    EVENT_STORE.set_cancel_event(record.id, cancel_event)

    try:
        options = _parse_json(record.options_json)
        source = _parse_json(record.source_json)
        if source.get("mode") != "custom":
            raise ValueError("platform source not supported")

        channel_id = _require_value(source, "channel_id")
        credentials = source.get("credentials") or {}

        lang_in = _require_value(options, "lang_in")
        lang_out = _require_value(options, "lang_out")

        job_dir = storage["jobs"] / record.folder_name
        input_path = job_dir / record.original_filename
        if not input_path.exists():
            raise FileNotFoundError("input file missing")

        translator = _build_translator(
            channel_id=channel_id,
            lang_in=lang_in,
            lang_out=lang_out,
            credentials=credentials,
        )
        config = _prepare_config(
            job_dir=job_dir,
            input_path=input_path,
            lang_in=lang_in,
            lang_out=lang_out,
            options=options,
            translator=translator,
        )
        def _progress_callback(**kwargs):
            event_type = kwargs.pop("type", "progress_update")
            EVENT_STORE.append_event(record.id, event_type, kwargs)

        babeldoc_init()
        def _finish_callback(**_kwargs):
            return

        with ProgressMonitor(
            get_translation_stage(config),
            progress_change_callback=_progress_callback,
            finish_callback=_finish_callback,
            cancel_event=cancel_event,
            report_interval=config.report_interval,
        ) as pm:
            result = do_translate(pm, config)
    except CancelledError:
        update_job_status(settings, record.id, "canceled", error="canceled")
        EVENT_STORE.append_event(record.id, "error", {"error": "canceled"})
        return {"job_id": record.id, "status": "canceled", "files": []}
    except Exception as exc:
        update_job_status(settings, record.id, "failed", error=str(exc))
        if isinstance(exc, (ValueError, FileNotFoundError)):
            raise
        EVENT_STORE.append_event(record.id, "error", {"error": str(exc)})
        raise TranslationError(str(exc)) from exc

    watermark_mode = _parse_watermark_mode(options.get("watermark_output_mode"))
    watermark_label = (
        "none"
        if watermark_mode == WatermarkOutputMode.NoWatermark
        else "watermarked"
    )

    if watermark_mode == WatermarkOutputMode.NoWatermark:
        mono_path = result.no_watermark_mono_pdf_path or result.mono_pdf_path
        dual_path = result.no_watermark_dual_pdf_path or result.dual_pdf_path
    else:
        mono_path = result.mono_pdf_path
        dual_path = result.dual_pdf_path

    files_created = []
    mono_target = _move_result(mono_path, job_dir / "mono.pdf")
    if mono_target:
        files_created.append(
            create_file_record(
                settings,
                job_id=record.id,
                file_type="mono",
                watermark=watermark_label,
                filename="mono.pdf",
                path=mono_target,
            )
        )

    dual_target = _move_result(dual_path, job_dir / "dual.pdf")
    if dual_target:
        files_created.append(
            create_file_record(
                settings,
                job_id=record.id,
                file_type="dual",
                watermark=watermark_label,
                filename="dual.pdf",
                path=dual_target,
            )
        )

    if not files_created:
        update_job_status(
            settings, record.id, "failed", error="no output files generated"
        )
        raise TranslationError("no output files generated")

    update_job_status(settings, record.id, "finished")
    EVENT_STORE.append_event(record.id, "finish", {"status": "finished"})

    return {
        "job_id": record.id,
        "status": "finished",
        "files": [
            {
                "file_id": f.id,
                "type": f.type,
                "watermark": f.watermark,
                "filename": f.filename,
                "size": f.size,
            }
            for f in files_created
        ],
    }
