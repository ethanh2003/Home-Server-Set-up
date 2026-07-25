from __future__ import annotations

import httpx


def check_ollama(base_url: str, model: str, timeout: float = 3.0) -> dict[str, object]:
    try:
        response = httpx.get(f"{base_url.rstrip('/')}/api/tags", timeout=timeout)
        response.raise_for_status()
        models = response.json().get("models", [])
        names = {item.get("name", "").split(":")[0] for item in models}
        return {
            "ok": model.split(":")[0] in names or bool(models),
            "base_url": base_url,
            "model": model,
            "available_models": sorted(name for name in names if name),
        }
    except Exception as exc:
        return {"ok": False, "base_url": base_url, "model": model, "error": str(exc)}
