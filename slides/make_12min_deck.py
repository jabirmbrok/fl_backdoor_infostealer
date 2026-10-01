"""Cut the 15-minute talk deck down to a simpler deck for a 12-minute slot.

Starts from the deck the presenter edited by hand (iwbis_channel_aware_backdoor_simple.pptx) and
leaves that file untouched. In the copy it writes:

  * three slides move behind the Thank-you slide as backup: the dataset table (Table I), backbone
    selection (Table III) and the seed-42 training curves (Figs. 5-6). Table II moves from the
    setup slide to the dataset backup slide;
  * the text on the remaining slides is shortened to a few lines each. Every number is one the
    15-minute deck already showed; nothing is computed here. Citation markers and footnotes stay;
  * each main slide's notes become: suggested time, SCRIPT (from speaker_script_12min.md), then
    Q&A NOTES (the notes the slide already had, plus what was cut from the spoken text);
  * each backup slide moved out of the talk keeps its 15-minute script under IF ASKED.

The script file is checked while building: every slot must cover its words at 125 words per
minute, and the talk must end before 12:00.

Run:  python slides/make_12min_deck.py [in.pptx] [script_12min.md] [out.pptx]
"""
import copy
import math
import os
import re
import sys

from pptx import Presentation
from pptx.oxml.ns import qn
from pptx.util import Inches

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from add_citations import restore_jpg_default  # noqa: E402
from embed_script import old_qa, sections, set_notes  # noqa: E402

WPM = 125
LIMIT = 12 * 60
CRLF = "\r\n"
NBSP = " "

# slide numbers of the 15-minute deck, in their new order
MAIN = [1, 2, 3, 4, 5, 7, 8, 10, 11, 12, 14, 15, 16, 17]
BACKUP = [6, 9, 13, 18, 19, 20]

# what was cut from the spoken text, by new slide number; appended to that slide's Q&A notes
QA_ADD = {
    5: "Cut from the 15-minute script: keeping only the largest-payload session is there to reduce "
       "leakage between samples. The dataset table (Table I) is on Backup 1.",
    7: "Cut from the 15-minute script: training runs in PyTorch on an RTX 3080, and the federated "
       "learning is a simulation we implemented ourselves in PyTorch. Batch size is 16; the learning rate "
       "and the weight decay are both ten to the minus four. There is no best-validation selection. The "
       "seeds are 42, 123 and 2026. Backbone selection (Table III) is on Backup 2: within RGB-stack, on "
       "seed 42, ResNet18 is the strongest backbone, at about 79 percent on both accuracy and macro-F1.",
    8: "Cut from the 15-minute script: the difference between red and green and their controls is not "
       "significant (both p = 1, 5/15 against 4/15, seed 42 only). The exact Fisher p-values are "
       "3.5 x 10^-19 (blue/fusion) and 2.6 x 10^-18 (full RGB) against their controls, and 4.0 x 10^-8 for "
       "blue against red and green. Pooling is legitimate because the split is re-drawn per seed.",
    9: "Cut from the 15-minute script: under Multi-Krum with the full-RGB trigger, clean accuracy drops "
       "from 84 to 76 percent on this seed.",
    10: "Cut from the 15-minute script: the shorter run is 30 rounds with one local epoch; re-trained at "
        "the full budget, the control rate is six out of fifteen instead of four.",
    11: "Cut from the 15-minute script: the seed-42 training curves (Figs. 5-6) are on Backup 3. The "
        "correlation is over the six Multi-Krum runs (r = 0.893, p = 0.017, n = 6).",
    13: "Cut from the 15-minute script: the trigger controls show that the effect comes from poisoning; "
        "the red and green results are on seed 42 only.",
}

# stale slide references in the notes the slides already had: (old slide number, old text, new text)
QA_FIX = [
    (6, "The text for Table I is on the backup slide.", "The paper's text for Table I is on Backup 4."),
    (8, "The text for Table II is on the backup slide. The seed-42 deviation belongs to Table VI; it is "
        "footnoted on slide 12 and given in full on the backup slide.",
        "Table II (experimental environment) is on Backup 1 and its text on Backup 4. The seed-42 deviation "
        "belongs to Table VI; it is footnoted on slide 10 and given in full on Backup 4."),
]


# ------------------------------------------------------------------ helpers

def text_of(sh):
    return sh.text_frame.text if sh.has_text_frame and sh._element.find(qn("p:txBody")) is not None else None


def find(slide, prefix):
    hits = [sh for sh in slide.shapes if (text_of(sh) or "").startswith(prefix)]
    assert len(hits) == 1, f"{len(hits)} shapes start with {prefix!r}"
    return hits[0]


