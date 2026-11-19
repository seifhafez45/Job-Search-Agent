requireAuth();
renderNav();

const createMsg = document.getElementById("create-msg");
const listMsg = document.getElementById("list-msg");
const table = document.getElementById("table");
const tableBody = document.getElementById("table-body");
const STATUSES = ["saved", "applied", "interviewing", "offer", "rejected"];

function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString();
}

function renderRows(apps) {
  if (!apps.length) {
    table.classList.add("hidden");
    listMsg.textContent = "No applications yet.";
    listMsg.className = "msg info";
    return;
  }
  listMsg.classList.add("hidden");
  table.classList.remove("hidden");

  tableBody.innerHTML = apps
    .map(
      (a) => `
      <tr data-id="${a.id}">
        <td>#${a.id} ${a.job_title}</td>
        <td>${a.company}</td>
        <td>
          <select class="status-select" data-id="${a.id}">
            ${STATUSES.map((s) => `<option value="${s}" ${s === a.status ? "selected" : ""}>${s}</option>`).join("")}
          </select>
        </td>
        <td>${fmtDate(a.applied_at)}</td>
        <td class="inline-actions">
          ${a.job_url ? `<a href="${a.job_url}" target="_blank" rel="noopener">link</a>` : ""}
          <button class="danger delete-btn" data-id="${a.id}" style="margin-top:0;">Delete</button>
        </td>
      </tr>`
    )
    .join("");

  tableBody.querySelectorAll(".status-select").forEach((sel) => {
    sel.addEventListener("change", async () => {
      try {
        await api(`/applications/${sel.dataset.id}`, {
          method: "PATCH",
          body: { status: sel.value },
        });
      } catch (err) {
        showMsg(listMsg, err.message, "error");
      }
    });
  });

  tableBody.querySelectorAll(".delete-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm("Delete this application?")) return;
      try {
        await api(`/applications/${btn.dataset.id}`, { method: "DELETE" });
        loadApplications();
      } catch (err) {
        showMsg(listMsg, err.message, "error");
      }
    });
  });
}

async function loadApplications() {
  hideMsg(listMsg);
  const filter = document.getElementById("filter").value;
  const qs = filter ? `?status_filter=${encodeURIComponent(filter)}` : "";
  try {
    const apps = await api(`/applications/${qs}`);
    renderRows(apps);
  } catch (err) {
    showMsg(listMsg, err.message, "error");
  }
}

async function loadStale() {
  hideMsg(listMsg);
  try {
    const apps = await api("/applications/stale");
    renderRows(apps);
    if (apps.length) showMsg(listMsg, `${apps.length} application(s) with no update in a while.`, "info");
  } catch (err) {
    showMsg(listMsg, err.message, "error");
  }
}

document.getElementById("create-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  hideMsg(createMsg);
  const btn = document.getElementById("create-btn");
  btn.disabled = true;

  const job_title = document.getElementById("job-title").value;
  const company = document.getElementById("company").value;
  const job_url = document.getElementById("job-url").value || null;
  const status = document.getElementById("status").value;

  try {
    await api("/applications/", { method: "POST", body: { job_title, company, job_url, status } });
    showMsg(createMsg, "Application added.", "success");
    e.target.reset();
    loadApplications();
  } catch (err) {
    showMsg(createMsg, err.message, "error");
  } finally {
    btn.disabled = false;
  }
});

document.getElementById("filter").addEventListener("change", loadApplications);
document.getElementById("refresh-btn").addEventListener("click", loadApplications);
document.getElementById("stale-btn").addEventListener("click", loadStale);

loadApplications();
