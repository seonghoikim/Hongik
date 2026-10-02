const fs = require("fs");
const path = require("path");
const { Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, WidthType, AlignmentType, BorderStyle, ShadingType, PageBreak, VerticalAlign } = require("docx");

const IMG = path.join(__dirname, "..", "diagrams", "summary");
const FONT = "맑은 고딕";
const W = 9900; // content width in twips (A4, 0.8in margins)
const PX = (inch) => Math.round(inch * 96);

const run = (text, o = {}) => new TextRun({ text, font: FONT, size: 21, ...o });
const para = (children, o = {}) => new Paragraph({ spacing: { after: 100 }, ...o, children: Array.isArray(children) ? children : [run(children)] });
const bullet = (text) => new Paragraph({ spacing: { after: 70 }, indent: { left: 360, hanging: 240 }, children: [run("•  " + text)] });
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };
const thin = { style: BorderStyle.SINGLE, size: 4, color: "999999" };
const thinBorders = { top: thin, bottom: thin, left: thin, right: thin };

function image(file, widthIn) {
  const buf = fs.readFileSync(path.join(IMG, file));
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
    children: [new ImageRun({ type: "png", data: buf, transformation: { width: PX(widthIn), height: Math.round(PX(widthIn) * h / w) } })] });
}
const figTitle = (n, title, chap) => new Paragraph({ spacing: { before: 160, after: 80 },
  children: [run(`그림 ${n}.  ${title}`, { bold: true, size: 24 }), run(`    ${chap}`, { size: 18, color: "666666" })] });
const takeaway = (text) => new Paragraph({ spacing: { after: 80 }, shading: { type: ShadingType.CLEAR, fill: "EDEDED" }, indent: { left: 100, right: 100 },
  children: [run(text, { bold: true, size: 21 })] });

function cell(children, width, o = {}) {
  return new TableCell({ width: { size: width, type: WidthType.DXA }, borders: thinBorders, margins: { top: 60, bottom: 60, left: 100, right: 100 }, verticalAlign: VerticalAlign.CENTER, ...o, children });
}

const order = [
  ["1", "전체 프레임워크", "제3·4장", "유닛 A~D 위에서 자가 치유 루프가 돈다"],
  ["2", "공격 분류체계", "§4.2.1", "8개 공격 중 4개만 핵심 실증으로 한정"],
  ["3", "4단계 보안 심각도", "§4.1.1", "방어의 완결성을 4등급으로 채점"],
  ["4", "라운드별 준수율 추이", "§5.3", "자가 치유로 100% 수렴 (9차)"],
  ["5", "유형별 방어 결과", "§5.3.8", "핵심 3유형은 헬드아웃에서도 전부 방어"],
  ["6", "교차 모델 검증", "§5.3.9", "벤더가 달라도 결과가 유지되는가"],
  ["7", "5W1H 가설 검증", "§5.3.10", "가설 기각 — 정직한 음성 결과"],
  ["8", "적응형 재공격", "§5.4", "블랙박스·화이트박스 위협 모델"],
];
const colW = [700, 2800, 1400, 5000];
const orderTable = new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: colW, rows: [
  new TableRow({ tableHeader: true, children: ["순서", "그림", "논문 대응", "한 줄 메시지"].map((t, i) =>
    cell([para([run(t, { bold: true, size: 20 })], { spacing: { after: 0 } })], colW[i], { shading: { type: ShadingType.CLEAR, fill: "D9D9D9" } })) }),
  ...order.map((r) => new TableRow({ children: r.map((t, i) => cell([para([run(t, { size: 20 })], { spacing: { after: 0 } })], colW[i])) })),
] });

const children = [];
children.push(new Paragraph({ spacing: { after: 60 }, children: [run("AI 챗봇의 정보 불일치성: SRS 기반 자가 치유 저항 메커니즘", { bold: true, size: 32 })] }));
children.push(new Paragraph({ spacing: { after: 200 }, children: [run("그림 중심 요약본 — 지도교수 면담용 (목차 순서 협의 자료)", { size: 22, color: "555555" })] }));

