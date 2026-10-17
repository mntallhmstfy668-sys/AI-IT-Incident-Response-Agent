import json


def json_instruction(model_cls) -> str:
    """Instruction text asking the model for JSON matching a Pydantic model."""
    schema = json.dumps(model_cls.model_json_schema())
    return (
        "\n\nReturn ONLY one valid JSON object. No markdown, no code fences, "
        "no extra text before or after it. It must match this JSON schema:\n"
        + schema
    )


def safe_json(text):
    try:
        return json.loads(text)
    except Exception:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except Exception:
                pass
    return None


def parse_model(output, model_cls):
    if isinstance(output, model_cls):
        return output
    data = safe_json(str(output))
    if data is None:
        raise ValueError(
            f"Model did not return valid JSON for {model_cls.__name__}."
        )
    return model_cls.model_validate(data) 