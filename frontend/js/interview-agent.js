requireAuth();
renderNav();

const startMsg = document.getElementById("start-msg");
const practiceMsg = document.getElementById("practice-msg");
const startBtn = document.getElementById("start-btn");

const planCard = document.getElementById("plan-card");
const practiceCard = document.getElementById("practice-card");
const questionBox = document.getElementById("question-box");
const answerForm = document.getElementById("answer-form");
const feedbackBox = document.getElementById("feedback-box");
const resourcesBox = document.getElementById("resources-box");
const completedBox = document.getElementById("completed-box");

/* In-memory session state, mirrored to localStorage so a page refresh
   doesn't lose your place mid-practice. There's no "fetch session" endpoint
   on the backend, so this page is the only place that remembers it. */
let session = null;

function saveSession() {
  localStorage.setItem("interview_session", JSON.stringify(session));
}

function loadSession() {
  const raw = localStorage.getItem("interview_session");
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch (_) {
    return null;
  }
}

function currentDayPlan() {
  return session.plan.days.find((d) => d.day_number === session.currentDay);
}

function renderPlan() {
  document.getElementById("session-id").textContent = session.id;
  document.getElementById("plan-days").innerHTML = session.plan.days
    .map(
      (d) => `
      <div class="resource-card ${d.day_number === session.currentDay ? "" : ""}">
        <h3>Day ${d.day_number}: ${d.topic} ${d.day_number === session.currentDay ? '<span class="pill">current</span>' : ""}</h3>
        <p>${(d.focus_areas || []).join(" · ")}</p>
      </div>`
    )
    .join("");
  planCard.classList.remove("hidden");
}

function resetPracticeUI() {
  questionBox.classList.add("hidden");
  answerForm.classList.add("hidden");
  feedbackBox.classList.add("hidden");
  resourcesBox.classList.add("hidden");
  completedBox.classList.add("hidden");
  hideMsg(practiceMsg);
}

function renderPractice() {
  resetPracticeUI();
  if (session.completed) {
    completedBox.classList.remove("hidden");
    document.getElementById("next-question-btn").disabled = true;
    return;
  }
  document.getElementById("next-question-btn").disabled = false;
  const day = currentDayPlan();
  document.getElementById("current-day").textContent = session.currentDay;
  document.getElementById("current-topic").textContent = day ? day.topic : "";
  practiceCard.classList.remove("hidden");
}

let currentQuestion = null;

document.getElementById("start-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  hideMsg(startMsg);
  startBtn.disabled = true;
  startBtn.textContent = "Starting… (this calls the LLM, can take a few seconds)";

  const target_role = document.getElementById("target-role").value;
  const days = Number(document.getElementById("days").value) || 5;

  try {
    const data = await api("/interview-prep/start", {
      method: "POST",
      body: { target_role, days },
    });
    session = {
      id: data.session_id,
      plan: JSON.parse(data.plan),
      currentDay: 1,
      completed: false,
    };
    saveSession();
    renderPlan();
    renderPractice();
    showMsg(startMsg, "Plan generated.", "success");
  } catch (err) {
    showMsg(startMsg, err.message, "error");
  } finally {
    startBtn.disabled = false;
    startBtn.textContent = "Start Plan";
  }
});

document.getElementById("next-question-btn").addEventListener("click", async () => {
  hideMsg(practiceMsg);
  const btn = document.getElementById("next-question-btn");
  btn.disabled = true;
  btn.textContent = "Generating…";

  try {
    const data = await api(`/interview-prep/${session.id}/next-question`);
    currentQuestion = data.question;
    renderMarkdown(questionBox, data.question);
    questionBox.classList.remove("hidden");
    answerForm.classList.remove("hidden");
    feedbackBox.classList.add("hidden");
    document.getElementById("answer").value = "";
  } catch (err) {
    showMsg(practiceMsg, err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Get Next Question";
  }
});

document.getElementById("answer-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  hideMsg(practiceMsg);
  const btn = document.getElementById("submit-answer-btn");
  btn.disabled = true;
  btn.textContent = "Scoring…";

  const user_answer = document.getElementById("answer").value;

  try {
    const result = await api("/interview-prep/answer", {
      method: "POST",
      body: {
        session_id: session.id,
        day_number: session.currentDay,
        question: currentQuestion,
        user_answer,
      },
    });

    document.getElementById("score").textContent = result.score;
    document.getElementById("next-action").textContent = result.next_action;
    renderMarkdown(document.getElementById("feedback-text"), result.feedback);
    feedbackBox.classList.remove("hidden");
    answerForm.classList.add("hidden");

    if (result.next_action === "advance") {
      session.currentDay += 1;
      if (session.currentDay > session.plan.days.length) {
        session.completed = true;
      }
    }
    saveSession();
    if (!session.completed) {
      document.getElementById("current-day").textContent = session.currentDay;
      const day = currentDayPlan();
      document.getElementById("current-topic").textContent = day ? day.topic : "";
    } else {
      completedBox.classList.remove("hidden");
      document.getElementById("next-question-btn").disabled = true;
    }
  } catch (err) {
    showMsg(practiceMsg, err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Submit Answer";
  }
});

document.getElementById("resources-btn").addEventListener("click", async () => {
  hideMsg(practiceMsg);
  const btn = document.getElementById("resources-btn");
  btn.disabled = true;
  btn.textContent = "Loading…";

  try {
    const data = await api(`/interview-prep/${session.id}/resources`);
    const list = document.getElementById("resources-list");
    if (!data.resources.length) {
      list.innerHTML = `<p class="empty-state">No resources found for "${data.topic}" yet.</p>`;
    } else {
      list.innerHTML = data.resources
        .map(
          (r) => `
          <div class="resource-card">
            <p>${r.excerpt}</p>
            ${r.source_url ? `<a href="${r.source_url}" target="_blank" rel="noopener">Read more →</a>` : ""}
          </div>`
        )
        .join("");
    }
    resourcesBox.classList.remove("hidden");
  } catch (err) {
    showMsg(practiceMsg, err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Show Study Resources";
  }
});

/* Restore an in-progress session on page load, if there is one. */
session = loadSession();
if (session) {
  renderPlan();
  renderPractice();
}
