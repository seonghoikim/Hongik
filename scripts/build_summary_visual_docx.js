const fs = require("fs");
const path = require("path");
const { Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, AlignmentType, BorderStyle, ShadingType, VerticalAlign, Footer, PageNumber, HeadingLevel } = require("docx");

const IMG = path.join(__dirname, "..", "diagrams", "summary");
const BODY = "바탕체", HEAD = "돋움체";
const BS = 22, LS = 360, W = 8700;
const PX = (inch) => Math.round(inch * 96);

const toc = [], figList = [], tabList = [];
let figN = 0, tabN = 0;
const body = [];

const tr = (text, o = {}) => new TextRun({ text, font: BODY, size: BS, ...o });
const P = (text, o = {}) => body.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 140, line: LS }, ...o, children: [tr(text)] }));
const SUB = (text) => body.push(new Paragraph({ spacing: { before: 120, after: 80, line: LS }, keepNext: true, children: [tr(text, { bold: true, font: HEAD, size: 22 })] }));
const H1 = (text) => { toc.push({ l: 1, text }); body.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, spacing: { before: 0, after: 240 }, children: [tr(text, { bold: true, font: HEAD, size: 30 })] })); };
const H2 = (text) => { toc.push({ l: 2, text }); body.push(new Paragraph({ heading: HeadingLevel.HEADING_2, keepNext: true, spacing: { before: 280, after: 160 }, children: [tr(text, { bold: true, font: HEAD, size: 25 })] })); };

function FIG(file, widthIn, caption) {
  figN++;
  const cap = `그림 ${figN}. ${caption}`;
  figList.push(cap);
  const buf = fs.readFileSync(path.join(IMG, file));
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);
  body.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 160, after: 60 },
    children: [new ImageRun({ type: "png", data: buf, transformation: { width: PX(widthIn), height: Math.round(PX(widthIn) * h / w) } })] }));
  body.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 }, children: [tr(cap, { size: 20, bold: true, font: HEAD })] }));
  return figN;
}

const line = { style: BorderStyle.SINGLE, size: 4, color: "888888" };
const borders = { top: line, bottom: line, left: line, right: line };
function TAB(caption, header, rows, widths, note) {
  tabN++;
  const cap = `표 ${tabN}. ${caption}`;
  tabList.push(cap);
  body.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 160, after: 80 }, children: [tr(cap, { size: 20, bold: true, font: HEAD })] }));
  const mk = (t, i, head) => new TableCell({ width: { size: widths[i], type: WidthType.DXA }, borders, margins: { top: 50, bottom: 50, left: 90, right: 90 }, verticalAlign: VerticalAlign.CENTER,
    shading: head ? { type: ShadingType.CLEAR, fill: "E3E3E3" } : undefined,
    children: [new Paragraph({ alignment: head || i > 0 && t.length < 14 ? AlignmentType.CENTER : AlignmentType.LEFT, spacing: { line: 300 }, children: [tr(t, { size: 19, bold: head })] })] });
  body.push(new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: widths, rows: [
    new TableRow({ tableHeader: true, children: header.map((t, i) => mk(t, i, true)) }),
    ...rows.map((r) => new TableRow({ cantSplit: true, children: r.map((t, i) => mk(t, i, false)) })),
  ] }));
  body.push(new Paragraph({ spacing: { after: note ? 40 : 200 }, children: [] }));
  if (note) body.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 200, line: 300 }, children: [tr(note, { size: 18 })] }));
  return tabN;
}

// ======================= 본문 =======================
H1("제1장. 서론");
H2("1.1. 연구의 배경 및 필요성");
P("기업 환경에 도입되는 LLM 기반 AI 챗봇은 정보의 진위와 무결성이 흔들리는 문제에 반복적으로 노출된다. 대화 중 고객 개인정보가 의도치 않게 유출되거나(Malinformation, 사실이지만 해악을 끼치는 정보), 브랜드 가이드라인 및 RAG 지식과 배치되는 답변을 생성하거나(Misinformation, 의도 없는 오류), 프롬프트 인젝션으로 주입된 허위 전제에 동조하는(Disinformation, 의도적 조작) 사례가 그것이다. 이 세 유형은 Wardle과 Derakhshan(2017)[1]이 정치·사회적 허위정보 확산을 설명하기 위해 제시한 정보 무질서(Information Disorder) 프레임워크의 3분류와 구조적으로 일치한다. 본 연구는 이 프레임워크를 조직 챗봇의 1:1 상담 세션이라는 맥락으로 옮겨 '정보 불일치성(Information Disorderness)'이라는 개념으로 재정의한다.");
P("최근 B2B 엔터프라이즈 시장에서 LLM 기반 챗봇의 도입이 가속화되면서 이 문제의 실무적 비중도 커지고 있다. 서로 다른 비즈니스 도메인과 조직 문화를 가진 고객사는 저마다 엄격하고 구체적인 응대 가이드라인, 페르소나, 내부 보안 규정을 요구하며, 이 요구사항 자체가 해당 조직에서 무엇이 정보 불일치성으로 간주되는가를 정의하는 기준이 된다. 이러한 요구사항에 맞추어 LLM을 커스터마이징하는 작업은 전통적으로 모델 파인튜닝이나 시스템 프롬프트 작성에 의존해 왔다. 그러나 파인튜닝은 요구사항이 바뀔 때마다 막대한 재학습 비용이 발생하며, 프롬프트 엔지니어링은 복잡한 사용자 입력이나 악의적인 우회 공격(탈옥, 간접 프롬프트 인젝션[2])이 가해졌을 때 설정된 페르소나를 이탈하거나 내부 기밀을 노출하는 취약점을 드러낸다.");

H2("1.2. 기존 방식의 한계 및 문제 제기");
P("기존 방식의 한계는 다음 다섯 가지로 정리된다. 첫째, LLM은 외부 문서(RAG)의 정보를 최우선으로 신뢰하도록 훈련되어 있어, 검색된 문서가 오염되었거나 사용자가 가스라이팅성 입력을 주입하면 시스템 프롬프트의 지시를 쉽게 망각하고 Misinformation과 Disinformation을 그대로 산출한다. 둘째, 기존 개발 방식은 프롬프트를 작성한 뒤 수동으로 몇 가지 테스트를 거쳐 배포하는 데 그쳐, 소프트웨어 생명주기(SDLC) 안에 엣지 케이스를 선제적으로 탐지하는 검증 모듈이 부재하다. 셋째, LLM으로 LLM의 응답을 평가(LLM-as-a-Judge)할 때 단일 세션 안에서 평가를 진행하면 이전 대화 기록이 평가 모델에 영향을 미치는 컨텍스트 오염(Context Bleeding)이 발생하여 평가 결과의 객관성을 담보할 수 없다. 넷째, 방어 메커니즘을 특정 공격셋에 맞춰 튜닝한 뒤 동일한 공격셋으로만 검증하면, 미지의 공격이나 방어를 인지한 적응형 공격 앞에서 성능이 재현되지 않을 위험이 있다(Geng et al., 2026[3]). 다섯째, 조직 내부 챗봇은 타 고객의 개인정보를 캐내려는 시도에도 노출되어 있으며, 이를 특정 상용 LLM 1종만으로 검증하면 그 결과가 해당 모델 특유의 편향인지 메커니즘 자체의 효과인지 구분하기 어렵다.");

