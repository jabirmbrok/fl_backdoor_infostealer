// IWBIS talk deck, laid out along the paper's own spine:
// Introduction, Methodology, Results, Discussion, Conclusion.
// Every number comes from paper/ieee_malware_fl_backdoor.tex or results/tables/.
const pptxgen = require("pptxgenjs");
const path = require("path");

const REPO = "C:/Users/wwyl5/Project/malware";
const SCRATCH = __dirname;

// palette: the paper is about the R, G and B channels of a malware image,
// so the data colors are the channels themselves against a deep slate ground
const INK = "101820";
const SLATE = "1B2A41";
const PAPER = "FFFFFF";
const MIST = "EDF1F5";
const MUTED = "5A6B7C";
const ACC = "2E86DE"; // fusion channel blue, the paper's finding
const RED = "C0392B";
const GRN = "27AE60";
const BLU = "2E86DE";
const FULL = "7D3C98";

const HEAD = "Cambria";
const BODY = "Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
pres.author = "Aziz, Mubarok, Fitria";
pres.title = "Channel-Aware Backdoor Attacks in Federated Malware Classification";

const W = 13.3, H = 7.5, M = 0.7;

const SPINE = ["Introduction", "Methodology", "Results", "Discussion", "Conclusion"];

// the motif: a small solid square, the 12x12 trigger patch
function patch(slide, x, y, size, color) {
  slide.addShape(pres.ShapeType.rect, { x, y, w: size, h: size, fill: { color } });
}

// five squares bottom-right, one per paper section, the current one filled,
// so the audience can always see which part of the paper they are in
function spine(slide, active, onDark) {
  const size = 0.15, gap = 0.24;
  const x0 = W - M - 4 * gap - size;
  SPINE.forEach((_, i) => {
    const on = i === active;
    patch(slide, x0 + i * gap, H - 0.62, size,
      on ? ACC : (onDark ? "36485C" : "D3DCE4"));
  });
}

function darkSlide() {
  const s = pres.addSlide();
  s.background = { color: INK };
  return s;
}

function lightSlide(title, section, step) {
  const s = pres.addSlide();
  s.background = { color: PAPER };
  const kicker = step
    ? SPINE[section].toUpperCase() + "   \u00b7   " + step
    : SPINE[section].toUpperCase();
  s.addText(kicker, {
    x: M, y: 0.42, w: 10, h: 0.28, isTextBox: true,
    fontFace: BODY, fontSize: 11, bold: true, color: ACC, charSpacing: 2, margin: 0,
  });
  s.addText(title, {
    x: M, y: 0.72, w: W - 2 * M, h: 0.75, isTextBox: true,
    fontFace: HEAD, fontSize: 30, bold: true, color: SLATE, margin: 0,
  });
  spine(s, section, false);
  return s;
}

function card(slide, x, y, w, h, fill) {
  slide.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.06,
    fill: { color: fill || MIST },
  });
}

function stat(slide, x, y, w, value, label, color, size) {
  slide.addText(value, {
    x, y, w, h: 0.66, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: size || 34, bold: true, color: color || SLATE,
  });
  slide.addText(label, {
    x, y: y + 0.68, w, h: 0.9, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 11.5, color: MUTED, lineSpacing: 15, valign: "top",
  });
}

// a tinted row: square, bold label, description alongside
function labelRow(slide, x, y, w, h, label, text, opts) {
  const o = opts || {};
  const labelW = o.labelW || 3.1;
  card(slide, x, y, w, h, o.fill || MIST);
  // align the square with the label's first line, not with the row's centre
  patch(slide, x + 0.3, y + 0.19, 0.24, o.mark || "AAB7C4");
  slide.addText(label, {
    x: x + 0.75, y: y + 0.18, w: labelW, h: h - 0.3, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 14.5, bold: true, color: o.labelColor || SLATE, valign: "top",
  });
  slide.addText(text, {
    x: x + 0.75 + labelW + 0.25, y: y + 0.18,
    w: w - 1.0 - labelW - 0.25, h: h - 0.3, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 13.5, color: SLATE, lineSpacing: 18, valign: "top",
  });
}

function bullets(slide, x, y, w, h, items, size) {
  slide.addText(items.map((t, i) => ({
    text: t,
    options: i === items.length - 1
      ? { bullet: true }
      : { bullet: true, breakLine: true, paraSpaceAfter: 11 },
  })), {
    x, y, w, h, isTextBox: true, margin: 0, valign: "top",
    fontFace: BODY, fontSize: size || 14, color: SLATE, lineSpacing: 20,
  });
}

function footnote(slide, y, text) {
  slide.addText(text, {
    x: M, y, w: W - 2 * M, h: 0.7, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 12.5, italic: true, color: MUTED, lineSpacing: 17, valign: "top",
  });
}

