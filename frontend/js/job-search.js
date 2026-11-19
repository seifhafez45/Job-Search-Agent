requireAuth();
renderNav();

const msgEl = document.getElementById("msg");
const resultsEl = document.getElementById("results");
const submitBtn = document.getElementById("submit-btn");

function renderJobs(jobs) {
  if (!jobs.length) {
    resultsEl.innerHTML = `<p class="empty-state">No jobs found. Try a broader keyword or fewer filters.</p>`;
    return;
  }
  resultsEl.innerHTML = jobs
    .map(
      (job) => `
      <div class="job-card">
        <h3>${job.title}</h3>
        <div class="meta">
          ${job.company}${job.location ? " · " + job.location : ""}
          ${job.remote ? ' · <span class="pill">remote</span>' : ""}
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

  const params = new URLSearchParams();
  params.set("keyword", document.getElementById("keyword").value);

  const location = document.getElementById("location").value;
  if (location) params.set("location", location);

  const country = document.getElementById("country").value;
  if (country) params.set("country", country);

  const datePosted = document.getElementById("date-posted").value;
  if (datePosted) params.set("date_posted", datePosted);

  params.set("results_per_page", document.getElementById("results-per-page").value || "20");
  params.set("remote", document.getElementById("remote").checked ? "true" : "false");
  if (document.getElementById("full-time").checked) params.set("full_time", "true");

  try {
    const jobs = await api(`/jobs/search?${params.toString()}`);
    renderJobs(jobs);
    showMsg(msgEl, `Found ${jobs.length} result(s).`, "success");
  } catch (err) {
    showMsg(msgEl, err.message, "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Search";
  }
});
