import re
import threading
from collections import Counter
from datetime import date
from difflib import SequenceMatcher, get_close_matches

from rag.matcher import DATE_RANGE, SELF_REPORTED, SKILLS, extract_skills, month_index, years_from_ranges

CRITICAL, WARNING, INFO = "critical", "warning", "info"

# ---- Resume structure ----

_HEADINGS = {
    "experience": ["experience", "work experience", "professional experience", "relevant experience",
                   "employment", "employment history", "work history", "career history"],
    "education": ["education", "academic background", "academic history", "education and training"],
    "skills": ["skills", "technical skills", "key skills", "core skills", "core competencies", "technologies"],
    "summary": ["summary", "professional summary", "career summary", "profile", "professional profile",
                "objective", "career objective", "about me"],
    "projects": ["projects", "academic projects", "personal projects", "selected projects"],
    "other": ["certifications", "certificates", "licenses", "publications", "awards", "honors", "languages",
              "interests", "activities", "volunteer experience", "volunteering", "references", "achievements"],
}
_HEADING_LOOKUP = {phrase: name for name, phrases in _HEADINGS.items() for phrase in phrases}

_BULLET = re.compile(r"^\s*[•●▪◦·*⋄‣–—-]\s*")
_TITLE_WORD = re.compile(
    r"\b(?:engineer|developer|programmer|manager|analyst|scientist|designer|architect|consultant|intern|"
    r"assistant|administrator|director|lead|specialist|coordinator|technician|officer|associate|researcher|"
    r"representative|barista|cashier|server|teacher|tutor|nurse|accountant|supervisor|recruiter|founder|"
    r"president|clerk|writer|editor|driver|attendant|salesperson|head of|vp)s?\b",
    re.IGNORECASE,
)
_TITLE_WORD_LIST = _TITLE_WORD.pattern.split("(?:", 1)[1].split(")s?", 1)[0].split("|")
_STRONG_SEPARATOR = re.compile(r"\s+[|–—-]\s+|\s+at\s+|\s*\t\s*|\s{2,}|\s+[|·⋄]\s*")
_COMPANY_SUFFIX = re.compile(r"^(?:inc|llc|ltd|llp|corp|co|gmbh|plc|pvt)\.?$", re.IGNORECASE)
_CITY_PREFIX = {"New", "San", "Los", "Las", "Saint", "St.", "Fort", "Salt", "El", "Santa"}
_SOFT_SKILLS = {"Leadership", "Communication", "Agile"}


def _heading_name(line):
    if len(line.split()) > 5:
        return None
    return _HEADING_LOOKUP.get(re.sub(r"[^a-z ]", "", line.lower()).strip())


def split_sections(text):
    sections = {"header": []}
    current = "header"
    for line in text.splitlines():
        name = _heading_name(line)
        if name:
            current = name
            sections.setdefault(name, [])
        else:
            sections[current].append(line)
    return sections


def _strip_location(piece):
    """'Acme Corp Raleigh, NC' -> 'Acme Corp'. PDFs flatten the gap between a company and
    its city, so the word before the last comma is assumed to be the city."""
    if "," not in piece:
        return piece
    before, after = piece.rsplit(",", 1)
    if _COMPANY_SUFFIX.match(after.strip()):
        return piece
    tokens = before.split()[:-1]
    if tokens and tokens[-1] in _CITY_PREFIX:
        tokens.pop()
    return " ".join(tokens).rstrip(" ,") or None


def _looks_like_header_line(line):
    stripped = line.strip()
    return bool(stripped) and not _BULLET.match(line) and len(stripped.split()) <= 10 \
        and not stripped.endswith(".") and not DATE_RANGE.search(stripped)


def _has_title_word(piece):
    if _TITLE_WORD.search(piece):
        return True
    # Catches a misspelt title such as "Software Enginer", so the typo can be reported rather than misread.
    return any(get_close_matches(word.lower(), _TITLE_WORD_LIST, n=1, cutoff=0.85) for word in re.findall(r"[A-Za-z]{5,}", piece))