const chartFrame = () => ({
  showTitle: false,
  showLegend: true, legendPos: "b", legendFontFace: BODY, legendFontSize: 11,
  catAxisLabelColor: MUTED, catAxisLabelFontFace: BODY, catAxisLabelFontSize: 11,
  valAxisLabelColor: MUTED, valAxisLabelFontFace: BODY, valAxisLabelFontSize: 11,
  valGridLine: { color: "E3E8EE", size: 1 },
  catGridLine: { style: "none" },
  showValue: true, dataLabelPosition: "outEnd",
  dataLabelFontFace: BODY, dataLabelFontSize: 11, dataLabelColor: SLATE,
  barGapWidthPct: 45,
  valAxisMinVal: 0,
});

const tableStyle = {
  fontFace: BODY, fontSize: 12.5, color: SLATE,
  border: { type: "solid", color: "DCE3EA", pt: 1 },
  fill: { color: PAPER }, rowH: 0.36, valign: "middle",
};

const c = (t, o) => ({ text: t, options: Object.assign({ align: "center" }, o || {}) });
const hd = t => ({ text: t, options: { bold: true } });
const hc = t => ({ text: t, options: { bold: true, align: "center" } });

/* ============================================================== 1  title */
{
  const s = darkSlide();
  s.addText("Channel-Aware Backdoor Attacks", {
    x: M, y: 2.05, w: 11.6, h: 0.9, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 44, bold: true, color: PAPER,
  });
  s.addText("Against Federated Infostealer Malware Classification", {
    x: M, y: 2.95, w: 11.6, h: 0.65, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 27, color: "9FB3C8",
  });
  s.addText("Using Dynamic API-Call and Network Representations", {
    x: M, y: 3.56, w: 11.6, h: 0.45, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 16, color: "7A8FA6",
  });
  [RED, GRN, BLU].forEach((col, i) => patch(s, M + i * 0.42, 4.5, 0.3, col));
  s.addText("Mochamad Asryl Aziz  \u00b7  Moh. Jabir Mubarok  \u00b7  Eka Fitria", {
    x: M, y: 5.3, w: 11.6, h: 0.35, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 14, color: PAPER,
  });
  s.addText("IWBIS", {
    x: M, y: 5.7, w: 11.6, h: 0.35, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 13, color: MUTED,
  });
  s.addNotes("The talk follows the paper: introduction, methodology, results, discussion, conclusion. The five squares at the bottom right of every slide show which section we are in. Headline result: a trigger confined to the fusion channel alone matches one spanning all three, even though that channel is derived from the other two.");
}

/* ================================================ 2  introduction 1 of 3 */
{
  const s = lightSlide("Federated learning helps, and opens a door", 0, "1 of 3");
  bullets(s, M, 1.85, 7.0, 2.9, [
    "Infostealers take credentials, browser data and session cookies, so classifying the family feeds triage and incident response.",
    "Dynamic analysis carries the signal: API calls for host execution, network artifacts for communication. Both encode as CNN images.",
    "Federated learning trains one classifier without moving raw data, but the server sees only client updates, never the local data.",
  ], 14.5);
  footnote(s, 5.0, "The server cannot inspect local training data. That is the opening a malicious client needs.");

  card(s, 8.3, 1.85, 4.3, 3.6, MIST);
  s.addText("One image, three channels", {
    x: 8.6, y: 2.08, w: 3.7, h: 0.32, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 13, bold: true, color: SLATE,
  });
  [
    ["R", "API-call tile", RED],
    ["G", "network tile", GRN],
    ["B", "edge map of (R+G)/2,\nderived from the other two", BLU],
  ].forEach(([ch, txt, col], i) => {
    const y = 2.6 + i * 0.85;
    patch(s, 8.6, y + 0.05, 0.26, col);
    s.addText(ch, {
      x: 9.0, y, w: 0.4, h: 0.35, isTextBox: true, margin: 0,
      fontFace: HEAD, fontSize: 16, bold: true, color: SLATE,
    });
    s.addText(txt, {
      x: 9.45, y, w: 2.85, h: 0.75, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 12.5, color: SLATE, lineSpacing: 16, valign: "top",
    });
  });
  s.addNotes("Set the threat up before the method. The infostealer capability and the image encoding are both prior work; we claim no novelty for them, only for what we do with the channels. Keep the 'can enable' wording on account compromise.");
}

/* ================================================ 3  introduction 2 of 3 */
{
  const s = lightSlide("Most FL backdoor work looks past the channels", 0, "2 of 3");
  [
    ["Prior FL backdoor work", "targets general image tasks or model-level poisoning, not channel-specific behavior in malware representations", {}],
    ["Malware backdoor work", "explanation-guided and family-selective triggers on static features of a centralized classifier", {}],
    ["This work", "attacks a federated model through the channels of a dynamic-behavior image, a setting that remains underexplored",
      { fill: "E8F1FC", mark: ACC, labelColor: ACC }],
  ].forEach(([l, t, o], i) => labelRow(s, M, 1.95 + i * 1.32, 11.9, 1.1, l, t, o));
  footnote(s, 6.05, "An RGB-stack puts API-call, network and fused information in separate channels, so a trigger in one channel need not behave like a trigger in another.");
  s.addNotes("The two closest papers are Severi et al., USENIX Security 2021, and Yang et al., IEEE S&P 2023, both added in the camera-ready at a reviewer's request. Say 'most' and 'underexplored', not 'nobody has ever'. Our delta runs on three axes at once: static to dynamic, centralized to federated, feature space to representation channels.");
}

