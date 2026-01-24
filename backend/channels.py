from typing import Any


def _field(key: str, label: str, required: bool, secret: bool) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "required": required,
        "secret": secret,
    }


def get_channels() -> dict[str, list[dict[str, Any]]]:
    platform = [
        {
            "id": "deepseek",
            "label": "DeepSeek",
            "enabled": False,
            "disabled_reason": "暂未开放",
            "visible": True,
        }
    ]

    custom = [
        {
            "id": "openai",
            "label": "OpenAI",
            "openai_compatible": True,
            "enabled": True,
            "visible": True,
            "fields": [
                _field("base_url", "Base URL", False, False),
                _field("api_key", "API Key", True, True),
                _field("model", "Model", True, False),
            ],
        },
        {
            "id": "azure-openai",
            "label": "AzureOpenAI",
            "openai_compatible": True,
            "enabled": True,
            "visible": True,
            "fields": [
                _field("base_url", "Base URL", True, False),
                _field("api_key", "API Key", True, True),
                _field("model", "Model", True, False),
                _field("api_version", "API Version", False, False),
            ],
        },
        {
            "id": "modelscope",
            "label": "ModelScope",
            "openai_compatible": True,
            "enabled": True,
            "visible": True,
            "fields": [
                _field("base_url", "Base URL", False, False),
                _field("api_key", "API Key", True, True),
                _field("model", "Model", True, False),
            ],
        },
        {
            "id": "zhipu",
            "label": "Zhipu",
            "openai_compatible": True,
            "enabled": True,
            "visible": True,
            "fields": [
                _field("api_key", "API Key", True, True),
                _field("model", "Model", True, False),
            ],
        },
        {
            "id": "silicon",
            "label": "Silicon",
            "openai_compatible": True,
            "enabled": True,
            "visible": True,
            "fields": [
                _field("api_key", "API Key", True, True),
                _field("model", "Model", True, False),
            ],
        },
        {
            "id": "gemini",
            "label": "Gemini",
            "openai_compatible": True,
            "enabled": True,
            "visible": True,
            "fields": [
                _field("api_key", "API Key", True, True),
                _field("model", "Model", True, False),
            ],
        },
        {
            "id": "grok",
            "label": "Grok",
            "openai_compatible": True,
            "enabled": True,
            "visible": True,
            "fields": [
                _field("api_key", "API Key", True, True),
                _field("model", "Model", True, False),
            ],
        },
        {
            "id": "groq",
            "label": "Groq",
            "openai_compatible": True,
            "enabled": True,
            "visible": True,
            "fields": [
                _field("api_key", "API Key", True, True),
                _field("model", "Model", True, False),
            ],
        },
        {
            "id": "deepseek",
            "label": "DeepSeek",
            "openai_compatible": True,
            "enabled": True,
            "visible": True,
            "fields": [
                _field("api_key", "API Key", True, True),
                _field("model", "Model", True, False),
            ],
        },
        {
            "id": "openai-liked",
            "label": "OpenAI-liked",
            "openai_compatible": True,
            "enabled": True,
            "visible": True,
            "fields": [
                _field("base_url", "Base URL", True, False),
                _field("api_key", "API Key", True, True),
                _field("model", "Model", True, False),
            ],
        },
        {
            "id": "ali-qwen-translation",
            "label": "Ali Qwen-Translation",
            "openai_compatible": True,
            "enabled": True,
            "visible": True,
            "fields": [
                _field("api_key", "API Key", True, True),
                _field("model", "Model", True, False),
                _field("domains", "Domains", False, False),
            ],
        },
    ]

    unsupported = [
        {"id": "google", "label": "Google", "reason": "非OpenAI兼容", "visible": True},
        {"id": "bing", "label": "Bing", "reason": "非OpenAI兼容", "visible": True},
        {"id": "deepl", "label": "DeepL", "reason": "非OpenAI兼容", "visible": True},
        {"id": "deeplx", "label": "DeepLX", "reason": "非OpenAI兼容", "visible": True},
        {
            "id": "azure",
            "label": "Azure Translator",
            "reason": "非OpenAI兼容",
            "visible": True,
        },
        {
            "id": "tencent",
            "label": "Tencent",
            "reason": "非OpenAI兼容",
            "visible": True,
        },
        {
            "id": "argos",
            "label": "Argos Translate",
            "reason": "非OpenAI兼容",
            "visible": True,
        },
        {"id": "ollama", "label": "Ollama", "reason": "非OpenAI兼容", "visible": True},
        {
            "id": "xinference",
            "label": "Xinference",
            "reason": "非OpenAI兼容",
            "visible": True,
        },
        {"id": "dify", "label": "Dify", "reason": "非OpenAI兼容", "visible": True},
        {
            "id": "anythingllm",
            "label": "AnythingLLM",
            "reason": "非OpenAI兼容",
            "visible": True,
        },
    ]

    return {"platform": platform, "custom": custom, "unsupported": unsupported}
