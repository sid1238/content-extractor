import io
import json
import os
import re
from collections import Counter
from xml.sax.saxutils import escape

import requests
from PyPDF2 import PdfReader
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Flowable, HRFlowable, Paragraph, SimpleDocTemplate

from rag.ats import _BULLET, _OFFICIAL_PATTERNS, _TITLE_WORD, _heading_name
from rag.matcher import DATE_RANGE, SKILLS, _SKILL_PATTERNS, extract_skills

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
LLM_MODEL = os.environ.get("RESUME_LLM_MODEL", "llama3.1:latest")
LLM_TIMEOUT_SECONDS = 300
LLM_ATTEMPTS = 3


class TailorError(Exception):
    def __init__(self, message, status=422):
        super().__init__(message)
        self.status = status


# ---- Resume structure ----
# The resume becomes an ordered list of blocks. Only blocks marked "rewrite" or "skills" can
# change, so headings, education, job titles, companies and dates are copied across as they are.

_REWRITE_SECTIONS = {"experience", "projects", "summary"}
_PRESENT = re.compile(r"\b(?:present|current|now|today)\b", re.IGNORECASE)


def _is_header_line(line, next_line):
    stripped = line.strip()
    if _BULLET.match(line) or len(stripped.split()) > 12 or stripped.endswith("."):
        return False
    return bool(DATE_RANGE.search(stripped) or _TITLE_WORD.search(stripped)
                or (next_line and DATE_RANGE.search(next_line)) or len(stripped.split()) <= 6)


def _merge_lines(lines):
    """Undoes line wrapping, so each bullet or paragraph is one piece of text."""
    merged = []
    for i, raw in enumerate(lines):
        line = raw.strip()
        if not line:
            continue
        previous = merged[-1] if merged else None
        next_line = lines[i + 1] if i + 1 < len(lines) else ""
        starts_new = _BULLET.match(line) or DATE_RANGE.search(line) or previous is None \
            or DATE_RANGE.search(previous) or previous.endswith((".", ":"))
        looks_like_header = _is_header_line(line, next_line) and not line[0].islower()
        if not starts_new and not looks_like_header:
            merged[-1] = f"{previous} {line}"
        else:
            merged.append(line)
    return merged


def _lines_for_section(section, lines):
    if section == "header":
        return [l.strip() for l in lines if l.strip()]
    if section == "skills":
        # Each line is its own category, so only rejoin a list that clearly wrapped.
        merged = []
        for line in (l.strip() for l in lines if l.strip()):
            if merged and (merged[-1].endswith(",") or line[0].islower()):
                merged[-1] = f"{merged[-1]} {line}"
            else:
                merged.append(line)
        return merged
    return _merge_lines(lines)


_IRREGULAR_VERBS = {"built", "led", "wrote", "ran", "made", "drove", "grew", "taught", "won", "began", "held"}
_VERB_STEMS = ("construct|creat|develop|build|manag|design|implement|lead|analyz|analys|maintain|writ|test|deploy|improv|"
               "coordinat|collaborat|work|support|optimiz|optimis|reduc|increas|present|perform|conduct|train|mentor|"
               "automat|integrat|deliver|research|prepar|monitor|track|review|ensur|launch|predict|detect|classif|"
               "generat|engineer|establish|produc|evaluat|explor|migrat|refactor|configur|architect|investigat|model")
_VERB_FORM = re.compile(rf"(?:{_VERB_STEMS})(?:e|es|ed|d|s|ing|ies|ied|y)?$", re.IGNORECASE)


def _split_project_name(text):
    """'Health Aware Constructed a chatbot...' -> ('Health Aware', 'Constructed a chatbot...').
    The name must survive unchanged, so finding it can't be left to the model. Returns (None, text)
    if there's no clear boundary, and the caller then leaves the paragraph as it is."""
    words = text.split()
    for i in range(1, min(len(words) - 1, 14)):
        word = words[i]
        # A verb followed by lowercase starts the description; "Using Deep Learning" is part of a name.
        if word[0].isupper() and (word.lower() in _IRREGULAR_VERBS or _VERB_FORM.fullmatch(word)) and words[i + 1][0].islower():
            return " ".join(words[:i]), " ".join(words[i:])
    return None, text


