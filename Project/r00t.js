
(function () {
    "use strict";

    const enrollForm    = document.getElementById("enrollForm");
    const enrollName    = document.getElementById("enrollName");
    const tokenBox      = document.getElementById("tokenBox");
    const copyTokenBtn  = document.getElementById("copyTokenBtn");

    const verifyForm    = document.getElementById("verifyForm");
    const verifyToken   = document.getElementById("verifyToken");
    const responseBox   = document.getElementById("responseBox");
    const clearRespBtn  = document.getElementById("clearResponseBtn");

    let lastToken = null;

    function setTokenBoxMessage(msg) {
        tokenBox.innerHTML = "";
        const span = document.createElement("span");
        span.className = "dim";
        span.textContent = "// " + msg;
        tokenBox.appendChild(span);
    }

    enrollForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = enrollName.value.trim();
        if (!name) return;

        const result = await apiIssue(name);
        if (result.status === 200 && result.body && result.body.token) {
            lastToken = result.body.token;
            tokenBox.textContent = lastToken;
            verifyToken.value = lastToken;
        } else {
            const msg = (result.body && result.body.error) || "issue failed";
            setTokenBoxMessage(msg);
        }
    });

    copyTokenBtn.addEventListener("click", async () => {
        if (!lastToken) return;
        try {
            await navigator.clipboard.writeText(lastToken);
            copyTokenBtn.textContent = "copied";
            setTimeout(() => { copyTokenBtn.textContent = "copy"; }, 1200);
        } catch {
            const range = document.createRange();
            range.selectNodeContents(tokenBox);
            const sel = window.getSelection();
            sel.removeAllRanges();
            sel.addRange(range);
        }
    });

    verifyForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const token = verifyToken.value.trim();
        if (!token) return;

        const result = await apiSubmit(token);
        renderResponse(responseBox, result.status, result.body);
    });

    clearRespBtn.addEventListener("click", () => {
        responseBox.classList.remove("ok", "warn", "bad");
        responseBox.classList.add("neutral");
        responseBox.innerHTML = '<span class="dim">// idle.</span>';
    });
})();