def _classify_pieces(pieces):
    """Picks the job title and company candidates out of the text around a date range.
    Returns (title, separate pieces, weak guesses)."""
    title, companies, weak = None, [], []
    for piece in pieces:
        if not _has_title_word(piece):
            companies.append(piece)
        elif title is None:
            # "Software Engineer, Acme Corp": the part after the comma might be the company.
            head, _, tail = piece.partition(",")
            title = head.strip()
            if tail.strip():
                weak.append(tail.strip())
    return title, companies, weak


def parse_entries(lines):
    """Finds job entries in the experience section: any short, non-bullet line holding a date range,
    with its title and company taken from that line and its neighbours."""
    now = date.today().year * 12 + date.today().month - 1
    found = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        m = DATE_RANGE.search(stripped)
        if not m or _BULLET.match(line) or len(stripped.split()) > 14:
            continue
        rest = (stripped[:m.start()] + "  " + stripped[m.end():]).strip(" ,|–—-·\t:()")
        pieces = [p.strip(" ,|–—-·:()") for p in _STRONG_SEPARATOR.split(rest) if p.strip(" ,|–—-·:()")]

        body_start, first_line = i + 1, i
        title, companies, weak = _classify_pieces(pieces)
        while body_start < min(i + 3, len(lines)) and (title is None or not companies) \
                and _looks_like_header_line(lines[body_start]):
            pieces.append(lines[body_start].strip())
            title, companies, weak = _classify_pieces(pieces)
            body_start += 1
        if title is None and i > 0 and _looks_like_header_line(lines[i - 1]):
            title, companies, weak = _classify_pieces([lines[i - 1].strip()] + pieces)
            first_line = i - 1

        company = next((c for c in map(_strip_location, companies + weak) if c), None)
        year_only_end = not m.group("present") and not (m.group("em") or m.group("en"))
        found.append({
            "title": title, "company": company, "dates": m.group(0),
            "start": month_index(m, "s", 1),
            "end": now if m.group("present") else month_index(m, "e", 12),
            "is_current": bool(m.group("present")),
            "start_year": int(m.group("sy")),
            "end_year": None if m.group("present") else int(m.group("ey")),
            "year_only_end": year_only_end,
            "match": m, "first_line": first_line, "body_start": body_start,
        })

    for k, entry in enumerate(found):
        stop = found[k + 1]["first_line"] if k + 1 < len(found) else len(lines)
        entry["body"] = lines[entry["body_start"]:stop]
        entry["words"] = sum(len(_BULLET.sub("", l).split()) for l in entry["body"])
    return found


def _describe(entry):
    who = " at ".join(p for p in (entry["title"], entry["company"]) if p)
    return f"{who} ({entry['dates']})" if who else entry["dates"]


# ---- Contact and format ----

_PHONE = re.compile(r"\+?\d[\d ().-]{8,18}\d")
_ONLY_YEARS = re.compile(r"(?:(?:19|20)\d{2}[ ().-]*)+")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def _has_phone(text):
    return any(
        10 <= sum(c.isdigit() for c in m.group(0)) <= 15 and not _ONLY_YEARS.fullmatch(m.group(0))
        for m in _PHONE.finditer(text)
    )