/* ================================================ 4  introduction 3 of 3 */
{
  const s = lightSlide("We treat the channels as the attack surface", 0, "3 of 3");
  [
    ["1", "Build dynamic API-call and network representations from Cuckoo Sandbox reports for five Windows infostealer families."],
    ["2", "Select the representation and backbone: RGB-stack for its explicit channel separation, then the strongest backbone within it."],
    ["3", "Evaluate red/API, green/network, blue/fusion and full-RGB triggers, with trigger controls and a Multi-Krum defense analysis."],
  ].forEach(([n, t], i) => {
    const y = 1.95 + i * 1.0;
    s.addText(n, {
      x: M, y, w: 0.45, h: 0.45, isTextBox: true, margin: 0,
      fontFace: HEAD, fontSize: 22, bold: true, color: ACC,
    });
    s.addText(t, {
      x: M + 0.55, y: y + 0.04, w: 7.3, h: 0.85, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 14, color: SLATE, lineSpacing: 19, valign: "top",
    });
  });

  card(s, 8.7, 1.9, 3.9, 3.2, "E8F1FC");
  s.addText("The finding", {
    x: 9.0, y: 2.1, w: 3.3, h: 0.3, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 12.5, bold: true, color: SLATE,
  });
  stat(s, 9.0, 2.45, 3.3, "15/15",
    "attack success on every seed, for a trigger in the fusion channel alone and for one spanning all three", ACC, 36);
  s.addText("Attack success rate: AgentTesla test images predicted FormBook.", {
    x: 9.0, y: 4.3, w: 3.3, h: 0.65, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 11.5, italic: true, color: MUTED, lineSpacing: 15, valign: "top",
  });

  footnote(s, 5.35, "Clean performance stays close to the clean federated baseline. Channel-aware backdoors are a serious threat to federated malware classifiers in this controlled IID setting, and motivate representation-aware defenses.");
  s.addNotes("Contribution 2 is 'select', not 'RGB-stack wins': the two representations were measured on different split files, so the camera-ready dropped the cross-representation comparison. Never deliver 'serious threat' without the controlled-IID qualifier.");
}

/* ================================================= 5  methodology 1 of 5 */
{
  const s = lightSlide("Five families, 100 samples each, 15 in test", 1, "1 of 5");
  s.addTable([
    [hd("Family"), hc("Train"), hc("Val"), hc("Test"), hc("Total")],
    ["AgentTesla", c("70"), c("15"), c("15"), c("100")],
    ["FormBook", c("70"), c("15"), c("15"), c("100")],
    ["SalatStealer", c("70"), c("15"), c("15"), c("100")],
    ["StealC", c("70"), c("15"), c("15"), c("100")],
    ["Vidar", c("70"), c("15"), c("15"), c("100")],
    [hd("Total"), c("350", { bold: true }), c("75", { bold: true }),
      c("75", { bold: true }), c("500", { bold: true })],
  ], Object.assign({}, tableStyle, {
    x: M, y: 1.95, w: 6.5, colW: [2.3, 1.05, 1.05, 1.05, 1.05], rowH: 0.5,
  }));

  bullets(s, 7.6, 2.0, 5.0, 3.4, [
    "Cuckoo Sandbox traces become a 16 x 16 API tile; packet captures become a 28 x 28 network tile.",
    "Only the largest-payload session per sample is kept, to limit sample-level leakage.",
    "Stratified by family and re-drawn for every seed, so the seeds do not share a test set.",
  ], 14.5);

  footnote(s, 5.8, "AgentTesla is the attack's source family, so every attack success rate in this talk is a count out of those 15 test images.");
  s.addNotes("Dynamic analysis only, no static features. Flag the scale out loud: 15 test images per family is small, and one flipped image is one fifteenth of the rate. The paper does not enumerate the behavior categories behind the API tile, so do not offer them if asked precisely.");
}

