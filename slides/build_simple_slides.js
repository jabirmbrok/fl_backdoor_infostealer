// A simpler IWBIS talk deck: one figure or one table from the paper per slide,
// explained with sentences taken from the camera-ready text.
//
// The tables, captions, figure numbers and figure files are parsed from
// paper/ieee_malware_fl_backdoor.tex when the deck is built, so every number
// in a table is the number printed in the paper. The prose on the slides is
// copied from the same file; nothing on a slide is computed here, and no
// visual appears that is not a figure or table of the paper.
//
// Run:   node slides/build_simple_slides.js [outdir]
// Needs: pptxgenjs (on NODE_PATH or installed next to this file) and
//        pdftoppm on PATH, which renders the one PDF figure (Fig. 7) to PNG.
"use strict";

const pptxgen = require("pptxgenjs");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");

const REPO = path.resolve(__dirname, "..");
const PAPER = path.join(REPO, "paper");
const TEX = fs.readFileSync(path.join(PAPER, "ieee_malware_fl_backdoor.tex"), "utf8");
const OUT_DIR = process.argv[2] ? path.resolve(process.argv[2]) : __dirname;
const OUT = path.join(OUT_DIR, "iwbis_channel_aware_backdoor_simple.pptx");

/* ------------------------------------------------------------------ paper */

// text inside the brace group that starts at src[from]
function balanced(src, from) {
  let depth = 0;
  for (let i = from; i < src.length; i++) {
    if (src[i] === "{") depth++;
    else if (src[i] === "}" && --depth === 0) return src.slice(from + 1, i);
  }
  throw new Error("unbalanced braces at " + from);
}

// LaTeX markup used in the paper's captions and table cells -> plain text
function unTex(s) {
  return s
    .replace(/\\textsuperscript\{\\dag\}/g, "†")
    .replace(/\\textbf\{([^}]*)\}/g, "$1")
    .replace(/\$([^$]*)\$/g, (m, inner) =>
      inner.replace(/\\pm/g, "±").replace(/\\times/g, "×").replace(/\s+/g, " ").trim())
    .replace(/\\%/g, "%")
    .replace(/--/g, "–")
    .replace(/~/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

const ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"];
const figLabels = [...TEX.matchAll(/\\label\{(fig:[^}]+)\}/g)].map((m) => m[1]);
const tabLabels = [...TEX.matchAll(/\\label\{(tab:[^}]+)\}/g)].map((m) => m[1]);

function captionBefore(idx) {
  const c = TEX.lastIndexOf("\\caption", idx);
  return unTex(balanced(TEX, TEX.indexOf("{", c)));
}

function texFigure(label) {
  const idx = TEX.indexOf(`\\label{${label}}`);
  if (idx < 0) throw new Error("no figure " + label);
  const g = TEX.lastIndexOf("\\includegraphics", idx);
  const file = balanced(TEX, TEX.indexOf("{", TEX.indexOf("]", g)));
  return { number: figLabels.indexOf(label) + 1, caption: captionBefore(idx), file: path.join(PAPER, file) };
}

function texTable(label) {
  const idx = TEX.indexOf(`\\label{${label}}`);
  if (idx < 0) throw new Error("no table " + label);
  const start = TEX.indexOf("\\begin{tabular}", idx);
  const spec = /\\begin\{tabular\}\{[^}]*\}/.exec(TEX.slice(start))[0];
  const body = TEX.slice(start + spec.length, TEX.indexOf("\\end{tabular}", start));
  const rows = [];
  let breakBefore = false;
  for (const raw of body.split("\n")) {
    const line = raw.trim();
    if (!line || /^\\(toprule|bottomrule)/.test(line)) continue;
    if (/^\\midrule/.test(line)) { breakBefore = rows.length > 1; continue; }
    if (!line.includes("&")) continue;
    const cells = line.replace(/\\\\\s*$/, "").split("&").map((c) => c.trim());
    rows.push({ breakBefore, cells: cells.map((c) => ({ text: unTex(c), bold: /\\textbf\{/.test(c) })) });
    breakBefore = false;
  }
  return { number: ROMAN[tabLabels.indexOf(label)], caption: captionBefore(idx), rows };
}

// pixel size of a PNG or JPEG, to place images at their true aspect ratio
function imageSize(file) {
  const b = fs.readFileSync(file);
  if (b.toString("ascii", 1, 4) === "PNG") return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
  let i = 2;
  while (i < b.length) {
    if (b[i] !== 0xff) throw new Error("bad JPEG " + file);
    const marker = b[i + 1];
    if (marker >= 0xc0 && marker <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(marker)) {
      return { h: b.readUInt16BE(i + 5), w: b.readUInt16BE(i + 7) };
    }
    i += 2 + b.readUInt16BE(i + 2);
  }
  throw new Error("no SOF in " + file);
}