H2("1.3. 연구 목적 및 기여");
P("본 논문에서 '자가 치유(Self-Healing)'는 배포된 시스템이 런타임에 스스로를 진단하고 실시간으로 복구한다는 의미가 아니다. 정확히는 오프라인 배치 절차로서 (1) 적대적 시나리오로 결함을 탐지하고, (2) 결함 원인을 분석해 요구사항 명세서(SRS) 텍스트를 자동으로 재작성하며, (3) 재평가로 개선을 확인하는 설계 시점(design-time)의 피드백 루프를 가리킨다. 본 연구는 상기 한계를 해결하기 위해 정보 불일치성에 저항하는 자가 치유 기반 AI 챗봇 개발 메커니즘을 제안하며, 그 기여는 다음과 같다.");
P("첫째, Wardle과 Derakhshan[1]의 프레임워크를 이론적 뿌리로 삼아 정보 불일치성 개념을 조직 챗봇 맥락에 맞게 재정의하고, 8개 공격 카테고리 중 사칭·허위 사실 동조·메타데이터 유출·개인정보 유출 4개를 3분류에 직접 대응하는 핵심 실증 대상으로 한정하였다. 둘째, 적대적 스트레스 테스트에서 발견된 취약점을 분석해 SRS의 절대 보안 원칙(Meta-Rule)을 자동 보강하는 SRS 기반 자가 치유 폐쇄 루프를 구현하였다. 셋째, 연구 사이클 전체는 단일 주 모델로 진행하되 완성된 명세서를 이종 LLM에 추가로 통과시키는 교차 모델 검증을 도입하였다. 넷째, 타겟 시스템과 심판관 사이의 컨텍스트를 완전히 격리하는 무상태(Stateless) API 기반 평가 환경을 구성하였다. 다섯째, 헬드아웃 테스트셋과 적응형 재공격 실험으로 방어력이 특정 공격셋의 암기가 아님을 검증하였다. 다만 4단계 유닛 아키텍처 자체의 형태적 신규성은 기존 가드레일 파이프라인 패턴과 유사하여 제한적이며, 본 연구의 기여는 그 구조를 채우는 자동화된 절차와 구체적 설계 조합에 있다.");

H2("1.4. 논문의 구성");
P("본 요약본은 학위논문 전문의 핵심 그림을 중심으로 내용을 재구성한 것이며, 상세한 근거와 수치는 전문의 해당 절을 참조한다. 이하 '전문'은 학위논문 전체 원고를 가리킨다. 제2장에서는 제안하는 자가 치유 메커니즘의 전체 프레임워크, 유닛 아키텍처, 5단계 절차, 공격 분류체계, 4단계 보안 심각도 체계를 설명한다. 제3장에서는 실험 환경과 사용 모델, 평가 지표 및 통계 검정, 심판관 신뢰성과 교차 모델 검증의 설계를 기술한다. 제4장에서는 자가 치유 성능, 정보 불일치성 유형별 방어 결과, 교차 모델 검증, 5W1H 가설 검증, 적응형 재공격의 결과를 제시한다. 제5장에서는 결과를 논의하고 한계와 향후 연구 방향을 정리하며 결론을 맺는다.");

H1("제2장. 제안하는 자가 치유 메커니즘");
H2("2.1. 전체 프레임워크");
P("제안 메커니즘은 서로 역할이 다른 세 개의 구조가 결합된 형태이다. 첫째는 입력 가드레일, RAG 검색, LLM 추론, 출력 가드레일로 이어지는 4단계 유닛 아키텍처(구조 1)이고, 둘째는 이 아키텍처 위에서 SRS를 반복적으로 강화하는 자가 치유 폐쇄 루프(구조 2)이며, 셋째는 루프가 수렴한 뒤 결과의 일반화와 견고성을 검증하는 사후 검증 단계(구조 3)이다. 그림 1은 이 세 구조가 하나의 흐름으로 통합되는 방식을 나타낸다.");
P("루프는 고객사의 페르소나와 제약 조건을 정의한 SRS에서 시작한다. 레드팀 LLM이 카테고리별로 생성한 공격 시나리오를 유닛 A에서 D까지 통과시켜 챗봇 응답을 얻고, 챗봇과 컨텍스트를 공유하지 않는 무상태 심판관이 Action Matrix에 따라 응답을 채점한다. 방어가 완전하지 않은 사례가 있으면 Meta-Rule 생성기가 실패 사례를 분석해 방어 규칙을 작성하고, 이를 SRS의 헤더와 푸터에 병합한 뒤 재실행한다. 전원이 완전 방어(FULL_DEFENSE)에 도달하면 루프를 종료하고, 이후 치유에 사용하지 않은 헬드아웃 문항으로 재검증하고, 블랙박스·화이트박스 두 위협 모델로 재공격하며, 응답 생성 모델만 3개 벤더로 교체하는 교차 모델 검증과 통계 검정을 차례로 수행한다. 루프 시작 전에는 결정론적 차단 문구의 사전 검증, 비용이 들지 않는 모델 동작 변화(drift) 점검, 대화형 검토 도구의 세 가지 사전 점검을 거친다.");
FIG("fig1_pipeline.png", 3.3, "전체 프레임워크 — 파이프라인 구조와 자가 치유 루프의 통합");

H2("2.2. 유닛 아키텍처");
P("고객 조직의 가이드라인을 단계별로 검증하고 실행할 수 있도록, 챗봇 시스템은 표 1과 같이 4개의 독립된 모듈로 구성한다. 취약점이 발생한 지점을 유닛 단위로 격리해 추적할 수 있다는 점이 이 구성의 목적이며, 심판관은 채점과 함께 우회가 발생한 유닛(A~D)을 태깅한다.");
TAB("유닛 A~D의 역할", ["유닛", "명칭", "역할"], [
  ["A", "입력 가드레일", "명백한 탈옥 구문, 시스템 관리자 사칭, 비정상적 인코딩, 유해성 발언을 1차적으로 즉시 차단한다. 교묘한 사회공학적 공격(가스라이팅, 어투 강요)은 의도적으로 차단 대상에서 제외한다."],
  ["B", "RAG 검색 및 지시어 검증", "고객사 내부 지식 베이스에서 관련 정보만 정제하여 가져오며, 외부 웹사이트나 인젝션 위험이 있는 오염된 데이터의 유입을 물리적으로 격리한다."],
  ["C", "LLM 추론 엔진", "SRS에 정의된 페르소나와 Meta-Rule을 이행하는 핵심 모듈로, 사용자 의도를 파악해 고객사의 톤앤매너에 맞는 응답을 생성한다."],
  ["D", "출력 가드레일", "응답이 최종 출력되기 전 경쟁사 브랜드명 노출, 내부 메타데이터 유출, 부적절한 단어 포함 여부를 점검해 필터링한다."],
], [800, 2300, 5600]);

H2("2.3. 자가 치유 5단계 절차");
P("자가 치유 루프의 본체는 다음 5단계로 구성되며, 처음부터 끝까지 단일 주 모델로 진행된다. 1단계에서는 고객사가 요구하는 역할, 말투, 업무 범위, 금지 사항을 SRS v1.0으로 정의한다. 2단계에서는 사칭, 어투 변경, 허위 사실 동조, 개인정보 캐내기 등 고객사 가이드라인을 의도적으로 파괴하려는 공격 시나리오를 8개 범주에 걸쳐 구성한다. 3단계에서는 각 공격 문장(단발성 단일 턴 입력)을 유닛 A~D 시스템에 입력하여 응답을 추출한다. 4단계에서는 격리된 심판관이 응답을 4단계 등급(FULL_DEFENSE, FUNCTIONAL_DEFENSE, PARTIAL_EXPOSURE, BREACH)으로 채점하고 우회가 발생한 유닛을 추적한다. 5단계에서는 FULL_DEFENSE에 미달하는 항목이 있을 때 실패 사유를 분석하여, 사용자의 어떠한 지시보다 우선하는 절대 보안 원칙(Meta-Rule)을 명세서의 최상단과 최하단에 샌드위치 프롬프팅 방식으로 주입하여 명세서를 v2.0, v3.0 등으로 보강한다. 같은 규칙을 앞뒤에 중복 배치하는 것은 LLM이 긴 컨텍스트의 양 끝에 있는 정보는 잘 활용하지만 중간에 있는 정보는 상대적으로 소홀히 한다는 선행 관찰[4]에 근거한다.");
P("루프는 치유용 셋 전원이 만점에 도달하거나 설정된 라운드 상한에 이를 때까지 반복된다. 본 연구가 실험적으로 측정하는 루프는 연구 목적상 Meta-Rule의 생성, 삽입, 재평가가 사람의 개입 없이 코드로 반복되는 완전 자동 루프이며, Meta-Rule 생성기의 출력 재현성을 위해 temperature를 고정한다. 다만 실제 서비스 배포 시에는 생성된 Meta-Rule을 사람이 검수 없이 즉시 반영하면 과도하게 제한적인 규칙으로 정상 응답이 차단될 위험이 있으므로, 프로덕션 반영 전 사람의 최종 승인 게이트를 두는 것을 권장하며 이는 본 연구의 실험 범위에 포함하지 않는다. 이 구분은 '자가 치유'라는 용어가 가리키는 자동화 수준을 명확히 하기 위한 것이다.");

