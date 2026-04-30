/* =========================================================================
   ROOT CLUB — client API helpers
   ========================================================================= */

// Override per-environment by defining window.API_BASE in an inline script
// tag before this file loads (useful for staging vs prod). Defaults to the
// production VPS.
const API_BASE = (typeof window !== "undefined" && window.API_BASE) || "https:<Enter-Domain>";

const FETCH_DEFAULTS = {
    headers: { "Accept": "application/json" },
};

async function apiFetch(path, opts = {}) {
    const url = API_BASE + path;
    const merged = {
        ...FETCH_DEFAULTS,
        ...opts,
        headers: { ...FETCH_DEFAULTS.headers, ...(opts.headers || {}) },
    };

    let resp;
    try {
        resp = await fetch(url, merged);
    } catch (err) {
        return {
            status: 0,
            ok: false,
            body: { message: `network error: ${err.message}`, _network: true },
        };
    }

    let body;
    const ctype = resp.headers.get("content-type") || "";
    try {
        if (ctype.includes("application/json")) {
            body = await resp.json();
        } else {
            const text = await resp.text();
            body = { message: text };
        }
    } catch (err) {
        body = { message: `failed to parse response body: ${err.message}` };
    }

    return { status: resp.status, ok: resp.ok, body };
}


function apiIssue(name) {
    return apiFetch("/api/issue", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
    });
}

function apiSubmit(token) {
    return apiFetch("/api/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token }),
    });
}


function classifyResponse(status, body) {
    if (status === 200) {
        return { cls: "ok",   headline: "OK" };
    }
    if (status === 403) {
        return { cls: "warn", headline: "FORBIDDEN" };
    }
    if (status === 400) {
        return { cls: "bad",  headline: "REJECTED" };
    }
    if (status === 401) {
        return { cls: "bad",  headline: "UNAUTHORIZED" };
    }
    if (status === 0) {
        return { cls: "bad",  headline: "NETWORK ERROR" };
    }
    return { cls: "neutral", headline: `HTTP ${status}` };
}

function renderResponse(boxEl, status, body) {
    if (!boxEl) return;
    const { cls, headline } = classifyResponse(status, body);

    boxEl.classList.remove("neutral", "ok", "warn", "bad");
    boxEl.classList.add(cls);

    const statusLabel = status === 0 ? "ERR" : `HTTP ${status}`;
    const bodyText = JSON.stringify(body, null, 2);

    boxEl.innerHTML = "";

    const headlineEl = document.createElement("span");
    headlineEl.className = "resp-headline";

    const statusEl = document.createElement("span");
    statusEl.className = "resp-status";
    statusEl.textContent = statusLabel;

    headlineEl.appendChild(statusEl);
    headlineEl.appendChild(document.createTextNode(headline));
    boxEl.appendChild(headlineEl);

    const bodyEl = document.createElement("span");
    bodyEl.className = "resp-body";
    bodyEl.textContent = bodyText;
    boxEl.appendChild(bodyEl);
}