def check_contact_and_format(text, sections, meta):
    findings = []
    if not _has_phone(text):
        findings.append({"severity": CRITICAL, "message": "No phone number found.",
                         "suggestion": "Add one near your name so recruiters can reach you."})
    if not _EMAIL.search(text):
        findings.append({"severity": CRITICAL, "message": "No email address found.",
                         "suggestion": "Add one near your name so recruiters can reach you."})
    if "linkedin.com" not in text.lower():
        findings.append({"severity": INFO, "message": "No LinkedIn profile link found."})

    headings = {"experience": (CRITICAL, "Experience"), "education": (WARNING, "Education"), "skills": (WARNING, "Skills")}
    for key, (severity, label) in headings.items():
        if key not in sections:
            findings.append({"severity": severity, "message": f'No "{label}" section heading found.',
                             "suggestion": f'ATS software looks for standard headings. Use "{label}" as a heading on its own line.'})

    if meta.get("tables"):
        findings.append({"severity": WARNING, "message": f"The document uses {meta['tables']} table(s).",
                         "suggestion": "Many ATS parsers read tables out of order. Use plain single-column text."})
    if meta.get("text_boxes"):
        findings.append({"severity": WARNING, "message": f"The document uses {meta['text_boxes']} text box(es).",
                         "suggestion": "Many ATS parsers skip text boxes. Move that text into the document body."})
    header_text = meta.get("header_footer_text", "")
    body_without_header = text.replace(header_text, "") if header_text else text
    if header_text and ((_has_phone(header_text) and not _has_phone(body_without_header))
                        or (_EMAIL.search(header_text) and not _EMAIL.search(body_without_header))):
        findings.append({"severity": WARNING, "message": "Your contact details are only in the page header or footer.",
                         "suggestion": "Some ATS parsers skip headers and footers. Move them into the document body."})
    if meta.get("images"):
        findings.append({"severity": INFO, "message": f"The document contains {meta['images']} image(s).",
                         "suggestion": "ATS software can't read text inside images, so keep key details out of them."})
    if meta.get("pages", 0) > 2:
        findings.append({"severity": INFO, "message": f"The resume is {meta['pages']} pages long.",
                         "suggestion": "One or two pages is the usual expectation."})
    return findings


# ---- Spelling and grammar ----

# Rules that mostly fire on normal resume layout rather than on real mistakes.
_IGNORED_RULES = {
    "DASH_RULE", "WHITESPACE_RULE", "UPPERCASE_SENTENCE_START", "PUNCTUATION_PARAGRAPH_END",
    "EN_QUOTES", "MULTIPLICATION_SIGN", "CONSECUTIVE_SPACES", "ENGLISH_WORD_REPEAT_BEGINNING_RULE", "SENT_START_CONJUNCTIVE_LINKING_ADVERB_COMMA",
}
_REPORTED_CATEGORIES = {"GRAMMAR", "PUNCTUATION", "TYPOGRAPHY", "CONFUSED_WORDS", "MISC", "NONSTANDARD_PHRASES"}
_MAX_CHECK_CHARS = 50000

# Correct spellings of tools the dictionary doesn't know. Each maps to a pattern for finding its variants.
_OFFICIAL_NAMES = {
    "JavaScript": r"java\s?script", "TypeScript": r"type\s?script", "PyTorch": r"py\s?torch",
    "TensorFlow": r"tensor\s?flow", "Keras": r"keras", "MySQL": r"my\s?sql", "PostgreSQL": r"postgre\s?sql",
    "MongoDB": r"mongo\s?db", "GitHub": r"git\s?hub", "GitLab": r"git\s?lab", "NumPy": r"num\s?py",
    "Kubernetes": r"kubernetes", "GraphQL": r"graph\s?ql", "Node.js": r"node\.?js", "FastAPI": r"fast\s?api",
    "Hugging Face": r"hugging\s?face", "scikit-learn": r"scikit[\s-]?learn", "AdaBoost": r"ada\s?boost",
    "FAISS": r"faiss", "Python": r"python", "SQL": r"sql", "HTML": r"html", "AWS": r"aws", "Linux": r"linux",
}
_OFFICIAL_PATTERNS = {name: re.compile(rf"(?<![\w.-]){p}(?![\w-])", re.IGNORECASE) for name, p in _OFFICIAL_NAMES.items()}
_EXTRA_KNOWN_WORDS = {"scikit", "sklearn", "huggingface", "adaboost", "xgboost", "gemma", "llama", "langchain", "chatbot",
                      "dockerfile", "backend", "frontend", "fullstack", "api", "apis", "webapp", "dataset", "datasets",
                      "microservice", "microservices", "kubernetes", "pyspark", "matplotlib", "seaborn", "opencv"}
_KNOWN_WORDS = _EXTRA_KNOWN_WORDS | {w.lower() for aliases in SKILLS.values() for a in aliases for w in a.split()} \
    | {w.lower() for name in _OFFICIAL_NAMES for w in name.split()}