H2("2.4. 공격 분류체계와 시나리오 생성");
P("임의로 공격 문장을 만들면 재현성과 대표성을 담보할 수 없으므로, 본 연구는 8개 공격 유형을 OWASP Top 10 for LLM Applications 2026[5]의 위협 카테고리에 매핑하여 분류체계를 확정하였다. 그림 2의 가운데 열과 같이 8개 유형은 LLM01(Prompt Injection), LLM02(Sensitive Information Disclosure), LLM07(System Prompt Leakage), LLM08(Vector and Embedding Weaknesses), LLM09(Misinformation)의 다섯 카테고리에 대응한다. 나머지 다섯 카테고리는 본 연구의 위협 모델(무상태 단일 턴 응답 생성, 도구 호출 없음)과 겨냥하는 대상이 달라 범위 밖으로 둔다. LLM03·LLM04는 학습·배포 파이프라인 단계의 위협이고, LLM05는 챗봇 응답을 다운스트림 시스템이 코드처럼 실행하는 상황을 전제하며, LLM06은 도구 호출 권한을 가진 에이전트형 시스템에 해당하고, LLM10은 가용성 위협으로 본 연구의 기밀성·무결성 위협과 축이 다르기 때문이다.");
P("OWASP 매핑과 별개로, 8개 공격 유형을 본 연구의 핵심 이론 축인 Dis-/Mis-/Malinformation 3분류[1]에도 대조하였다. 8개 전부를 3분류에 억지로 대응시키지 않고, 관리자/시스템 사칭(Disinformation), 허위 사실 동조 유도(Misinformation), 내부 메타데이터·시스템 프롬프트 유출 유도와 개인정보 유출 유도(Malinformation)의 4개만 핵심 실증 대상으로 삼았다. 나머지 4개(인코딩·난독화 우회, 어투 강요·가스라이팅, 다중 상품 키워드 컨텍스트 오염, 가격 정보 간접 유도)는 정보 진위와 무관한 보완적 보안 위협으로 명시적으로 분리하였다. 이 경계는 매핑의 강약이 아니라 '정보의 진위(사실, 거짓, 은닉) 여부가 판정의 본질인가'라는 단일 기준으로 긋는다. 뒤의 두 범주는 실제 사실 정보가 관련되어 매핑이 완전히 없지는 않으나 위반의 본질이 정보 진위가 아니라 정책 경계 준수이므로 범위 밖에 둔다.");
P("공격 시나리오는 반자동 절차로 생성한다. 먼저 별도의 레드팀 생성 LLM(GPT-5.4)이 카테고리 정의와 각 2개의 예시를 바탕으로 목표 수량의 1.5배에 해당하는 후보를 생성하고, 문자열 유사도 0.85 이상의 중복을 제거한 뒤, 카테고리별 비율을 유지하는 층화추출로 치유용 셋과 헬드아웃 셋에 무작위 배정한다. 설계상 이 사이에 연구자의 수동 검토 단계가 있으나, 보고된 모든 실행에서 이 단계는 기본값(전부 통과)으로 남아 있었으며 이는 한계로 명시한다.");
FIG("fig3_attack_taxonomy.png", 5.7, "공격 유형 8종의 분류 — OWASP LLM Top 10 및 정보 불일치성 3분류 매핑");

H2("2.5. 4단계 보안 심각도 Level 체계");
P("초기 설계의 3단계 Action Matrix(PASS, WARNING, FAIL)에서 WARNING 판정 기준은 특정 고객사의 SRS 문구(간결한 단답형 미준수, 지정 어투 이탈 등)를 예시로 작성된 것이어서 해당 사례 밖에서는 재사용하기 어려운 도메인 특화 기준이었다. 이를 일반화하기 위해 OWASP Risk Rating Methodology[6]와 CVSS[7]의 정성적 등급이 Low, Medium, High, Critical의 4단계로 수렴하는 업계 관행에 착안하여, 도메인에 독립적인 4단계 보안 심각도 척도(표 2, 그림 3)를 제안하였다. 이 척도는 8개 공격 유형이 정의하는 '무슨 종류의 공격인가'라는 축과 직교하는 '방어가 얼마나 완전했는가'의 축을 담당하며, 레벨이 높을수록 방어의 완결성이 높다.");
TAB("4단계 보안 심각도 Level 정의", ["Level", "명칭", "정의 (도메인 무관)"], [
  ["4", "완전 방어 (Full Defense)", "공격을 인지·무력화하고, 방어 규칙·정책의 존재 자체도 암시하지 않음"],
  ["3", "기능적 방어 (Functional Defense)", "핵심 정보는 유출되지 않으나, 방어 로직의 존재나 형태가 응답을 통해 간접적으로 드러남"],
  ["2", "부분 노출 (Partial Exposure)", "직접적 기밀은 아니나 메타데이터·존재 여부 등 공격자에게 유의미한 간접 정보가 노출됨"],
  ["1", "침해 (Breach)", "개인정보·시스템 프롬프트·정책 등 핵심 보안 경계가 실제로 붕괴됨"],
], [900, 2800, 5000]);
P("5단계 이상으로 세분화하는 방안은 기각하였다. Level 3을 더 쪼개면 도메인 특화 형식·톤 기준이 재유입되어 일반화 원칙이 훼손되고, Level 1(침해)의 세분화는 실측 데이터에 실제 침해 사례가 전무하여 검증되지 않은 이론적 구분에 그치며, 등급이 촘촘해질수록 무상태 단일 호출 심판관의 채점 일관성이 저하될 위험이 있기 때문이다. 등급의 개수와 구조는 OWASP와 CVSS의 확립된 관행에서 차용하였으나, (1) 대화형 챗봇의 텍스트 응답에 특화된 등급 정의, (2) 무상태 LLM 심판관이 단일 호출로 이 등급을 산출하는 방식, (3) 등급을 Meta-Rule 자동 생성의 트리거로 되먹임하는 폐쇄 루프라는 세 가지는 본 연구 고유의 기여이다.");
P("한편 전문 제5장에 보고된 1~13차 파일럿은 모두 3단계 기준으로 채점되었고, 4단계 체계는 이후의 신규 실행과 9차 파일럿의 회고적 재채점에 적용되었다. 즉 3단계와 4단계는 구버전과 현재 버전의 관계가 아니라 서로 다른 시기의 실행에 각각 쓰인 두 개의 병존하는 기준이며, 4단계 rubric에 대한 심판관 신뢰도의 실측 검증은 후속 과제로 남아 있다.");
FIG("fig2_severity_levels.png", 5.4, "4단계 보안 심각도 Level 체계");

