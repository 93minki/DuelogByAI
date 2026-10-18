"""발언 본문의 [n] 출처 표기를 검증하고 정리한다."""

import re

# [1], [1, 2], [1,2,3] 형태
_CITATION_GROUP = re.compile(r"\[\s*(\d+(?:\s*[,，]\s*\d+)*)\s*\]")
_SPACE_BEFORE_PUNCT = re.compile(r"[ \t]+([.,!?。])")
_MULTI_SPACE = re.compile(r"[ \t]{2,}")


def clean_citations(text: str, valid_numbers: set[int]) -> tuple[str, list[int]]:
    """레지스트리에 없는 번호를 제거하고 `[1, 2]`를 `[1][2]`로 정규화한다.

    반환값: (정리된 본문, 실제로 인용된 유효 번호 목록(등장 순))
    """
    used: list[int] = []

    def replace(match: re.Match[str]) -> str:
        numbers = [int(n) for n in re.split(r"\s*[,，]\s*", match.group(1))]
        kept = []
        for n in numbers:
            if n in valid_numbers and n not in kept:
                kept.append(n)
                if n not in used:
                    used.append(n)
        return "".join(f"[{n}]" for n in kept)

    cleaned = _CITATION_GROUP.sub(replace, text)
    cleaned = _SPACE_BEFORE_PUNCT.sub(r"\1", cleaned)
    cleaned = _MULTI_SPACE.sub(" ", cleaned)
    return cleaned.strip(), used
