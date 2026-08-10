/* DairyOS browser authentication bridge.
 *
 * The existing operator UI is a static HTML application that talks directly
 * to the FastAPI API. This bridge adds a real login session without creating
 * a second frontend architecture: it waits for authentication before API
 * calls, attaches the signed bearer token to subsequent requests, and opens
 * the login dialog again if the session expires.
 */
(function () {
  "use strict";

  const TOKEN_KEY = "dairyos.access_token";
  const USER_KEY = "dairyos.user";
  const pending = [];
  const originalFetch = window.fetch.bind(window);
  let authenticated = false;

  function token() {
    return sessionStorage.getItem(TOKEN_KEY);
  }

  function setSession(payload) {
    sessionStorage.setItem(TOKEN_KEY, payload.access_token);
    sessionStorage.setItem(USER_KEY, JSON.stringify(payload.user || {}));
    authenticated = true;
    hideLogin();
    flushPending();
  }

  function clearSession() {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
    authenticated = false;
  }

  function showLogin(message) {
    let modal = document.getElementById("dairyos-login-modal");
    if (!modal) {
      modal = document.createElement("div");
      modal.id = "dairyos-login-modal";
      modal.innerHTML = `
        <div style="position:fixed;inset:0;background:rgba(16,42,42,.55);display:flex;align-items:center;justify-content:center;z-index:9999;padding:20px">
          <form id="dairyos-login-form" style="width:min(420px,100%);background:#fff;border-radius:14px;padding:24px;box-shadow:0 20px 60px rgba(0,0,0,.25);display:block">
            <h2 style="margin:0 0 6px">DairyOS Operator Login</h2>
            <p id="dairyos-login-message" style="margin:0 0 18px;color:#667085">Sign in to record operator-attributable farm activity.</p>
            <label style="display:flex;flex-direction:column;gap:5px;font-size:12px;color:#667085;margin-bottom:12px">Username<input id="dairyos-login-user" autocomplete="username" value="admin" required style="border:1px solid #cfd5dc;border-radius:7px;padding:10px;font:inherit;color:#17202a"></label>
            <label style="display:flex;flex-direction:column;gap:5px;font-size:12px;color:#667085;margin-bottom:16px">Password<input id="dairyos-login-password" type="password" autocomplete="current-password" value="dairyos" required style="border:1px solid #cfd5dc;border-radius:7px;padding:10px;font:inherit;color:#17202a"></label>
            <button type="submit" style="width:100%;border:0;background:#176b5b;color:#fff;border-radius:7px;padding:10px 14px;cursor:pointer;font-weight:600">Sign in</button>
          </form>
        </div>`;
      document.body.appendChild(modal);
      modal.querySelector("form").addEventListener("submit", async function (event) {
        event.preventDefault();
        const message = document.getElementById("dairyos-login-message");
        message.textContent = "Signing in…";
        try {
          const response = await originalFetch("/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              username: document.getElementById("dairyos-login-user").value,
              password: document.getElementById("dairyos-login-password").value,
            }),
          });
          const data = await response.json();
          if (!response.ok) throw new Error(data.detail || "Login failed");
          setSession(data);
        } catch (error) {
          message.textContent = error.message || "Login failed";
          message.style.color = "#b42318";
        }
      });
    }
    document.getElementById("dairyos-login-message").textContent = message || "Sign in to continue.";
    modal.style.display = "block";
    setTimeout(() => document.getElementById("dairyos-login-password")?.focus(), 0);
  }

  function hideLogin() {
    const modal = document.getElementById("dairyos-login-modal");
    if (modal) modal.style.display = "none";
  }

  function flushPending() {
    while (pending.length) {
      const item = pending.shift();
      originalFetch(item.url, withAuth(item.options)).then(item.resolve, item.reject);
    }
  }

  function withAuth(options) {
    const next = Object.assign({}, options || {});
    const headers = new Headers(next.headers || {});
    const current = token();
    if (current && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${current}`);
    }
    next.headers = headers;
    return next;
  }

  window.fetch = function (url, options) {
    const requestUrl = typeof url === "string" ? url : (url && url.url) || "";
    const isLogin = requestUrl === "/login" || requestUrl.endsWith("/login");
    if (isLogin) return originalFetch(url, options);

    if (!authenticated && !token()) {
      return new Promise((resolve, reject) => {
        pending.push({ url, options, resolve, reject });
        showLogin();
      });
    }

    authenticated = true;
    return originalFetch(url, withAuth(options)).then(response => {
      if (response.status === 401) {
        clearSession();
        showLogin("Your session has expired. Please sign in again.");
      }
      return response;
    });
  };

  window.dairyosLogout = function () {
    clearSession();
    showLogin("You have been signed out.");
  };

  if (token()) {
    authenticated = true;
  } else {
    showLogin();
  }
})();
