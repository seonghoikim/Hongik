/**
 * thesis.md -> thesis_draft.docx 변환 스크립트 (2026-09-01).
 *
 * 사용법: 이 저장소 바깥 아무 디렉터리에서 `npm install docx`(docx.js, v9+) 후
 *   node scripts/build_thesis_docx.js
 * 를 실행하면 /home/user/hongik/thesis_draft.docx가 생성된다. thesis.md를 라인
 * 단위로 파싱해 제목/헤더(#~####)/표/목록/굵게-기울임/인용문/코드블록을 Word
 * 스타일로 변환하고, mermaid 코드블록 2개는 thesis_assets/의 사전 렌더링된
 * PNG(그림1_질의응답시퀀스.png, 그림2_전체프레임워크.png)로 대체한다 — 이
 * PNG들은 thesis_assets/*.mmd 원본을 `npx @mermaid-js/mermaid-cli`로 렌더링한
 * 것이다. thesis.md 본문이 바뀌면 이 스크립트만 재실행하면 문서가 갱신된다.
 * (이 스크립트는 재현성을 위해 git에 커밋하며, 생성물인 .docx 자체는 커밋하지
 * 않는다 — 필요할 때마다 재실행해서 만든다.)
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, BorderStyle, AlignmentType, TableOfContents, ImageRun, LevelFormat,
  ShadingType, VerticalAlign, PageBreak, convertInchesToTwip,
} = require("docx");

const SRC = "/home/user/hongik/thesis.md";
const ASSETS = "/home/user/hongik/thesis_assets";
const OUT = "/home/user/hongik/thesis_draft.docx";

const BODY_FONT = "바탕체";
const HEADING_FONT = "돋움체";
const CODE_FONT = "Consolas";
const BODY_SIZE = 22; // half-points = 11pt
const LINE_SPACING = 360; // 240 = single; 360 = 150%

const raw = fs.readFileSync(SRC, "utf-8");
const lines = raw.split("\n");

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

function imagePara(file, width, height) {
  const data = fs.readFileSync(path.join(ASSETS, file));
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 240 },
    children: [new ImageRun({ data, type: "png", transformation: { width, height } })],
  });
}

// ---------- main walk ----------
const children = [];
let mermaidCount = 0;
let i = 0;
let firstLine = true;

while (i < lines.length) {
  const line = lines[i];

  if (firstLine) {
    // title (line 0) then blank then subtitle (**...**) then blank then --- then blank
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
    // Table of contents right after title page
    children.push(new Paragraph({ children: [new PageBreak()] }));
    children.push(new Paragraph({
      spacing: { after: 240 },
      children: [new TextRun({ text: "목차", bold: true, size: 30, font: HEADING_FONT })],
    }));
    children.push(new TableOfContents("목차", { hyperlink: true, headingStyleRange: "1-3" }));
    continue;
  }

  const trimmed = line.trim();

  // blank line
  if (trimmed === "") { i++; continue; }

  // horizontal rule
  if (trimmed === "---") { i++; continue; }

  // headings
  let mHead = trimmed.match(/^(#{1,4})\s+(.*)$/);
  if (mHead) {
    children.push(headingPara(mHead[1].length, mHead[2]));
    i++; continue;
  }

  // fenced code block
  if (trimmed.startsWith("```")) {
    const lang = trimmed.slice(3).trim();
    const codeLines = [];
    i++;
    while (i < lines.length && lines[i].trim() !== "```") { codeLines.push(lines[i]); i++; }
    i++; // skip closing fence
    if (lang === "mermaid") {
      mermaidCount++;
      if (mermaidCount === 1) {
        children.push(imagePara("그림1_질의응답시퀀스.png", 480, 376));
      } else {
        children.push(imagePara("그림2_전체프레임워크.png", 260, 733));
      }
    } else {
      codeLines.forEach((cl) => children.push(codeLine(cl)));
      children.push(new Paragraph({ spacing: { after: 200 } }));
    }
    continue;
  }

  // blockquote block
  if (/^>/.test(trimmed)) {
    while (i < lines.length && /^\s*>/.test(lines[i])) {
      const content = lines[i].replace(/^\s*>\s?/, "");
      children.push(quotePara(content));
      i++;
    }
    children.push(new Paragraph({ spacing: { after: 120 } }));
    continue;
  }

  // table block
  if (/^\s*\|.*\|\s*$/.test(line)) {
    const tblLines = [];
    while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) { tblLines.push(lines[i]); i++; }
    const rows = [];
    tblLines.forEach((tl, idx) => {
      if (idx === 1 && isSepRow(tl)) return; // skip markdown separator row
      rows.push(parseTableRow(tl));
    });
    children.push(makeTable(rows));
    children.push(new Paragraph({ spacing: { after: 240 } }));
    continue;
  }

  // ordered list "N. text"
  let mOrd = trimmed.match(/^(\d+)\.\s+(.*)$/);
  if (mOrd) {
    children.push(orderedLikePara(mOrd[1], mOrd[2]));
    i++; continue;
  }

  // bullet list "- text" or "  - text"
  let mBul = line.match(/^(\s*)-\s+(.*)$/);
  if (mBul) {
    const level = mBul[1].length >= 3 ? 1 : 0;
    children.push(bulletPara(mBul[2], level));
    i++; continue;
  }

  // warning callout line (starts with warning emoji)
  if (trimmed.startsWith("⚠️") || trimmed.startsWith("⚠")) {
    children.push(warningPara(trimmed));
    i++; continue;
  }

  // default paragraph
  children.push(bodyPara(trimmed));
  i++;
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
          size: { width: convertInchesToTwip(8.27), height: convertInchesToTwip(11.69) }, // A4
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
});
