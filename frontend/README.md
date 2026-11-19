# Frontend

A plain HTML/CSS/JavaScript app — no build tools, no npm, no framework.
Open the files directly through a simple local server (not `file://`, see
below) and it talks to the FastAPI backend in `app/`.

## Running it

1. Start the backend first, from the project root:
   ```bash
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```
   Leave that running (defaults to `http://127.0.0.1:8000`).

2. In a **second terminal**, serve this folder with Python's built-in server:
   ```bash
   cd frontend
   python3 -m http.server 5500
   ```

3. Open `http://127.0.0.1:5500` in your browser.

Why a local server and not just double-clicking `index.html`: opening a file
directly gives it an origin the browser treats as blocked by the backend's
CORS policy. A simple HTTP server avoids that with no extra setup.

## Structure

- `index.html` — login / signup (the entry point)
- `dashboard.html` — links to every feature
- One HTML file + matching `js/<name>.js` file per feature
- `js/api.js` — shared helpers: API base URL, the login token (kept in
  `localStorage`), a `fetch()` wrapper that attaches it, and the shared nav bar
- `css/style.css` — shared styling

## Notes

- The login token is stored in the browser's `localStorage`, so it survives a
  page refresh but is specific to the browser/computer you're using.
- The Interview Prep page keeps its in-progress session (plan + current day)
  in `localStorage` too, since the backend has no endpoint to re-fetch an
  existing session's state.