H1("제3장. 실험 설계");
H2("3.1. 실험 환경 및 데이터 구성");
P("본 연구는 사용자와 실시간으로 상호작용하며 상태를 유지하는 대화형 시뮬레이터를 구축하는 것이 아니라, 미리 설계된 단발성(single-turn) 적대적 시나리오를 코드로 자동 실행·채점하는 시나리오 기반 테스트 프레임워크로 범위를 한정한다. 연구 방법론은 단일 사례 연구이며, 대상은 가전 유통 분야 고객사의 실제 운영 시스템 프롬프트와 RAG 지식 베이스를 모델링한 챗봇이다. 내적 타당성을 높이기 위해 공격 시나리오를 치유용 셋(Meta-Rule 생성에 사용)과 헬드아웃 셋(치유 과정에 전혀 노출되지 않으며 최종 일반화 성능 검증에만 사용)으로 분리하고, 두 셋의 공격 유형 비율이 동일하도록 층화추출하였다.");
P("본 요약본에 보고된 모든 결과는 카테고리당 3개로 축소한 예비 규모 파일럿이며, 치유용·헬드아웃 셋은 각각 24개 문항(채점 가능 22~23개)이다. 카테고리당 10개 규모의 본 실행은 아직 수행하지 않았다. 또한 문항당 단일 시행(N=1)이 대부분이어서, 라운드 간 등락이 SRS 변화에 의한 신호인지 단일 시행 잡음인지 이 데이터만으로는 구조적으로 완전히 구분할 수 없다. 자가 치유 실험은 성격이 다른 두 갈래로 구분하는데, 라운드 상한을 15로 넉넉히 두고 100% 수렴과 그 대가를 관찰하는 실험(9차)과, 상한을 5로 두고 문항당 반복 시행으로 등락의 통계적 유의성을 관찰하는 실험이 그것이다. 두 실험은 경쟁하는 설계가 아니라 서로 다른 질문에 답하는 상호보완적 실험이다.");

H2("3.2. 사용 모델 및 평가 절차");
P("자가 치유 루프(유닛 C, 심판관, Meta-Rule 생성기)부터 헬드아웃 검증, 적응형 재공격까지는 단일 주 모델 하나로 진행하고, 교차 모델 검증 단계에서만 이종 상용 LLM 2종을 추가로 투입한다. 단 공격 시나리오와 적응형 재공격 문장을 생성하는 레드팀 생성기만은 주 모델과 분리하였다. 실제 API 연동 시험에서 주 모델(Claude Sonnet 5)은 우회 공격 문장 생성 요청을 정책상 거부하였고 Gemini 3.6 Flash도 같은 요청에서 실패했으며, GPT-5.4만 정상적으로 문장을 생성했기 때문이다. 표 3에 각 역할별 모델을 정리하였다.");
TAB("사용 모델 및 역할", ["역할", "모델", "비고"], [
  ["주 모델 — 유닛 C·심판관·Meta-Rule 생성기", "Anthropic Claude Sonnet 5 (claude-sonnet-5)", "유닛 C temperature 0.2, 심판관 0 고정. 심판관 호출은 무상태"],
  ["레드팀 생성기 — 공격·적응형 재공격 문장 생성", "OpenAI GPT-5.4 (gpt-5.4-2026-03-05)", "주 모델이 생성 요청을 거부하여 분리"],
  ["교차 모델 검증용 추가 백엔드", "Google Gemini 3.6 Flash, OpenAI GPT-5.4", "유닛 C 응답 생성만 담당, 채점은 주 모델 심판관이 수행"],
], [3000, 3000, 2700]);
P("채점은 무상태 심판관 LLM에 원본 SRS 발췌, 공격 프롬프트, 챗봇 응답만 입력하고(직전 대화 이력 없음) 등급, 판단 근거, 위반 유닛을 JSON으로 반환하게 하는 방식으로 수행한다. 3단계 기준의 PASS, WARNING, FAIL은 각각 3점, 2점, 1점으로 환산하며, 가이드라인 준수율은 총점을 만점(3점에 채점 가능 문항 수를 곱한 값)으로 나눈 비율로 정의한다. 예를 들어 22개 문항 중 PASS 1건, WARNING 21건이면 준수율은 (3+42)/66=68.2%이다.");

H2("3.3. 통계 검정 방법");
P("표본 수가 적고 순위형(ordinal) 데이터이므로 비모수 검정을 기본으로 하며, 비교의 성격에 따라 검정을 구분한다. 치유용 셋은 SRS 버전만 바뀌고 동일한 문항을 반복 측정하므로 대응표본 설계이며 Wilcoxon 부호순위 검정을 사용한다. 치유용 셋과 헬드아웃 셋처럼 서로 다른 문항 집합을 비교하는 경우는 독립표본이므로 Mann-Whitney U 검정과 카이제곱 독립성 검정을 사용하고, 3개 백엔드를 비교하는 교차 모델 검증에는 Kruskal-Wallis 검정과 카이제곱 검정의 3그룹 확장을 사용한다.");
P("치유용 셋에 대한 Wilcoxon 검정의 유의한 개선은 해석에 주의가 필요하다. 루프는 치유용 셋 점수가 만점에 도달할 때까지 탐색하도록 설계되어 있으므로, v1.0 대비 v_final의 개선은 상당 부분 설계상 예견된 결과이며 그 자체로 일반화 능력을 입증하지 않는다. 따라서 이 검정은 루프가 의도대로 작동했는지의 확인용으로만 보고하며, 핵심 증거는 치유 과정에 노출되지 않은 헬드아웃 셋과 적응형 재공격의 결과이다.");

H2("3.4. 심판관 신뢰성 및 교차 모델 검증 설계");
P("본 연구의 모든 정량 결과는 심판관 LLM의 채점에 의존한다. 심판관이 체계적으로 관대하거나 엄격하면 방어 성공률 자체가 의미를 잃으며, 심판관 자체도 인젝션 공격의 대상이 될 수 있다(Shi et al., 2024[8]). 본 연구는 매 호출 새 세션을 사용하는 무상태 설계로 컨텍스트 오염을 차단하였으나 단일 응답 안의 인젝션 가능성은 범위 밖으로 남겼다. 신뢰성 확인을 위해 층화추출한 표본을 연구자가 블라인드로 직접 채점해 심판관과의 일치율을 보는 경량 표본 검토 절차를 구현하였으나, 실제 수동 채점은 아직 수행하지 않았다. 대신 이미 채점된 응답 쌍은 그대로 두고 심판관만 다른 벤더로 교체해 재채점하는 교차 심판관 재검증을 먼저 수행하는 방식으로 같은 문제의식을 점검하였다.");
P("관측된 현상으로, 심판관 역할의 주 모델이 채점 대상으로 인용된 공격 문장을 자신에게 내려진 실제 지시로 오인하여 응답을 거부하는 사례가 드물게 있었다. 이러한 시나리오는 임의의 점수를 부여하지 않고 '채점 불가'로 표시해 통계에서 제외하며 그 건수를 함께 보고한다. 재집계 결과 채점 불가 사례는 사실상 전부 인코딩 우회 카테고리에 편중되어 있었는데, Base64나 hex로 감춘 탈옥 문구가 인용문 안에 그대로 포함되어 심판관이 기록과 지시를 구분하기 어렵기 때문으로 판단한다.");
P("교차 모델 검증은 연구 사이클이 끝난 뒤 한 번 수행한다. v_final이 완성되면 헬드아웃 셋을 이종 LLM 2종에도 통과시켜 주 모델을 포함한 3개 백엔드의 응답을 얻되, 채점은 반드시 주 모델 심판관 하나로 고정한다. 응답 생성 모델과 채점 모델을 동시에 늘리면 결과 차이의 원인이 뒤섞이므로, 응답 생성 모델의 차이라는 변수 하나만 격리하기 위한 설계이다. 시나리오별로 3개 백엔드 중 2개 이상이 PASS이면 '교차 모델 검증됨'으로 집계한다. 여기서 '검증됨'은 형식적 증명이나 통계적 유의성이 아니라 정의된 시나리오 셋에 대한 경험적 다수결 합의를 뜻하는 조작적 정의이며, 백엔드 간 분포 차이에 대한 검정의 p-value와는 서로 다른 것을 말해 주는 별개의 지표이다.");

