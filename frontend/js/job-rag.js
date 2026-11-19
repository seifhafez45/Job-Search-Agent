requireAuth();
renderNav();

const msgEl = document.getElementById("msg");
const resultsEl = document.getElementById("results");
const submitBtn = document.getElementById("submit-btn");

function renderJobs(jobs) {
  if (!jobs.length) {
    resultsEl.innerHTML = `<p class="empty-state">No matches found. This feature only searches jobs already stored in the vector database.</p>`;
    return;
  }
  resultsEl.innerHTML = jobs
    .map(
      (job) => `
      <div class="job-card">
        <h3>${job.title}</h3>
        <div class="meta">
          ${job.company}${job.location ? " · " + job.location : ""}
          ${job.match_score != null ? ` · match ${(job.match_score * 100).toFixed(0)}%` : ""}
        </div>
        <p>${(job.description || "").slice(0, 220)}${job.description && job.description.length > 220 ? "…" : ""}</p>
        <a href="${job.url}" target="_blank" rel="noopener">View posting →</a>
      </div>`
    )
    .join("");
}

document.getElementById("search-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  hideMsg(msgEl);
  resultsEl.innerHTML = "";
  submitBtn.disabled = true;
  submitBtn.textContent = "Searching…";

  const query = document.getElementById("query").value;

  try {
    const jobs = await api(`/jobs/semantic/search?${new URLSearchParams({ query })}`);
    renderJobs(jobs);
    showMsg(msgEl, `Found ${jobs.length} result(s).`, "success");
  } catch (err) {
    showMsg(msgEl, err.message, "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Search";
  }
});
