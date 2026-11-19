/* Shared across every page: where the API lives, how we store the login
   token, a fetch() wrapper that attaches it, and the top nav bar. */

const API_BASE = "http://127.0.0.1:8000";

function getToken() {
  return localStorage.getItem("token");
}

function setSession(token, email) {
  localStorage.setItem("token", token);
  localStorage.setItem("email", email || "");
}

function clearSession() {
  localStorage.removeItem("token");
  localStorage.removeItem("email");
}

function getEmail() {
  return localStorage.getItem("email") || "";
}

/* Every protected page calls this first. No token -> bounce to login. */
function requireAuth() {
  if (!getToken()) {
    window.location.href = "index.html";
  }
}

/**
 * Calls the API. `auth: true` attaches the Bearer token (default).
 * Returns the parsed JSON body. Throws an Error with a readable message
 * on any non-2xx response, or a 401 redirects to the login page.
 */
async function api(path, { method = "GET", body, auth = true, isForm = false } = {}) {
  const headers = {};
  if (!isForm) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: isForm ? body : body ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401) {
    clearSession();
    window.location.href = "index.html";
    throw new Error("Session expired, please log in again.");
  }

  if (response.status === 204) return null;

  let data = null;
  try {
    data = await response.json();
  } catch (_) {
    /* empty body is fine */
  }

  if (!response.ok) {
    const detail = data && data.detail ? data.detail : response.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }

  return data;
}

const NAV_LINKS = [
  ["dashboard.html", "Dashboard"],
  ["cv-upload.html", "CV Upload"],
  ["job-search.html", "Job Search"],
  ["job-rag.html", "Semantic Job Search"],
  ["skill-gap.html", "Skill Gap"],
  ["applications.html", "Applications"],
  ["tailoring.html", "Cover Letter"],
  ["career-rag.html", "Career Q&A"],
  ["interview-agent.html", "Interview Prep"],
];

function renderNav() {
  const mount = document.getElementById("nav");
  if (!mount) return;

  const here = window.location.pathname.split("/").pop();
  const links = NAV_LINKS.map(
    ([href, label]) =>
      `<a href="${href}" class="${href === here ? "active" : ""}">${label}</a>`
  ).join("");

  mount.innerHTML = `
    ${links}
    <span class="spacer"></span>
    <span class="user-email">${getEmail()}</span>
    <button class="secondary" id="logout-btn" style="margin-top:0;">Log out</button>
  `;

  document.getElementById("logout-btn").addEventListener("click", () => {
    clearSession();
    window.location.href = "index.html";
  });
}

function showMsg(el, text, type = "info") {
  el.textContent = text;
  el.className = `msg ${type}`;
  el.classList.remove("hidden");
}

function hideMsg(el) {
  el.classList.add("hidden");
}
