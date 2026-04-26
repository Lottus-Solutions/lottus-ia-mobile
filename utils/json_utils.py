import json
import re
from typing import Any


JSON_ARRAY_RE = re.compile(r"\[.*\]", re.DOTALL)


def extract_json_array(text: str) -> list[dict[str, Any]]:
    if not text:
        return []

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass

    match = JSON_ARRAY_RE.search(text)
    if not match:
        return []

    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []
