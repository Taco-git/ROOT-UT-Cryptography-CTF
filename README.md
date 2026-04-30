# Root Club Special Login

A deliberately vulnerable Flask + vanilla-JS web app, built as a CTF-style challenge for a cybersecurity club. Enroll a name, receive a credential token, submit it back — and find a way to elevate your access.

> **Vulnerable by design.** Do not deploy this to anything you actually care about. The cryptographic weakness is the entire point.

---

## Stack

- **Backend**: Python 3.9+ / Flask / flask-cors / cryptography
- **Frontend**: HTML / CSS / vanilla JS (no bundler, no framework)
- No database; tokens are stateless

---

## Quick start

### Backend

```bash
git clone <this-repo>
cd <repo-folder>

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

By default the backend binds `127.0.0.1:5000`. Override with `HOST` / `PORT` env vars.

### Frontend

In a separate terminal:

```bash
python -m http.server 5173
```

Then open `http://localhost:5173/r00t.html` in a browser. The entry point is `r00t.html` — there is no `index.html`.

---

## Configuration

Fill in these placeholders before public deployment:

| Where | What |
|---|---|
| `app.py` &nbsp;`origins=[...]` | Allowed frontend origin (CORS) |
| `app.py` &nbsp;`FLAG = "FLAG{}"` | Flag returned on successful elite submit |
| `api.js` &nbsp;`API_BASE` default | Backend URL (e.g. `https://your-vps.example`) |
| `r00t.html` &nbsp;`apiTargetDisplay` | Topbar label (cosmetic only) |

### Environment variables

| Var | Default | Purpose |
|---|---|---|
| `HOST` | `127.0.0.1` | Bind address |
| `PORT` | `5000` | Bind port |
| `AES_KEY` | random per run | 16-byte AES key as 32 hex chars. **Set this in production** — otherwise every server restart invalidates every issued token. |

The frontend's `API_BASE` can also be overridden at runtime: drop an inline `<script>window.API_BASE = "https://..."</script>` into `r00t.html` before `<script src="api.js">`. Useful for staging.

---

## File map

| File | Purpose |
|---|---|
| `app.py` | Flask backend (issue / submit / source) |
| `requirements.txt` | Python deps |
| `r00t.html` | Single-page frontend |
| `r00t.js` | Page logic |
| `api.js` | API client helpers |
| `styles.css` | Theme |

---

## The challenge

The flag is gated behind `tier == "elite"` on the credential token. `/api/issue` will only ever hand out `tier=basic` tokens. Recon, look closely at how the server treats different tokens, and find a way.

Have fun.
