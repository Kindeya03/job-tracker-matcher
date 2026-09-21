const form = document.querySelector("#match-form");
const results = document.querySelector("#results");
const words = (value) => value.trim() ? value.trim().split(/\s+/).length : 0;

for (const [name, id] of [["job_description", "jd-count"], ["resume", "resume-count"]]) {
  const field = form.elements[name];
  field.addEventListener("input", () => {
    document.querySelector("#" + id).textContent = words(field.value) + " words";
  });
}

document.querySelectorAll('input[type="file"]').forEach((input) => {
  input.addEventListener("change", () => {
    const box = input.closest(".upload-box");
    const hint = box.querySelector("small:last-of-type");
    if (input.files[0]) {
      hint.textContent = input.files[0].name;
      box.classList.add("has-file");
    }
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = form.querySelector('button[type="submit"]');
  button.disabled = true;
  button.textContent = "Reviewing application…";
  try {
    const response = await fetch("/matcher", {method: "POST", body: new FormData(form)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error);
    renderResults(data);
  } catch (error) {
    results.innerHTML = '<div class="result-placeholder"><h2>Could not complete the review</h2><p>' + escapeHtml(error.message) + '</p></div>';
  } finally {
    button.disabled = false;
    button.textContent = "Run ATS review";
  }
});

function renderResults(data) {
  const breakdown = Object.entries(data.breakdown).map(([label, value]) =>
    '<div class="breakdown-row"><span>' + escapeHtml(label) + '</span><div><i style="width:' + value / categoryMaximum(label) * 100 + '%"></i></div><strong>' + value + '</strong></div>'
  ).join("");
  const feedback = data.feedback.map(item =>
    '<li><span class="priority priority-' + item.priority.toLowerCase() + '">' + escapeHtml(item.priority) + '</span><div><strong>' + escapeHtml(item.title) + '</strong><p>' + escapeHtml(item.detail) + '</p></div></li>'
  ).join("");
  const missing = data.missing_terms.length ? data.missing_terms.map(term => "<li>" + escapeHtml(term) + "</li>").join("") : "<li>No major missing terms detected.</li>";
  const matched = data.matched_skills.length ? data.matched_skills.map(term => "<span>" + escapeHtml(term) + "</span>").join("") : "<em>No exact skill matches detected.</em>";
  results.innerHTML = '<div class="score-wrap"><p class="tier">' + escapeHtml(data.estimated_tier) + '</p><div class="score-ring" style="--score:' + data.score + '"><div><strong>' + data.score + '</strong><small>/ 100</small></div></div><p class="score-label">' + escapeHtml(data.ranking) + '</p><p>' + escapeHtml(data.disclaimer) + '</p></div><div class="result-section"><h3>Score breakdown</h3>' + breakdown + '</div><div class="result-section"><h3>Prioritized feedback</h3><ul class="feedback-list">' + feedback + '</ul></div><div class="result-section"><h3>Matched skills</h3><div class="matched-tags">' + matched + '</div></div><div class="result-section"><h3>Missing terms to review</h3><p>Only add terms that truthfully reflect your experience.</p><ul class="keyword-list">' + missing + '</ul></div>';
}

function categoryMaximum(label) {
  return {"Keyword alignment": 45, "Required skill coverage": 35, "Evidence and impact": 15, "Readable length": 5}[label] || 100;
}

function escapeHtml(value) {
  const node = document.createElement("div");
  node.textContent = value;
  return node.innerHTML;
}
