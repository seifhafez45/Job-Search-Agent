requireAuth();
renderNav();

const msgEl = document.getElementById("msg");
const resultCard = document.getElementById("result-card");
const resultEl = document.getElementById("result");
const submitBtn = document.getElementById("submit-btn");

document.getElementById("upload-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fileInput = document.getElementById("file");
  if (!fileInput.files.length) return;

  hideMsg(msgEl);
  resultCard.classList.add("hidden");
  submitBtn.disabled = true;
  submitBtn.textContent = "Uploading…";

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  try {
    const profile = await api("/cv/upload", {
      method: "POST",
      isForm: true,
      body: formData,
    });

    resultEl.textContent = JSON.stringify(profile, null, 2);
    resultCard.classList.remove("hidden");
    showMsg(msgEl, "Resume parsed successfully.", "success");
  } catch (err) {
    showMsg(msgEl, err.message, "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Upload & Extract";
  }
});