def parse_blocks(text):
    blocks, section, tense, group = [], "header", "past", 0
    pending = []

    def flush():
        nonlocal tense, group
        for line in _lines_for_section(section, pending):
            if section == "skills":
                blocks.append({"kind": "skills", "section": section, "text": line, "group": group})
            elif section in _REWRITE_SECTIONS and (_BULLET.match(line) or not _is_header_line(line, "")):
                bullet = bool(_BULLET.match(line))
                body = _BULLET.sub("", line).strip()
                name = None
                if not bullet and section == "projects":
                    name, body = _split_project_name(body)
                    if name is None:
                        blocks.append({"kind": "fixed", "section": section, "text": line, "group": group, "paragraph": True})
                        continue
                blocks.append({"kind": "rewrite", "section": section, "text": body, "name": name, "bullet": bullet,
                               "tense": tense, "group": group})
            else:
                match = DATE_RANGE.search(line)
                if match and section in _REWRITE_SECTIONS:
                    tense = "present" if _PRESENT.search(match.group(0)) else "past"
                    group += 1
                blocks.append({"kind": "fixed", "section": section, "text": line, "group": group})
        pending.clear()

    for line in text.splitlines():
        name = _heading_name(line)
        if name:
            flush()
            section, tense = name, "past"
            blocks.append({"kind": "heading", "section": name, "text": line.strip(), "group": group})
        else:
            pending.append(line)
    flush()
    return blocks


# ---- Checks on what the model writes ----

_NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
_WORD = re.compile(r"[A-Za-z][\w+#-]*")
_ACRONYM = re.compile(r"\b[A-Z]{2,}[A-Za-z0-9]*\b")
_QUOTED = re.compile(r"[“”\"]([^“”\"]{4,})[“”\"]")
_STOPWORDS = set("""a an and are as at be been by for from has have in into is it its of on or that the their them they this
to was were which with while across using used use via each all both also such than then these those through per over""".split())
_WEAK_OPENERS = {"utilized", "utilised", "leveraged", "worked", "responsible", "helped", "assisted"}
# Words that claim something about scope or seniority. Each must already be in the original text.
_CLAIM_WORDS = re.compile(
    r"\b(?:deploy\w*|production|scal(?:e|ed|able|ing|ability)|robust|massive|large-scale|enterprise|mission-critical|"
    r"led|lead\w*|managed|architect\w*|spearhead\w*|million\w*|billion\w*|thousand\w*|hundred\w*|real-time|cloud|"
    r"cross-functional|stakeholder\w*|customer\w*|significant\w*|substantial\w*|dramatic\w*|revenue|cost\w*)\b",
    re.IGNORECASE,
)
_PAST_OPENER = re.compile(r"\w+(?:ed|d)$|built|led|wrote|ran|made|drove|grew|taught|won|began|held|did|set|cut|spent|sent|found|kept|took", re.IGNORECASE)


def _numbers(text):
    return {n.replace(",", "") for n in _NUMBER.findall(text)}


def _content_words(text):
    return {w.lower() for w in _WORD.findall(text)} - _STOPWORDS


def _stem(word):
    return re.sub(r"(?:ing|ed|es|e|s|d|al|ly|ion|ions|ation)$", "", word.lower())


