"""외부 입력(LLM 출력, 웹 페이지)을 DB에 넣기 전에 정리한다."""

import re
from typing import Any

# PostgreSQL은 NUL(\x00)을 TEXT/JSONB에 저장하지 못한다. 줄바꿈·탭을 뺀 제어 문자와 서로게이트를 지운다.
_INVALID = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\ud800-\udfff]")


def clean_text(value: str) -> str:
    return _INVALID.sub("", value)


def clean_optional(value: str | None) -> str | None:
    return clean_text(value) if value is not None else None


def clean_deep(value: Any) -> Any:
    """dict/list 안의 문자열까지 모두 정리한다."""
    if isinstance(value, str):
        return clean_text(value)
    if isinstance(value, list):
        return [clean_deep(v) for v in value]
    if isinstance(value, dict):
        return {k: clean_deep(v) for k, v in value.items()}
    return value


_LITERAL_UNICODE_ESCAPE = re.compile(r"\\u([0-9a-fA-F]{4})")


def clean_query(value: str) -> str:
    """모델이 검색어를 `\\uc54c`처럼 이스케이프 문자열로 보낼 때가 있어 되돌린 뒤 정리한다."""
    decoded = _LITERAL_UNICODE_ESCAPE.sub(lambda m: chr(int(m.group(1), 16)), value)
    return " ".join(clean_text(decoded).split())