def tables(slide):
    return [sh for sh in slide.shapes if getattr(sh, "has_table", False) and sh.has_table]


def place(sh, x=None, y=None, w=None, h=None):
    if x is not None:
        sh.left = Inches(x)
    if y is not None:
        sh.top = Inches(y)
    if w is not None:
        sh.width = Inches(w)
    if h is not None:
        sh.height = Inches(h)


def set_paras(sh, items, size=None, line=None, gap=None):
    """Replace a text box's paragraphs, keeping the look of its first paragraph.

    items: strings, or (string, True) for a bold paragraph. size, line and gap are in points.
    """
    body = sh._element.find(qn("p:txBody"))
    old = body.findall(qn("a:p"))
    template = old[0]
    for p in old:
        body.remove(p)
    for i, item in enumerate(items):
        text, bold = (item, False) if isinstance(item, str) else item
        p = copy.deepcopy(template)
        runs = p.findall(qn("a:r"))
        for r in runs[1:]:
            p.remove(r)
        runs[0].find(qn("a:t")).text = text
        rpr = runs[0].find(qn("a:rPr"))
        rpr.attrib.pop("err", None)
        if bold:
            rpr.set("b", "1")
        else:
            rpr.attrib.pop("b", None)
        end = p.find(qn("a:endParaRPr"))
        if size:
            rpr.set("sz", str(round(size * 100)))
            if end is not None:
                end.set("sz", str(round(size * 100)))
        ppr = p.find(qn("a:pPr"))
        if ppr is None:     # a paragraph retyped in PowerPoint may carry no properties
            ppr = p.makeelement(qn("a:pPr"), {})
            p.insert(0, ppr)
        lnspc = ppr.find(qn("a:lnSpc"))
        if line and lnspc is not None:
            lnspc.find(qn("a:spcPts")).set("val", str(round(line * 100)))
        aft = ppr.find(qn("a:spcAft"))
        if aft is not None:
            ppr.remove(aft)
        if gap and i < len(items) - 1:
            aft = ppr.makeelement(qn("a:spcAft"), {})
            aft.append(aft.makeelement(qn("a:spcPts"), {"val": str(round(gap * 100))}))
            if lnspc is not None:
                lnspc.addnext(aft)
            else:
                ppr.insert(0, aft)
        body.append(p)


def set_line(sh, text, size=None):
    """One paragraph, one run: for kickers, titles and page labels."""
    set_paras(sh, [(text, sh.text_frame.paragraphs[0].runs[0].font.bold)], size=size)


def restyle_table(sh, row_h=None, font=None, width=None):
    tbl = sh._element.find(".//" + qn("a:tbl"))
    rows = tbl.findall(qn("a:tr"))
    if row_h:
        for tr in rows:
            tr.set("h", str(Inches(row_h)))
        sh.height = Inches(row_h) * len(rows)
    if font:
        for tag in ("a:rPr", "a:endParaRPr"):
            for el in tbl.iter(qn(tag)):
                el.set("sz", str(round(font * 100)))
    if width:
        cols = tbl.find(qn("a:tblGrid")).findall(qn("a:gridCol"))
        scale = Inches(width) / sum(int(c.get("w")) for c in cols)
        for c in cols:
            c.set("w", str(round(int(c.get("w")) * scale)))
        sh.width = Inches(width)


def move_shape(sh, dest):
    """Move a shape to another slide (text boxes and tables only: they carry no relationships)."""
    tree = dest.shapes._spTree
    new_id = max(int(e.get("id")) for e in tree.iter(qn("p:cNvPr"))) + 1
    el = sh._element
    tree.append(el)
    el.find(".//" + qn("p:cNvPr")).set("id", str(new_id))


def notes_of(slide):
    return slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ""


def seconds(mmss):
    m, s = mmss.split(":")
    return int(m) * 60 + int(s)


def check_timing(secs):
    """Every slot covers its words at WPM, the clock adds up, and the talk ends before LIMIT."""
    clock = 0
    print("slide  words  spoken  slot   clock")
    for n in sorted(secs):
        slot, at, paras = secs[n]
        words = sum(len(re.sub(r"\[[^\]]*\]", "", p).split()) for p in paras)
        spoken = math.ceil(words * 60 / WPM)
        clock += seconds(slot)
        print(f"{n:5d}  {words:5d}  {spoken // 60}:{spoken % 60:02d}    {slot}   {at}")
        assert spoken <= seconds(slot), f"slide {n}: {words} words need {spoken} s, slot is {slot}"
        assert clock == seconds(at), f"slide {n}: clock should be {clock // 60}:{clock % 60:02d}, script says {at}"
    assert clock < LIMIT, f"the talk ends at {clock} s, not under {LIMIT} s"
    return f"{clock // 60}:{clock % 60:02d}"