// the per-round figure is a PDF; render it to a PNG, again whenever the PDF is newer
function rasterized(file) {
  if (!/\.pdf$/i.test(file)) return file;
  const prefix = path.join(os.tmpdir(), path.basename(file, ".pdf") + "_400dpi");
  const png = prefix + ".png";
  if (!fs.existsSync(png) || fs.statSync(png).mtimeMs < fs.statSync(file).mtimeMs) {
    execFileSync("pdftoppm", ["-r", "400", "-png", "-singlefile", file, prefix]);
  }
  return png;
}


/* ----------------------------------------------------------------- design */
//
// The main talk follows the IWBIS presenter guideline: title; background and
// motivation; research problem and objectives; proposed approach; experimental
// setup; results; discussion; conclusion and future work. The paper has no
// acknowledgment section, so the talk closes with a thank-you slide. The slot is
// 15 minutes; every main slide carries a suggested time in its speaker notes.
// Tables I and II and Figs. 5-6 are shown in the main talk without their
// explanatory text, which is kept on one backup slide for questions.

const W = 13.3, H = 7.5, M = 0.7;
const INK = "101820", SLATE = "1B2A41", MUTED = "5A6B7C", MIST = "EDF1F5", LINE = "D3DCE4", WHITE = "FFFFFF";
const SOFT = "9FB3C8", HILITE = "DCEBFA";
const RED = "C0392B", GRN = "1E8449", BLU = "2E86DE", FULL = "7D3C98";
const HEAD = "Cambria", BODY = "Calibri";

const CHANNEL_COLOR = { "Red/API": RED, "Green/network": GRN, "Blue/fusion": BLU, "Full RGB": FULL };

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Aziz, Mubarok, Fitria";
pres.title = "Channel-Aware Backdoor Attacks Against Federated Infostealer Malware Classification";

function slide(kicker, title, dark) {
  const s = pres.addSlide();
  s.background = { color: dark ? INK : WHITE };
  if (kicker) {
    s.addText(kicker, {
      x: M, y: 0.45, w: W - 2 * M, h: 0.3, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 12, bold: true, color: BLU, charSpacing: 2,
    });
  }
  if (title) {
    s.addText(title, {
      x: M, y: 0.8, w: W - 2 * M, h: 0.65, isTextBox: true, margin: 0, valign: "top",
      fontFace: HEAD, fontSize: 30, bold: true, color: dark ? WHITE : SLATE,
    });
  }
  return s;
}

// a paragraph is a string, or {text, bold, color} for a sentence to emphasise
function runs(texts, bullet, gap) {
  return texts.map((t, i) => {
    const p = typeof t === "string" ? { text: t } : t;
    const o = i === texts.length - 1 ? {} : { breakLine: true, paraSpaceAfter: gap };
    if (bullet) o.bullet = true;
    if (p.bold) o.bold = true;
    if (p.color) o.color = p.color;
    const text = p.text.replace(/ = /g, "\u00a0=\u00a0").replace(/ \u00d7 /g, "\u00a0\u00d7\u00a0");
    return { text, options: o };
  });
}

function paras(s, x, y, w, h, texts, o = {}) {
  s.addText(runs(texts, !!o.bullet, o.gap || 12), {
    x, y, w, h, isTextBox: true, margin: 0, valign: o.valign || "top",
    fontFace: BODY, fontSize: o.size || 16, color: o.color || SLATE, lineSpacing: o.line || 22,
    italic: !!o.italic,
  });
}

function caption(s, text, x, y, w, h, align) {
  s.addText(text, {
    x, y, w, h, isTextBox: true, margin: 0, valign: align === "left" ? "bottom" : "top",
    fontFace: BODY, fontSize: 11.5, italic: true, color: MUTED, align: align || "center", lineSpacing: 15,
  });
}

// image at its own aspect ratio inside the box, with the paper's caption either
// centred under it or bottom-aligned beside it (o.capBeside = {x, w})
function figure(s, label, x, y, w, h, o = {}) {
  const f = texFigure(label);
  const file = rasterized(f.file);
  const px = imageSize(file);
  const scale = Math.min(w / px.w, h / px.h);
  const iw = px.w * scale, ih = px.h * scale;
  const ix = o.capBeside ? x : x + (w - iw) / 2;
  s.addImage({ path: file, x: ix, y, w: iw, h: ih });
  const text = `Fig. ${f.number}. ${f.caption}`;
  const capH = o.capH || 0.5;
  if (o.capBeside) caption(s, text, o.capBeside.x, y + ih - capH, o.capBeside.w, capH, "left");
  else caption(s, text, x, y + ih + 0.12, w, capH, "center");
  return { right: ix + iw, bottom: y + ih };
}

