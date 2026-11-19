const msgEl = document.getElementById("msg");

/* Already logged in? Skip straight to the dashboard. */
if (getToken()) {
  window.location.href = "dashboard.html";
}

document.getElementById("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("login-email").value;
  const password = document.getElementById("login-password").value;

  try {
    const data = await api("/auth/login", {
      method: "POST",
      auth: false,
      body: { email, password },
    });
    setSession(data.access_token, email);
    window.location.href = "dashboard.html";
  } catch (err) {
    showMsg(msgEl, err.message, "error");
  }
});

document.getElementById("signup-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("signup-email").value;
  const password = document.getElementById("signup-password").value;

  try {
    const data = await api("/auth/signup", {
      method: "POST",
      auth: false,
      body: { email, password },
    });
    setSession(data.access_token, email);
    window.location.href = "dashboard.html";
  } catch (err) {
    showMsg(msgEl, err.message, "error");
  }
});
