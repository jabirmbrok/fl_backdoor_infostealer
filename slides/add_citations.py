"""Add the paper's citations to the talk deck: [n] markers in the text and a small footnote.

Numbers are the paper's own reference numbers ([1]-[25], in order of first citation), so the
audience can look them up in the proceedings. Which slide sentence carries which citation is
curated below from the paper source: each rule is the opening of a sentence as it appears on a
slide (the paper's wording, and the presenter's shortened wording where it differs) and the
references the paper attaches to that sentence. Slides that show a paper figure or table also
get, in the footnote only, the references the paper cites for the method shown.

Main slides get an inline marker before the sentence's full stop plus a footnote. Backup slides
get the footnote only, so their wording stays exactly as the presenter left it.

The script is idempotent: it removes the markers and footnotes it added earlier before adding
them again, so it can be rerun after the deck is edited.

Run:  python slides/add_citations.py <in.pptx> <out.pptx>
"""
import re
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

SHORT = {
    1: "K. Thomas et al., ACM CCS, 2017",
    2: "G. Franken et al., USENIX Security, 2018",
    3: "P. Wu et al., Computers & Security, 2025",
    4: "R. E. Davis et al., IEEE Access, 2024",
    5: "B. Xuan et al., Computers & Security, 2024",
    6: "M. Nobakht et al., Computers and Electrical Engineering, 2024",
    7: "Q. Ren et al., Computers & Security, 2024",
    8: "W. Jiang et al., CVPR, 2023",
    9: "C. Ma et al., PLOS ONE, 2025",
    10: "B. McMahan et al., AISTATS, 2017",
    11: "E. Bagdasaryan et al., AISTATS, 2020",
    12: "P. Blanchard et al., NeurIPS, 2017",
    13: "D. Yin et al., ICML, 2018",
    14: "Y. Wang et al., Knowledge-Based Systems, 2024",
    15: "G. Severi et al., USENIX Security, 2021",
    16: "L. Yang et al., IEEE S&P, 2023",
    17: "A. Pektaş and T. Acarman, IET Information Security, 2018",
    18: "T. Chen et al., Computers & Security, 2024",
    19: "D. Vasan et al., Computers & Security, 2020",
    20: "D. Zhang et al., Alexandria Engineering Journal, 2025",
    21: "M. Sandler et al., CVPR, 2018",
    22: "K. He et al., CVPR, 2016",
    23: "P. Fang and J. Chen, AAAI, 2023",
    24: "B. Bhanot et al., DICCT, 2025",
    25: "T. Liu et al., AAAI, 2024",
}

# opening of a slide sentence -> the paper's citations for that sentence
RULES = [
    ("Infostealer malware targets authentication artifacts", [1, 2]),
    ("Dynamic analysis captures runtime behavior", [3, 4, 5]),
    ("Federated learning (FL) allows participants", [6, 7]),
    ("Most FL backdoor work targets", [7]),
    ("An RGB-stack representation places", [5], "separate channels"),   # the paper cites [5] here
    ("We assume a targeted backdoor", [7, 8]),
    ("Targeted backdoor with one malicious client", [7, 8]),
    ("Multi-Krum is the primary defense", [12]),
    ("L₂-norm clipping, coordinate-wise median and trimmed mean", [13]),
    ("Tiles are aligned per sample", [19]),
    ("API-call events are converted into", [18]),
    ("To reduce sample-level leakage", [4]),
    ("In RGB-stack the API and network tiles", [5]),
]

# slide title (opening) -> references for the method a paper figure or table shows (footnote only)
VISUAL = [
    ("From Sandbox Reports to Image Tiles", [3, 4, 5, 17, 18, 19]),   # Figs. 2-3: sandbox, tiles, RGB fusion
    ("Channel-Aware Backdoor in Federated Learning", [6, 10, 23]),    # Fig. 4: aggregation, FedAvg, malicious client
    ("Backbone Selection Results", [20, 21, 22]),                     # Table III: the backbones
    ("Defense Screening", [12, 13]),                                  # Table V: the defenses
]

