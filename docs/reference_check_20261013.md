# 참고문헌 확인 목록 — 요약본 v8 (2026-10-13)

키트 R15: 새 문헌은 DOI(또는 arXiv 번호)를 확인한 뒤 추가한다. 이 작업 환경에서는 CrossRef·arXiv 접속이 막혀
(`academic_search.py verify` 실패) 아래 23건 모두 도구로 확인하지 못했다. 저자가 직접 확인하거나, 접속 가능한 환경에서
`python kim-paper-kit/scripts/academic_search.py verify <DOI>`로 확인한다.

확인할 것: 저자 이름과 순서, 연도, 게재처(학회·권호), arXiv 번호. "et al."로 줄인 항목은 저자 목록을 원문에서 채운다.

| v8 번호 | 문헌 | 출처 | 우선순위 |
|---|---|---|---|
| 2 | Bai et al. (2022) Constitutional AI, arXiv:2212.08073 | v7 추가, 기억에 근거 | 높음 |
| 11 | Perez et al. (2022) Red Teaming LMs with LMs, EMNLP 2022, arXiv:2202.03286 | v7 추가, 기억에 근거 | 높음 |
| 12 | Pryzant et al. (2023) ProTeGi, EMNLP 2023, arXiv:2305.03495 | v7 추가, 기억에 근거 | 높음 |
| 14 | Sharma et al. (2024) Sycophancy, ICLR 2024, arXiv:2310.13548 | v7 추가, 기억에 근거 | 높음 |
| 20 | Xiang et al. (2024) Certifiably Robust RAG, arXiv:2405.15556 | v7 추가, 기억에 근거 | 높음 |
| 21 | Yang et al. (2024) OPRO, ICLR 2024, arXiv:2309.03409 | v7 추가, 기억에 근거 | 높음 |
| 22 | Zheng et al. (2023) MT-Bench, NeurIPS 2023 D&B, arXiv:2306.05685 | v7 추가, 기억에 근거 | 높음 |
| 23 | Zou et al. (2025) PoisonedRAG, USENIX Security 2025, arXiv:2402.07867 | v7 추가, 기억에 근거 | 높음 |
| 1, 3, 4, 6, 16, 17, 18 | Aswin RRV, Chaitanya(PRISM), Chen(Promptware), Geng(PIArena), Sivaroopan(SHIELD), Slater(SISF), Tamber(FaithJudge) | 기존 전문 원고에서 가져옴(v3), 미확인 | 중간 |
| 5, 7, 8, 9, 10, 13, 15, 19 | FIRST(CVSS), Greshake, Liu, OWASP 2건, Rebedea, Shi, Wardle | 기존 전문 원고 | 낮음 |

참고: PRISM·SISF는 원문 전체를 확인하지 못해 표 1에 "미상"으로 두었다. 원문을 확인하면 표 1과 2.2절 서술을 갱신한다.

> 2026-10-16: 요약본 v11에서 Bai(Constitutional AI), Geng(PIArena), Perez, Sivaroopan(SHIELD) 4건을 본문에서 빼며 참고문헌에서도 삭제. 남은 19건만 확인하면 된다.