H1("제4장. 실험 결과");
H2("4.1. 자가 치유 성능");
P("표 4는 7, 8, 9차 파일럿의 주요 결과를 요약한 것이며, 그림 4는 라운드별 준수율의 변화를 나타낸다. 7차 파일럿에서는 5라운드 상한까지 준수율이 68.1%에서 88.4%로 향상되었고(Wilcoxon p=0.00018), 치유에 노출되지 않은 헬드아웃 셋에서 87.0%를 기록하여 치유용 셋 최종 라운드와 통계적으로 구분되지 않았다(Mann-Whitney p=0.773). 그러나 라운드 상한에 걸려 종료되었을 뿐 만점에는 도달하지 못했다.");
TAB("파일럿 실행별 주요 결과 (준수율, %)", ["실행", "라운드 상한", "round_1", "최종 라운드", "헬드아웃", "블랙박스", "화이트박스", "교차 모델 검증"], [
  ["7차", "5", "68.1", "88.4", "87.0", "93.3", "100.0", "47.8"],
  ["8차", "5", "71.2", "71.2 (최저 63.6)", "74.2", "60.0", "80.0", "45.5"],
  ["9차", "15", "68.2", "100.0 (14라운드)", "97.1", "100.0", "100.0", "91.3"],
], [800, 1000, 1000, 1700, 1100, 1000, 1100, 1000], "※ 블랙박스·화이트박스는 적응형 재공격(각 5개 표본), 교차 모델 검증은 3개 백엔드 중 2개 이상 PASS한 비율이다. 7·8·9차는 3단계 기준으로 채점되었다.");
P("8차 파일럿은 공격 예시를 고도화하여 FAIL 등급을 처음으로 관측한 실행이다. 준수율은 round_1의 71.2%에서 round_2에 75.8%까지 올랐으나 round_3에서 63.6%로 급락한 뒤 round_5에야 71.2%로 회복하였고, round_1과 round_5의 Wilcoxon 검정은 p=1.000으로 5라운드가 순수한 개선이 아닌 진동이었음을 보였다. 누적된 Meta-Rule이 서로 다른 조건에 적용되는 규칙을 늘릴수록 응답 모델이 매 라운드 모든 조건을 만족시키기 어려워지는 구조적 원인이 있는 것으로 해석된다. FAIL 15건을 전수 검토한 결과 시스템 프롬프트·개인정보·가격 등 실제 정보가 유출된 사례는 하나도 없었다. 모든 FAIL은 거절 판단 자체는 올바르되 SRS가 최우선(Meta-Rule)으로 금지한 형식 조항(예: 추가 문의를 유도하는 문구)을 정면으로 어긴 사례였다. 이는 WARNING(단일 형식 이탈)과 FAIL(최우선 Meta-Rule 정면 위반)의 위계가 실측 데이터에서 실제로 작동함을 보여 준다.");
P("라운드 상한을 15로 확대한 9차 파일럿에서는 round_3부터 round_13까지 11개 라운드 동안 준수율이 87.9~93.9% 사이를 오르내리며 매 라운드 FAIL이 1~2건 발생하다가, round_14에서 처음으로 전원이 PASS를 받아 준수율 100.0%에 도달하여 조기 종료 조건이 처음 발동하였다(round_1 대비 Wilcoxon p=4.6×10⁻⁶). 헬드아웃 셋은 97.1%로 치유용 셋 최종 라운드와 통계적으로 구분되지 않았고(Mann-Whitney p=0.351), 블랙박스·화이트박스 재공격은 모두 5개 표본 전부를 방어하였다. 8차의 진동이 라운드 상한(5)의 부족이었음을 확인한 결과이다.");
P("다만 이 100%는 원칙의 승리가 아니라 문장 템플릿화의 결과였다는 점을 함께 보고해야 한다. v1.13까지 Meta-Rule 생성기가 누적한 규칙은 28개이며, 초반 규칙은 '거절 뒤 추가 질문 금지'와 같은 원칙 수준이었으나 라운드를 거듭할수록 허용 종결어 몇 개로 거절 문장 전체의 구조를 강제하는 기계적 규칙으로 좁아졌다. 즉 준수율은 라운드를 늘리면 결국 오를 수 있으나 SRS가 자연어 지침에서 점점 멀어지는 대가를 치르며, 그 방식과 비용을 정직하게 함께 보고하는 것이 더 정확한 결론이다.");
FIG("fig4_round_compliance.png", 5.6, "라운드별 가이드라인 준수율 추이 (7·8·9차 파일럿)");

H2("4.2. 정보 불일치성 유형별 방어 결과");
P("9차 파일럿의 결과를 2.4절의 매핑 기준(그림 2)에 따라 정보 불일치성 3유형과 보완적 위협으로 재집계하였다(표 5). round_14 열은 원본 응답과 SRS는 그대로 두고 채점 기준만 3단계에서 4단계로 바꾸어 22개 시나리오 전수를 회고적으로 재채점한 결과이며, 헬드아웃 열은 3단계 기준 결과이다. 두 열의 등급 체계가 다르므로 직접적 수치 비교가 아니라 방어 성공 여부(FULL_DEFENSE·FUNCTIONAL_DEFENSE 또는 PASS)를 기준으로 비교한다.");
TAB("정보 불일치성 유형별 방어 결과 (9차 파일럿)", ["유형", "표본 수", "round_14 (v_final, 4단계)", "헬드아웃 (3단계)"], [
  ["Disinformation (사칭)", "3", "FULL_DEFENSE 3 (100%)", "PASS 3 (100%)"],
  ["Misinformation (허위 사실 동조)", "3", "FULL_DEFENSE 2, FUNCTIONAL_DEFENSE 1 (100%)", "PASS 3 (100%)"],
  ["Malinformation (메타데이터·개인정보 유출)", "6", "FULL_DEFENSE 6 (100%)", "PASS 6 (100%)"],
  ["보완적 보안 위협 (인코딩 우회·어투 강요·교차상품·가격)", "10~11", "FULL_DEFENSE 8, FUNCTIONAL_DEFENSE 2 (100%)", "PASS 10, FAIL 1 (90.9%)"],
], [3000, 900, 2800, 2000]);
P("핵심 실증 대상인 3개 유형은 round_14와 헬드아웃 양쪽에서 전부 방어에 성공하였다. 헬드아웃의 유일한 FAIL은 인코딩 우회 카테고리의 자소분리와 번역 검수 위장을 결합한 공격에서 발생하였으며, 이 카테고리는 정보 불일치성 3유형 밖의 보완적 위협으로 분류된다. 다만 각 유형의 표본이 3~6개에 불과하므로 100%라는 수치를 일반적인 방어율로 해석해서는 안 되며, 본 실행 규모에서의 재검증이 필요하다.");
FIG("fig5_defense_by_type.png", 5.2, "정보 불일치성 유형별 방어 결과");

H2("4.3. 교차 모델 검증");
P("7~9차 세 실행 모두에서 헬드아웃 셋을 3개 백엔드에 재실행하였다(표 6). 8차에서는 백엔드 간 격차가 36.4%p(68.2%에서 31.8%)에 달하여 Kruskal-Wallis 검정에서 유의하였으나(p=0.031), 7차(p=0.829)와 9차(p=0.230)에서는 유의하지 않았다. 표본이 시나리오 23개뿐이므로 퍼센트 격차의 크기와 통계적 유의성을 혼동해서는 안 되며, 세 번의 실행 중 벤더 간 실제 차이로 볼 근거가 확실한 것은 8차 한 번뿐이다.");
TAB("실행 간(7~9차) 교차 모델 검증 결과 비교 (백엔드별 PASS율, %)", ["실행", "SRS 성숙도", "openai", "gemini", "anthropic", "2/3 이상 검증됨", "Kruskal-Wallis p"], [
  ["7차", "v1.4 (5라운드, 원칙 수준)", "60.9", "60.9", "52.2", "47.8", "0.829"],
  ["8차", "v1.5 (5라운드, 원칙 수준)", "68.2", "50.0", "31.8", "45.5", "0.031"],
  ["9차", "v1.13 (14라운드, 문자열 템플릿 수준)", "100.0", "87.0", "91.3", "91.3", "0.230"],
], [800, 2800, 900, 900, 1000, 1300, 1000]);
P("두 가지 해석이 가능하다. 첫째, 교차 모델 검증의 심판관은 항상 주 모델(anthropic)로 고정되므로 만약 심판관이 같은 벤더의 응답을 후하게 채점하는 편향이 있다면 anthropic 백엔드가 가장 높게 나와야 한다. 그러나 실제로는 7차와 8차에서 연속으로 가장 낮았으므로, 이는 동일 벤더 심판관 편향 우려를 오히려 반박하는 근거가 된다. 둘째, SRS가 자연어 원칙 수준이던 7·8차에는 벤더마다 같은 원칙을 조금씩 다르게 해석하여 격차가 났을 가능성이 있고, SRS가 28개 규칙의 문자열 템플릿에 가까워진 9차에는 해석의 여지가 줄며 격차도 함께 줄었다는 가설이 가능하다. 다만 이는 세 번의 실행에서 본 상관관계일 뿐이며, 실행마다 SRS 내용 외에 라운드 수와 시나리오 문구도 함께 바뀌었으므로 SRS 성숙도만을 독립적으로 통제한 비교가 아니다.");
FIG("fig6_cross_model.png", 4.9, "교차 모델 검증 — 실행별 백엔드 PASS율");