_language_tool = None
_language_tool_lock = threading.Lock()


def _check_language(text):
    """Runs LanguageTool on this machine (never its public API, since resumes are personal data).
    It starts a Java server on first use and keeps it running for later scans."""
    global _language_tool
    import language_tool_python
    with _language_tool_lock:
        if _language_tool is None:
            _language_tool = language_tool_python.LanguageTool("en-US")
        try:
            return _language_tool.check(text)
        except Exception:
            _language_tool = None  # start a fresh server on the next scan in case this one died
            raise


def _is_likely_typo(word, replacements, known_words):
    """Unknown words on resumes are usually names and tools, so only report a word
    when the dictionary has a close suggestion for it."""
    if any(ch.isdigit() for ch in word) or word.isupper() or re.search(r"[a-z][A-Z]", word):
        return False
    if word.lower() in known_words or not replacements:
        return False
    # A top suggestion of "Sci kit" or "Gemma" for "scikit" or "gemma" means the word is fine, just unfamiliar.
    if replacements[0].lower().replace(" ", "") == word.lower():
        return False
    return any(
        SequenceMatcher(None, word.lower(), r.lower()).ratio() >= 0.75 or sorted(word.lower()) == sorted(r.lower())
        for r in replacements[:3]
    )


def _snippet(text, offset, length):
    return re.sub(r"\s+", " ", text[max(0, offset - 40):offset + length + 40]).strip()


def check_language(text, organisations):
    """Returns (spelling findings, grammar findings), or raises if LanguageTool can't run.
    Words from employer and school names are skipped, since the dictionary won't know them."""
    spelling, grammar, seen = [], [], set()
    known_words = _KNOWN_WORDS | {w.lower() for org in organisations for w in org.split()}
    for m in _check_language(text[:_MAX_CHECK_CHARS]):
        word = text[m.offset:m.offset + m.error_length]
        if m.rule_id in _IGNORED_RULES or (m.rule_id, word.lower()) in seen:
            continue
        seen.add((m.rule_id, word.lower()))
        if m.rule_id.startswith("MORFOLOGIK") or m.category == "TYPOS":
            if _is_likely_typo(word, m.replacements, known_words):
                spelling.append({"severity": WARNING, "message": f'Possible spelling mistake: "{word}"',
                                 "suggestion": f"Did you mean: {', '.join(r for r in m.replacements[:3] if ' ' not in r)}?",
                                 "snippet": _snippet(text, m.offset, m.error_length)})
        elif m.category in _REPORTED_CATEGORIES:
            severity = INFO if m.category == "TYPOGRAPHY" else WARNING
            suggestion = f"Suggested: {', '.join(m.replacements[:3])}" if m.replacements and severity != INFO else None
            grammar.append({"severity": severity, "message": m.message, "suggestion": suggestion,
                            "snippet": _snippet(text, m.offset, m.error_length)})
    return spelling, grammar


_BASE_VERBS = ("create|develop|build|manage|design|implement|lead|analyze|analyse|maintain|write|test|deploy|improve|"
               "coordinate|collaborate|work|support|optimize|optimise|reduce|increase|present|perform|conduct|"
               "train|mentor|automate|integrate|deliver|research|prepare|monitor|track|review|ensure|drive|launch")
_PAST_THEN_BASE = re.compile(rf"\b[A-Za-z]+ed\b[^.,;]*?\band\s+({_BASE_VERBS})\b(?!\s+(?:of|for|in)\b)", re.IGNORECASE)
_BULLET_OPENER = re.compile(rf"^(?:({_BASE_VERBS})|([A-Z][a-z]+ing))\b", re.IGNORECASE)
_NON_VERB_ING = {"Engineering", "Marketing", "Training", "Building"}


