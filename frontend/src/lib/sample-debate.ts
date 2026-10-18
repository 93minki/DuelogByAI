import type { DebateDetail } from "@/lib/types";

/**
 * 랜딩 페이지용 고정 샘플(축약본). 출처는 실제 기사이며, 본문은 각 기사의 보도 내용 범위 안에서만 작성했다.
 */
export const SAMPLE_DEBATE: DebateDetail = {
  id: "sample",
  topic_raw: "학교 휴대전화 일괄 수거",
  proposition: "학교는 일과 시간 동안 학생 휴대전화를 일괄 수거해야 한다",
  pro_stance: "학습권과 교육활동 보호를 위해 일과 시간 동안 휴대전화를 일괄 수거해야 한다.",
  con_stance: "일괄 수거는 과도한 제한이므로 수업 중 사용 제한 수준에 그쳐야 한다.",
  status: "completed",
  current_round: 1,
  total_rounds: 1,
  created_at: "2026-10-01T09:00:00+09:00",
  completed_at: "2026-10-01T09:12:00+09:00",
  error: null,
  turns: [
    {
      seq: 0,
      round: 0,
      phase: "opening_remarks",
      speaker: "moderator",
      content:
        "오늘의 논제는 '학교는 일과 시간 동안 학생 휴대전화를 일괄 수거해야 한다'입니다. 찬성 측은 일괄 수거가 필요하다는 입장, 반대 측은 수업 중 사용 제한 수준에 그쳐야 한다는 입장입니다.\n\n매 라운드 사회자 안내 후 찬성, 반대 순서로 발언하며, 모든 주장은 웹 검색으로 찾은 근거와 출처 번호로 뒷받침됩니다.",
      search_queries: [],
    },
    {
      seq: 1,
      round: 1,
      phase: "moderation",
      speaker: "moderator",
      content: "1라운드를 시작합니다. 양측은 입론을 해 주시기 바랍니다. 찬성 측부터 발언해 주십시오.",
      search_queries: [],
    },
    {
      seq: 2,
      round: 1,
      phase: "opening",
      speaker: "pro",
      content:
        "찬성 측은 일과 시간 동안의 일괄 수거가 학습 환경을 지키는 현실적인 방법이라고 봅니다.\n\n첫째, 국제기구도 교내 스마트폰 제한을 권고했습니다. 유네스코의 2023년 글로벌 교육 모니터링 보고서는 학교의 스마트폰 사용 금지를 촉구했고, 휴대전화가 가까이 있는 것만으로도 학생의 주의가 흐트러질 수 있다는 연구 결과를 근거로 들었습니다[1].\n\n둘째, 국내에서도 판단이 바뀌었습니다. 국가인권위원회는 2024년 학칙에 근거해 일과 시간에 휴대전화를 수거·보관하는 것을 인권침해로 보지 않는다고 결정해, 기존 입장을 뒤집었습니다[2].\n\n셋째, 2025년 8월 국회를 통과한 초중등교육법 개정안은 수업 중 사용 금지에 더해, 필요하면 수업 시간 외 교내 사용과 소지까지 제한할 수 있는 근거를 마련했습니다[3]. 일괄 수거는 이 법 취지에 부합하는 방식입니다.",
      search_queries: ["유네스코 교내 스마트폰 금지 권고", "인권위 휴대전화 수거 인권침해 판단 변경", "초중등교육법 스마트폰 개정안 통과"],
    },
    {
      seq: 3,
      round: 1,
      phase: "opening",
      speaker: "con",
      content:
        "반대 측은 수업 중 사용 제한에는 동의하지만, 일과 시간 전체의 일괄 수거는 지나친 제한이라고 봅니다.\n\n첫째, 일괄 수거에 대한 인권 측면의 우려는 오래 이어져 왔습니다. 국가인권위원회는 2017년 학생 휴대전화 일괄 수거가 과잉금지원칙에 어긋나 통신의 자유를 침해한다고 판단한 바 있습니다[4]. 2024년 판단 변경만으로 이 쟁점이 사라졌다고 보기는 어렵습니다.\n\n둘째, 법 자체도 일괄 수거를 강제하지 않습니다. 개정법은 제한 기준과 방법을 학칙에 맡겼고[3], 위반 시 처벌 방식이나 기준은 담지 않았다는 지적이 나옵니다[6].\n\n셋째, 효과도 확정적이지 않습니다. 수업 중 스마트폰 금지가 학생들에게 미친 영향에 대해서는 의견이 엇갈린다는 보도가 있습니다[5]. 찬성 측이 인용한 유네스코 권고 역시 기술이 학습을 돕는 방향으로 쓰여야 한다는 취지를 함께 담고 있어[1], 일괄 차단만이 답이라고 보기는 어렵습니다.",
      search_queries: ["인권위 2017 휴대전화 일괄수거 통신의 자유", "스마트폰 금지법 처벌 기준 학칙 위임", "수업 중 스마트폰 금지 효과 논란"],
    },
  ],
  sources: [
    {
      number: 1,
      url: "https://www.euronews.com/2023/07/26/unesco-calls-for-schools-around-the-world-to-ban-smartphones-in-the-classroom",
      title: "UNESCO calls for schools around the world to ban smartphones in the classroom",
      published_date: "2023-07-26",
      author: "Euronews",
      excerpt: "",
    },
    {
      number: 2,
      url: "https://hangyo.com/mobile/article.html?no=102779",
      title: "인권위, 학생 휴대전화 수거 인권침해 아냐",
      published_date: "2024-10-08",
      author: "한국교육신문",
      excerpt: "",
    },
    {
      number: 3,
      url: "https://www.khan.co.kr/article/202508290700001",
      title: "내년부터 '수업 중 스마트폰 금지'···어떻게 생각하시나요?",
      published_date: "2025-08-29",
      author: "경향신문",
      excerpt: "",
    },
    {
      number: 4,
      url: "https://www.ajunews.com/view/20211114063735545",
      title: "[학생 인권] 교내 휴대전화 사용금지 '인권 침해' 논란",
      published_date: "2021-11-14",
      author: "아주경제",
      excerpt: "",
    },
    {
      number: 5,
      url: "https://v.daum.net/v/20250906070215377",
      title: "\"수업 중 스마트폰 못 써요?\" 학생들 난리인데…효과 있나 봤더니",
      published_date: "2025-09-06",
      author: "아시아경제",
      excerpt: "",
    },
    {
      number: 6,
      url: "https://v.daum.net/v/8fPCAMzT6g",
      title: "처벌 기준·책임 학교에 떠넘긴 학교 스마트폰 금지법 \"효과 있을까\"",
      published_date: null,
      author: "르데스크",
      excerpt: "",
    },
  ],
  summary: {
    pro_summary:
      "찬성 측은 유네스코가 교내 스마트폰 제한을 권고하며 주의 분산 문제를 지적한 점[1], 국가인권위원회가 2024년 학칙에 근거한 일과 시간 수거를 인권침해로 보지 않기로 한 점[2], 개정 초중등교육법이 수업 외 시간의 사용·소지 제한 근거를 마련한 점[3]을 들어 일괄 수거가 필요하다고 주장했습니다.",
    con_summary:
      "반대 측은 인권위가 2017년 일괄 수거를 통신의 자유 침해로 판단했던 점[4], 개정법이 제한 기준을 학칙에 맡겼고[3] 처벌 기준이 없다는 지적[6], 금지 효과에 대한 평가가 엇갈린다는 보도[5]를 들어 수업 중 제한 수준이 적절하다고 주장했습니다.",
    final_summary: {
      overview:
        "양측은 수업 중 사용 제한의 필요성에는 이견이 적었으나, 일과 시간 전체로 제한을 넓히는 일괄 수거가 정당한지를 두고 인권 판단의 변화와 법의 취지를 다르게 해석했습니다.",
      key_issues: ["일괄 수거와 학생 기본권의 관계", "개정 초중등교육법의 취지와 학칙 위임 범위", "스마트폰 제한의 실제 학습 효과"],
      agreements: ["수업 중 스마트폰 사용은 제한할 필요가 있다는 점"],
      disagreements: ["인권위 2024년 판단 변경의 의미", "수업 시간 외까지 제한하는 것이 필요한지 여부"],
      open_questions: ["일괄 수거와 부분 제한의 학습 효과를 비교한 국내 자료가 있는가?", "긴급 연락 등 예외는 어떻게 보장해야 하는가?"],
    },
  },
};