// table parsed from the paper, IEEE-style caption above it. A \midrule inside the
// body becomes a thick rule on both sides of the shared edge, so PowerPoint draws
// it; o.highlight(cells) tints the rows that carry the slide's key finding.
function table(s, label, x, y, w, colW, o = {}) {
  const t = texTable(label);
  const rowH = o.rowH || 0.42;
  const leftCols = o.leftCols || 1;
  const thin = { type: "solid", pt: 0.5, color: LINE };
  const rule = { type: "solid", pt: 2.25, color: SLATE };
  const rows = t.rows.map((r, ri) => {
    const head = ri === 0;
    const texts = r.cells.map((c) => c.text);
    const hot = !head && o.highlight && o.highlight(texts);
    const next = t.rows[ri + 1];
    return r.cells.map((c, ci) => ({
      text: c.text,
      options: {
        bold: head || c.bold || hot,
        align: ci < leftCols ? "left" : "center",
        color: head ? WHITE : (o.colorize && CHANNEL_COLOR[c.text]) || SLATE,
        fill: { color: head ? SLATE : hot ? HILITE : ri % 2 === 0 ? MIST : WHITE },
        fontFace: BODY, fontSize: o.fontSize || 15, valign: "middle",
        margin: [3, 7, 3, 7],
        border: [r.breakBefore ? rule : thin, thin, next && next.breakBefore ? rule : thin, thin],
      },
    }));
  });
  s.addText(`TABLE ${t.number}. ${t.caption}`, {
    x, y, w, h: 0.3, isTextBox: true, margin: 0, valign: "bottom",
    fontFace: BODY, fontSize: 12.5, bold: true, color: MUTED, align: "center",
  });
  s.addTable(rows, { x, y: y + 0.4, w, colW, rowH, fontFace: BODY });
  return y + 0.4 + rowH * rows.length;
}

function card(s, x, y, w, h, title, texts, o = {}) {
  s.addShape(pres.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: o.fill || MIST } });
  s.addText(title, {
    x: x + 0.4, y: y + 0.3, w: w - 0.8, h: 0.45, isTextBox: true, margin: 0, valign: "top",
    fontFace: BODY, fontSize: o.titleSize || 18, bold: true, color: o.titleColor || SLATE,
  });
  paras(s, x + 0.4, y + 0.95, w - 0.8, h - 1.2, texts, o);
}

// one emphasised line in a tinted band, used for the paper's main claim
function band(s, y, text, h) {
  s.addShape(pres.ShapeType.roundRect, { x: M, y, w: W - 2 * M, h: h || 0.8, rectRadius: 0.08, fill: { color: HILITE } });
  s.addText(text, {
    x: M + 0.4, y, w: W - 2 * M - 0.8, h: h || 0.8, isTextBox: true, margin: 0, valign: "middle",
    fontFace: BODY, fontSize: 18, bold: true, color: SLATE,
  });
}

function setNotes(s, text) {
  s.__notes = s.__notes ? s.__notes + "\n\n" + text : text;
}

/* ----------------------------------------------------------------- slides */

const main = [];
const backup = [];
const add = (fn) => main.push(fn);
const addBackup = (fn) => backup.push(fn);

/* 1. title, authors, affiliations, over the background made by make_title_background.py */
const TITLE_BG = path.join(__dirname, "title_background.jpg");
add(() => {
  const s = pres.addSlide();
  if (fs.existsSync(TITLE_BG)) {
    s.background = { path: TITLE_BG };
  } else {
    console.warn("title_background.jpg missing; run python slides/make_title_background.py");
    s.background = { color: INK };
  }
  const TAN = "C6AB8E", PALE = "D5E0EA";
  // the image's accent bars run across the left panel at about 3.65-4.20 in;
  // the title sits above them and the authors below, all inside the dark panel
  s.addText([
    { text: "Channel-Aware Backdoor Attacks", options: { breakLine: true } },
    { text: "Against Federated Infostealer", options: { breakLine: true } },
    { text: "Malware Classification Using", options: { breakLine: true } },
    { text: "Dynamic API-Call and Network", options: { breakLine: true } },
    { text: "Representations" },
  ], {
    x: M, y: 0.55, w: 6.0, h: 2.75, isTextBox: true, margin: 0, valign: "bottom",
    fontFace: HEAD, fontSize: 27, bold: true, color: WHITE, lineSpacing: 34,
  });
  [
    ["Mochamad Asryl Aziz", "BPS-Statistics Indonesia, Bantaeng Regency"],
    ["Moh. Jabir Mubarok", "Institut Teknologi Sepuluh Nopember, Surabaya"],
    ["Eka Fitria", "Universitas Syiah Kuala, Banda Aceh"],
  ].forEach(([name, aff], k) => {
    s.addText([
      { text: name, options: { bold: true, fontSize: 15, color: WHITE, breakLine: true } },
      { text: aff, options: { fontSize: 12.5, color: PALE } },
    ], {
      x: M, y: 4.55 + k * 0.62, w: 5.6, h: 0.6, isTextBox: true, margin: 0, valign: "top",
      fontFace: BODY, lineSpacing: 18,
    });
  });
  s.addText("2026 8th International Workshop on Big Data and Information Security (IWBIS)", {
    x: M, y: 6.5, w: 5.6, h: 0.5, isTextBox: true, margin: 0, valign: "top",
    fontFace: BODY, fontSize: 12, bold: true, color: TAN, lineSpacing: 15,
  });
});