/* ================================================= 6  methodology 2 of 5 */
{
  const s = lightSlide("Blue is derived from red and green, and is nearly empty", 1, "2 of 5");
  [
    ["R", "API-call tile, 16 x 16, upscaled", RED],
    ["G", "network tile, 28 x 28, upscaled", GRN],
    ["B", "edge map of the average of R and G", BLU],
  ].forEach(([ch, txt, col], i) => {
    const y = 1.95 + i * 0.62;
    patch(s, M, y + 0.05, 0.3, col);
    s.addText(ch, {
      x: M + 0.42, y, w: 0.45, h: 0.38, isTextBox: true, margin: 0,
      fontFace: HEAD, fontSize: 17, bold: true, color: SLATE,
    });
    s.addText(txt, {
      x: M + 0.95, y: y + 0.03, w: 5.5, h: 0.38, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13.5, color: SLATE,
    });
  });

  card(s, M, 3.95, 6.7, 2.0, "E8F1FC");
  s.addText("B = FindEdges( (R + G) / 2 )", {
    x: M + 0.3, y: 4.12, w: 6.1, h: 0.42, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 19, bold: true, color: ACC,
  });
  s.addText("A 3 x 3 edge convolution, so blue is a deterministic function of the other two and adds no independent information. It is also the emptiest channel: 62.8% of its pixels are exactly zero across the 500 images, 54.5% in AgentTesla.", {
    x: M + 0.3, y: 4.58, w: 6.1, h: 1.25, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 12.5, color: SLATE, lineSpacing: 17, valign: "top",
  });

  s.addImage({
    path: path.join(REPO, "paper", "malware.png"),
    x: 7.85, y: 1.9, w: 4.75, h: 3.75, sizing: { type: "contain", w: 4.75, h: 3.75 },
  });
  s.addText("Processed representations, one column per family", {
    x: 7.85, y: 5.7, w: 4.75, h: 0.3, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 11, color: MUTED,
  });
  footnote(s, 6.15, "Opacity blend mixes both sources into every channel; RGB-stack is used because only it separates the sources by channel.");
  s.addNotes("The determinism was verified against the shipped dataset: FindEdges(mean(R,G)) reproduced with zero difference on 400 of 400 images. This answers a reviewer directly: blue cannot owe its effectiveness to information content, because it has none the other two lack. Zero-pixel share 62.8% dataset-wide, 54.5% on the AgentTesla row of results/tables/channel_stats.csv.");
}

/* ================================================= 7  methodology 3 of 5 */
{
  const s = lightSlide("RGB-stack for channel separation, ResNet18 within it", 1, "3 of 5");
  s.addTable([
    [hd("Representation"), hd("Backbone"), hc("Acc."), hc("Macro-F1")],
    ["Opacity blend", "SmallCNN", c("0.5333"), c("0.5298")],
    ["Opacity blend", "MobileNetV2", c("0.6933"), c("0.6903")],
    ["Opacity blend", "ResNet18", c("0.7733"), c("0.7730")],
    ["RGB-stack", "SmallCNN", c("0.5200"), c("0.5144")],
    ["RGB-stack", "MobileNetV2", c("0.7200"), c("0.7200")],
    [hd("RGB-stack"), hd("ResNet18"), c("0.7867", { bold: true, color: ACC }),
      c("0.7884", { bold: true, color: ACC })],
  ], Object.assign({}, tableStyle, {
    x: M, y: 1.95, w: 7.0, colW: [2.2, 1.9, 1.45, 1.45], rowH: 0.5,
  }));

  card(s, 8.35, 1.95, 4.25, 3.5, MIST);
  s.addText("Federated setting", {
    x: 8.65, y: 2.2, w: 3.65, h: 0.3, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 12.5, bold: true, color: SLATE,
  });
  [
    ["FedAvg", "one server, five clients"],
    ["70 images", "per client, 14 per family, IID"],
    ["50 x 2", "rounds x local epochs, final-round model"],
  ].forEach(([k, v], i) => {
    const y = 2.75 + i * 0.82;
    s.addText(k, {
      x: 8.65, y, w: 1.35, h: 0.3, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13, bold: true, color: ACC, valign: "top",
    });
    s.addText(v, {
      x: 10.05, y, w: 2.3, h: 0.55, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 12, color: SLATE, lineSpacing: 15, valign: "top",
    });
  });

  footnote(s, 5.8, "The two representations were generated from different split files, so this table is not a paired comparison. RGB-stack is chosen because channel separation is required here; macro-F1 selects only the backbone within it. Seed 42, ResNet18 trained from scratch with AdamW.");
  s.addNotes("Be explicit that RGB-stack is not shown to be the better representation. That claim was removed in the camera-ready because the rows sit on different test sets. All backbones are trained from scratch. SmallCNN is three conv blocks of 32, 64 and 128 channels if anyone asks.");
}

/* ================================================= 8  methodology 4 of 5 */
{
  const s = lightSlide("The attacker is weak by design: two images per round", 1, "4 of 5");
  [
    ["1 of 5", "clients is malicious, and takes part in every round"],
    ["2 images", "poisoned per round, resampled each round"],
    ["12 x 12", "white trigger, bottom-right, written after normalization"],
    ["0 scaling", "pure data poisoning, no model replacement"],
  ].forEach(([v, l], i) => {
    const x = M + i * 3.05;
    card(s, x, 1.95, 2.8, 2.0);
    s.addText(v, {
      x: x + 0.25, y: 2.15, w: 2.3, h: 0.55, isTextBox: true, margin: 0,
      fontFace: HEAD, fontSize: 24, bold: true, color: ACC,
    });
    s.addText(l, {
      x: x + 0.25, y: 2.75, w: 2.35, h: 1.05, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 12.5, color: SLATE, lineSpacing: 17, valign: "top",
    });
  });

  s.addText("AgentTesla is relabelled as FormBook. Both are infostealers, so the pair is a plausible same-category target.", {
    x: M, y: 4.2, w: 11.9, h: 0.35, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 14, color: SLATE,
  });
  s.addText("Four trigger settings: red/API, green/network, blue/fusion, and all three channels at once. Attack success rate is the share of the 15 triggered AgentTesla test images that the model calls FormBook.", {
    x: M, y: 4.65, w: 11.9, h: 0.75, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 14, color: SLATE, lineSpacing: 20, valign: "top",
  });
  footnote(s, 5.6, "The configured poison rate is 20% of the attacker's 14 AgentTesla images; the code truncates, so two images are poisoned each round, an effective 14.3%. That is 2 of the 350 global training images.");
  s.addNotes("The capability is deliberately weak: no update scaling, no model replacement, so model-replacement work is background rather than the attack used here. The trigger is written after normalization.");
}

