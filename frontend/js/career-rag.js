requireAuth();
renderNav();

const msgEl = document.getElementById("msg");
const resultCard = document.getElementById("result-card");
const answerEl = document.getElementById("answer");
const sourcesEl = document.getElementById("sources-used");
const submitBtn = document.getElementById("submit-btn");

document.getElementById("ask-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  hideMsg(msgEl);
  resultCard.classList.add("hidden");
  submitBtn.disabled = true;
  submitBtn.textContent = "Asking…";

  const question = document.getElementById("question").value;

  try {
    const data = await api(`/career-resources/ask?${new URLSearchParams({ question })}`);
    renderMarkdown(answerEl, data.answer);
    sourcesEl.textContent = `Grounded in ${data.sources_used} retrieved source chunk(s).`;
    resultCard.classList.remove("hidden");
  } catch (err) {
    showMsg(msgEl, err.message, "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Ask";
  }
});