/* 2. background and motivation */
add(() => {
  const s = slide("BACKGROUND AND MOTIVATION", "Background and Motivation");
  const cw = (W - 2 * M - 2 * 0.3) / 3;
  [
    ["Infostealer malware", [
      "Infostealer malware targets authentication artifacts such as credentials, browser data and session cookies, which can enable account compromise and unauthorized access.",
      "Classifying infostealer families therefore matters for threat intelligence, triage and incident response.",
    ]],
    ["Dynamic analysis", [
      "Dynamic analysis captures runtime behavior beyond static file properties: API-call sequences represent host-level execution, network artifacts capture communication patterns, and both can be encoded into CNN-compatible images.",
    ]],
    ["Federated learning", [
      "Federated learning (FL) allows participants to train such a classifier together without moving raw data to a central server, but its reliance on client-submitted updates lets a malicious client inject backdoor behavior.",
    ]],
  ].forEach(([title, texts], i) => {
    card(s, M + i * (cw + 0.3), 1.75, cw, 4.95, title, texts, { size: 17.5, line: 24, gap: 16 });
  });
});

/* 3. research problem and objectives */
add(() => {
  const s = slide("RESEARCH PROBLEM AND OBJECTIVES", "Research Problem and Objectives");
  s.addText("Research problem", {
    x: M, y: 1.95, w: 5.8, h: 0.45, isTextBox: true, margin: 0, valign: "top",
    fontFace: BODY, fontSize: 18, bold: true, color: SLATE,
  });
  paras(s, M, 2.6, 5.8, 3.0, [
    "Most FL backdoor work targets general image or model-level poisoning rather than channel-specific behavior in malware representations.",
    "An RGB-stack representation places API-call, network and fused information in separate channels, so a trigger in one channel need not behave like a trigger in another.",
    "That behavior remains underexplored on dynamic API-call and network representations, and this paper investigates it in federated infostealer malware classification.",
  ], { size: 15, line: 21, gap: 12 });
  card(s, 6.85, 1.65, 5.75, 4.0, "Objectives", [
    "We construct dynamic API-call and network representations from Cuckoo Sandbox reports of five infostealer families.",
    "We select the main representation–backbone pair by comparing RGB-stack and opacity blend with SmallCNN, MobileNetV2 and ResNet18.",
    "We evaluate channel-aware backdoor attacks in FL using red/API, green/network, blue/fusion and full-RGB triggers, with trigger-control and Multi-Krum defense analysis.",
  ], { bullet: true, size: 14, line: 19, gap: 8 });
  band(s, 5.85, "The novelty is to treat the representation's channels as the attack surface: a trigger confined to the fusion channel alone matches one spanning all three, even though that channel is derived from the other two.", 1.05);
});

/* 4. proposed approach: overall workflow */
add(() => {
  const s = slide("PROPOSED APPROACH  ·  1 / 4", "Overall Research Workflow");
  figure(s, "fig:methodology", M, 1.6, W - 2 * M, 4.85, { capH: 0.4 });
});

/* 5. proposed approach: dataset creation */
add(() => {
  const s = slide("PROPOSED APPROACH  ·  2 / 4", "From Sandbox Reports to Image Tiles");
  figure(s, "fig:dataset", M, 1.55, 6.0, 5.3, { capBeside: { x: 6.05, w: 6.55 }, capH: 0.5 });
  paras(s, 6.05, 1.8, 6.55, 4.2, [
    "The dataset is built from Cuckoo Sandbox reports for five Windows infostealer families: AgentTesla, FormBook, SalatStealer, StealC and Vidar.",
    "API-call events are converted into a 16 × 16 category-by-time tile by normalizing the execution timeline, mapping API names into predefined behavior categories, and counting category occurrences over fixed time intervals.",
    "To reduce sample-level leakage, only the session with the largest payload is selected for each malware sample, then truncated or padded and reshaped into a 28 × 28 network tile.",
  ], { gap: 18 });
});