def check_tense(entries):
    """Finished jobs should be described in the past tense; LanguageTool can't know a job has ended."""
    findings = []
    for entry in entries:
        if entry["is_current"]:
            continue
        for line in entry["body"]:
            if not _BULLET.match(line):
                continue
            bullet = _BULLET.sub("", line).strip()
            opener = _BULLET_OPENER.match(bullet)
            if opener and opener.group(0) not in _NON_VERB_ING:
                findings.append({"severity": WARNING, "message": f'"{opener.group(0)}" isn\'t past tense, but this job has ended.',
                                 "suggestion": "Start bullets for past jobs with a past-tense verb.", "snippet": bullet[:90]})
            mixed = _PAST_THEN_BASE.search(bullet)
            # "Built a tool to analyze X and track Y" is a correct infinitive, not a tense change.
            if mixed and not re.search(r"\bto\b", mixed.group(0), re.IGNORECASE):
                findings.append({"severity": WARNING, "message": f'Tense changes mid-sentence at "and {mixed.group(1)}".',
                                 "suggestion": "Keep both verbs in the past tense.", "snippet": bullet[:90]})
    return findings


# ---- Dates ----

def _date_style(match, prefix):
    month = match.group(f"{prefix}m")
    if month:
        if month.lower() == "may":
            return None  # "May" is both the short and the long form
        return "Mon YYYY" if len(month) <= 4 else "Month YYYY"
    return "MM/YYYY" if match.group(f"{prefix}n") else "YYYY"


def _education_spans(lines):
    spans = []
    for m in DATE_RANGE.finditer("\n".join(lines)):
        today = date.today()
        end = today.year * 12 + today.month - 1 if m.group("present") else month_index(m, "e", 12)
        spans.append((month_index(m, "s", 1), end))
    return sorted(spans)


def _covered(gap_start, gap_end, spans):
    """Whether merged spans cover the whole gap."""
    reach = gap_start
    for start, end in spans:
        if start <= reach + 1:
            reach = max(reach, end)
    return reach + 1 >= gap_end


def check_dates(entries, sections, text):
    findings = []
    today = date.today()
    now = today.year * 12 + today.month - 1

    for e in entries:
        if e["start"] > e["end"]:
            findings.append({"severity": CRITICAL, "message": f"End date is before the start date: {_describe(e)}."})
        future_end = e["end_year"] and (e["end_year"] > today.year or (not e["year_only_end"] and e["end"] > now))
        if e["start"] > now or future_end:
            findings.append({"severity": CRITICAL, "message": f"This job has a date in the future: {_describe(e)}."})

    styles = Counter(s for e in entries for s in (_date_style(e["match"], "s"), None if e["is_current"] else _date_style(e["match"], "e")) if s)
    if len(styles) > 1:
        findings.append({"severity": WARNING, "message": f"Job dates use mixed formats: {', '.join(styles)}.",
                         "suggestion": "Use one format, such as Jan 2024, for every job."})
    elif "YYYY" in styles:
        findings.append({"severity": INFO, "message": "Job dates show years only.",
                         "suggestion": "Include months so your time in each job is clear, such as Jan 2024."})

    valid = [e for e in entries if e["start"] <= e["end"]]
    starts = [e["start"] for e in valid]
    if starts != sorted(starts, reverse=True):
        findings.append({"severity": WARNING, "message": "Jobs aren't listed newest first.",
                         "suggestion": "List your most recent job at the top of the experience section."})

    ordered = sorted(valid, key=lambda e: e["start"])
    education = _education_spans(sections.get("education", []))
    for earlier, later in zip(ordered, ordered[1:]):
        overlap = earlier["end"] - later["start"]
        if overlap >= 2:
            findings.append({"severity": INFO, "message": f"These dates overlap by {overlap} months: {_describe(earlier)} and {_describe(later)}.",
                             "suggestion": "That's fine if you held both jobs at once. Otherwise, correct the dates."})
        gap = later["start"] - earlier["end"]
        if gap > 6 and not _covered(earlier["end"], later["start"], education):
            findings.append({"severity": INFO, "message": f"There is a {gap}-month gap between {_describe(earlier)} and {_describe(later)}.",
                             "suggestion": "Recruiters may ask about it, so be ready to explain it."})
    if ordered:
        latest_end = max(e["end"] for e in ordered)
        idle = now - latest_end
        if idle > 6 and not _covered(latest_end, now, education):
            findings.append({"severity": INFO, "message": f"Your most recent job ended {idle} months ago and no job is marked as current.",
                             "suggestion": "If you're still working there, write Present as the end date."})

    stated = [int(m.group(1)) for m in SELF_REPORTED.finditer(text) if int(m.group(1)) <= 40]
    computed = years_from_ranges("\n".join(sections.get("experience", [])))
    if stated and computed is not None and abs(max(stated) - computed) >= 2:
        findings.append({"severity": WARNING, "message": f"Your resume says {max(stated)} years of experience, but the job dates add up to about {computed}.",
                         "suggestion": "Make sure the two agree, or explain any earlier jobs you left out."})
    return findings