/* ================================================= 9  methodology 5 of 5 */
{
  const s = lightSlide("Four defenses screened, and one deviation disclosed", 1, "5 of 5");
  [
    ["Multi-Krum", "scores updates by distance to the others and averages the |S| = 2 lowest of five, with f = 1", { mark: ACC }],
    ["Three baselines", "L2-norm clipping, coordinate-wise median and trimmed mean, screened alongside it", {}],
    ["Trigger control", "the same trigger applied at test time to a clean model that never saw poisoned data", {}],
  ].forEach(([l, t, o], i) => labelRow(s, M, 1.95 + i * 1.28, 7.8, 1.08, l, t,
    Object.assign({ labelW: 1.9 }, o)));

  card(s, 8.85, 1.95, 3.75, 3.84, "FBEDEC");
  s.addText("Disclosed deviation", {
    x: 9.15, y: 2.2, w: 3.15, h: 0.3, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 12.5, bold: true, color: RED,
  });
  s.addText("The seed-42 clean baseline and its trigger controls come from a 30-round, one-local-epoch run, not the common 50 x 2 budget.", {
    x: 9.15, y: 2.62, w: 3.15, h: 1.3, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 12.5, color: SLATE, lineSpacing: 17, valign: "top",
  });
  s.addText("No attack success result is affected: every backdoor and defense run uses the common budget.", {
    x: 9.15, y: 4.15, w: 3.15, h: 1.2, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 12.5, bold: true, color: SLATE, lineSpacing: 17, valign: "top",
  });

  footnote(s, 6.05, "Screening every defense on every seed would multiply the budget for candidates that may not survive, and all runs share one GPU, so the screening narrows the field on a single seed first.");
  s.addNotes("Disclose the deviation here and give the retrained numbers later, when the trigger-control result is on screen. Multi-Krum is taken as a standard robust-aggregation baseline, not as a defense we propose.");
}

/* ===================================================== 10  results 1 of 4 */
{
  const s = lightSlide("The channel decides whether the backdoor works", 2, "1 of 4");
  s.addChart(pres.ChartType.bar, [
    { name: "With poisoning", labels: ["Red / API", "Green / network", "Blue / fusion", "Full RGB"], values: [5, 5, 15, 15] },
    { name: "Trigger control (clean model)", labels: ["Red / API", "Green / network", "Blue / fusion", "Full RGB"], values: [4, 4, 4, 4] },
  ], Object.assign(chartFrame(), {
    x: M, y: 1.85, w: 7.6, h: 3.9,
    chartColors: [ACC, "B8C4D0"],
    valAxisMaxVal: 16, valAxisTitle: "AgentTesla flipped to FormBook, of 15",
    showValAxisTitle: true, valAxisTitleFontFace: BODY, valAxisTitleFontSize: 11,
    valAxisTitleColor: MUTED,
  }));

  card(s, 8.55, 1.85, 4.05, 3.9, "E8F1FC");
  s.addText("Fisher exact, pooled", {
    x: 8.85, y: 2.05, w: 3.45, h: 0.32, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 12.5, bold: true, color: SLATE,
  });
  [
    ["Blue vs its control", "p = 3.5e-19", ACC],
    ["Full RGB vs its control", "p = 2.6e-18", ACC],
    ["Blue vs red and green", "p = 4.0e-08", ACC],
    ["Red, green vs their controls", "p = 1", RED],
  ].forEach(([l, v, col], i) => {
    const y = 2.48 + i * 0.66;
    s.addText(l, {
      x: 8.85, y, w: 3.45, h: 0.28, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 11.5, color: MUTED,
    });
    s.addText(v, {
      x: 8.85, y: y + 0.24, w: 3.45, h: 0.33, isTextBox: true, margin: 0,
      fontFace: HEAD, fontSize: 15, bold: true, color: col,
    });
  });
  s.addText("Red and green are not distinguishable from a clean model at all.", {
    x: 8.85, y: 5.15, w: 3.45, h: 0.5, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 12, italic: true, color: SLATE, lineSpacing: 15, valign: "top",
  });

  footnote(s, 5.95, "Blue alone matches all three channels at once, and blue is a deterministic edge map of red and green, so it carries nothing they lack. That is the paper's central claim. Seed 42; why blue and not green comes after the defenses.");
  s.addNotes("Pooling across seeds is legitimate because the split is re-drawn per seed, so the pooled samples are distinct. Red and green were run on seed 42 only. Leave the mechanism to the discussion slides.");
}