/* 6. proposed approach: channel-separated representation */
add(() => {
  const s = slide("PROPOSED APPROACH  ·  3 / 4", "Channel-Separated RGB-Stack Representation");
  figure(s, "fig:sample", M, 1.55, 6.8, 5.3, { capBeside: { x: 7.9, w: 4.7 }, capH: 0.95 });
  paras(s, 7.9, 1.7, 4.7, 4.2, [
    "In RGB-stack the API and network tiles are converted to grayscale, min–max normalized per image and resized to 128 × 128; red carries API-call behavior, green network behavior, and blue is the edge map of their average, B = FindEdges((R+G)/2).",
    { text: "Blue is thus a deterministic function of the other two channels, adds no independent information, and is by far the emptiest: 62.8% of its pixels are exactly zero.", bold: true },
    "RGB-stack is used here because only it separates the sources by channel.",
  ], { size: 15, line: 20.5, gap: 14 });
});

/* 7. proposed approach: federated setting and channel-aware backdoor */
add(() => {
  const s = slide("PROPOSED APPROACH  ·  4 / 4", "Channel-Aware Backdoor in Federated Learning");
  figure(s, "fig:federated", M, 1.55, 6.6, 5.3, { capBeside: { x: 7.75, w: 4.85 }, capH: 0.75 });
  paras(s, 7.75, 1.7, 4.85, 4.3, [
    "The selected representation\u2013backbone pair is trained in a simulated FL setting with one central server and five clients. Each client holds 70 images, 14 per family, so the partition is balanced and IID.",
    "We assume a targeted backdoor with one malicious client: it inserts a square image-level trigger into AgentTesla training images and relabels them as FormBook.",
    "The poison rate is 20% of the attacker's 14 AgentTesla training images, i.e., two images per round, resampled every round.",
    { text: "Because RGB-stack preserves channel-level semantics, four trigger settings are evaluated: red/API, green/network, blue/fusion and full RGB.", bold: true },
  ], { size: 14.5, line: 19.5, gap: 11 });
});

/* 8. experimental setup: dataset and model selection */
add(() => {
  const s = slide("EXPERIMENTAL SETUP  \u00b7  1 / 2", "Dataset and Model Selection");
  table(s, "tab:dataset", M, 1.6, 5.45, [1.85, 0.9, 0.9, 0.9, 0.9], { rowH: 0.42, fontSize: 14 });
  table(s, "tab:backbone", 6.55, 1.6, 6.05, [1.85, 1.8, 1.2, 1.2], {
    rowH: 0.42, leftCols: 2, fontSize: 14,
    highlight: (c) => c[0] === "RGB-stack" && c[1] === "ResNet18",
  });
  paras(s, M, 5.35, W - 2 * M, 1.4, [
    { text: "Among the RGB-stack backbones in Table III, measured on seed 42, ResNet18 is the strongest, at 78.67% accuracy and 78.84% macro-F1, and is used for all later experiments; the opacity-blend rows come from a different split and are listed for reference only.", bold: true },
  ], { size: 15.5, line: 21.5 });
  setNotes(s, "From the paper, III.C: The two representations use different split files, so Table III is not a paired comparison: RGB-stack is chosen because channel separation is required here, and macro-F1 selects only the backbone within it. The text for Table I is on the backup slide.");
});

/* 9. experimental setup: environment, training, defense and evaluation */
add(() => {
  const s = slide("EXPERIMENTAL SETUP  \u00b7  2 / 2", "Training, Defense and Evaluation");
  const bottom = table(s, "tab:environment", M, 1.6, 5.85, [2.1, 3.75], { rowH: 0.4, fontSize: 13.5 });
  s.addText("Training", {
    x: M, y: bottom + 0.25, w: 5.85, h: 0.4, isTextBox: true, margin: 0, valign: "top",
    fontFace: BODY, fontSize: 18, bold: true, color: SLATE,
  });
  paras(s, M, bottom + 0.72, 5.85, 6.8 - bottom - 0.72, [
    "Training uses a batch size of 16, learning and weight decay rates of 10\u207b\u2074, 50 FL rounds, and two local epochs per round.",
    "ResNet18 is trained from scratch with AdamW, and the reported FL model is the final-round global model, with no best-validation selection.",
    "Clean accuracy, macro-F1 and ASR are the primary metrics, over seeds 42, 123 and 2026.",
  ], { size: 14, line: 19, gap: 7 });
  card(s, 6.75, 1.6, 5.85, 5.2, "Defense and trigger control", [
    "Multi-Krum is the primary defense, taken as a standard robust-aggregation baseline: it scores client updates by their distances to other updates and aggregates those with the lowest scores.",
    "L\u2082-norm clipping, coordinate-wise median and trimmed mean are screened alongside it.",
    "As a control, the same triggers are applied at test time to the clean FL model, which never saw poisoned data, so its target predictions are baseline family confusion.",
  ], { size: 16.5, line: 22.5, gap: 16 });
  setNotes(s, "The text for Table II is on the backup slide. The seed-42 deviation belongs to Table VI; it is footnoted on slide 12 and given in full on the backup slide.");
});