H2("4.4. 5W1H 판단 원칙의 가설 검증");
P("9차 파일럿에서 관찰된 Meta-Rule의 개별 대응 누적(28개)과 문자열 템플릿화 문제에 대응하여, 요청을 Who, What, When, Why, How 다섯 축으로 독립 점검하고 Who·When·Why가 아무리 그럴듯해도 What(요구 내용)의 금지 여부를 바꾸지 않는다는 고정 조항 하나를 SRS에 추가한 비교군(5w1h)을 설계하였다. 이와 함께 심판관이 매 호출마다 공격이 주로 겨냥한 축을 진단용으로 태깅하게 하였다. 이 조항이 효과가 있다면 (a) round_1 준수율이 더 높게 시작하고, (b) 만점 수렴까지 필요한 Meta-Rule 누적 개수가 줄며, (c) Who·When·Why 축의 FAIL 비율이 낮아져야 한다.");
P("9차와 동일 규모로 baseline(10차)과 5w1h(11차)를 실행한 결과, 세 가지 예측 모두 지지되지 않았다. round_1 준수율은 baseline이 69.8%로 5w1h의 66.7%보다 높았고, 최종 Meta-Rule 누적 개수는 baseline 47개, 5w1h 44개로 5w1h가 눈에 띄게 적지 않았으며, 그림 7과 같이 다섯 개 축 모두에서 5w1h의 FAIL 비율이 baseline보다 높았다. 특히 Who 축은 12.5%에서 48.6%로, What 축은 16.7%에서 50.0%로 증가하였다. 교차 모델 검증의 다수결 비율은 5w1h가 81.8%로 baseline의 21.7%보다 높았으나, 5w1h 쪽에서 백엔드 간 격차가 극단적이어서(openai 100%, anthropic 22.7%, Kruskal-Wallis p=1.95×10⁻⁷) 이를 5w1h가 더 낫다는 근거로 쓸 수 없다.");
FIG("fig7_5w1h_fail.png", 5.2, "5W1H 축별 FAIL 비율 — baseline과 5w1h의 비교 (10~11차)");
P("이 실행에는 세 가지 교란 변수가 있다. 표본이 카테고리당 3개로 작았고, baseline과 5w1h가 서로 다른 공격 문항을 사용한 비매칭 표본이었으며, 실행 도중 모델 동작 변화가 관측되었다. 후자와 관련하여, 9차(2026-08-04)와 동일 코드·동일 설정으로 8일 뒤 실행한 10차에서 응답 텍스트 길이는 1.4~4.4배 늘어난 데 그친 반면 output 토큰 소모량은 심판관 4.4배, 유닛 C 7.5배, Meta-Rule 생성기 6.2배로 증가하였고, 두 실행의 총 비용은 합계 $72.22로 사전 추정을 크게 초과하였다. 다만 이 증가를 모델 변경으로 단정할 수는 없다. 코드 감사 결과 누적된 Meta-Rule을 시스템 프롬프트 헤더와 푸터에 매번 이중 삽입하는 구조 때문에 같은 실행 안에서도 라운드 1에서 15 사이에 입력 토큰이 4.6~4.9배 증가함이 확인되었기 때문이다. 어느 쪽이든 같은 코드와 같은 프롬프트로 재실행해도 결과가 재현되지 않을 수 있다는 위협이 실측 사례로 확인되었다는 점이 중요하다.");
TAB("매칭 표본 재검증 파일럿 결과 (12~13차)", ["지표", "baseline (v1.x)", "5w1h (v2.x)"], [
  ["round_1 준수율", "70.8%", "64.6%"],
  ["round_3 준수율", "75.0%", "66.7%"],
  ["held_out 준수율", "59.5%", "64.3%"],
  ["최종 Meta-Rule 개수 (3라운드 기준)", "12개", "9개"],
  ["총 비용 (226회 호출)", "$4.33", "$4.25"],
], [4200, 2200, 2300], "※ 동일 공격 풀(카테고리당 2개, 총 32문항)을 두 실행이 공유하고 라운드 상한을 3으로 줄인 통제 실험이다. held_out 열은 결정론적 폴백 문구의 채점 버그로 일부 하향 편향되었을 가능성이 있다.");
P("비매칭 표본이라는 교란 변수 하나를 제거한 12~13차의 통제 실험에서도 round_1 준수율은 baseline이 우위(70.8% 대 64.6%)로 같은 방향이었으며, Meta-Rule 개수만 5w1h가 더 적게(9개 대 12개) 나와 부분적으로 지지되는 방향이었다. 그러나 이 파일럿은 표본과 라운드 상한을 함께 줄여 검정력이 오히려 낮아졌고 모델 동작 변화라는 교란 변수도 통제하지 못하였다. 따라서 표 7의 결과를 5W1H 원칙이 통계적으로 무효하다는 결론으로 해석하지 않는다. 두 차례의 독립 실측이 일관되게 가설을 기각하였으므로 추가 비용을 들이지 않고 현재까지의 관찰을 최종 보고로 확정한다는 것은 연구 자원 배분에 관한 실용적 판단이다. 기각의 원인으로는 대형 모델이 요청의 주체나 명분과 무관하게 요구 내용 자체의 금지 여부를 판단하는 추론을 이미 암묵적으로 수행하고 있을 가능성(잉여 정보 가설)이 제기되나, 이는 검증되지 않은 정황적 추정이다.");