/* ===================================================== 11  results 2 of 4 */
{
  const s = lightSlide("Only one of four defenses moves the attack at all", 2, "2 of 4");
  s.addTable([
    [hd("Defense"), hc("Blue / fusion"), hc("Full RGB"), hc("Clean acc., full RGB")],
    ["No defense", c("15/15"), c("15/15"), c("0.8400")],
    ["L2 clipping", c("15/15"), c("15/15"), c("0.8533")],
    ["Coordinate-wise median", c("15/15"), c("15/15"), c("0.8400")],
    ["Trimmed mean", c("15/15"), c("15/15"), c("0.8133")],
    [hd("Multi-Krum"), c("15/15"), c("6/15", { bold: true, color: ACC }),
      c("0.7600", { bold: true, color: RED })],
  ], Object.assign({}, tableStyle, {
    x: M, y: 1.95, w: 8.4, colW: [3.0, 1.8, 1.8, 1.8], rowH: 0.56,
  }));

  s.addText("Multi-Krum is the only defense that moved the attack at all, so it is the one carried to the multi-seed stage \u2014 even though under blue/fusion it too leaves the backdoor at 15 of 15.", {
    x: 9.3, y: 2.0, w: 3.3, h: 2.5, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 13.5, color: SLATE, lineSpacing: 19, valign: "top",
  });

  footnote(s, 5.75, "Single seed, seed 42 \u2014 which turns out to be the seed where blue/fusion defeats Multi-Krum. Counts are out of the 15 AgentTesla test images; the paper prints them as rates, 1.0000 and 0.4000.");
  s.addNotes("Point out that the single-seed screening is exactly the bias a reviewer flagged, and that the next two slides show why it matters. The clean-accuracy column is seed 42 only.");
}

/* ===================================================== 12  results 3 of 4 */
{
  const s = lightSlide("Across three seeds, both strong triggers hit 15 of 15", 2, "3 of 4");
  [
    ["15/15", "on every seed, for blue/fusion and for full RGB under FedAvg", ACC],
    ["0.8311 \u00b1 0.0539", "clean accuracy under the blue/fusion backdoor, against 0.8267 \u00b1 0.0134 for clean FL", SLATE],
    ["7 of 8", "trigger controls give exactly the same target rate with and without the trigger", ACC],
  ].forEach(([v, l, col], i) => {
    const x = M + i * 4.05;
    card(s, x, 1.9, 3.8, 2.25);
    stat(s, x + 0.28, 2.12, 3.25, v, l, col, 26);
  });

  bullets(s, M, 4.45, 11.9, 1.4, [
    "The control applies the same trigger, at test time, to a clean model that never saw poisoned data. Its residual rate is the model's own AgentTesla-to-FormBook confusion.",
    "Per-seed control rates for blue/fusion are 4/15, 1/15 and 1/15, so the 15 of 15 under poisoning cannot be credited to the trigger pattern itself.",
  ], 13.5);

  footnote(s, 6.1, "Clean accuracy stays comparable on average, but its spread is four times the baseline's and on seed 123 it falls to 0.7733. Re-trained under the common budget, the seed-42 baseline gives 0.7867 accuracy, 0.7869 macro-F1 and a control rate of 6/15 rather than 4/15.");
  s.addNotes("Do not say the aggregate metrics never flag the attack: nothing here tests a detector, and the per-seed numbers move. The honest statement is that accuracy and macro-F1 alone did not separate poisoned from clean runs here.");
}

/* ===================================================== 13  results 4 of 4 */
{
  const s = lightSlide("Multi-Krum does not half-work. It flips.", 2, "4 of 4");
  s.addChart(pres.ChartType.bar, [
    { name: "Blue / fusion", labels: ["seed 42", "seed 123", "seed 2026"], values: [15, 3, 5] },
    { name: "Full RGB", labels: ["seed 42", "seed 123", "seed 2026"], values: [6, 15, 6] },
  ], Object.assign(chartFrame(), {
    x: M, y: 1.85, w: 7.3, h: 3.9,
    chartColors: [BLU, FULL],
    valAxisMaxVal: 16, valAxisTitle: "attack success under Multi-Krum, of 15",
    showValAxisTitle: true, valAxisTitleFontFace: BODY, valAxisTitleFontSize: 11,
    valAxisTitleColor: MUTED,
  }));

  card(s, 8.3, 1.85, 4.3, 3.9, "FBEDEC");
  s.addText("0.5111 \u00b1 0.4286", {
    x: 8.6, y: 2.05, w: 3.7, h: 0.5, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 22, bold: true, color: RED,
  });
  s.addText("describes no run we actually observed.", {
    x: 8.6, y: 2.52, w: 3.7, h: 0.4, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 12.5, color: SLATE,
  });
  bullets(s, 8.6, 3.0, 3.7, 2.55, [
    "For each trigger, one seed of three shows no suppression at all: 15 of 15.",
    "Multi-Krum does cut the attack against FedAvg, p = 1.5e-08 and 9.1e-07. It is unreliable as a standalone defense, not ineffective.",
    "Clean accuracy is nominally lower, but no paired difference is significant at n = 3, all p \u2265 0.42.",
  ], 12);

  footnote(s, 5.95, "The across-seed range is at least 0.5, so the paper reports per-seed counts and never the mean alone. The one concrete utility cost is on seed 42, where full-RGB clean accuracy falls from 0.8400 to 0.7600.");
  s.addNotes("This is the correction a reviewer prompted and it is the honest reading: bimodal, not graded. Seed 42, the seed that chose the defense, is the seed where blue/fusion defeats it.");
}