# ------------------------------------------------------------------ slide text

def simplify(old):
    """old: {slide number in the 15-minute deck: slide}."""
    c12 = f"{NBSP}[12]"
    c13 = f"{NBSP}[13]"

    s = old[2]
    set_paras(find(s, "Infostealer malware targets"), [
        f"Steals credentials, browser data and session cookies{NBSP}[1],{NBSP}[2].",
        "Knowing the family helps threat intelligence, triage and incident response.",
    ], size=21, line=28, gap=16)
    set_paras(find(s, "Dynamic analysis captures"), [
        "API calls show what the malware does on the host; network artifacts show how it communicates.",
        f"Both can be encoded as images for a CNN{NBSP}[3],{NBSP}[4],{NBSP}[5].",
    ], size=21, line=28, gap=16)
    set_paras(find(s, "Federated learning (FL) allows"), [
        "Clients train one classifier together without moving raw data.",
        f"A malicious client can inject a backdoor through its updates{NBSP}[6],{NBSP}[7].",
    ], size=21, line=28, gap=16)

    s = old[3]
    set_paras(find(s, "Most FL backdoor work"), [
        f"Most FL backdoor work targets general image or model-level poisoning, not the channels of a malware representation{NBSP}[7].",
        f"RGB-stack places API-call, network and fused information in separate channels{NBSP}[5], so a trigger in one channel need not behave like a trigger in another.",
    ], size=17, line=23, gap=14)
    set_paras(find(s, "We construct dynamic"), [
        "Build API-call and network representations from Cuckoo Sandbox reports of five latest and most prevalent infostealer families.",
        "Select the representation and the CNN backbone.",
        "Evaluate channel-aware backdoors in FL with red, green, blue and full-RGB triggers, trigger controls and Multi-Krum.",
    ], size=15.5, line=20.5, gap=9)

    set_line(find(old[4], "PROPOSED METHOD"), "PROPOSED METHOD  ·  1 / 3")

    s = old[5]
    set_line(find(s, "PROPOSED METHOD"), "PROPOSED METHOD  ·  2 / 3")
    set_line(find(s, "From Sandbox Reports"), "From Sandbox Reports to Image Tiles and RGB-Stack", size=30)

    s = old[7]
    set_line(find(s, "PROPOSED METHOD"), "PROPOSED METHOD  ·  3 / 3")
    box = find(s, "Each client holds")
    place(box, w=4.85)
    set_paras(box, [
        "Five clients, 70 images each, 14 per family: balanced and IID.",
        f"One malicious client puts a trigger on AgentTesla training images and relabels them as FormBook{NBSP}[7],{NBSP}[8].",
        "Poison rate 20% of its 14 AgentTesla images: two images per round, resampled every round.",
        ("Four trigger settings: red/API, green/network, blue/fusion and full RGB.", True),
    ], size=17, line=23, gap=13)

    s = old[8]
    cap2, tab2 = find(s, "TABLE II."), tables(s)[0]
    assert tab2.table.cell(1, 0).text == "Dynamic analysis"
    training = tables(s)[1]
    heads = [sh for sh in s.shapes if text_of(sh) == "Training"]
    assert len(heads) == 1
    place(heads[0], y=1.62)
    place(training, y=2.10)
    restyle_table(training, row_h=0.6, font=16)
    set_line(find(s, "Training Federated Learning"), "Model and evaluation")
    box = find(s, "The best model reported")
    place(box, y=2.45, w=5.05, h=1.75)
    set_paras(box, [
        "ResNet18 on RGB-stack, trained from scratch.",
        "Final-round global model, with no best-validation selection.",
        "Clean accuracy, macro-F1 and ASR over seeds 42, 123 and 2026.",
    ], size=16, line=21.5, gap=8)
    place(find(s, "Defense and trigger control"), y=4.38)
    box = find(s, "Multi-Krum is the primary defense")
    place(box, y=4.90, h=1.75)
    set_paras(box, [
        f"Multi-Krum is the primary defense{c12}.",
        f"Clipping, coordinate-wise median and trimmed mean are also screened{c13}.",
        "Trigger control: the same triggers on the clean FL model at test time.",
    ], size=16, line=21.5, gap=8)

    s = old[10]
    set_line(find(s, "RESULTS"), "RESULTS  ·  1 / 3")
    box = find(s, "Table IV shows")
    place(box, y=2.10, h=4.5)
    set_paras(box, [
        ("Blue/fusion and full RGB reach 100% ASR; red/API and green/network do not.", True),
        "Blue/fusion does so without modifying all three channels.",
        f"Not a trigger artifact: blue/fusion and full RGB differ from their trigger controls at p{NBSP}<{NBSP}10⁻¹⁷ (Fisher exact); red and green do not (p{NBSP}={NBSP}1, 5/15 against 4/15).",
    ], size=17, line=23, gap=14)

    s = old[11]
    set_line(find(s, "RESULTS"), "RESULTS  ·  2 / 3")
    box = find(s, "Table V gives")
    place(box, y=2.00, h=4.6)
    set_paras(box, [
        "Clipping, coordinate-wise median and trimmed mean leave ASR at 1.0000.",
        ("Only Multi-Krum reduces it, and only under full RGB: 1.0000 to 0.4000.", True),
        "Multi-Krum is taken to the multi-seed evaluation.",
    ], size=17, line=23, gap=16)

    s = old[12]
    set_line(find(s, "RESULTS"), "RESULTS  ·  3 / 3")
    set_paras(find(s, "† Across-seed"), [
        "† Across-seed ASR range ≥ 0.5: the outcome is bimodal, so read the per-seed counts (out of 15 source samples), not the mean.",
        "The seed-42 clean baseline and trigger controls come from a 30-round, one-local-epoch run. No ASR result is affected.",
    ], gap=4)
    box = find(s, "Across three seeds")
    place(box, y=5.65, h=1.15)
    set_paras(box, [
        ("Across three seeds, blue/fusion and full-RGB backdoors reach 100% ASR, with clean performance comparable to the clean FL baseline.", True),
        "In seven of the eight trigger controls the target rate is identical with and without the trigger: the ASR is not an artifact of the pattern.",
    ], size=15.5, line=20.5, gap=7)

    s = old[14]
    set_paras(find(s, "The last two rows"), [
        "Under Multi-Krum the mean is misleading. Per seed: 15/15, 3/15, 5/15 for blue/fusion and 6/15, 15/15, 6/15 for full RGB.",
        ("Bimodal: on some seeds the backdoor remains fully effective, on the others most of it is suppressed.", True),
        f"It tracks selection: the malicious client is retained in 8–50% of rounds, and that rate correlates with the final ASR (r{NBSP}={NBSP}0.893, p{NBSP}={NBSP}0.017, n{NBSP}={NBSP}6).",
        "Multi-Krum is unreliable as a standalone defense.",
    ], size=16.5, line=22.5, gap=13)

    s = old[15]
    set_paras(find(s, "The ordering follows"), [
        "Mean value inside the trigger region of the clean images: 214.6 in R, 48.3 in G and 21.6 in B.",
        "37.7% of red trigger-region pixels are already at least 254, where the trigger changes nothing.",
        "Contrast explains red's failure but not green's, whose contrast is 207.",
    ], size=20, line=27, gap=16)
    set_paras(find(s, "Since blue is"), [
        ("Blue is an edge map of the other two, so its effectiveness cannot come from information they lack.", True),
        ("It is almost empty, so the trigger is the only strong response there.", True),
        "Consistent with the measurements, but not established.",
    ], size=20, line=27, gap=16)

    s = old[16]
    set_paras(find(s, "The novelty is"), [
        ("The representation's channels are an attack surface: a trigger confined to the fusion channel alone matches one spanning all three.", True),
        "Blue/fusion and full-RGB triggers reached 100% ASR across three seeds, with clean performance close to the baseline.",
        "Multi-Krum reduced ASR bimodally rather than partially, leaving the backdoor fully effective (15/15) on one of the three seeds for each trigger.",
        ("Channel-aware backdoors are a serious threat to federated malware classifiers in this controlled IID setting, and motivate representation-aware defenses.", True),
    ], size=17, line=23, gap=13)
    box = find(s, "The main limitations")
    place(box, w=11.9)
    set_paras(box, [
        "Limitations: the IID-only partition, a single source–target pair, and three seeds, with the red and green results resting on seed 42 alone.",
        "Future work: a non-IID partition, a second source–target pair and a contrast-matched trigger.",
    ], size=14.5, line=19.5, gap=6)

    # backup: Table I, joined by Table II from the setup slide
    s = old[6]
    set_line(find(s, "PROPOSED METHOD"), "BACKUP")
    set_line(find(s, "Dataset Creation"), "Dataset and Experimental Environment")
    place(find(s, "TABLE I."), x=0.70, w=5.85)
    tab1 = tables(s)[0]
    place(tab1, x=0.70)
    restyle_table(tab1, width=5.85)
    move_shape(cap2, s)
    move_shape(tab2, s)
    place(cap2, x=6.75, y=1.68)
    place(tab2, x=6.75, y=2.10)
    restyle_table(tab2, row_h=0.58, font=15)

    set_line(find(old[9], "RESULTS"), "BACKUP")
    set_line(find(old[13], "RESULTS"), "BACKUP")

    # the backup slide that points at the slides its notes belong to
    s = old[18]
    for label, where in [("Table I", "Backup 1"), ("Table II", "Backup 1"), ("Table VI", "slide 10"), ("Figs. 5–6", "Backup 3")]:
        box = [sh for sh in s.shapes if (text_of(sh) or "").split("\n")[0] == label]
        assert len(box) == 1, label
        box[0].text_frame.paragraphs[1].runs[0].text = where