# ---- Job titles and company names ----

_URL = re.compile(r"(?:https?://|www\.)\S+|\S+@\S+|\b[\w-]+\.(?:com|org|net|io)\S*")
_WORD_SUFFIX = re.compile(r"(?:ing|ed|er|es|s|d|r|ion|ment|al)$")
_SCHOOL = re.compile(r"((?:[A-Z][\w&'-]*\s+){0,5}(?:University|Institute|College|School)(?:\s+of(?:\s+[A-Z][\w&'-]*)+)?)")
_SUMMARY_TITLE = re.compile(
    r"\b((?:[A-Z][\w+#.-]*\s+){1,3}(?:Engineer|Developer|Programmer|Manager|Analyst|Scientist|Designer|Architect|Consultant|Researcher))\b"
)


def _same_word_form(a, b):
    return _WORD_SUFFIX.sub("", a.lower()) == _WORD_SUFFIX.sub("", b.lower())


def _windows(line, size):
    tokens = re.findall(r"[\w&.'+#-]+", line)
    for i in range(len(tokens) - size + 1):
        yield " ".join(t.strip(".'") for t in tokens[i:i + size])


def _is_misspelt_variant(a, b):
    if a.lower() == b.lower() or SequenceMatcher(None, a.lower(), b.lower()).ratio() < 0.88:
        return False
    a_tokens, b_tokens = a.split(), b.split()
    differing = [(x, y) for x, y in zip(a_tokens, b_tokens) if x.lower() != y.lower()]
    return len(a_tokens) == len(b_tokens) and not all(_same_word_form(x, y) for x, y in differing)


def _organisations(entries, sections):
    organisations = {e["company"] for e in entries if e["company"]}
    for line in sections.get("education", []):
        organisations.update(m.group(1).strip() for m in _SCHOOL.finditer(line))
    return organisations