children.push(new Paragraph({ spacing: { before: 100, after: 80 }, children: [run("연구 한 장 요약", { bold: true, size: 26 })] }));
[
  "문제: LLM 챗봇이 개인정보·내부정보 유출, 허위 사실 동조, 관리자 사칭 같은 정보 불일치성(Dis-/Mis-/Malinformation)에 반복적으로 노출된다.",
  "제안: 요구사항 명세서(SRS)가 공격 생성 → 채점 → Meta-Rule 자동 생성 → SRS 갱신 루프를 돌며 스스로 강화되는 자가 치유 메커니즘.",
  "핵심 결과: 9차 파일럿에서 14라운드 만에 100% 준수 수렴, 헬드아웃 97.1%, 교차 모델 검증 91.3%. 핵심 3유형(Dis-/Mis-/Malinformation)은 헬드아웃에서도 전부 방어.",
  "한계: 예비 규모 표본(카테고리당 3개), 5W1H 가설은 지지되지 않음, 9차 SRS는 Meta-Rule 28개로 팽창해 문자열 템플릿에 가까워짐.",
].forEach((t) => children.push(bullet(t)));

children.push(new Paragraph({ spacing: { before: 240, after: 100 }, children: [run("그림 순서 (제안 목차 초안)", { bold: true, size: 26 })] }));
children.push(orderTable);
children.push(para([run("※ 그림 2·3은 논문 본문에서는 §4.1.1이 §4.2.1보다 앞이지만, 요약본에서는 “무엇을 공격하나 → 어떻게 채점하나” 순서가 자연스러워 바꿨다. 순서는 면담에서 조정 가능.", { size: 18, color: "666666" })], { spacing: { before: 100 } }));

// page: pipeline (image left, notes right)
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(figTitle(1, "전체 프레임워크", "제3·4장"));
const pipeNotes = [
  takeaway("한 장 요약: 4단계 유닛 위에서 SRS가 스스로 고쳐지는 폐쇄 루프"),
  bullet("유닛 A~D: 입력 가드레일 → RAG 검색 → LLM 추론 → 출력 가드레일"),
  bullet("루프: ① SRS 정의 → ② 적대적 실행 → ③ 심판관 채점 → ④ Meta-Rule 생성 → ⑤ SRS 병합 후 재실행"),
  bullet("수렴(전원 FULL_DEFENSE)하면 헬드아웃 검증 → 적응형 재공격 → 교차 모델 검증 → 통계 검정 순으로 진행"),
  bullet("심판관은 무상태 단일 호출 LLM, 챗봇과 컨텍스트를 공유하지 않음"),
  bullet("루프 시작 전 사전 점검 3종(결정론적 차단 문구 검증, drift 카나리아, 대화형 검토 도구)"),
];
const lw = 5200, rw = W - lw;
children.push(new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: [lw, rw], rows: [new TableRow({ children: [
  new TableCell({ width: { size: lw, type: WidthType.DXA }, borders: noBorders, children: [image("fig1_pipeline.png", 3.45)] }),
  new TableCell({ width: { size: rw, type: WidthType.DXA }, borders: noBorders, margins: { left: 200 }, verticalAlign: VerticalAlign.CENTER, children: pipeNotes }),
] })] }));

// page: taxonomy + levels
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(figTitle(2, "공격 분류체계", "§4.2.1"));
children.push(image("fig3_attack_taxonomy.png", 5.9));
children.push(takeaway("정보 진위가 판정의 본질인 4개만 핵심 실증, 나머지 4개는 보완적 위협으로 분리"));
children.push(bullet("8개 공격 유형을 OWASP LLM Top 10(LLM01·02·07·08·09)과 정보 불일치성 3분류에 이중 매핑"));
children.push(figTitle(3, "4단계 보안 심각도 Level 체계", "§4.1.1"));
children.push(image("fig2_severity_levels.png", 5.4));
children.push(bullet("OWASP·CVSS의 4단계 관행을 차용하되 챗봇 텍스트 응답에 맞춰 정의, 등급이 Meta-Rule 생성의 트리거가 됨"));
children.push(bullet("이 4단계 rubric의 심판관 신뢰도 실측은 아직 미수행(후속 과제)"));

