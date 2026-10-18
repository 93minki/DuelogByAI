from dataclasses import dataclass

from exa_py import AsyncExa

# 근거로 쓰지 않을 블로그·커뮤니티 도메인 (나무위키는 허용)
EXCLUDED_DOMAINS = [
    # 블로그
    "blog.naver.com",
    "m.blog.naver.com",
    "tistory.com",
    "brunch.co.kr",
    "velog.io",
    "medium.com",
    "blog.daum.net",
    "egloos.com",
    "blogspot.com",
    "wordpress.com",
    "substack.com",
    # 커뮤니티
    "cafe.naver.com",
    "cafe.daum.net",
    "kin.naver.com",
    "dcinside.com",
    "fmkorea.com",
    "theqoo.net",
    "ruliweb.com",
    "clien.net",
    "ppomppu.co.kr",
    "instiz.net",
    "pann.nate.com",
    "mlbpark.donga.com",
    "bobaedream.co.kr",
    "82cook.com",
    "todayhumor.co.kr",
    "inven.co.kr",
    "dogdrip.net",
    "reddit.com",
    "quora.com",
]

TEXT_MAX_CHARS = 1500


@dataclass
class SearchHit:
    url: str
    title: str
    text: str
    published_date: str | None = None
    author: str | None = None


class ExaSearcher:
    def __init__(self, api_key: str, num_results: int = 5):
        self._exa = AsyncExa(api_key=api_key)
        self._num_results = num_results

    async def search(self, query: str) -> list[SearchHit]:
        response = await self._exa.search(
            query,
            type="auto",
            num_results=self._num_results,
            exclude_domains=EXCLUDED_DOMAINS,
            user_location="KR",
            contents={"text": {"max_characters": TEXT_MAX_CHARS}},
        )
        hits: list[SearchHit] = []
        for r in response.results:
            text = (r.text or "").strip()
            if not r.url or not text:
                continue
            hits.append(
                SearchHit(
                    url=r.url,
                    title=(r.title or r.url).strip(),
                    text=text,
                    published_date=(r.published_date or None),
                    author=(r.author or None),
                )
            )
        return hits