/* ================================================== 14  discussion 1 of 3 */
{
  const s = lightSlide("The leading explanation: blue's channel is nearly empty", 3, "1 of 3");
  s.addChart(pres.ChartType.bar, [
    { name: "Contrast against a white trigger", labels: ["R (API)", "G (network)", "B (fusion)"], values: [40.4, 206.7, 233.4] },
  ], Object.assign(chartFrame(), {
    x: M, y: 1.85, w: 6.4, h: 3.9,
    chartColors: [RED, GRN, BLU], varyColors: true, showLegend: false,
    valAxisMaxVal: 255, valAxisTitle: "levels the trigger moves the channel",
    showValAxisTitle: true, valAxisTitleFontFace: BODY, valAxisTitleFontSize: 11,
    valAxisTitleColor: MUTED, dataLabelFormatCode: "0.0",
  }));

  bullets(s, 7.4, 1.9, 5.2, 2.9, [
    "37.7% of red trigger-region pixels are already at 254 or above, where writing a white trigger changes nothing.",
    "Contrast explains red's failure but not green's, whose contrast is 207 and which still fails.",
    "Blue is a deterministic edge map, so its effect cannot come from information red and green lack. What is left is that it is almost empty.",
  ], 13.5);

  card(s, 7.4, 5.0, 5.2, 0.9, MIST);
  s.addText("Stated as a hypothesis, not a finding. A contrast-matched trigger is the experiment that would settle it.", {
    x: 7.7, y: 5.15, w: 4.6, h: 0.65, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 12.5, italic: true, color: SLATE, lineSpacing: 16, valign: "top",
  });

  footnote(s, 6.1, "Contrast is 255 minus the mean intensity inside the bottom-right trigger region, over the 500 clean images. Region means are 214.6 / 48.3 / 21.6; whole-image channel means are 241.7 / 81.5 / 10.2. The measured region is about 13 px per side, 10% of the image.");
  s.addNotes("The measurement is on clean images, not on the trained model, so the evidence is correlational. Green is the open case: its contrast is high and the trigger still does nothing measurable there.");
}

/* ================================================== 15  discussion 2 of 3 */
{
  const s = lightSlide("It flips because selection is close to a coin flip", 3, "2 of 3");
  s.addTable([
    [hd("Run"), hc("Malicious client kept"), hc("Rate"), hc("Final attack success")],
    ["Blue / fusion, seed 42", c("25 of 50"), c("50%"), c("15/15", { bold: true, color: RED })],
    ["Blue / fusion, seed 123", c("4 of 50"), c("8%"), c("3/15")],
    ["Blue / fusion, seed 2026", c("16 of 50"), c("32%"), c("5/15")],
    ["Full RGB, seed 42", c("14 of 50"), c("28%"), c("6/15")],
    ["Full RGB, seed 123", c("22 of 50"), c("44%"), c("15/15", { bold: true, color: RED })],
    ["Full RGB, seed 2026", c("9 of 50"), c("18%"), c("6/15")],
  ], Object.assign({}, tableStyle, {
    x: M, y: 1.9, w: 8.1, colW: [2.7, 2.0, 1.2, 2.2], rowH: 0.5,
  }));

  card(s, 9.1, 1.9, 3.5, 1.4, "E8F1FC");
  s.addText("r = 0.893,  p = 0.017", {
    x: 9.35, y: 2.15, w: 3.0, h: 0.42, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 18, bold: true, color: ACC,
  });
  s.addText("Pearson, across the six runs, n = 6", {
    x: 9.35, y: 2.6, w: 3.0, h: 0.4, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 11.5, color: MUTED, lineSpacing: 15, valign: "top",
  });
  bullets(s, 9.1, 3.6, 3.5, 2.2, [
    "With f = 1 and |S| = 2 of five clients, the poisoned update is not an outlier in parameter space.",
    "Surviving selection is close to a coin flip, and the attacker only has to win often enough.",
  ], 12.5);

  footnote(s, 6.05, "The rank correlation is weaker and not significant at this size: Spearman rho = 0.794, p = 0.059, n = 6. Retention tracks the outcome; it is not established as the cause.");
  s.addNotes("This is the mechanism behind the bimodality. Be candid about n = 6 and about the Pearson value leaning on the two 15/15 runs, because a hostile question here is free otherwise.");
}