def find_violations(new, block, source, allowed_terms):
    """Every reason a rewrite can't be trusted. The model never gets the last word on facts:
    anything not backed by this person's own text is rejected here."""
    original = block["text"]
    problems = []

    # Nothing true may be lost.
    lost_numbers = _numbers(original) - _numbers(new)
    if lost_numbers:
        problems.append(f"drops these numbers from the original: {', '.join(sorted(lost_numbers))}")
    lost_skills = set(extract_skills(original)) - set(extract_skills(new))
    lost_skills |= {name for name, pattern in _OFFICIAL_PATTERNS.items() if pattern.search(original) and not pattern.search(new)}
    lost_skills |= set(_ACRONYM.findall(original)) - set(_ACRONYM.findall(new))
    if lost_skills:
        problems.append(f"drops these tools from the original: {', '.join(sorted(lost_skills))}")
    for quoted in _QUOTED.findall(original):
        if quoted.lower() not in new.lower():
            problems.append(f'drops the title "{quoted}"')

    # Nothing untrue may be added.
    invented = _numbers(new) - _numbers(source)
    if invented:
        problems.append(f"uses numbers that aren't in the resume: {', '.join(sorted(invented))}")
    new_skills = set(extract_skills(new)) - set(extract_skills(source))
    # "scikit-learn" for "scikit learn" is the same skill, only written properly.
    new_skills = {s for s in new_skills if not (s in _OFFICIAL_PATTERNS and _OFFICIAL_PATTERNS[s].search(source))}
    if new_skills:
        problems.append(f"mentions skills the person hasn't listed: {', '.join(sorted(new_skills))}")
    claims = {m.group(0).lower() for m in _CLAIM_WORDS.finditer(new)} - {m.group(0).lower() for m in _CLAIM_WORDS.finditer(source)}
    if claims:
        problems.append(f"makes claims the original doesn't support: {', '.join(sorted(claims))}")

    # Mostly the person's own words, apart from the opening verb and permitted job terms.
    known = {_stem(w) for w in _content_words(original) | _content_words(allowed_terms)}
    body_words = _content_words(new)
    unknown = {w for w in body_words if _stem(w) not in known and w != new.split()[0].lower()} if new.split() else set()
    if len(unknown) > max(3, len(body_words) // 4):
        problems.append(f"adds too many words the original doesn't use: {', '.join(sorted(unknown)[:8])}")

    if len(new.split()) > max(len(original.split()) + 6, int(len(original.split()) * 1.2)):
        problems.append("is too long")
    if len(new.split()) < max(4, int(len(original.split()) * 0.6)):
        problems.append("drops too much of the original content")

    opener = new.split()[0].lower().strip(",.") if new.split() else ""
    if opener in _WEAK_OPENERS and block["section"] != "summary":
        problems.append(f'starts with the weak verb "{opener}"')
    if block["section"] != "summary" and block["tense"] == "past" and not _PAST_OPENER.fullmatch(opener):
        problems.append(f'starts with "{opener}", which isn\'t a past-tense verb')
    return problems


# ---- Rewriting ----

def _ask_model(system, user, schema):
    try:
        resp = requests.post(f"{OLLAMA_URL}/api/chat", timeout=LLM_TIMEOUT_SECONDS, json={
            "model": LLM_MODEL, "stream": False, "format": schema, "options": {"temperature": 0.2},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        })
    except requests.RequestException:
        raise TailorError("The local AI model isn't reachable. Start Ollama and try again.", 503)
    if resp.status_code == 404:
        raise TailorError(f"The AI model {LLM_MODEL} isn't installed. Run: ollama pull {LLM_MODEL}", 503)
    if resp.status_code >= 400:
        raise TailorError("The local AI model returned an error. Try again.", 503)
    try:
        return json.loads(resp.json()["message"]["content"])
    except (ValueError, KeyError, TypeError):
        return None


_FILLER_USING = re.compile(r"\b(?:utilizing|utilising|leveraging|employing)\b")
_FILLER_USED = re.compile(r"(?<=[.!?] )(?:Utilized|Utilised|Leveraged)\b")
_REWRITE_SCHEMA = {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]}

_SYSTEM = """You polish one line of a real person's resume. It must stay completely true.

Rules:
- Describe exactly the same work as the original. Keep every tool, name, title and number it mentions.
- Never add a tool, a number, a result, or a claim about scale that the original doesn't state.
- {opening}{avoid}
- Fix grammar and remove filler. Keep about the same length: {words} words.
- If it fits the work, swap in a term from the list you're given. Otherwise ignore the list.

Example
Original: Made a script in Python to pull 200 reports and put them in a spreadsheet.
Rewritten: Automated the collection of 200 reports into a spreadsheet using a Python script.

Reply with JSON in the form {{"text": "..."}}."""


def _opening_rule(block):
    if block["section"] == "summary":
        return "This is a professional summary, so keep it in the same form as the original."
    tense = " in the past tense" if block["tense"] == "past" else ""
    return (f"Start with a strong action verb{tense} that says what the person actually did. Evaluating something is not building it.\n"
            "- Never start with Utilized, Leveraged, Worked, Responsible or Helped.")


