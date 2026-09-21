import math
import re
from collections import Counter

STOP_WORDS = {"a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from", "has", "have", "in", "is", "it", "of", "on", "or", "our", "that", "the", "their", "this", "to", "we", "will", "with", "you", "your", "years", "work", "working", "role", "team", "skills", "experience", "required"}
SKILLS = ("Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "React", "Angular", "Vue", "Node.js", "Flask", "Django", "FastAPI", "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Git", "Linux", "REST APIs", "GraphQL", "Machine Learning", "Deep Learning", "NLP", "TensorFlow", "PyTorch", "scikit-learn", "Pandas", "NumPy", "Spark", "Tableau", "Power BI", "CI/CD", "Agile", "Data Structures", "Algorithms", "Microservices")


def _tokens(text):
    return [token for token in re.findall(r"[a-zA-Z][a-zA-Z+#./-]*", text.lower()) if len(token) > 2 and token not in STOP_WORDS]


def _contains(text, term):
    normalized = re.sub(r"[^a-z0-9+#]+", " ", text.lower())
    target = re.sub(r"[^a-z0-9+#]+", " ", term.lower()).strip()
    return bool(re.search(rf"(?<!\\w){re.escape(target)}(?!\\w)", normalized))


def score_match(job_description, resume):
    """Return a transparent TF-IDF cosine score and missing JD terms."""
    jd_tokens, resume_tokens = _tokens(job_description), _tokens(resume)
    if not jd_tokens or not resume_tokens:
        return {"score": 0, "missing_terms": [], "matched_skills": []}
    jd_counts, resume_counts = Counter(jd_tokens), Counter(resume_tokens)
    vocabulary = set(jd_counts) | set(resume_counts)
    jd_vector, resume_vector = [], []
    for term in vocabulary:
        document_frequency = int(term in jd_counts) + int(term in resume_counts)
        inverse_frequency = math.log(3 / (document_frequency + 1)) + 1
        jd_vector.append(jd_counts[term] * inverse_frequency)
        resume_vector.append(resume_counts[term] * inverse_frequency)
    dot = sum(a * b for a, b in zip(jd_vector, resume_vector))
    magnitude = math.sqrt(sum(x * x for x in jd_vector)) * math.sqrt(sum(x * x for x in resume_vector))
    cosine = dot / magnitude if magnitude else 0
    jd_skills = [skill for skill in SKILLS if _contains(job_description, skill)]
    matched_skills = [skill for skill in jd_skills if _contains(resume, skill)]
    missing_skills = [skill for skill in jd_skills if skill not in matched_skills]
    missing_keywords = [term for term, _ in jd_counts.most_common() if term not in resume_counts and term not in {x.lower() for x in missing_skills}]
    coverage = len(matched_skills) / len(jd_skills) if jd_skills else cosine
    return {"score": round(min(100, max(0, (0.7 * cosine + 0.3 * coverage) * 100))), "missing_terms": (missing_skills + [term.title() for term in missing_keywords])[:12], "matched_skills": matched_skills}