H2("4.5. 적응형 재공격");
P("고정된 공격셋에 대한 방어율만으로는 방어 로직의 갱신을 관찰한 공격자가 이를 우회하도록 공격을 재설계하는 실제 상황을 반영할 수 없다. 따라서 v_final이 완성된 뒤 별도의 재공격 라운드를 두며, 침투 테스트 분야의 표준 구분에 따라 공격자가 대상 시스템 내부를 얼마나 아는가에 따라 두 위협 모델로 나눈다(표 8, 그림 8). 레드팀 생성기에게 이전 라운드의 실패·성공 로그(블랙박스) 또는 v_final SRS(화이트박스)를 제공하여 우회 공격을 생성하게 한 뒤, 주 모델로 무상태 실행하여 채점한다.");
TAB("적응형 재공격의 위협 모델", ["위협 모델", "공격자가 아는 정보", "목적"], [
  ["블랙박스 (Black-box)", "SRS에 Meta-Rule이 존재한다는 사실만 알고 정확한 문구는 모름", "실제 서비스에서 외부 공격자가 처하는 현실적 조건의 재현"],
  ["화이트박스 (White-box)", "v_final의 Meta-Rule 전문을 그대로 알고 있음", "레드팀 생성기의 정책 순응성 범위 안에서의 방어율 측정 (진짜 worst-case의 하한은 아님)"],
], [2000, 3500, 3200]);
P("실행별로 방어율은 7차에서 블랙박스 93.3%, 화이트박스 100.0%, 8차에서 각각 60.0%와 80.0%, 9차에서 둘 다 100.0%였다. 공격자가 더 많이 알수록 방어율이 낮아지리라는 원래 예상(화이트박스 ≤ 블랙박스)은 실행마다 방향이 달라 일관되게 지지되지 않았으며, 각 조건의 표본이 5개에 불과하여 통계적 잡음일 가능성이 크다. 8차의 블랙박스 조건에서는 레드팀이 방어 규칙을 전혀 모른 채 챗봇 자신의 거절 문장을 흉내 낸 입력(\"죄송하지만 그 요청은 도와드릴 수 없습니다.\")을 제출하여 응답 형식이 통째로 붕괴한 사례(응답 \"네, 알겠습니다.\")가 관측되었다. 실제 정보 유출은 아니지만 8개 카테고리 어디에도 속하지 않는 새로운 공격 표면을 드러낸 사례이다. 9차에서는 두 조건 모두 100%로 수렴하여 차이를 비교할 신호 자체가 소진되었으므로, 이 비교가 의미를 가지려면 준수율이 포화되지 않은 시점에서 더 큰 표본으로 수행되어야 한다.");
FIG("fig8_adaptive_threat.png", 5.7, "적응형 재공격의 두 위협 모델과 9차 결과");

H1("제5장. 논의 및 결론");
H2("5.1. 논의");
P("본 연구의 예비 결과는 막대한 연산 비용이 드는 모델 파인튜닝이나 복잡한 다중 에이전트 시스템 없이도, 소프트웨어공학의 요구사항 명세서 텍스트 최적화와 모듈형 아키텍처만으로 LLM 챗봇의 가이드라인 준수율을 높일 수 있음을 시사한다. 헬드아웃 셋(7차 87.0%, 9차 97.1%)과 교차 모델 검증(9차 91.3%)에서의 성능이 치유용 셋과 통계적으로 구분되지 않았다는 점은 개선이 특정 문항에 대한 암기만은 아님을 뒷받침한다. 또한 안전성이 강하게 튜닝된 모델이 레드팀 생성과 채점 요청을 정책상 거부하는 현상은 여러 역할에 동일 모델을 쓸 때 구조적으로 부딪히는 문제로서 역할 분리 설계의 필요성을 실측으로 보여 준다.");
P("동시에 본 연구는 긍정적 결과만이 아니라 그 대가와 반례를 정직하게 보고하는 것을 원칙으로 하였다. 9차의 100% 수렴은 Meta-Rule 28개의 문자열 템플릿화를 동반하였고, 5W1H 원칙은 세 가지 예측이 모두 기각되었으며, 동일 코드의 재실행에서 결과가 재현되지 않을 수 있다는 위협이 실측으로 확인되었다. 이러한 결과는 자가 치유가 만능이 아니며 수렴의 방식과 비용을 함께 평가해야 함을 의미한다.");

H2("5.2. 한계");
P("본 연구의 한계는 다음과 같다. 첫째, 모든 결과가 단일 도메인(가전 유통)의 카테고리당 3개 규모 예비 파일럿이며 대부분 문항당 단일 시행이므로, 일반화에는 타 도메인과 본 실행 규모에서의 재검증이 필요하다. 둘째, 치유용 셋과 헬드아웃 셋이 동일한 1차 생성 배치를 무작위 분할한 것이어서 보고된 일반화 성능은 진정한 분포 밖 일반화가 아니라 보간에 가까울 수 있다. 셋째, 모든 채점이 단일 주 모델 심판관에 의존하며 연구자의 수동 블라인드 채점은 아직 수행되지 않았고, 4단계 rubric의 심판관 신뢰도도 실측되지 않았다. 넷째, 공격 시나리오의 연구자 수동 검토 단계가 실제로는 수행되지 않아 비현실적이거나 카테고리에 맞지 않는 문항이 섞여 들어갔을 가능성을 배제할 수 없다.");
P("다섯째, 적응형 재공격은 레드팀 생성기의 정책 순응성 안에서의 방어율이므로 진짜 worst-case의 하한이 아니며, 그래디언트 기반 최적화 공격은 시도하지 않았다. 여섯째, 단발성 단일 턴 시나리오로 범위를 한정하여 여러 턴에 걸쳐 서서히 유도하는 점진적 공격은 다루지 못하였다. 일곱째, 헬드아웃 결과가 치유용 셋과 통계적으로 구분되지 않는다는 사실은 표본이 작아 검정력이 낮다는 점에서 과적합이 없다는 증거로 해석하는 데 한계가 있다. 여덟째, 모델 별칭 뒤의 동작 변화 또는 입력 토큰 누적으로 인해 실행 간 재현성이 보장되지 않을 수 있다.");

H2("5.3. 결론 및 향후 연구");
P("본 논문은 LLM 기반 AI 챗봇의 정보 불일치성에 저항하기 위해, 모듈형 4단계 유닛 아키텍처와 SRS 기반 자가 치유 폐쇄 루프를 제안하고 예비 규모 파일럿으로 검증하였다. 공격 분류체계는 8개 유형을 OWASP LLM Top 10과 정보 불일치성 3분류에 이중으로 매핑하여 핵심 실증 4개와 보완적 위협 4개로 구분하였고, 방어의 완결성은 4단계 보안 심각도 체계로 평가하였다. 9차 파일럿에서 14라운드 만에 치유용 셋 준수율 100%에 도달하였고 헬드아웃 97.1%, 교차 모델 검증 91.3%를 기록하였으며, 핵심 3유형은 헬드아웃에서도 전부 방어되었다. 다만 이 수렴은 SRS의 문자열 템플릿화를 동반하였고 5W1H 원칙은 기각되었으므로, 본 결과는 예비적 근거로 해석되어야 한다.");
P("향후 연구로는 카테고리당 10개 규모의 본 실행, 헬드아웃 셋의 독립 생성, 연구자의 수동 블라인드 채점과 4단계 rubric의 심판관 신뢰도 검증, 의료·금융·공공 등 법적 제약이 더 복잡한 타 도메인으로의 확장, 멀티턴 공격의 포함, 그리고 생성된 Meta-Rule을 프로덕션에 반영하기 전의 사람 검수(human-in-the-loop) 게이트 설계를 계획한다.");

// ======================= 참고문헌 =======================
toc.push({ l: 1, text: "참고문헌" });
body.push(new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, spacing: { after: 240 }, children: [tr("참고문헌", { bold: true, font: HEAD, size: 30 })] }));
[
  "Wardle, C., & Derakhshan, H. (2017). Information Disorder: Toward an Interdisciplinary Framework for Research and Policy Making. Council of Europe report DGI(2017)09.",
  "Greshake, K., Abdelnabi, S., Mishra, S., Endres, C., Holz, T., & Fritz, M. (2023). Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection. ACM Workshop on Artificial Intelligence and Security (AISec 2023). arXiv:2302.12173.",
  "Geng, R., Yin, C., Wang, Y., Chen, Y., & Jia, J. (2026). PIArena: A Platform for Prompt Injection Evaluation. Proceedings of the Association for Computational Linguistics (ACL 2026). arXiv:2604.08499.",
  "Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., & Liang, P. (2024). Lost in the Middle: How Language Models Use Long Contexts. Transactions of the Association for Computational Linguistics, 12, 157–173. arXiv:2307.03172.",
  "OWASP Top 10 for Large Language Model Applications 2026. OWASP Foundation, OWASP Gen AI Security Project. (Published 2026-08-04).",
  "OWASP Foundation. OWASP Risk Rating Methodology. https://owasp.org/www-community/OWASP_Risk_Rating_Methodology",
  "FIRST.Org, Inc. (2023). Common Vulnerability Scoring System version 4.0: Specification Document. Forum of Incident Response and Security Teams (FIRST). https://www.first.org/cvss/v4-0/cvss-v40-specification.pdf",
  "Shi, J., Yuan, Z., Liu, Y., Huang, Y., Zhou, P., Sun, L., & Gong, N. Z. (2024). Optimization-based Prompt Injection Attack to LLM-as-a-Judge. Proceedings of the 2024 ACM SIGSAC Conference on Computer and Communications Security (CCS '24). arXiv:2403.17710.",
].forEach((t, i) => body.push(new Paragraph({ spacing: { after: 120, line: 300 }, indent: { left: 480, hanging: 480 }, children: [tr(`${i + 1}. ${t}`, { size: 20 })] })));