FOOT_NAME = "Citation footnote"
FOOT_TOP, FOOT_BOTTOM = 6.9, 7.32          # inches; the page number sits at 11.2-12.6 in
LEFT, RIGHT = 0.7, 11.05


def label(nums):
    """IEEE style: [1], [2] or a range [3]-[5]."""
    nums = sorted(set(nums))
    groups, start = [], nums[0]
    for a, b in zip(nums, nums[1:] + [None]):
        if b != a + 1:
            groups.append((start, a))
            start = b
    parts = [f"[{s}]–[{e}]" if e - s >= 2 else ", ".join(f"[{k}]" for k in range(s, e + 1)) for s, e in groups]
    return ", ".join(parts)


NBSP = " "


def inline_label(nums):
    """In-text marker: '[3], [4], [5]' joined with no-break spaces, so it never splits over a line."""
    return ("," + NBSP).join(f"[{n}]" for n in sorted(set(nums)))


def has_text(sh):
    return sh.has_text_frame and sh._element.find(qn("p:txBody")) is not None


def para_text(p):
    return "".join(r.text for r in p.runs)


def insert_at(p, index, text):
    """Insert text at a character index of a paragraph, inside the run that holds it."""
    pos = 0
    for r in p.runs:
        if index <= pos + len(r.text):
            o = index - pos
            r.text = r.text[:o] + text + r.text[o:]
            return
        pos += len(r.text)
    p.runs[-1].text += text


def strip_markers(p):
    for r in p.runs:
        # markers are only ever inserted before a sentence's full stop or at a run's end
        r.text = re.sub(r"[  ]\[\d+\](?:(?:,[  ]|–)\[\d+\])*(?=[.;:,]|$)", "", r.text)


def cite_paragraph(p, inline):
    """Return the references for sentences in this paragraph; insert markers if inline.

    A rule may name an anchor phrase; the marker then goes right after it, where the paper
    puts the citation, instead of before the sentence's full stop.
    """
    found = []
    text = para_text(p)
    for rule in RULES:
        prefix, refs = rule[0], rule[1]
        anchor = rule[2] if len(rule) > 2 else None
        k = text.find(prefix)
        if k < 0:
            continue
        found += refs
        if not inline:
            continue
        a = text.find(anchor, k) if anchor else -1
        if a >= 0:
            end = a + len(anchor)
        else:
            m = re.search(r"\.(\s|$)", text[k:])
            end = k + m.start() if m else len(text)
        insert_at(p, end, NBSP + inline_label(refs))
        text = para_text(p)
    return found


def title_of(slide):
    for sh in slide.shapes:
        if has_text(sh) and sh.top < Inches(1.0) and sh.top >= Inches(0.7):
            return sh.text_frame.text
    return ""


GAP = 0.2   # inches kept clear between the footnote and any shape beside it


def free_band(slide):
    """Widest horizontal gap in the footnote band not covered by any shape, with a margin."""
    busy = []
    for sh in slide.shapes:
        if sh.name == FOOT_NAME:
            continue
        top, bottom = Emu(sh.top).inches, Emu(sh.top + sh.height).inches
        left, right = Emu(sh.left).inches, Emu(sh.left + sh.width).inches
        if bottom > FOOT_TOP + 0.02 and top < FOOT_BOTTOM and not (left <= 0.05 and right >= 13.2):
            busy.append((left, right))
    x, best = LEFT, (0.0, LEFT, LEFT)
    for l, r in sorted(busy):
        stop = min(l - GAP, RIGHT)
        if stop > x:
            best = max(best, (stop - x, x, stop))
        x = max(x, r + GAP)
    if RIGHT > x:
        best = max(best, (RIGHT - x, x, RIGHT))
    return best[1], best[2]


# Slides whose figures and captions fill the footnote band. Their pictures are shortened by
# ROOM inches (keeping top-left and aspect ratio) and their "Fig." captions move up by the same
# amount, trimmed so they end above the band. Runs only while a caption still reaches the band.
MAKE_ROOM = ["From Sandbox Reports to Image Tiles"]
ROOM = 0.30