/* ================================================== 16  discussion 3 of 3 */
{
  const s = lightSlide("Under Multi-Krum the attack never settles", 3, "3 of 3");
  s.addImage({
    path: path.join(SCRATCH, "perround-1.png"),
    x: M, y: 1.9, w: 7.5, h: 4.0, sizing: { type: "contain", w: 7.5, h: 4.0 },
  });
  bullets(s, 8.5, 1.95, 4.1, 3.5, [
    "The backdoored models track the clean baseline in macro-F1 throughout training.",
    "Under FedAvg both triggers climb to 15 of 15 and stay there.",
    "Under Multi-Krum the curves stay unstable round to round, so there is no stable partial suppression level to rely on.",
  ], 13);
  footnote(s, 6.1, "Per-round test-set curves across the three seeds; shaded areas are the standard deviation across seeds. The first rounds are not meaningful: the global model is still close to initialization and collapses onto one or two classes.");
  s.addNotes("This is the per-round view of the same bimodality. The instability is the point: a defense you cannot predict round to round is not one you can deploy on its own.");
}

/* ================================================== 17  conclusion 1 of 2 */
{
  const s = lightSlide("What the evidence supports, and where it stops", 4, "1 of 2");
  s.addText("ESTABLISHED", {
    x: M, y: 1.85, w: 5.8, h: 0.3, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 12, bold: true, color: ACC, charSpacing: 1.5,
  });
  bullets(s, M, 2.3, 5.8, 3.6, [
    "Blue/fusion and full-RGB triggers reach 15 of 15 across three seeds, with clean performance close to the baseline.",
    "In seven of the eight trigger controls the target rate is identical with and without the trigger, so the effect comes from poisoning.",
    "Multi-Krum reduces the attack bimodally rather than partially, leaving it fully effective on one of the three seeds for each trigger.",
  ], 14.5);

  s.addText("NOT ESTABLISHED", {
    x: 7.1, y: 1.85, w: 5.5, h: 0.3, isTextBox: true, margin: 0,
    fontFace: BODY, fontSize: 12, bold: true, color: RED, charSpacing: 1.5,
  });
  [
    ["Three seeds", "and the red and green results rest on seed 42 alone"],
    ["One source-target pair", "AgentTesla to FormBook only"],
    ["IID partition only", "although the motivation for federation is non-IID data"],
    ["Emptiness is a hypothesis", "consistent with the measurements, not established"],
  ].forEach(([h, t], i) => {
    const y = 2.3 + i * 0.95;
    patch(s, 7.1, y + 0.06, 0.22, RED);
    s.addText(h, {
      x: 7.5, y, w: 5.1, h: 0.3, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 13.5, bold: true, color: SLATE, valign: "top",
    });
    s.addText(t, {
      x: 7.5, y: y + 0.3, w: 5.1, h: 0.45, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 12.5, color: MUTED, lineSpacing: 16, valign: "top",
    });
  });

  footnote(s, 6.15, "A non-IID partition, a second source-target pair and a contrast-matched trigger are the three experiments left to future work. The split files already carry a non-IID client assignment, so that one is available rather than blocked.");
  s.addNotes("Say the limitations out loud rather than waiting to be asked. Every threat claim in this talk is scoped to a controlled IID setting.");
}

/* ================================================== 18  conclusion 2 of 2 */
{
  const s = darkSlide();
  spine(s, 4, true);
  s.addText("CONCLUSION   \u00b7   2 of 2", {
    x: M, y: 0.5, w: 10, h: 0.28, isTextBox: true,
    fontFace: BODY, fontSize: 11, bold: true, color: ACC, charSpacing: 2, margin: 0,
  });
  s.addText("What to take away", {
    x: M, y: 0.88, w: 11.9, h: 0.7, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 34, bold: true, color: PAPER,
  });
  [
    ["The channel is the attack surface", "A trigger in the fusion channel alone matches one spanning all three. Red and green do nothing measurable."],
    ["The effective channel carries no information", "Blue is a deterministic edge map of the other two, and the emptiest of the three."],
    ["Robust aggregation flips rather than degrades", "Multi-Krum leaves the backdoor fully effective on one seed in three, so it is unreliable on its own."],
  ].forEach(([h, t], i) => {
    const y = 2.05 + i * 1.35;
    patch(s, M, y + 0.1, 0.3, ACC);
    s.addText(h, {
      x: M + 0.6, y, w: 11.2, h: 0.4, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 18, bold: true, color: PAPER,
    });
    s.addText(t, {
      x: M + 0.6, y: y + 0.42, w: 11.2, h: 0.6, isTextBox: true, margin: 0,
      fontFace: BODY, fontSize: 14, color: "9FB3C8", lineSpacing: 19, valign: "top",
    });
  });
  s.addText("Defenses that inspect updates miss a threat that lives in the representation. In this controlled IID setting, that motivates representation-aware defenses.", {
    x: M, y: 6.15, w: 11.9, h: 0.7, isTextBox: true, margin: 0,
    fontFace: HEAD, fontSize: 16, italic: true, color: PAPER, lineSpacing: 21, valign: "top",
  });
  s.addNotes("Close on the defense implication: the attack surface sits in the representation, and we propose no defense here. Thank the reviewers; the per-seed reporting and the significance tests came from their comments.");
}

const out = path.join(SCRATCH, "iwbis_channel_aware_backdoor.pptx");
pres.writeFile({ fileName: out }).then(() => console.log("wrote " + out));