/* 10. results: channel-aware sweep */
add(() => {
  const s = slide("RESULTS  ·  1 / 4", "Channel-Aware Backdoor Sweep");
  table(s, "tab:sweep", M, 1.7, 6.8, [2.45, 1.45, 1.45, 1.45], {
    rowH: 0.75, colorize: true, fontSize: 17,
    highlight: (c) => c[0] === "Blue/fusion",
  });
  paras(s, 7.95, 1.8, 4.65, 5.0, [
    { text: "Table IV shows that blue/fusion and full-RGB triggers achieve 100% ASR while red/API and green/network do not, and that blue/fusion does so without modifying all three channels.", bold: true },
    "The difference is categorical. Pooled over the triggered samples, blue/fusion and full RGB differ from their trigger controls with Fisher exact p = 3.5 × 10⁻¹⁹ and p = 2.6 × 10⁻¹⁸, and blue differs from red and green at p = 4.0 × 10⁻⁸, whereas red and green are indistinguishable from their own controls (both p = 1, 5/15 against 4/15, seed 42 only).",
    "Pooling is legitimate because the split is re-drawn per seed.",
  ], { size: 14.5, line: 20, gap: 12 });
});

/* 11. results: defense screening */
add(() => {
  const s = slide("RESULTS  ·  2 / 4", "Defense Screening");
  table(s, "tab:defense_screening", M, 1.6, 7.9, [1.8, 1.9, 1.4, 1.4, 1.4], {
    rowH: 0.44, leftCols: 2, colorize: true, fontSize: 14,
    highlight: (c) => c[1] === "Multi-Krum",
  });
  paras(s, 9.0, 1.8, 3.6, 5.0, [
    "Table V gives a seed-42 screening against both strongest attacks: clipping, coordinate-wise median and trimmed mean all leave ASR at 1.0000.",
    { text: "Only Multi-Krum reduces it, and only under full RGB (1.0000 to 0.4000, clean accuracy 0.8400 to 0.7600), so Multi-Krum is taken to the multi-seed evaluation.", bold: true },
  ], { size: 15.5, line: 21.5, gap: 18 });
});

/* 12. results: multi-seed */
add(() => {
  const s = slide("RESULTS  ·  3 / 4", "Multi-Seed Results");
  const bottom = table(s, "tab:main", M, 1.55, W - 2 * M, [2.3, 1.45, 1.8, 1.8, 2.0, 2.55], {
    rowH: 0.36, leftCols: 2, colorize: true, fontSize: 13.5,
    highlight: (c) => c[0] === "Backdoor, FedAvg",
  });
  paras(s, M, bottom + 0.08, W - 2 * M, 0.6, [
    "† Across-seed ASR range ≥ 0.5: the outcome is bimodal, so the mean describes no individual run and the per-seed counts (out of 15 source samples) should be read instead.",
    "One deviation must be stated: the seed-42 clean baseline in Table VI and the seed-42 trigger controls come from a 30-round, one-local-epoch run. No ASR result is affected; every backdoor and defense run uses the common budget.",
  ], { size: 12, line: 15, gap: 6, italic: true, color: MUTED });
  paras(s, M, bottom + 0.98, W - 2 * M, 6.95 - bottom - 0.98, [
    { text: "Across three seeds, blue/fusion and full-RGB backdoors achieve 100% ASR while keeping clean performance comparable to the clean FL baseline.", bold: true },
    "In seven of the eight trigger controls the target rate is identical with and without the trigger, so the ASR is not an artifact of the pattern.",
  ], { size: 14.5, line: 19.5, gap: 8 });
  setNotes(s, "On the 30-round, one-local-epoch seed-42 clean baseline, from the paper, III.H: Re-training it under the common budget gives 0.7867 accuracy, 0.7869 macro-F1 and a control rate of 6/15 rather than 4/15, so the reported run sets a higher bar for the clean-performance claim and a lower one for the trigger-control argument. No ASR result is affected; every backdoor and defense run uses the common budget. From IV.B: red and green are indistinguishable from their own controls (both p = 1, 5/15 against 4/15, seed 42 only). The 5/15 is their backdoor ASR; their clean-model controls give 4/15 both with and without the trigger (results/trigger_control).");
});

/* 12b. results: seed-42 per-round curves, figures only (their text is on the backup slide) */
add(() => {
  const s = slide("RESULTS  \u00b7  4 / 4", "Clean Macro-F1 and ASR over FL Rounds");
  figure(s, "fig:f1_round", M, 1.6, 5.85, 4.6, { capH: 0.5 });
  figure(s, "fig:asr_round", 6.75, 1.6, 5.85, 4.6, { capH: 0.5 });
  setNotes(s, "From the paper, IV.D: Figures 5 and 6 show clean macro-F1 holding steady while ASR climbs to 100%. The first rounds are not meaningful: the global model is still close to initialization and collapses onto one or two classes, producing the early spike before clean accuracy rises.");
});