def rewrite_block(block, source, terms, used_openers):
    original = block["text"]
    # Varied verbs read better, but a repeat isn't worth rejecting an otherwise good line over.
    avoid = f"\n- Other lines already start with: {', '.join(sorted(used_openers))}. Prefer a different verb." if used_openers else ""
    system = _SYSTEM.format(opening=_opening_rule(block), words=len(original.split()), avoid=avoid)
    allowed_terms = " ".join(terms)
    feedback, problems = "", []
    for _ in range(LLM_ATTEMPTS):
        user = f"Terms from the job posting: {', '.join(terms) or 'none'}\n\nOriginal: {original}{feedback}"
        new = str((_ask_model(system, user, _REWRITE_SCHEMA) or {}).get("text", "")).strip()
        new = _FILLER_USED.sub("Used", _FILLER_USING.sub("using", new))
        problems = find_violations(new, block, source, allowed_terms) if new else ["returned nothing"]
        if not problems:
            return new, []
        feedback = f"\n\nYour last attempt was rejected because it {'; '.join(problems)}.\nLast attempt: {new}\nWrite a corrected version."
    return None, problems


_JOB_STOPWORDS = _STOPWORDS | set("""you your our we will can may must should would able work working team teams role company job
experience years year including include strong ability new more other about what who how when where why not if but our us
benefits salary equal employment opportunity apply candidates application location""".split())


def _job_phrases(job_text):
    """Two-word phrases the posting repeats, such as 'model evaluation'."""
    words = [w.lower() for w in _WORD.findall(job_text)]
    pairs = Counter((a, b) for a, b in zip(words, words[1:]) if a not in _JOB_STOPWORDS and b not in _JOB_STOPWORDS)
    return [f"{a} {b}" for (a, b), count in pairs.most_common(40) if count >= 2]


def _terms_for_block(block, usable_skills, phrases):
    """Only job terms that connect to this line's own wording, so the model has nothing else to borrow."""
    own = {_stem(w) for w in _content_words(block["text"])}
    related = [p for p in phrases if any(_stem(w) in own for w in p.split())]
    skills_here = [s for s in usable_skills if any(_stem(w) in own for w in _content_words(s))]
    return (skills_here + related)[:6]


# ---- Skills ----

_ML_SKILLS = {"Machine Learning", "Deep Learning", "NLP", "Computer Vision", "LLMs", "PyTorch", "TensorFlow",
              "scikit-learn", "Pandas", "NumPy", "Statistics", "Data Analysis"}
_ML_LABEL = re.compile(r"machine learning|data science|\bai\b|\bml\b", re.IGNORECASE)


def _is_known_skill(phrase):
    if any(pattern.fullmatch(phrase) for pattern in _OFFICIAL_PATTERNS.values()):
        return True
    return any(pattern.fullmatch(phrase) for _, pattern in _SKILL_PATTERNS)


def _split_skill_line(line):
    """Separates 'Programming Languages Python, C++' into ('Programming Languages', ['Python', 'C++']).
    Returns (None, []) if the first item can't be recognized, and the line is then left as it is."""
    if "," not in line:
        return None, []
    if ":" in line:
        label, items = line.split(":", 1)
        return label.strip() + ":", [i.strip() for i in items.split(",") if i.strip()]
    first, rest = line.split(",", 1)
    words = first.split()
    for size in range(1, min(len(words), 4) + 1):
        candidate = " ".join(words[-size:])
        if _is_known_skill(candidate):
            items = [candidate] + [i.strip() for i in rest.split(",") if i.strip()]
            return " ".join(words[:-size]), items
    return None, []


def _official_form(item):
    for name, pattern in _OFFICIAL_PATTERNS.items():
        if pattern.fullmatch(item):
            return name
    return item


def _line_for_new_skill(skill, parsed, usable):
    if skill in _ML_SKILLS:
        for i in usable:
            if _ML_LABEL.search(parsed[i][1]):
                return i
    return usable[-1]