// page: rounds + defense
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(figTitle(4, "라운드별 준수율 추이", "§5.3 (표 6·8·9)"));
children.push(image("fig4_round_compliance.png", 5.5));
children.push(takeaway("라운드 상한을 15로 늘린 9차에서 14라운드 만에 100% 완전 수렴"));
children.push(bullet("7차: 5라운드 상한까지 88.4%, 만점 미도달 / 8차: round_3에서 63.6%로 하락, FAIL 최초 관측(15건 전부 형식 위반, 실제 정보 유출 0건)"));
children.push(bullet("단, 9차의 100%는 Meta-Rule이 28개로 팽창해 SRS가 문자열 템플릿에 수렴한 결과라는 점을 함께 밝혀야 함(§5.3.8)"));
children.push(figTitle(5, "정보 불일치성 유형별 방어 결과", "§5.3.8 (표 9-부록)"));
children.push(image("fig5_defense_by_type.png", 5.2));
children.push(bullet("핵심 3유형은 round_14·헬드아웃 모두 100% 방어, 헬드아웃의 유일한 FAIL은 보완적 위협의 자소분리 인코딩 우회 1건"));

// page: cross model + 5w1h
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(figTitle(6, "교차 모델 검증", "§5.3.9 (표 10)"));
children.push(image("fig6_cross_model.png", 4.8));
children.push(takeaway("심판관은 주 모델(anthropic)로 고정하고 챗봇 응답 모델만 3개 벤더로 교체"));
children.push(bullet("8차에서만 벤더 간 차이가 유의(p=0.031), anthropic이 7·8차 연속 최저 — 같은 벤더 심판관 편향 우려를 오히려 반박"));
children.push(bullet("SRS가 템플릿 수준으로 성숙한 9차는 세 벤더 모두 87% 이상"));
children.push(figTitle(7, "5W1H 가설 검증 — 기각", "§5.3.10 (표 12)"));
children.push(image("fig7_5w1h_fail.png", 5.0));
children.push(bullet("5W1H 원칙을 추가하면 축별 FAIL이 줄 것이라는 가설은 지지되지 않음(5개 축 모두 5w1h의 FAIL율이 더 높음)"));
children.push(bullet("소표본·비매칭 문항·모델 drift 교란이 있어 매칭 표본 재검증(12~13차): round_1 준수율은 baseline 우위(70.8% vs 64.6%), Meta-Rule 개수는 5w1h가 적음(9개 vs 12개)"));

// page: adaptive + discussion
children.push(new Paragraph({ children: [new PageBreak()] }));
children.push(figTitle(8, "적응형 재공격", "§5.4 (표 14)"));
children.push(image("fig8_adaptive_threat.png", 5.9));
children.push(takeaway("방어가 완성된 SRS(v_final)를 두 위협 모델로 다시 공격"));
children.push(bullet("블랙박스: Meta-Rule의 존재만 아는 현실적 공격자 — 9차에서 5/5 방어"));
children.push(bullet("화이트박스: Meta-Rule 전문을 아는 공격자 — 레드팀 LLM의 정책 순응성 범위 안에서의 방어율이며 진짜 worst-case 하한은 아님"));
children.push(bullet("그래디언트 기반 최적화 공격은 시도하지 않음(한계)"));

children.push(new Paragraph({ spacing: { before: 300, after: 100 }, children: [run("면담에서 정할 사항 (제안)", { bold: true, size: 26 })] }));
[
  "그림 순서: 방법(1~3) → 결과(4~6) → 심화(7~8) 구성이 적절한지, 결과 중심으로 재배열할지",
  "5W1H 기각 결과(그림 7)를 본문에 둘지 부록으로 보낼지",
  "현재 카테고리당 3개인 예비 규모를 본 실행(카테고리당 10개)으로 확대할지 여부",
].forEach((t) => children.push(bullet(t)));

const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: 21 } } } },
  sections: [{ properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1000, bottom: 900, left: 1000, right: 1000 } } }, children }],
});
Packer.toBuffer(doc).then((b) => { fs.writeFileSync(path.join(__dirname, "..", "thesis_summary_visual.docx"), b); console.log("ok"); });