def check_names(entries, sections, text):
    findings, seen = [], set()
    text = _URL.sub(" ", text)  # "github.com/me" isn't a misspelling of GitHub
    lines = [l for l in text.splitlines() if l.strip()]

    def add(key, message, suggestion, severity=WARNING):
        if frozenset(key) not in seen:
            seen.add(frozenset(key))
            findings.append({"severity": severity, "message": message, "suggestion": suggestion})

    for org in _organisations(entries, sections):
        size = len(org.split())
        if len(org) < 6:
            continue
        for line in lines:
            for window in _windows(line, size):
                if window == org:
                    continue
                if window.lower() == org.lower():
                    if size > 1 or window[0].isupper():
                        add((org, window), f'"{org}" is also written as "{window}".', "Use the same capitalization everywhere.")
                elif window[0].isupper() and _is_misspelt_variant(org, window):
                    add((org, window), f'"{org}" is also written as "{window}".', "One of these may be a typo. Use the correct name everywhere.")
        if size >= 3:
            short = " ".join(org.split()[:-1])
            if re.search(rf"\b{re.escape(short)}\b(?!\s+{re.escape(org.split()[-1])})", text):
                add((org, short), f'"{org}" is also written as "{short}".', "If they're the same organization, use one name everywhere.", INFO)

    titles = sorted({e["title"] for e in entries if e["title"]})
    for i, a in enumerate(titles):
        for b in titles[i + 1:]:
            if a.lower() == b.lower():
                add((a, b), f'The job title "{a}" is also written as "{b}".', "Use the same capitalization for both.")
            elif _is_misspelt_variant(a, b):
                add((a, b), f'The job title "{a}" looks similar to "{b}".', "One of these may be a typo.")

    # A title the summary claims that no job entry backs up, e.g. "Senior Engineer" vs "Engineer".
    intro = " ".join(sections.get("summary", []) + sections["header"])
    entry_titles = {t.lower() for t in titles}
    recent = max((e for e in entries if e["title"]), key=lambda e: e["end"], default=None)
    for m in _SUMMARY_TITLE.finditer(intro):
        claimed = m.group(1)
        if recent and claimed.lower() not in entry_titles and set(claimed.lower().split()) & set(recent["title"].lower().split()):
            add((claimed, recent["title"]), f'Your summary or headline says "{claimed}", but your latest job title is "{recent["title"]}".',
                "Make sure these agree. ATS software and recruiters compare them.")

    for name, pattern in _OFFICIAL_PATTERNS.items():
        forms = Counter()
        for m in pattern.finditer(text):
            form = m.group(0)
            before = text[max(0, m.start() - 2):m.start()]
            at_sentence_start = m.start() == 0 or before.endswith(("\n", ". ", "•"))
            if at_sentence_start and form == form.capitalize() and form.lower() == name.lower():
                continue
            forms[form] += 1
        variants = [f for f in forms if f != name]
        if len(forms) > 1 and variants:
            add((name, "variants"), f'"{name}" is written in {len(forms)} different ways: {", ".join(forms)}.', f'Use "{name}" everywhere.')
        elif variants:
            add((name, "variants"), f'"{variants[0]}" is usually written "{name}".', f'Use "{name}".', INFO)
    return findings


# ---- Experience balance ----

OLD_JOB_YEARS = 10
DOMINANCE_RATIO = 1.25
MIN_WORDS_TO_DOMINATE = 30


def _meaningful_skills(text):
    return set(extract_skills(text)) - _SOFT_SKILLS


def check_balance(entries, sections):
    """Flags older or unrelated jobs that take up more of the resume than the current one."""
    if not entries:
        return [], []
    now = date.today().year * 12 + date.today().month - 1
    ordered = sorted(entries, key=lambda e: (e["is_current"], min(e["end"], now), e["start"]), reverse=True)
    latest = ordered[0]
    latest_label = "current" if latest["is_current"] else "most recent"
    total = sum(e["words"] for e in entries) or 1

    # What this resume is aiming at: the latest job plus the skills it lists up front.
    target_skills = _meaningful_skills(" ".join(sections.get("skills", []) + latest["body"] + [latest["title"] or ""]))
    target_title = set(re.findall(r"[a-z+#]+", (latest["title"] or "").lower())) - {"senior", "junior", "lead", "intern", "of", "and"}

    findings, breakdown = [], []
    for e in ordered:
        own_skills = _meaningful_skills(" ".join(e["body"] + [e["title"] or ""]))
        own_title = set(re.findall(r"[a-z+#]+", (e["title"] or "").lower()))
        is_latest = e is latest
        if is_latest:
            related = True
        elif not target_skills and not target_title:
            related = None
        else:
            related = bool(own_skills & target_skills or own_title & target_title)
        years_ago = (now - e["end"]) / 12
        breakdown.append({
            "title": e["title"], "company": e["company"], "dates": e["dates"], "words": e["words"],
            "share": round(100 * e["words"] / total), "is_latest": is_latest, "is_current": e["is_current"], "related": related,
        })
        if is_latest:
            continue
        dominates = e["words"] >= MIN_WORDS_TO_DOMINATE and e["words"] > latest["words"] * DOMINANCE_RATIO
        if dominates and related is False:
            findings.append({"severity": WARNING, "message": f"{_describe(e)} looks unrelated to your {latest_label} job but takes up more space ({e['words']} vs {latest['words']} words).",
                             "suggestion": "Shorten it, and put more detail into your latest job."})
        elif dominates:
            findings.append({"severity": WARNING, "message": f"{_describe(e)} is older but takes up more space than your {latest_label} job ({e['words']} vs {latest['words']} words).",
                             "suggestion": "Shorten it, and put more detail into your latest job."})
        elif years_ago >= OLD_JOB_YEARS and e["words"] >= MIN_WORDS_TO_DOMINATE:
            findings.append({"severity": INFO, "message": f"{_describe(e)} ended over {OLD_JOB_YEARS} years ago but still has {e['words']} words.",
                             "suggestion": "Consider cutting it down to a line or two."})
    return findings, breakdown


