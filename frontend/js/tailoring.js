requireAuth();
renderNav();

const msgEl = document.getElementById("msg");
const resultCard = document.getElementById("result-card");
const resultEl = document.getElementById("result");
const submitBtn = document.getElementById("submit-btn");

document.getElementById("generate-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  hideMsg(msgEl);
  resultCard.classList.add("hidden");
  submitBtn.disabled = true;
  submitBtn.textContent = "Generating… (this can take a while)";

  const application_id = Number(document.getElementById("application-id").value);
  const job_description = document.getElementById("job-description").value;

  try {
    const data = await api("/tailoring/generate", {
      method: "POST",
      body: { application_id, job_description },
    });
    resultEl.textContent = data.cover_letter;
    resultCard.classList.remove("hidden");
  } catch (err) {
    showMsg(msgEl, err.message, "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Generate Cover Letter";
  }
});
