"""토론 전체에서 공통 번호를 쓰는 출처 레지스트리."""

from typing import Any

from app.search.exa import SearchHit

EXCERPT_CHARS = 300


def _normalize_url(url: str) -> str:
    return url.strip().rstrip("/")


def register_hits(
    sources: list[dict[str, Any]], hits: list[SearchHit]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[tuple[int, SearchHit]]]:
    """검색 결과를 레지스트리에 등록한다.

    반환값: (갱신된 전체 출처, 새로 추가된 출처, (번호, 검색 결과) 목록)
    이미 등록된 URL은 기존 번호를 재사용한다.
    """
    all_sources = list(sources)
    by_url = {_normalize_url(s["url"]): s["number"] for s in all_sources}
    next_number = max((s["number"] for s in all_sources), default=0) + 1
    added: list[dict[str, Any]] = []
    numbered: list[tuple[int, SearchHit]] = []

    for hit in hits:
        key = _normalize_url(hit.url)
        number = by_url.get(key)
        if number is None:
            number = next_number
            next_number += 1
            by_url[key] = number
            entry = {
                "number": number,
                "url": hit.url,
                "title": hit.title,
                "published_date": hit.published_date,
                "author": hit.author,
                "excerpt": hit.text[:EXCERPT_CHARS],
            }
            all_sources.append(entry)
            added.append(entry)
        numbered.append((number, hit))

    return all_sources, added, numbered


def format_hits_for_model(numbered: list[tuple[int, SearchHit]]) -> str:
    if not numbered:
        return "검색 결과가 없습니다. 이 근거로는 주장할 수 없으니 다른 검색어로 찾거나 다른 주장을 선택하세요."
    blocks = []
    for number, hit in numbered:
        meta = " / ".join(x for x in [hit.published_date and hit.published_date[:10], hit.author] if x)
        header = f"[{number}] {hit.title}" + (f" ({meta})" if meta else "")
        blocks.append(f"{header}\nURL: {hit.url}\n{hit.text}")
    return "\n\n---\n\n".join(blocks)


def format_source_index(sources: list[dict[str, Any]]) -> str:
    if not sources:
        return "(아직 등록된 출처 없음)"
    return "\n".join(f"[{s['number']}] {s['title']} — {s['url']}" for s in sources)