# ---- Report ----

_SEVERITY_ORDER = {CRITICAL: 0, WARNING: 1, INFO: 2}


def _section(section_id, title, findings=None, status=None, note=None):
    findings = sorted(findings or [], key=lambda f: _SEVERITY_ORDER[f["severity"]])
    return {"id": section_id, "title": title, "status": status or ("issues" if findings else "ok"), "note": note, "findings": findings}


def scan_resume(resume):
    """Builds the ATS report for the output of retriever.read_resume_upload."""
    text, meta = resume["text"], resume["meta"]

    if len(text.strip()) < 50:
        unread = "Not checked, because no text could be read from this file."
        report_sections = [
            _section("format", "Contact and format", [{
                "severity": CRITICAL, "message": "No readable text found in this file.",
                "suggestion": "It may be a scanned image, which ATS software can't read. Export a text-based PDF or Word file.",
            }]),
            *[_section(i, t, status="skipped", note=unread) for i, t in (
                ("spelling", "Spelling and typos"), ("grammar", "Grammar and tense"), ("dates", "Date consistency"),
                ("names", "Job titles, company and tool names"), ("balance", "Experience balance"))],
        ]
        return {"summary": {CRITICAL: 1, WARNING: 0, INFO: 0}, "sections": report_sections, "experience_breakdown": []}

    sections = split_sections(text)
    entries = parse_entries(sections.get("experience", []))
    no_entries = "Not checked, because no job entries with date ranges (such as Jan 2022 - Mar 2024) were found under an experience heading."

    # The name and contact block at the top isn't prose, and names would read as typos.
    body = "\n".join(line for name, lines in sections.items() if name != "header" for line in lines)
    tense = check_tense(entries)
    try:
        spelling, grammar = check_language(body, _organisations(entries, sections))
        spelling_section = _section("spelling", "Spelling and typos", spelling)
        grammar_section = _section("grammar", "Grammar and tense", grammar + tense)
    except Exception:
        unavailable = "Not checked, because the LanguageTool spelling and grammar checker couldn't start. It needs Java 17 or newer on the server."
        spelling_section = _section("spelling", "Spelling and typos", status="unavailable", note=unavailable)
        grammar_section = _section("grammar", "Grammar and tense", tense, status="unavailable", note=unavailable)

    names = check_names(entries, sections, text)
    no_dates = [{"severity": WARNING, "message": "No job dates could be read in your experience section.",
                 "suggestion": "Give each job a date range on its title line, such as Jan 2022 - Mar 2024."}]
    balance, breakdown = check_balance(entries, sections)
    report_sections = [
        _section("format", "Contact and format", check_contact_and_format(text, sections, meta)),
        spelling_section,
        grammar_section,
        _section("dates", "Date consistency", check_dates(entries, sections, text)) if entries
        else _section("dates", "Date consistency", no_dates if "experience" in sections else None,
                      status="issues" if "experience" in sections else "skipped", note=no_entries),
        _section("names", "Job titles, company and tool names", names,
                 status=None if entries or names else "skipped",
                 note=None if entries else "Job titles and company names weren't compared, because no job entries were found. Only tool names were checked."),
        _section("balance", "Experience balance", balance) if entries
        else _section("balance", "Experience balance", status="skipped", note=no_entries),
    ]
    summary = Counter(f["severity"] for s in report_sections for f in s["findings"])
    return {
        "summary": {level: summary[level] for level in (CRITICAL, WARNING, INFO)},
        "sections": report_sections,
        "experience_breakdown": breakdown,
    }
