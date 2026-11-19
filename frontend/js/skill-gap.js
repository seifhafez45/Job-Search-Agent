requireAuth();
renderNav();

const msgEl = document.getElementById("msg");
const resultCard = document.getElementById("result-card");
const submitBtn = document.getElementById("submit-btn");

function renderPills(mount, items) {
  if (!items || !items.length) {
    mount.innerHTML = `<p class="empty-state">None.</p>`;
    return;
  }
  mount.innerHTML = items.map((s) => `<span class="pill" style="margin:3px 4px 3px 0;">${s}</span>`).join("");
}

document.getElementById("analyze-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  hideMsg(msgEl);
  resultCard.classList.add("hidden");
  submitBtn.disabled = true;
  submitBtn.textContent = "Analyzing…";

  const job_title = document.getElementById("job-title").value;
  const job_description = document.getElementById("job-description").value;

  try {
    const report = await api("/skill-gap/analyze", {
      method: "POST",
      body: { job_title, job_description },
    });

    renderPills(document.getElementById("matched"), report.matched_skills);
    renderPills(document.getElementById("missing"), report.missing_skills);
    document.getElementById("fit-summary").textContent = report.fit_summary;
    resultCard.classList.remove("hidden");
  } catch (err) {
    showMsg(msgEl, err.message, "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Analyze";
  }
});