/* 13. discussion: why the blue channel */
add(() => {
  const s = slide("DISCUSSION  ·  1 / 2", "The Blue/Fusion Channel");
  card(s, M, 1.7, 5.85, 5.1, "The ordering in Table IV", [
    "The ordering follows the intensity of the clean images: over all 500 images the mean value inside the trigger region is 214.6 in R, 48.3 in G and 21.6 in B, and 37.7% of red trigger-region pixels are already at least 254, where the trigger changes nothing.",
    "Contrast explains red's failure but not green's, whose contrast is 207.",
  ], { size: 17.5, line: 24, gap: 16 });
  card(s, 6.75, 1.7, 5.85, 5.1, "What it suggests, and what it does not", [
    { text: "Since blue is a deterministic edge map of the other two, its effectiveness cannot come from information they lack; what distinguishes it is that it is almost empty, so the trigger is the only strong response there.", bold: true },
    "That the blue trigger works because its channel is nearly empty, rather than because of what that channel encodes, is consistent with the measurements but not established.",
  ], { size: 17.5, line: 24, gap: 16 });
  setNotes(s, "Contrast here is 255 minus the mean value inside the trigger region, so green's contrast is 255 - 48.3, about 207 (docs/CODE_FACTS.md). The contrast-matched trigger that would test the emptiness explanation is future work.");
});

/* 14. discussion: Multi-Krum */
add(() => {
  const s = slide("DISCUSSION  ·  2 / 2", "Defense Analysis: Bimodal Rather Than Partial");
  figure(s, "fig:all_settings_round", M, 1.6, 7.2, 4.4, { capH: 0.6 });
  paras(s, 8.25, 1.65, 4.35, 5.25, [
    "The last two rows of Table VI report Multi-Krum per seed as well as on average, because the mean is misleading here.",
    { text: "For both triggers the across-seed ASR range is at least 0.5, with nothing in between: on some seeds the backdoor remains fully effective, on the others most of it is suppressed.", bold: true },
    "The outcome tracks how often the poisoned update survives selection: across the six runs the malicious client is retained in 8–50% of rounds, and that rate correlates with the final ASR (r = 0.893, p = 0.017, n = 6).",
    "Consistent with Table VI, Multi-Krum does not settle at a stable partial suppression level: for each trigger one seed shows no suppression at all, so it is unreliable as a standalone defense.",
  ], { size: 13.5, line: 18, gap: 9 });
  setNotes(s, "Per seed (42, 123, 2026), Table VI: blue/fusion 15/15, 3/15, 5/15; full RGB 6/15, 15/15, 6/15. The shaded bands in Fig. 7 are the standard deviation across those seeds. From the paper, IV.E: With f = 1 and |S| = 2 of five, the poisoned update is not an outlier in parameter space, so keeping it is close to a coin flip that the attacker need only win often enough.");
});

/* 15. conclusion and future work */
add(() => {
  const s = slide("CONCLUSION AND FUTURE WORK", "Conclusion and Future Work", true);
  paras(s, M, 1.7, W - 2 * M, 3.3, [
    { text: "The novelty is to treat the representation's channels as the attack surface: a trigger confined to the fusion channel alone matches one spanning all three, even though that channel is derived from the other two.", bold: true },
    "Blue/fusion and full-RGB triggers reached 100% ASR across three seeds while keeping clean performance close to the baseline, and in seven of the eight trigger controls the target rate was identical with and without the trigger, so the effect came from poisoning rather than the trigger pattern.",
    "Multi-Krum reduced ASR bimodally rather than partially, leaving the backdoor fully effective (15/15) on one of the three seeds for each trigger.",
    { text: "Channel-aware backdoors therefore pose a serious threat to federated malware classifiers in this controlled IID setting, and motivate representation-aware defenses.", bold: true },
  ], { bullet: true, size: 15.5, line: 21, gap: 11, color: WHITE });
  s.addText("Limitations and future work", {
    x: M, y: 5.12, w: 6, h: 0.35, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 14.5, bold: true, color: SOFT,
  });
  paras(s, M, 5.5, 11.2, 1.45, [
    "The main limitations are the IID-only partition, a single source–target pair, and three seeds, with the red and green results resting on seed 42 alone. That the blue trigger works because its channel is nearly empty, rather than because of what that channel encodes, is consistent with the measurements but not established; a non-IID partition, a second source–target pair and a contrast-matched trigger are left to future work.",
  ], { size: 13.5, line: 18, color: SOFT });
});