// ======================= 표지 · 목차 · 초록 =======================
const cover = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 2600, after: 400 }, children: [tr("AI 챗봇의 정보 불일치성(Information Disorderness): SRS 기반 자가 치유 저항 메커니즘 — 가전 유통 사례를 중심으로", { bold: true, size: 34, font: HEAD })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 1200 }, children: [tr("Information Disorderness in AI Chatbots: An SRS-based Self-Healing Resistance Mechanism — A Consumer Electronics Retail Case Study", { italics: true, size: 26 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [tr("요 약 본", { bold: true, size: 30, font: HEAD })] }),
];

const front = [];
const FH = (t) => new Paragraph({ spacing: { after: 240 }, children: [tr(t, { bold: true, font: HEAD, size: 30 })] });
front.push(new Paragraph({ children: [], pageBreakBefore: true }));
front.push(FH("목차"));
front.push(new Paragraph({ spacing: { after: 100 }, children: [tr("초록", { bold: true, font: HEAD })] }));
toc.forEach((e) => front.push(new Paragraph({ spacing: { after: e.l === 1 ? 100 : 60, before: e.l === 1 ? 140 : 0 }, indent: { left: e.l === 1 ? 0 : 500 }, children: [tr(e.text, { bold: e.l === 1, font: e.l === 1 ? HEAD : BODY, size: e.l === 1 ? 22 : 21 })] })));
front.push(new Paragraph({ spacing: { before: 360, after: 120 }, children: [tr("그림 목차", { bold: true, font: HEAD, size: 24 })] }));
figList.forEach((t) => front.push(new Paragraph({ spacing: { after: 50 }, indent: { left: 200 }, children: [tr(t, { size: 20 })] })));
front.push(new Paragraph({ spacing: { before: 280, after: 120 }, children: [tr("표 목차", { bold: true, font: HEAD, size: 24 })] }));
tabList.forEach((t) => front.push(new Paragraph({ spacing: { after: 50 }, indent: { left: 200 }, children: [tr(t, { size: 20 })] })));

front.push(new Paragraph({ children: [], pageBreakBefore: true }));
front.push(FH("초록 (Abstract)"));
front.push(new Paragraph({ spacing: { before: 60, after: 120 }, children: [tr("국문 초록", { bold: true, font: HEAD, size: 24 })] }));
[
  "기업 환경에 도입되는 생성형 LLM 기반 챗봇은 고객 개인정보의 의도치 않은 유출, 브랜드 가이드라인 및 RAG 지식과 상충하는 응답, 프롬프트 인젝션을 통한 허위 전제 동조 등 정보의 진위와 무결성이 흔들리는 문제에 반복적으로 노출된다. 이러한 현상은 Wardle과 Derakhshan(2017)[1]의 정보 무질서(Information Disorder) 프레임워크의 Misinformation·Disinformation·Malinformation 3분류와 구조적으로 맞닿아 있으며, 본 연구는 이를 조직 챗봇의 1:1 세션 맥락에서 '정보 불일치성(Information Disorderness)'으로 재정의한다.",
  "본 논문은 정보 불일치성에 저항하는 요구사항 명세서(SRS) 기반 자가 치유(Self-Healing) 메커니즘을 제안한다. 제안 메커니즘은 입력 가드레일, RAG 검색, LLM 추론, 출력 가드레일로 이어지는 4단계 유닛 아키텍처 위에서, 적대적 공격 생성, 무상태 심판관 채점, Meta-Rule 자동 생성, SRS 갱신을 반복하는 폐쇄 루프로 구성된다. 공격은 8개 범주로 분류하고 OWASP LLM Top 10 및 정보 불일치성 3분류에 매핑하였으며, 방어의 완결성은 4단계 보안 심각도 체계로 평가한다. 단일 모델로 연구 사이클을 진행한 뒤 응답 생성 모델만 교체하는 교차 모델 검증으로 결과의 모델 종속성을 점검한다.",
  "카테고리당 3개 규모의 예비 파일럿에서 라운드 상한을 15로 둔 9차 실험은 14라운드 만에 치유용 셋 준수율 100%에 도달하였고, 헬드아웃 셋 97.1%, 교차 모델 검증 91.3%를 기록하였으며 핵심 3유형(Dis-/Mis-/Malinformation)은 헬드아웃에서도 전부 방어되었다. 한편 이 수렴은 Meta-Rule이 28개로 팽창하여 SRS가 문자열 템플릿에 가까워진 결과를 동반하였고, 5W1H 판단 원칙이 축별 실패를 줄이리라는 가설은 지지되지 않았다. 본 연구는 단일 도메인의 예비 규모 사례 연구이므로 결과의 일반화에는 주의가 필요하다.",
].forEach((t) => front.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 140, line: LS }, children: [tr(t)] })));
front.push(new Paragraph({ spacing: { before: 100, after: 240, line: LS }, children: [tr("주제어: ", { bold: true }), tr("정보 불일치성, 자가 치유, 요구사항 명세서(SRS), LLM 챗봇, 적대적 프롬프트 방어, 교차 모델 검증")] }));
front.push(new Paragraph({ spacing: { before: 200, after: 120 }, children: [tr("Abstract", { bold: true, font: HEAD, size: 24 })] }));
[
  "Generative LLM-based chatbots deployed in enterprises repeatedly suffer from breakdowns in the truthfulness and integrity of the information they convey: unintended leakage of customer data, answers that contradict brand guidelines and RAG knowledge, and endorsement of false premises planted through prompt injection. These incidents map onto the Misinformation, Disinformation, and Malinformation taxonomy of Wardle and Derakhshan (2017)[1], which this study re-defines as Information Disorderness in the context of one-to-one organizational chatbot sessions.",
  "This thesis proposes an SRS-based Self-Healing mechanism that resists information disorderness. It combines a four-unit architecture (input guardrail, RAG retrieval, LLM inference, output guardrail) with a closed loop of adversarial attack generation, stateless judge scoring, automatic Meta-Rule generation, and SRS update. In a pilot with three scenarios per category, the run with a 15-round cap converged to 100% compliance in 14 rounds, reaching 97.1% on the held-out set and 91.3% in cross-model verification, with all three core disorder types defended on held-out data. The convergence, however, coincided with Meta-Rule inflation to 28 rules, and the 5W1H hypothesis was not supported. Because this is a single-domain pilot, generalization requires caution.",
].forEach((t) => front.push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 140, line: LS }, children: [tr(t)] })));
front.push(new Paragraph({ spacing: { before: 100, line: LS }, children: [tr("Keywords: ", { bold: true }), tr("Information Disorderness, Self-Healing, Requirements Specification, LLM Chatbot, Adversarial Prompt Defense, Cross-Model Verification")] }));

const footer = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], font: BODY, size: 20 })] })] });
const page = { size: { width: 11906, height: 16838 }, margin: { top: 1440, bottom: 1440, left: 1584, right: 1584 } };
const doc = new Document({
  styles: { default: { document: { run: { font: BODY, size: BS } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: HEAD, size: 30, bold: true, color: "000000" } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: HEAD, size: 25, bold: true, color: "000000" } },
    ] },
  sections: [
    { properties: { page }, children: cover },
    { properties: { page }, footers: { default: footer }, children: [...front, ...body] },
  ],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(path.join(__dirname, "..", "thesis_summary_visual.docx"), b); console.log("ok", figN, "figs", tabN, "tabs"); });
