const form = document.querySelector("#match-form");
const results = document.querySelector("#results");
const words = (value) => value.trim() ? value.trim().split(/\s+/).length : 0;

for (const [name, id] of [["job_description", "jd-count"], ["resume", "resume-count"]]) {
  const field = form.elements[name];
  const output = document.querySelector("#" + id);
  field.addEventListener("input", () => output.textContent = words(field.value) + " words");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = form.querySelector("button");
  button.disabled = true;
  button.textContent = "Analyzing…";
  try {
    const response = await fetch("/matcher", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({job_description: form.elements.job_description.value, resume: form.elements.resume.value})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    const tone = data.score >= 75 ? "Strong match" : data.score >= 50 ? "Good foundation" : "Needs tailoring";
    const missing = data.missing_terms.length ? data.missing_terms.map(term => "<li>" + escapeHtml(term) + "</li>").join("") : "<li>No major missing terms detected.</li>";
    const matched = data.matched_skills.length ? data.matched_skills.map(term => "<span>" + escapeHtml(term) + "</span>").join("") : "<em>No exact skill matches detected.</em>";
    results.innerHTML = '<div class="score-wrap"><div class="score-ring" style="--score:' + data.score + '"><div><strong>' + data.score + '</strong><small>/ 100</small></div></div><p class="score-label">' + tone + '</p><p>Use this as a tailoring signal—not an automated hiring prediction.</p></div><div class="result-section"><h3>Matched skills</h3><div class="matched-tags">' + matched + '</div></div><div class="result-section"><h3>Missing from your resume</h3><p>Only add terms that truthfully reflect your experience.</p><ul class="keyword-list">' + missing + '</ul></div>';
  } catch (error) {
    results.innerHTML = '<div class="result-placeholder"><h2>Could not score</h2><p>' + escapeHtml(error.message) + '</p></div>';
  } finally {
    button.disabled = false;
    button.textContent = "Calculate match score";
  }
});

function escapeHtml(value) {
  const node = document.createElement("div");
  node.textContent = value;
  return node.innerHTML;
}