# ------------------------------------------------------------------ build

def main(src, script, dst):
    secs = sections(open(script, encoding="utf8").read())
    assert sorted(secs) == list(range(1, len(MAIN) + 1)), "the script needs one section per main slide"
    total = check_timing(secs)
    secs15 = sections(open(os.path.join(HERE, "speaker_script_15min.md"), encoding="utf8").read())

    prs = Presentation(src)
    slides = list(prs.slides)
    assert len(slides) == len(MAIN) + len(BACKUP), "this script expects the 20-slide 15-minute deck"
    old = {i + 1: s for i, s in enumerate(slides)}
    assert text_of(old[17].shapes[0]).strip() == "Thank you"
    before = {n: notes_of(s) for n, s in old.items()}

    simplify(old)

    # reorder: the talk, then the backup slides
    lst = prs.slides._sldIdLst
    ids = list(lst)
    for el in ids:
        lst.remove(el)
    for n in MAIN + BACKUP:
        lst.append(ids[n - 1])

    def qa_of(n):
        qa = old_qa(before[n])
        for m, was, now in QA_FIX:
            if m == n:
                assert was in qa, f"slide {n}: expected note not found"
                qa = qa.replace(was, now)
        return qa

    for new, n in enumerate(MAIN, start=1):
        s = old[n]
        slot, clock, paras = secs[new]
        qa = "\n\n".join(t for t in (qa_of(n), QA_ADD.get(new)) if t)
        text = f"Suggested time: {slot} ({clock} of {total} at the end of this slide)." + CRLF + CRLF
        text += "SCRIPT" + CRLF + (CRLF + CRLF).join(paras)
        if qa:
            text += CRLF + CRLF + "Q&A NOTES" + CRLF + qa.replace("\n", CRLF)
        set_notes(s, text)
        if new > 1:
            for sh in s.shapes:
                if re.fullmatch(r"\d+ / \d+", (text_of(sh) or "").strip()):
                    sh.text_frame.paragraphs[0].runs[0].text = f"{new} / {len(MAIN)}"

    for k, n in enumerate(BACKUP, start=1):
        s = old[n]
        for sh in s.shapes:
            if re.fullmatch(r"\d+ / \d+|Backup \d+", (text_of(sh) or "").strip()):
                sh.text_frame.paragraphs[0].runs[0].text = f"Backup {k}"
        if n not in secs15:
            continue
        paras = list(secs15[n][2])
        if n == 6:      # Table II came from the setup slide; so does the sentence about it
            first = re.sub(r"^\[[^\]]*\]\s*", "", secs15[8][2][0])
            assert ". The model is trained" in first
            paras.append(first.split(". The model is trained")[0] + ".")
        text = "BACKUP SLIDE. Not part of the 12-minute talk; show it only if a question needs it." + CRLF + CRLF
        text += "IF ASKED" + CRLF + (CRLF + CRLF).join(paras)
        qa = qa_of(n)
        if qa:
            text += CRLF + CRLF + "Q&A NOTES" + CRLF + qa.replace("\n", CRLF)
        set_notes(s, text)

    prs.save(dst)
    restore_jpg_default(dst)
    print(f"{len(MAIN)} main slides ending at {total}, {len(BACKUP)} backup slides")
    print("saved", dst)


if __name__ == "__main__":
    args = sys.argv[1:]
    main(
        args[0] if len(args) > 0 else os.path.join(HERE, "iwbis_channel_aware_backdoor_simple.pptx"),
        args[1] if len(args) > 1 else os.path.join(HERE, "speaker_script_12min.md"),
        args[2] if len(args) > 2 else os.path.join(HERE, "iwbis_channel_aware_backdoor_12min.pptx"),
    )
