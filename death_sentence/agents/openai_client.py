from __future__ import annotations

import json
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape
from openai import OpenAI

from .schemas import ComposeResponse
from .settings import settings


def _render_system_prompt(scents: Dict[str, Any]) -> str:
    env = Environment(
        loader=FileSystemLoader(settings.prompts_dir),
        autoescape=select_autoescape(enabled_extensions=("j2",)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("system_prompt.j2")
    scents_json = json.dumps(scents, ensure_ascii=False, indent=4)
    return template.render(scents_json=scents_json)


def _build_schema(scents: Dict[str, Any]) -> Dict[str, Any]:
    # Kept for reference if switching back to json_schema; not used by parse()
    scent_names = list(scents.keys())
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "scent_sequence": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "scent_name": {"type": "string", "enum": scent_names},
                        "scent_duration": {"type": "integer", "minimum": 1, "maximum": 30},
                    },
                    "required": ["scent_name", "scent_duration"],
                },
            },
            "justification": {"type": "string"},
        },
        "required": ["scent_sequence", "justification"],
    }


def compose_with_openai(sentence: str, scents: Dict[str, Any]) -> ComposeResponse:
    system_prompt = _render_system_prompt(scents)
    client = OpenAI(api_key=settings.openai_api_key)

    # Use Responses API structured parsing into a Pydantic model
    try:
        response = client.responses.parse(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": sentence},
            ],
            text_format=ComposeResponse,
        )
        # New SDKs expose the parsed object directly
        if hasattr(response, "output_parsed") and response.output_parsed is not None:
            parsed = response.output_parsed
            # Ensure it's a Pydantic model instance
            if isinstance(parsed, ComposeResponse):
                return parsed
            # If SDK returns dict instead
            return ComposeResponse.model_validate(parsed)
        # Fallback: try output_text
        if hasattr(response, "output_text") and response.output_text:
            return ComposeResponse.model_validate_json(response.output_text)
    except Exception:
        # Fall back to a json_schema flow for older SDKs
        schema = _build_schema(scents)
        legacy = client.responses.create(
            model=settings.openai_model,
            instructions=system_prompt,
            input=sentence,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "ScentSequence",
                    "schema": schema,
                    "strict": True,
                },
            },
        )
        raw_text = getattr(legacy, "output_text", None)
        if not raw_text:
            try:
                raw_text = legacy.output[0].content[0].text  # type: ignore[index]
            except Exception:
                raw_text = str(legacy)
        return ComposeResponse.model_validate_json(raw_text)

