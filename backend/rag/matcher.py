import html
import ipaddress
import json
import re
import socket
from datetime import date
from urllib.parse import urljoin, urlparse

import requests
from lxml import html as lxml_html

# ---- Skill vocabulary ----
# Canonical skill name -> aliases. Aliases are matched case-insensitively on word
# boundaries, except those listed in CASE_SENSITIVE (short words that are also
# common English, e.g. "Go").
SKILLS = {
    "Python": ["python"],
    "Java": ["java"],
    "JavaScript": ["javascript", "js", "ecmascript", "es6"],
    "TypeScript": ["typescript", "ts"],
    "C++": ["c++", "cpp"],
    "C#": ["c#", "csharp"],
    "C": ["C"],
    "Go": ["Go", "golang"],
    "Rust": ["rust"],
    "Ruby": ["ruby"],
    "PHP": ["php"],
    "Kotlin": ["kotlin"],
    "Swift": ["swift"],
    "Scala": ["scala"],
    "R": ["R"],
    "Solidity": ["solidity"],
    "Bash": ["bash", "shell scripting", "shell script"],
    "SQL": ["sql"],
    "HTML": ["html", "html5"],
    "CSS": ["css", "css3", "sass", "scss"],
    "React": ["react", "react.js", "reactjs"],
    "React Native": ["react native"],
    "Angular": ["angular", "angularjs"],
    "Vue": ["vue", "vue.js", "vuejs"],
    "Next.js": ["next.js", "nextjs"],
    "Redux": ["redux"],
    "Node.js": ["node.js", "nodejs", "node"],
    "Express": ["express", "express.js", "expressjs"],
    "Django": ["django"],
    "Flask": ["flask"],
    "FastAPI": ["fastapi"],
    "Spring Boot": ["spring boot", "springboot", "spring"],
    "Ruby on Rails": ["ruby on rails", "rails"],
    ".NET": [".net", "dotnet", "asp.net"],
    "GraphQL": ["graphql"],
    "REST APIs": ["rest", "restful", "rest api", "rest apis"],
    "gRPC": ["grpc"],
    "Microservices": ["microservices", "microservice"],
    "PostgreSQL": ["postgresql", "postgres"],
    "MySQL": ["mysql"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "Elasticsearch": ["elasticsearch", "elastic search"],
    "DynamoDB": ["dynamodb"],
    "Cassandra": ["cassandra"],
    "Snowflake": ["snowflake"],
    "Kafka": ["kafka"],
    "RabbitMQ": ["rabbitmq"],
    "Spark": ["spark", "pyspark", "apache spark"],
    "Hadoop": ["hadoop"],
    "Airflow": ["airflow"],
    "dbt": ["dbt"],
    "Databricks": ["databricks"],
    "AWS": ["aws", "amazon web services"],
    "Azure": ["azure"],
    "GCP": ["gcp", "google cloud"],
    "Docker": ["docker"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Terraform": ["terraform"],
    "Ansible": ["ansible"],
    "Jenkins": ["jenkins"],
    "GitHub Actions": ["github actions"],
    "CI/CD": ["ci/cd", "ci / cd", "continuous integration", "continuous delivery", "continuous deployment"],
    "Git": ["git"],
    "Linux": ["linux", "unix"],
    "Prometheus": ["prometheus"],
    "Grafana": ["grafana"],
    "Machine Learning": ["machine learning", "ml"],
    "Deep Learning": ["deep learning"],
    "NLP": ["nlp", "natural language processing"],
    "Computer Vision": ["computer vision"],
    "LLMs": ["llm", "llms", "large language models", "large language model", "generative ai", "genai"],
    "PyTorch": ["pytorch"],
    "TensorFlow": ["tensorflow"],
    "scikit-learn": ["scikit-learn", "sklearn"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Statistics": ["statistics", "statistical"],
    "Data Analysis": ["data analysis", "data analytics"],
    "Tableau": ["tableau"],
    "Power BI": ["power bi", "powerbi"],
    "Excel": ["excel"],
    "Selenium": ["selenium"],
    "Cypress": ["cypress"],
    "Jest": ["jest"],
    "Unit Testing": ["unit testing", "unit tests", "test automation", "automated testing"],
    "Figma": ["figma"],
    "UI/UX": ["ui/ux", "ux design", "ui design", "user experience"],
    "Agile": ["agile", "scrum", "kanban"],
    "System Design": ["system design", "distributed systems", "scalable systems"],
    "Data Structures & Algorithms": ["data structures", "algorithms"],
    "OOP": ["object-oriented", "object oriented", "oop"],
    "Security": ["cybersecurity", "application security", "network security", "owasp"],
    "Embedded Systems": ["embedded systems", "embedded", "rtos", "firmware"],
    "Android": ["android"],
    "iOS": ["ios"],
    "Leadership": ["leadership", "mentoring", "mentorship", "people management"],
    "Communication": ["communication skills", "excellent communication", "written and verbal"],
}

CASE_SENSITIVE = {"C", "Go", "R"}

# Characters that make up a token in skill names (so "Java" doesn't match inside "JavaScript"
# and "C" doesn't match inside "C++").
_TOKEN_CHARS = r"A-Za-z0-9+#"


def _compile_skill_patterns():
    patterns = []
    for skill, aliases in SKILLS.items():
        for alias in aliases:
            flags = 0 if alias in CASE_SENSITIVE else re.IGNORECASE
            body = re.escape(alias).replace(r"\ ", r"\s+")
            pattern = re.compile(rf"(?<![{_TOKEN_CHARS}.]){body}(?![{_TOKEN_CHARS}])", flags)
            patterns.append((skill, pattern))
    return patterns


_SKILL_PATTERNS = _compile_skill_patterns()


def extract_skills(text):
    found = []
    for skill, pattern in _SKILL_PATTERNS:
        if skill not in found and pattern.search(text):
            found.append(skill)
    return found


# ---- Experience ----

_NUM = r"(\d{1,2})(?:\.\d)?"
_YEARS_REQUIRED = re.compile(
    rf"{_NUM}\s*\+?\s*(?:(?:-|–|to)\s*{_NUM}\s*\+?\s*)?(?:years?|yrs?)\b[^.\n]{{0,60}}?experience"
    rf"|experience[^.\n]{{0,40}}?\b{_NUM}\s*\+?\s*(?:(?:-|–|to)\s*{_NUM}\s*\+?\s*)?(?:years?|yrs?)\b",
    re.IGNORECASE,
)


def extract_required_years(text):
    """Minimum years of experience a job asks for. When several are mentioned
    (e.g. '5+ years Python, 2+ years AWS'), the largest minimum is used."""
    mins = []
    for m in _YEARS_REQUIRED.finditer(text):
        low = m.group(1) or m.group(3)
        if low and 0 < int(low) <= 30:
            mins.append(int(low))
    return max(mins) if mins else None


_MONTHS = {
    m: i + 1
    for i, names in enumerate([
        ("jan", "january"), ("feb", "february"), ("mar", "march"), ("apr", "april"),
        ("may",), ("jun", "june"), ("jul", "july"), ("aug", "august"),
        ("sep", "sept", "september"), ("oct", "october"), ("nov", "november"), ("dec", "december"),
    ])
    for m in names
}
_MONTH_RE = r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|sept?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
def _date_point(p):
    # "Jan 2020", "January, 2020", "01/2020" or just "2020"; groups named <p>m, <p>n, <p>y
    return rf"(?:(?P<{p}m>{_MONTH_RE})\.?\s*,?\s*|(?P<{p}n>\d{{1,2}})\s*/\s*)?(?P<{p}y>(?:19|20)\d{{2}})"


DATE_RANGE = re.compile(
    _date_point("s")
    + r"\s*(?:-|–|—|to|until)\s*"
    + rf"(?:(?P<present>present|current|now|today|date)|{_date_point('e')})",
    re.IGNORECASE,
)
SELF_REPORTED = re.compile(r"(\d{1,2})(?:\.\d)?\s*\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional\s+|industry\s+|work\s+|hands-on\s+)?experience", re.IGNORECASE)
EDUCATION_WORDS = re.compile(
    r"\b(?:university|college|institute|school|b\.?\s?tech|b\.?\s?e\b|b\.?s\.?c?|m\.?s\.?c?|m\.?\s?tech|bachelor|master|ph\.?d|degree|gpa|cgpa)\b",
    re.IGNORECASE,
)


def month_index(match, prefix, default_month):
    year = int(match.group(f"{prefix}y"))
    if match.group(f"{prefix}m"):
        month = _MONTHS[match.group(f"{prefix}m").lower()]
    elif match.group(f"{prefix}n") and 1 <= int(match.group(f"{prefix}n")) <= 12:
        month = int(match.group(f"{prefix}n"))
    else:
        month = default_month
    return year * 12 + (month - 1)


def years_from_ranges(text):
    """Adds up employment date ranges, skipping ones that look like education and
    merging overlaps so concurrent roles aren't double counted. None if no ranges."""
    today = date.today()
    now = today.year * 12 + (today.month - 1)
    intervals = []
    for m in DATE_RANGE.finditer(text):
        # Only look at the line the date sits on: degrees list their dates on the same line,
        # while a job's next line is often an employer like "X University".
        line_start = max(text.rfind("\n", 0, m.start()) + 1, m.start() - 120)
        line_end = text.find("\n", m.end())
        line_end = min(line_end if line_end != -1 else len(text), m.end() + 60)
        if EDUCATION_WORDS.search(text[line_start:line_end]):
            continue
        start = month_index(m, "s", 1)
        end = now if m.group("present") else month_index(m, "e", 12)
        # A year-only end in the current year defaults to December, so cap it at today.
        if start <= end and start <= now:
            intervals.append((start, min(end, now)))

    if not intervals:
        return None

    intervals.sort()
    total, (cur_start, cur_end) = 0, intervals[0]
    for start, end in intervals[1:]:
        if start <= cur_end:
            cur_end = max(cur_end, end)
        else:
            total += cur_end - cur_start + 1
            cur_start, cur_end = start, end
    total += cur_end - cur_start + 1
    return round(total / 12, 1)


def extract_resume_years(text):
    """Returns (years, how) for a resume, preferring a self-reported figure
    ('5+ years of experience') over adding up the employment dates."""
    reported = [int(m.group(1)) for m in SELF_REPORTED.finditer(text) if int(m.group(1)) <= 40]
    if reported:
        return max(reported), "stated in resume"

    years = years_from_ranges(text)
    if years is None:
        return None, "not found"
    return years, "estimated from work history dates"


# ---- Job page fetching ----

MAX_REDIRECTS = 5


class JobFetchError(Exception):
    pass


def _check_public_url(url):
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise JobFetchError("Enter a full job URL starting with http:// or https://")
    try:
        infos = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror:
        raise JobFetchError(f"Could not resolve {parsed.hostname}")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
            raise JobFetchError("That URL points to a private network address")


def _job_posting_from_json_ld(tree):
    """Most job sites embed a schema.org JobPosting, which is far cleaner than page text."""
    for script in tree.xpath('//script[@type="application/ld+json"]/text()'):
        try:
            data = json.loads(script)
        except ValueError:
            continue
        candidates = data if isinstance(data, list) else data.get("@graph", [data]) if isinstance(data, dict) else []
        for item in candidates:
            if isinstance(item, dict) and item.get("@type") == "JobPosting":
                return item
    return None


def _html_to_text(markup):
    # JSON-LD descriptions are usually HTML-escaped, so unescape before parsing the tags.
    fragment = lxml_html.fromstring(f"<div>{html.unescape(markup)}</div>")
    return fragment.text_content()


def fetch_job_posting(url):
    _check_public_url(url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        # Follow redirects by hand so each hop gets the private-address check too.
        for _ in range(MAX_REDIRECTS + 1):
            resp = requests.get(url, headers=headers, timeout=15, allow_redirects=False)
            if not resp.is_redirect:
                break
            url = urljoin(url, resp.headers["Location"])
            _check_public_url(url)
        else:
            raise JobFetchError("The job page redirected too many times.")
    except requests.RequestException as err:
        raise JobFetchError(f"Could not reach the job page: {err.__class__.__name__}")
    if resp.status_code >= 400:
        raise JobFetchError(f"The job site returned HTTP {resp.status_code}. It may block automated access.")

    tree = lxml_html.fromstring(resp.content)
    posting = _job_posting_from_json_ld(tree)
    if posting:
        org = posting.get("hiringOrganization")
        company = org.get("name") if isinstance(org, dict) else None
        parts = [_html_to_text(posting.get(k, "")) for k in
                 ("description", "qualifications", "skills", "experienceRequirements", "responsibilities")
                 if isinstance(posting.get(k), str)]
        text = "\n".join(parts)
        if text.strip():
            return {"title": posting.get("title"), "company": company, "text": text}

    for bad in tree.xpath("//script|//style|//noscript|//nav|//header|//footer|//svg"):
        bad.drop_tree()
    main = tree.xpath("//main") or tree.xpath("//body") or [tree]
    text = re.sub(r"[ \t]+", " ", main[0].text_content())
    text = re.sub(r"\n\s*\n+", "\n", text).strip()
    title = (tree.findtext(".//title") or "").strip() or None
    if len(text) < 200:
        raise JobFetchError("Could not read a job description from that page. "
                            "The site may need JavaScript or a login to show it.")
    return {"title": title, "company": None, "text": text}


# ---- Matching ----

SKILL_WEIGHT = 0.7
EXPERIENCE_WEIGHT = 0.3


def match_resume_to_job(resume_text, job):
    job_skills = extract_skills(job["text"])
    resume_skills = set(extract_skills(resume_text))
    matched = [s for s in job_skills if s in resume_skills]
    missing = [s for s in job_skills if s not in resume_skills]
    skill_score = len(matched) / len(job_skills) if job_skills else None

    required = extract_required_years(job["text"])
    have, how = extract_resume_years(resume_text)
    if required is None:
        exp_score, exp_met = None, None
    elif have is None:
        exp_score, exp_met = 0.0, False
    else:
        exp_score, exp_met = min(1.0, have / required), have >= required

    weighted = [(s, w) for s, w in ((skill_score, SKILL_WEIGHT), (exp_score, EXPERIENCE_WEIGHT)) if s is not None]
    overall = round(100 * sum(s * w for s, w in weighted) / sum(w for _, w in weighted)) if weighted else None

    return {
        "match_percentage": overall,
        "job": {"title": job.get("title"), "company": job.get("company")},
        "skills": {
            "required": job_skills,
            "matched": matched,
            "missing": missing,
            "score": None if skill_score is None else round(100 * skill_score),
        },
        "experience": {
            "required_years": required,
            "resume_years": have,
            "resume_years_source": how,
            "met": exp_met,
            "score": None if exp_score is None else round(100 * exp_score),
        },
        "extra_skills": [s for s in extract_skills(resume_text) if s not in job_skills],
    }