def make_room(slide):
    caps = [sh for sh in slide.shapes if has_text(sh) and sh.text_frame.text.startswith("Fig.")]
    if not caps or max(Emu(c.top + c.height).inches for c in caps) <= FOOT_TOP:
        return False
    for sh in slide.shapes:
        if sh.shape_type == 13 and Emu(sh.width).inches < 13.0:
            h = Emu(sh.height).inches
            scale = (h - ROOM) / h
            sh.width, sh.height = int(sh.width * scale), int(sh.height * scale)
    limit = FOOT_TOP - 0.04
    for c in caps:
        top = Emu(c.top).inches - ROOM
        c.top = Inches(top)
        c.height = Inches(min(Emu(c.height).inches, limit - top))
    return True


MIN_WIDTH = 3.0   # inches; narrower than this and the footnote would wrap into a column


def add_footnote(slide, nums, dark):
    left, right = free_band(slide)
    # no-break spaces inside each entry, so a line only ever breaks between entries
    text = "; ".join(f"[{n}]{NBSP}{SHORT[n].replace(' ', NBSP)}" for n in sorted(set(nums)))
    if right - left < MIN_WIDTH:
        return right - left, None
    box = slide.shapes.add_textbox(Inches(left), Inches(FOOT_TOP), Inches(right - left), Inches(FOOT_BOTTOM - FOOT_TOP))
    box.name = FOOT_NAME
    tf = box.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.BOTTOM
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    run = tf.paragraphs[0].add_run()
    run.text = text
    run.font.size = Pt(9)
    run.font.name = "Calibri"
    run.font.color.rgb = RGBColor.from_string("9FB3C8" if dark else "5A6B7C")
    return right - left, text


def is_dark(slide):
    from lxml import etree
    bg = slide._element.find(qn("p:cSld")).find(qn("p:bg"))
    if bg is None:
        return False
    m = re.search(r'srgbClr val="([0-9A-Fa-f]{6})"', etree.tostring(bg).decode())
    return bool(m) and int(m.group(1)[:2], 16) < 0x40


def restore_jpg_default(path):
    """python-pptx replaces the Default content type for .jpg with per-part Overrides; put it back."""
    import os
    import shutil
    import tempfile
    import zipfile
    fd, tmp = tempfile.mkstemp(suffix=".pptx")
    os.close(fd)
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "[Content_Types].xml":
                ct = data.decode("utf8")
                if 'Extension="jpg"' not in ct:
                    ct = ct.replace("<Default ", '<Default Extension="jpg" ContentType="image/jpeg"/><Default ', 1)
                data = ct.encode("utf8")
            zout.writestr(item, data)
    shutil.move(tmp, path)


def main(src, dst):
    prs = Presentation(src)
    slides = list(prs.slides)
    closing = next(i for i, s in enumerate(slides) if any(has_text(sh) and sh.text_frame.text.strip() == "Thank you" for sh in s.shapes))
    report = []
    for i, s in enumerate(slides):
        main_slide = i < closing
        for sh in list(s.shapes):
            if sh.name == FOOT_NAME:
                sh._element.getparent().remove(sh._element)
        nums = []
        for sh in s.shapes:
            if not has_text(sh):
                continue
            for p in sh.text_frame.paragraphs:
                if main_slide:
                    strip_markers(p)
                nums += cite_paragraph(p, inline=main_slide)
        t = title_of(s)
        for prefix, refs in VISUAL:
            if t.startswith(prefix):
                nums += refs
        if nums and any(t.startswith(m) for m in MAKE_ROOM) and make_room(s):
            report.append(f"slide {i + 1:2d}: figures shortened by {ROOM} in and captions raised to free the footnote band")
        if nums:
            width, text = add_footnote(s, nums, is_dark(s))
            where = f"footnote width {width:.2f} in" if text else f"NO FOOTNOTE: only {width:.2f} in free at the bottom"
            report.append(f"slide {i + 1:2d} ({'main' if main_slide else 'backup'}): {label(nums)}  {where}")
    prs.save(dst)
    restore_jpg_default(dst)
    print("\n".join(report))
    print("saved", dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
