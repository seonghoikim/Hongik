/**
 * thesis_report.md -> thesis_report_with_visuals.docx 변환 스크립트.
 *
 * build_thesis_report_docx.js와 동일한 마크다운 변환 로직에, diagrams/drafts_visualization/
 * 아래 13개 시각화 초안(PNG)을 본문 관련 위치에 그림으로 삽입하는 기능을 추가한다.
 * thesis_report.md 자체는 건드리지 않고, 이 스크립트가 만드는 별도 산출물에만 반영한다.
 *
 * 사용법: 이 저장소 바깥 아무 디렉터리에서 `npm install docx`(docx.js, v9+) 후
 *   node scripts/build_thesis_report_with_visuals.js
 * 를 실행하면 /home/user/hongik/thesis_report_with_visuals.docx가 생성된다.
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, BorderStyle, AlignmentType, TableOfContents, ImageRun, LevelFormat,
  ShadingType, VerticalAlign, PageBreak, convertInchesToTwip,
} = require("docx");

const SRC = "/home/user/hongik/thesis_report.md";
const ASSETS = "/home/user/hongik/thesis_assets";
const VISUALS = "/home/user/hongik/diagrams/drafts_visualization";
const OUT = "/home/user/hongik/thesis_report_with_visuals.docx";

const BODY_FONT = "바탕체";
const HEADING_FONT = "돋움체";
const CODE_FONT = "Consolas";
const BODY_SIZE = 22; // half-points = 11pt
const LINE_SPACING = 360; // 240 = single; 360 = 150%

const raw = fs.readFileSync(SRC, "utf-8");
const lines = raw.split("\n");

// ---------- 목차: docx.js의 동적 TableOfContents 필드는 실제 Word가 한 번 열어서
// "필드 업데이트"를 실행하기 전까지는 빈 채로 보인다(페이지 번호를 계산할 워드 엔진이
// 이 스크립트 실행 시점엔 없기 때문). 대신 헤딩을 미리 훑어 정적 목차를 직접 만든다 —
// 페이지 번호는 못 넣지만(최종 인쇄본에서 Word가 다시 계산), 열자마자 전체 구조가 보인다.
const tocEntries = [];
for (const l of lines) {
  const m = l.match(/^(#{2,4})\s+(.*)$/);
  if (m) tocEntries.push({ level: m[1].length, text: m[2] });
}

// ---------- 새로 삽입할 그림 목록 (문서 순서대로) ----------
// tableTrigger: 표 캡션 줄에 포함된 문자열 -> 그 표가 끝난 직후 삽입
// lineTrigger : 특정 본문/목록 줄에 포함된 문자열 -> 그 줄 문단이 끝난 직후 삽입
// quoteTrigger: 인용문(blockquote) 블록 안에 포함된 문자열 -> 그 인용 블록이 끝난 직후 삽입
const VISUAL_INSERTS = [
  { kind: "table", match: "표 4. 4단계 보안 심각도 Level 정의",
    file: "2_4단계_보안심각도_Level체계.png", w: 240, h: 820,
    caption: "그림 3. 4단계 보안심각도 Level 체계 (§4.1.1 표4)" },
  { kind: "table", match: "표 5. 공격 유형 – OWASP LLM Top 10 매핑",
    file: "3_공격유형_OWASP_매핑.png", w: 560, h: 752,
    caption: "그림 4. 공격유형–OWASP LLM Top 10 매핑 (§4.2.1 표5)" },
  { kind: "table", match: "표 5-부록. 정보 불일치성 3분류 매핑",
    file: "1_정보불일치성_3분류_매핑.png", w: 560, h: 571,
    caption: "그림 5. 정보 불일치성 3분류 매핑 (§4.2.1 표5-부록)" },
  { kind: "line", match: "1차 생성(레드팀 LLM, GPT-5.4)과 3차 분할(층화추출)은 코드로 구현·실행되어",
    file: "13_데이터분할_구조.png", w: 327, h: 820,
    caption: "그림 6. 치유용/헬드아웃 데이터 분할 구조 (§4.2.2)" },
  { kind: "quote", match: "명세서에 명시된 절대 금지 조항을 정면으로 어긴 사례이므로 FAIL에 해당한다",
    file: "11_공격응답판정_예시카드.png", w: 560, h: 615,
    caption: "그림 8. Action Matrix 실제 채점 사례 — 공격 → 응답 → 판정 (§5.3.7)" },
  { kind: "table", match: "표 9. 9차 파일럿(`real_20260804_102353`) 라운드별 채점 결과",
    file: "4_라운드별_준수율_추이.png", w: 560, h: 335,
    caption: "그림 9. 라운드별 준수율 추이 — 7·8·9차 파일럿 비교 (표6·표8·표9)" },
  { kind: "table", match: "표 9-부록. round_14(v_final)·헬드아웃의 정보 불일치성 3유형별 결과",
    file: "9_정보불일치성_유형별_방어결과.png", w: 560, h: 342,
    caption: "그림 10. 정보 불일치성 유형별 방어 결과 (표9-부록)" },
  { kind: "table", match: "표 10. 실행 간(7~9차) 교차 모델 검증 결과 비교",
    file: "5_교차모델_검증_벤더별_비교.png", w: 560, h: 389,
    caption: "그림 11. 교차 모델 검증 벤더별 비교 (표10)" },
  { kind: "table", match: "표 12. 5W1H 축별 FAIL 비율 비교",
    file: "6_5W1H_축별_FAIL율_비교.png", w: 560, h: 381,
    caption: "그림 12. 5W1H 축별 FAIL율 비교 (표12)" },
  { kind: "line", match: "응답 텍스트 길이는 별로 늘지 않았는데 output 토큰 소모량만 4~7배 뛰었다",
    file: "7_토큰소비량_증가_drift.png", w: 560, h: 381,
    caption: "그림 13. 역할별 평균 output 토큰 증가 (§5.3.10)" },
  { kind: "table", match: "표 13. 매칭 표본 파일럿 결과 비교",
    file: "8_MetaRule_누적개수.png", w: 560, h: 345,
    caption: "그림 14. 실행별 누적 Meta-Rule 개수 (§5.3.8·§5.3.10·§5.3.11)" },
  { kind: "table", match: "표 14. 적응형 재공격의 2가지 위협 모델",
    file: "10_적응형재공격_위협모델_비교.png", w: 560, h: 355,
    caption: "그림 15. 적응형 재공격 — 블랙박스 vs 화이트박스 위협모델 비교 (표14)" },
  { kind: "line", match: "부록 H. 실행 환경 스냅샷 및 토큰 사용량·비용 실측치",
    file: "12_실행별_비용_실측치.png", w: 560, h: 345,
    caption: "그림 16. 실행별 비용 실측치 (부록 H)" },
];
const usedInserts = new Set();

// ---------- inline markdown -> TextRun[] ----------
function parseInline(text, extra = {}) {
  const runs = [];
  const re = /(\*\*.+?\*\*|`[^`]+`|\*[^*]*\s[^*]*\*)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) runs.push(new TextRun({ text: text.slice(last, m.index), font: BODY_FONT, size: BODY_SIZE, ...extra }));
    const t = m[0];
    if (t.startsWith("**")) {
      runs.push(new TextRun({ text: t.slice(2, -2), bold: true, font: BODY_FONT, size: BODY_SIZE, ...extra }));
    } else if (t.startsWith("`")) {
      runs.push(new TextRun({ text: t.slice(1, -1), font: CODE_FONT, size: BODY_SIZE - 2, ...extra }));
    } else {
      runs.push(new TextRun({ text: t.slice(1, -1), italics: true, font: BODY_FONT, size: BODY_SIZE, ...extra }));
    }
    last = re.lastIndex;
  }
  if (last < text.length) runs.push(new TextRun({ text: text.slice(last), font: BODY_FONT, size: BODY_SIZE, ...extra }));
  if (runs.length === 0) runs.push(new TextRun({ text: "", font: BODY_FONT, size: BODY_SIZE, ...extra }));
  return runs;
}

function bodyPara(text, opts = {}) {
  return new Paragraph({
    children: parseInline(text, opts.runExtra || {}),
    spacing: { after: 160, line: LINE_SPACING },
    alignment: AlignmentType.JUSTIFIED,
    ...opts.paraProps,
  });
}

function warningPara(text) {
  return new Paragraph({
    children: parseInline(text, { italics: true, color: "555555" }),
    spacing: { before: 80, after: 160, line: LINE_SPACING },
    shading: { type: ShadingType.CLEAR, fill: "F2F2F2" },
    border: { left: { style: BorderStyle.SINGLE, size: 12, color: "AAAAAA", space: 8 } },
    indent: { left: 200 },
  });
}

function quotePara(text) {
  return new Paragraph({
    children: parseInline(text || "", { italics: true, color: "444444" }),
    spacing: { after: 60, line: LINE_SPACING },
    indent: { left: 400 },
    border: { left: { style: BorderStyle.SINGLE, size: 8, color: "CCCCCC", space: 8 } },
  });
}

function codeLine(text) {
  return new Paragraph({
    children: [new TextRun({ text: text.length ? text : " ", font: CODE_FONT, size: 17 })],
    spacing: { before: 0, after: 0, line: 260 },
    shading: { type: ShadingType.CLEAR, fill: "EDEDED" },
  });
}

function bulletPara(text, level = 0) {
  return new Paragraph({
    children: parseInline(text),
    numbering: { reference: "bullet-list", level },
    spacing: { after: 120, line: LINE_SPACING },
  });
}

function orderedLikePara(num, text) {
  return new Paragraph({
    children: [
      new TextRun({ text: num + ". ", font: BODY_FONT, size: BODY_SIZE, bold: true }),
      ...parseInline(text),
    ],
    indent: { left: 400, hanging: 400 },
    spacing: { after: 140, line: LINE_SPACING },
  });
}

function headingPara(level, text) {
  const map = { 1: HeadingLevel.TITLE, 2: HeadingLevel.HEADING_1, 3: HeadingLevel.HEADING_2, 4: HeadingLevel.HEADING_3 };
  return new Paragraph({
    heading: map[level],
    pageBreakBefore: level === 2,
    spacing: { before: level === 2 ? 0 : 360, after: 240 },
    children: [new TextRun({ text, font: HEADING_FONT, bold: true })],
  });
}

function parseTableRow(line) {
  let l = line.trim();
  if (l.startsWith("|")) l = l.slice(1);
  if (l.endsWith("|")) l = l.slice(0, -1);
  return l.split("|").map((c) => c.trim());
}
function isSepRow(line) {
  const cells = parseTableRow(line);
  return cells.every((c) => /^:?-+:?$/.test(c));
}

function makeTable(rows) {
  const nCols = rows[0].length;
  const colWidth = Math.floor(9000 / nCols);
  const trows = rows.map((cells, ri) => {
    return new TableRow({
      tableHeader: ri === 0,
      children: cells.map((c) => new TableCell({
        width: { size: colWidth, type: WidthType.DXA },
        shading: ri === 0 ? { type: ShadingType.CLEAR, fill: "DCE6F1" } : undefined,
        verticalAlign: VerticalAlign.CENTER,
        margins: { top: 60, bottom: 60, left: 100, right: 100 },
        children: [new Paragraph({
          children: parseInline(c, ri === 0 ? { bold: true } : {}),
          spacing: { line: 300 },
        })],
      })),
    });
  });
  return new Table({
    rows: trows,
    width: { size: 9000, type: WidthType.DXA },
    columnWidths: Array(nCols).fill(colWidth),
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: "888888" },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: "888888" },
      left: { style: BorderStyle.SINGLE, size: 4, color: "888888" },
      right: { style: BorderStyle.SINGLE, size: 4, color: "888888" },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: "BBBBBB" },
      insideVertical: { style: BorderStyle.SINGLE, size: 2, color: "BBBBBB" },
    },
  });
}

function imagePara(file, width, height, baseDir) {
  const data = fs.readFileSync(path.join(baseDir, file));
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 60 },
    children: [new ImageRun({ data, type: "png", transformation: { width, height } })],
  });
}

function captionPara(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 240 },
    children: [new TextRun({ text, italics: true, size: BODY_SIZE - 4, font: BODY_FONT, color: "555555" })],
  });
}

// 트리거 문자열이 포함된 텍스트를 만나면 해당 종류(kind)의 미사용 삽입 항목을 하나 소비해 그림+캡션을 추가
function tryInsertVisual(children, kind, text) {
  for (const v of VISUAL_INSERTS) {
    if (v.kind !== kind || usedInserts.has(v)) continue;
    if (text.includes(v.match)) {
      children.push(imagePara(v.file, v.w, v.h, VISUALS));
      children.push(captionPara(v.caption));
      usedInserts.add(v);
      return;
    }
  }
}

// ---------- main walk ----------
const children = [];
let mermaidCount = 0;
let i = 0;
let firstLine = true;
let previousMeaningfulLine = "";

while (i < lines.length) {
  const line = lines[i];

  if (firstLine) {
    const titleText = line.replace(/^#\s+/, "");
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 2400, after: 400 },
      children: [new TextRun({ text: titleText, bold: true, size: 34, font: HEADING_FONT })],
    }));
    i++;
    while (lines[i] !== undefined && lines[i].trim() === "") i++;
    const subtitleLine = lines[i] || "";
    const subtitleText = subtitleLine.replace(/^\*\*|\*\*$/g, "");
    children.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 800 },
      children: [new TextRun({ text: subtitleText, italics: true, size: 26, font: BODY_FONT })],
    }));
    i++;
    while (lines[i] !== undefined && (lines[i].trim() === "" || lines[i].trim() === "---")) i++;
    firstLine = false;
    children.push(new Paragraph({ children: [new PageBreak()] }));
    children.push(new Paragraph({
      spacing: { after: 240 },
      children: [new TextRun({ text: "목차", bold: true, size: 30, font: HEADING_FONT })],
    }));
    tocEntries.forEach((e) => {
      const indent = { 2: 0, 3: 400, 4: 800 }[e.level];
      const size = { 2: 24, 3: 22, 4: 20 }[e.level];
      const bold = e.level === 2;
      children.push(new Paragraph({
        indent: { left: indent },
        spacing: { after: e.level === 2 ? 120 : 80 },
        children: [new TextRun({ text: e.text, bold, size, font: e.level === 2 ? HEADING_FONT : BODY_FONT })],
      }));
    });
    children.push(new Paragraph({ children: [new PageBreak()] }));
    continue;
  }

  const trimmed = line.trim();

  if (trimmed === "") { i++; continue; }
  if (trimmed === "---") { i++; continue; }

  let mHead = trimmed.match(/^(#{1,4})\s+(.*)$/);
  if (mHead) {
    children.push(headingPara(mHead[1].length, mHead[2]));
    previousMeaningfulLine = trimmed;
    i++; continue;
  }

  if (trimmed.startsWith("```")) {
    const lang = trimmed.slice(3).trim();
    const codeLines = [];
    i++;
    while (i < lines.length && lines[i].trim() !== "```") { codeLines.push(lines[i]); i++; }
    i++;
    if (lang === "mermaid") {
      mermaidCount++;
      if (mermaidCount === 1) {
        children.push(imagePara("그림1_질의응답시퀀스.png", 480, 376, ASSETS));
      } else {
        children.push(imagePara("그림2_전체프레임워크.png", 260, 733, ASSETS));
      }
    } else {
      codeLines.forEach((cl) => children.push(codeLine(cl)));
      children.push(new Paragraph({ spacing: { after: 200 } }));
    }
    continue;
  }

  if (/^>/.test(trimmed)) {
    const quoteParts = [];
    while (i < lines.length && /^\s*>/.test(lines[i])) {
      const content = lines[i].replace(/^\s*>\s?/, "");
      quoteParts.push(content);
      children.push(quotePara(content));
      i++;
    }
    children.push(new Paragraph({ spacing: { after: 120 } }));
    tryInsertVisual(children, "quote", quoteParts.join(" "));
    continue;
  }

  if (/^\s*\|.*\|\s*$/.test(line)) {
    const tblLines = [];
    while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) { tblLines.push(lines[i]); i++; }
    const rows = [];
    tblLines.forEach((tl, idx) => {
      if (idx === 1 && isSepRow(tl)) return;
      rows.push(parseTableRow(tl));
    });
    children.push(makeTable(rows));
    children.push(new Paragraph({ spacing: { after: 240 } }));
    tryInsertVisual(children, "table", previousMeaningfulLine);
    continue;
  }

  let mOrd = trimmed.match(/^(\d+)\.\s+(.*)$/);
  if (mOrd) {
    children.push(orderedLikePara(mOrd[1], mOrd[2]));
    tryInsertVisual(children, "line", trimmed);
    previousMeaningfulLine = trimmed;
    i++; continue;
  }

  let mBul = line.match(/^(\s*)-\s+(.*)$/);
  if (mBul) {
    const level = mBul[1].length >= 3 ? 1 : 0;
    children.push(bulletPara(mBul[2], level));
    tryInsertVisual(children, "line", trimmed);
    previousMeaningfulLine = trimmed;
    i++; continue;
  }

  if (trimmed.startsWith("⚠️") || trimmed.startsWith("⚠")) {
    children.push(warningPara(trimmed));
    previousMeaningfulLine = trimmed;
    i++; continue;
  }

  // 새 그림 6개를 §4.1.1~§4.2.2 사이에 끼워 넣으면서 원래 "그림 3"(§5.2 코드 예시)의
  // 번호가 밀리므로, 이 통합본에서만 표시용으로 "그림 7"로 고쳐 렌더링한다
  // (thesis_report.md 원본 텍스트 자체는 건드리지 않음).
  const renumbered = trimmed.startsWith("**그림 3. 평가 변인 통제를 위한 API 파이프라인 예시 코드**")
    ? trimmed.replace("그림 3.", "그림 7.")
    : trimmed;
  children.push(bodyPara(renumbered));
  tryInsertVisual(children, "line", trimmed);
  previousMeaningfulLine = trimmed;
  i++;
}

const missed = VISUAL_INSERTS.filter((v) => !usedInserts.has(v));
if (missed.length) {
  console.warn("WARNING: the following visual inserts never matched and were NOT placed:");
  missed.forEach((v) => console.warn("  -", v.caption, "(match:", JSON.stringify(v.match), ")"));
}

const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullet-list",
        levels: [
          { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 420, hanging: 260 } } } },
          { level: 1, format: LevelFormat.BULLET, text: "◦", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 820, hanging: 260 } } } },
        ],
      },
    ],
  },
  styles: {
    default: {
      document: { run: { font: BODY_FONT, size: BODY_SIZE }, paragraph: { spacing: { line: LINE_SPACING } } },
      heading1: { run: { font: HEADING_FONT, size: 30, bold: true, color: "1F1F1F" }, paragraph: { spacing: { before: 360, after: 240 } } },
      heading2: { run: { font: HEADING_FONT, size: 26, bold: true, color: "1F1F1F" }, paragraph: { spacing: { before: 300, after: 180 } } },
      heading3: { run: { font: HEADING_FONT, size: 23, bold: true, color: "333333" }, paragraph: { spacing: { before: 240, after: 140 } } },
    },
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: convertInchesToTwip(8.27), height: convertInchesToTwip(11.69) },
          margin: { top: convertInchesToTwip(1), bottom: convertInchesToTwip(1), left: convertInchesToTwip(1.1), right: convertInchesToTwip(1.1) },
        },
      },
      children,
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log("Wrote", OUT, buf.length, "bytes");
  console.log("Visuals placed:", usedInserts.size, "/", VISUAL_INSERTS.length);
});