def tailor_skills(skill_blocks, job_skills, source):
    """Puts the job's skills first in each line and adds any the person has shown elsewhere in
    their resume or notes. A skill with no evidence is never added, and none are removed."""
    resume_skills = set(extract_skills(source))
    parsed = []
    for block in skill_blocks:
        label, items = _split_skill_line(block["text"])
        parsed.append((block, label, [_official_form(i) for i in items]))

    listed = set(extract_skills(" ".join(b["text"] for b in skill_blocks)))
    evidenced = [s for s in job_skills if s in resume_skills and s not in listed]
    usable = [i for i, (_, label, items) in enumerate(parsed) if label is not None and items]
    added = []
    for skill in evidenced:
        if usable:
            parsed[_line_for_new_skill(skill, parsed, usable)][2].append(skill)
            added.append(skill)

    changes = []
    for block, label, items in parsed:
        if label is None or not items:
            continue
        in_job = [i for i in items if set(extract_skills(i)) & set(job_skills)]
        ordered = in_job + [i for i in items if i not in in_job]
        new = f"{label} {', '.join(ordered)}".strip()
        block["label"] = label
        if new != block["text"]:
            changes.append({"section": "Skills", "before": block["text"], "after": new})
            block["text"] = new
    return changes, added


def tailor_blocks(blocks, job, notes):
    source = "\n".join((b.get("name") or "") + " " + b["text"] for b in blocks) + "\n" + notes
    job_skills = extract_skills(job["text"])
    resume_skills = set(extract_skills(source))
    usable = [s for s in job_skills if s in resume_skills]
    missing = [s for s in job_skills if s not in resume_skills]
    phrases = _job_phrases(job["text"])

    skill_blocks = [b for b in blocks if b["kind"] == "skills"]
    changes, added_skills = tailor_skills(skill_blocks, job_skills, source)
    kept, used_openers = [], set()
    for block in blocks:
        if block["kind"] != "rewrite":
            continue
        new, problems = rewrite_block(block, source, _terms_for_block(block, usable, phrases), used_openers)
        if new is None:
            kept.append({"text": block["text"], "reason": "; ".join(problems)})
            continue
        if block["section"] != "summary":
            used_openers.add(new.split()[0].lower().strip(",."))
        if new != block["text"]:
            changes.append({"section": block["section"].title(), "before": block["text"], "after": new})
            block["text"] = new
    needs_metric = [b["text"] for b in blocks if b["kind"] == "rewrite" and not _NUMBER.search(b["text"])]
    return {"changes": changes, "kept": kept, "added_skills": added_skills, "missing_skills": missing, "needs_metric": needs_metric}


# ---- PDF ----
# Plain single-column text in a standard font, which is what ATS software reads most reliably.

_FONT_SIZES = [10.5, 10.25, 10, 9.75, 9.5, 9.25, 9]
_MARGINS = [0.7, 0.6, 0.5]


def _clean(text):
    text = re.sub(r"[ \t]*[⋄◇][ \t]*", " | ", text)
    return re.sub(r"[●▪◦‣]", "•", text).replace("\t", " ")


class _DatedLine(Flowable):
    """Text on the left and dates on the right, written as one line so parsers read them together."""

    def __init__(self, left, right, font, size, width):
        super().__init__()
        self.left, self.right, self.font, self.size, self.width = left, right, font, size, width
        self.height = size * 1.25

    def wrap(self, *_):
        return self.width, self.height

    def draw(self):
        text = self.canv.beginText(0, self.size * 0.25)
        text.setFont(self.font, self.size)
        text.textOut(self.left)
        gap = self.width - stringWidth(self.left, self.font, self.size) - stringWidth(self.right, "Times-Roman", self.size)
        text.moveCursor(stringWidth(self.left, self.font, self.size) + gap, 0)
        text.setFont("Times-Roman", self.size)
        text.textOut(self.right)
        self.canv.drawText(text)


