import ipaddress
import math
import re
import socket
from collections import Counter
from io import BytesIO
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from docx import Document
from pypdf import PdfReader

STOP_WORDS = {"a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from", "has", "have", "in", "is", "it", "of", "on", "or", "our", "that", "the", "their", "this", "to", "we", "will", "with", "you", "your", "years", "work", "working", "role", "team", "skills", "experience", "required"}
SKILLS = ("Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "React", "Angular", "Vue", "Node.js", "Flask", "Django", "FastAPI", "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git", "Linux", "REST APIs", "GraphQL", "Machine Learning", "Deep Learning", "NLP", "TensorFlow", "PyTorch", "scikit-learn", "Pandas", "NumPy", "Spark", "Tableau", "Power BI", "CI/CD", "Agile", "Data Structures", "Algorithms", "Microservices")
ACTION_VERBS = ("built", "created", "developed", "designed", "implemented", "improved", "increased", "launched", "led", "optimized", "reduced", "shipped")
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


def extract_document(upload):
    """Extract text from an uploaded PDF, DOCX, or TXT without saving it."""
    if not upload or not upload.filename:
        return ""
    extension = upload.filename.rsplit(".", 1)[-1].lower() if "." in upload.filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Upload a PDF, DOCX, or TXT file.")
    data = upload.read()
    try:
        if extension == "pdf":
            return "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(data)).pages).strip()
        if extension == "docx":
            return "\n".join(paragraph.text for paragraph in Document(BytesIO(data)).paragraphs).strip()
        return data.decode("utf-8").strip()
    except Exception as error:
        raise ValueError("The uploaded file could not be read. Try exporting it again.") from error


def extract_job_url(url):
    """Fetch readable text from a public job-posting page with SSRF safeguards."""
    if not url:
        return ""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Enter a complete public http:// or https:// job link.")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443, type=socket.SOCK_STREAM)
        if any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise ValueError("The job link must point to a public website.")
        response = requests.get(
            url,
            headers={"User-Agent": "JobMatch/1.0 (resume alignment tool)"},
            timeout=8,
            stream=True,
            allow_redirects=True,
        )
        response.raise_for_status()
        if "text/html" not in response.headers.get("Content-Type", ""):
            raise ValueError("The job link must point to a web page.")
        content = response.raw.read(1_000_001, decode_content=True)
        if len(content) > 1_000_000:
            raise ValueError("The job page is too large to analyze.")
    except ValueError:
        raise
    except (requests.RequestException, OSError) as error:
        raise ValueError("The job page could not be read. Paste the description instead.") from error
    soup = BeautifulSoup(content, "html.parser")
    for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        element.decompose()
    text = " ".join(soup.get_text(" ", strip=True).split())
    if len(text.split()) < 40:
        raise ValueError("The page did not expose enough job text. Paste the description instead.")
    return text


def _tokens(text):
    return [token for token in re.findall(r"[a-zA-Z][a-zA-Z+#./-]*", text.lower()) if len(token) > 2 and token not in STOP_WORDS]


def _contains(text, term):
    normalized = re.sub(r"[^a-z0-9+#]+", " ", text.lower())
    target = re.sub(r"[^a-z0-9+#]+", " ", term.lower()).strip()
    return bool(re.search(rf"(?<!\w){re.escape(target)}(?!\w)", normalized))


def _cosine_similarity(first_tokens, second_tokens):
    first_counts, second_counts = Counter(first_tokens), Counter(second_tokens)
    vocabulary = set(first_counts) | set(second_counts)
    first_vector, second_vector = [], []
    for term in vocabulary:
        document_frequency = int(term in first_counts) + int(term in second_counts)
        inverse_frequency = math.log(3 / (document_frequency + 1)) + 1
        first_vector.append(first_counts[term] * inverse_frequency)
        second_vector.append(second_counts[term] * inverse_frequency)
    dot = sum(a * b for a, b in zip(first_vector, second_vector))
    magnitude = math.sqrt(sum(x * x for x in first_vector)) * math.sqrt(sum(x * x for x in second_vector))
    return dot / magnitude if magnitude else 0


def score_match(job_description, resume, cover_letter=""):
    """Create an explainable ATS-style alignment estimate and feedback."""
    application_text = f"{resume}\n{cover_letter}".strip()
    jd_tokens, application_tokens = _tokens(job_description), _tokens(application_text)
    if not jd_tokens or not application_tokens:
        return {"score": 0, "missing_terms": [], "matched_skills": [], "feedback": [], "breakdown": {}}
    similarity = _cosine_similarity(jd_tokens, application_tokens)
    jd_counts, application_counts = Counter(jd_tokens), Counter(application_tokens)
    jd_skills = [skill for skill in SKILLS if _contains(job_description, skill)]
    matched_skills = [skill for skill in jd_skills if _contains(application_text, skill)]
    missing_skills = [skill for skill in jd_skills if skill not in matched_skills]
    missing_keywords = [term for term, _ in jd_counts.most_common() if term not in application_counts and term not in {x.lower() for x in missing_skills}]
    skill_coverage = len(matched_skills) / len(jd_skills) if jd_skills else similarity
    evidence_hits = sum(_contains(resume, verb) for verb in ACTION_VERBS)
    has_metrics = bool(re.search(r"\b\d+(?:\.\d+)?%|\b\d+[kKmM+]?\b", resume))
    evidence_score = min(1, evidence_hits / 4 + (0.25 if has_metrics else 0))
    readable_score = 1 if 150 <= len(_tokens(resume)) <= 1200 else 0.65
    breakdown = {"Keyword alignment": round(similarity * 45), "Required skill coverage": round(skill_coverage * 35), "Evidence and impact": round(evidence_score * 15), "Readable length": round(readable_score * 5)}
    score = min(100, sum(breakdown.values()))
    if score >= 80:
        ranking, estimated_tier = "Highly aligned", "Estimated top tier"
    elif score >= 65:
        ranking, estimated_tier = "Competitive match", "Estimated upper-middle tier"
    elif score >= 45:
        ranking, estimated_tier = "Partial match", "Estimated middle tier"
    else:
        ranking, estimated_tier = "Needs tailoring", "Estimated lower tier"
    feedback = []
    if missing_skills:
        feedback.append({"priority": "High", "title": "Address required skills", "detail": f"Show truthful evidence for: {', '.join(missing_skills[:6])}."})
    if similarity < 0.55:
        feedback.append({"priority": "High", "title": "Mirror the role's language", "detail": "Use the job description's terminology in relevant bullets instead of relying on broad synonyms."})
    if evidence_hits < 3:
        feedback.append({"priority": "Medium", "title": "Start bullets with strong actions", "detail": "Use verbs such as built, implemented, optimized, or led to make ownership clear."})
    if not has_metrics:
        feedback.append({"priority": "Medium", "title": "Quantify impact", "detail": "Add credible numbers—users, speed, accuracy, scale, or time saved—to your strongest bullets."})
    if not cover_letter:
        feedback.append({"priority": "Optional", "title": "Add a tailored cover letter", "detail": "For roles that request one, connect two relevant experiences directly to the employer's needs."})
    if not feedback:
        feedback.append({"priority": "Review", "title": "Keep the application specific", "detail": "The alignment is strong. Proofread and confirm every claimed skill is supported by evidence."})
    return {"score": score, "ranking": ranking, "estimated_tier": estimated_tier, "missing_terms": (missing_skills + [term.title() for term in missing_keywords])[:12], "matched_skills": matched_skills, "feedback": feedback, "breakdown": breakdown, "disclaimer": "This is an explainable alignment estimate, not a prediction from a specific employer's ATS or a hiring guarantee."}