/* 16. closing (the paper has no acknowledgment section) */
add(() => {
  const s = slide(null, null, true);
  s.addText("Thank you", {
    x: M, y: 2.3, w: W - 2 * M, h: 1.0, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 48, bold: true, color: WHITE,
  });
  s.addText("Mochamad Asryl Aziz  ·  Moh. Jabir Mubarok  ·  Eka Fitria", {
    x: M, y: 3.6, w: W - 2 * M, h: 0.4, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 18, bold: true, color: WHITE,
  });
  s.addText("mochamadasryl93@gmail.com  ·  jabirmubarok@gmail.com  ·  ekafitria2@mhs.usk.ac.id", {
    x: M, y: 4.1, w: W - 2 * M, h: 0.4, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 14, color: SOFT,
  });
});

/* backup: the explanatory text for the visuals shown without text in the main talk */
addBackup(() => {
  const s = slide("BACKUP", "Notes on Tables I, II and VI and Figs. 5\u20136");
  const rows = [
    ["Table I", "slide 8", 1.3, [
      "Tiles are aligned per sample and recorded in a manifest organized by family, which supports stratified splitting and reproducibility.",
      "With 100 samples per family the dataset holds 500 representations, split 70%\u201315%\u201315% into training, validation and test partitions, stratified by family.",
    ]],
    ["Table II", "slide 9", 0.72, [
      "Dynamic analysis and model training run on the separate environments listed in Table II.",
    ]],
    ["Table VI", "slide 12", 1.35, [
      "One deviation must be stated: the seed-42 clean baseline in Table VI and the seed-42 trigger controls come from a 30-round, one-local-epoch run. Re-training it under the common budget gives 0.7867 accuracy, 0.7869 macro-F1 and a control rate of 6/15 rather than 4/15, so the reported run sets a higher bar for the clean-performance claim and a lower one for the trigger-control argument. No ASR result is affected; every backdoor and defense run uses the common budget.",
    ]],
    ["Figs. 5\u20136", "slide 13", 1.12, [
      "Figures 5 and 6 show clean macro-F1 holding steady while ASR climbs to 100%. The first rounds are not meaningful: the global model is still close to initialization and collapses onto one or two classes, producing the early spike before clean accuracy rises.",
    ]],
  ];
  let y = 1.6;
  rows.forEach(([label, where, h, texts]) => {
    s.addShape(pres.ShapeType.roundRect, { x: M, y, w: W - 2 * M, h, rectRadius: 0.06, fill: { color: MIST } });
    s.addText([
      { text: label, options: { bold: true, fontSize: 17, color: SLATE, breakLine: true } },
      { text: where, options: { fontSize: 13, color: MUTED } },
    ], { x: M + 0.35, y: y + 0.2, w: 2.2, h: h - 0.4, isTextBox: true, margin: 0, valign: "top", fontFace: BODY });
    paras(s, M + 2.5, y + 0.18, W - 2 * M - 2.85, h - 0.3, texts, { size: 13, line: 17, gap: 5 });
    y += h + 0.2;
  });
});

/* ------------------------------------------------------------------ build */

function footer(s, text) {
  const dark = s.background && s.background.color === INK;
  s.addText(text, {
    x: W - M - 1.4, y: H - 0.62, w: 1.4, h: 0.3, isTextBox: true, margin: 0, align: "right",
    fontFace: BODY, fontSize: 11, color: dark ? "6B7C8C" : MUTED,
  });
}

// seconds per main slide; they add up to the 15-minute slot
const TIMES = [20, 60, 70, 30, 45, 55, 55, 45, 65, 70, 50, 75, 40, 55, 75, 80, 10];
if (TIMES.length !== main.length) throw new Error(`TIMES has ${TIMES.length} entries for ${main.length} slides`);
if (TIMES.reduce((a, b) => a + b, 0) !== 900) throw new Error("TIMES must add up to 15 minutes");
const mmss = (t) => `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`;

let elapsed = 0;
main.forEach((build, i) => {
  build();
  const s = pres.slides[pres.slides.length - 1];
  if (i > 0) footer(s, `${i + 1} / ${main.length}`);
  elapsed += TIMES[i];
  const timing = `Suggested time: ${mmss(TIMES[i])} (${mmss(elapsed)} of 15:00 at the end of this slide).`;
  s.addNotes(s.__notes ? timing + "\n\n" + s.__notes : timing);
});
backup.forEach((build, i) => {
  build();
  const s = pres.slides[pres.slides.length - 1];
  footer(s, `Backup ${i + 1}`);
  if (s.__notes) s.addNotes(s.__notes);
});

fs.mkdirSync(OUT_DIR, { recursive: true });
pres.writeFile({ fileName: OUT }).then(() => console.log("wrote " + OUT));