def _render(blocks, size, margin):
    buffer = io.BytesIO()
    margin_points = margin * inch
    doc = SimpleDocTemplate(buffer, pagesize=LETTER, leftMargin=margin_points, rightMargin=margin_points,
                            topMargin=margin_points * 0.8, bottomMargin=margin_points * 0.8, title="Resume")
    width = LETTER[0] - 2 * margin_points - 12  # the document frame pads each side by 6 points
    leading = size * 1.17
    body = ParagraphStyle("body", fontName="Times-Roman", fontSize=size, leading=leading, spaceAfter=1)
    bullet = ParagraphStyle("bullet", parent=body, leftIndent=10, firstLineIndent=-7, spaceAfter=1.5)
    centered = ParagraphStyle("contact", parent=body, alignment=TA_CENTER)
    name_style = ParagraphStyle("name", parent=centered, fontName="Times-Bold", fontSize=size + 6, leading=size + 9)
    heading = ParagraphStyle("heading", parent=body, fontName="Times-Bold", fontSize=size + 0.5, spaceBefore=5, spaceAfter=1)

    story = []
    first_header_line = True
    for block in blocks:
        text = block["text"]
        safe = escape(text)
        if block["kind"] == "heading":
            story.append(Paragraph(safe, heading))
            story.append(HRFlowable(width="100%", thickness=0.5, color="#000000", spaceAfter=2, spaceBefore=0))
        elif block["section"] == "header":
            story.append(Paragraph(safe, name_style if first_header_line else centered))
            first_header_line = False
        elif block["kind"] == "fixed":
            match = DATE_RANGE.search(text)
            left = (text[:match.start()] + text[match.end():]).strip(" ,|–—-") if match else ""
            font = "Times-Bold" if block["section"] in _REWRITE_SECTIONS else "Times-Roman"
            if match and left and stringWidth(left, font, size) + stringWidth(match.group(0), "Times-Roman", size) + 12 < width:
                story.append(_DatedLine(left, match.group(0), font, size, width))
            else:
                story.append(Paragraph(safe, body))
        elif block.get("name"):
            story.append(Paragraph(f"<b>{escape(block['name'])}</b> {safe}", body))
        elif block.get("label"):
            story.append(Paragraph(f"<b>{escape(block['label'])}</b>{escape(text[len(block['label']):])}", body))
        elif block.get("bullet"):
            # A plain hyphen: the font's bullet character can extract as a control character, which ATS parsers trip on.
            story.append(Paragraph(f"- {safe}", bullet))
        else:
            story.append(Paragraph(safe, body))
    doc.build(story)
    return buffer.getvalue()


def _page_count(pdf):
    return len(PdfReader(io.BytesIO(pdf)).pages)


def _render_one_page(blocks):
    for margin in _MARGINS:
        for size in _FONT_SIZES:
            pdf = _render(blocks, size, margin)
            if _page_count(pdf) == 1:
                return pdf
    return None


def render_to_one_page(blocks, job_skills):
    """Renders at the largest size that fits one page. If even the smallest size doesn't fit, removes
    the bullets least relevant to the job, always leaving each job at least one. Returns (pdf, removed)."""
    pdf = _render_one_page(blocks)
    removed = []
    blocks = list(blocks)
    while pdf is None:
        per_group = Counter(b["group"] for b in blocks if b["kind"] == "rewrite" and b.get("bullet"))
        candidates = [b for b in blocks if b["kind"] == "rewrite" and b.get("bullet") and per_group[b["group"]] > 1]
        if not candidates:
            raise TailorError("This resume is too long to fit on one page, even at the smallest readable size. Shorten it and try again.")
        # Least relevant first; among equals, cut from the job listed furthest down.
        victim = min(candidates, key=lambda b: (len(set(extract_skills(b["text"])) & set(job_skills)), -blocks.index(b)))
        blocks.remove(victim)
        removed.append(victim["text"])
        pdf = _render_one_page(blocks)
    return pdf, removed


def _unencodable_characters(blocks):
    found = set()
    for block in blocks:
        for char in block["text"]:
            try:
                char.encode("cp1252")
            except UnicodeEncodeError:
                found.add(char)
    return sorted(found)


def tailor_resume(resume_text, job, notes=""):
    """Returns the one-page PDF and a record of what changed."""
    blocks = parse_blocks(_clean(resume_text))
    unsupported = _unencodable_characters(blocks)
    if unsupported:
        raise TailorError(f"The resume contains characters the PDF font can't show: {' '.join(unsupported)}")
    if not any(b["kind"] == "rewrite" for b in blocks):
        raise TailorError("No experience or project descriptions were found to rewrite. Check that your resume uses standard section headings.")

    outcome = tailor_blocks(blocks, job, notes.strip())
    outcome["untouched_paragraphs"] = [b["text"] for b in blocks if b.get("paragraph")]
    pdf, removed = render_to_one_page(blocks, extract_skills(job["text"]))
    outcome.update({
        "pdf": pdf,
        "removed": removed,
        "text": "\n".join(page.extract_text() for page in PdfReader(io.BytesIO(pdf)).pages),
    })
    return outcome
