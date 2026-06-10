document.addEventListener("DOMContentLoaded", () => {
  const navItems = document.querySelectorAll(".nav-links li");
  const tabPanes = document.querySelectorAll(".tab-pane");

  navItems.forEach((item) => {
    item.addEventListener("click", () => {
      navItems.forEach((nav) => nav.classList.remove("active"));
      tabPanes.forEach((tab) => tab.classList.remove("active"));
      item.classList.add("active");
      document.getElementById(item.dataset.target).classList.add("active");
    });
  });

  const logMsg = (msg) => {
    const terminal = document.getElementById("log");
    const time = new Date().toLocaleTimeString("en-US", { hour12: false });
    terminal.innerHTML += `<div><span class="time">[${time}]</span> <span style="color: #e0e0e0;">${msg}</span></div>`;
    terminal.scrollTop = terminal.scrollHeight;
  };

  setInterval(async () => {
    try {
      const res = await fetch("/api/logs");
      const data = await res.json();
      if (data.logs && data.logs.length > 0) {
        data.logs.forEach((log) => logMsg(log));
      }
    } catch (e) {}
  }, 1000);

  const loadConfig = async () => {
    const res = await fetch("/api/config");
    const config = await res.json();
    document.getElementById("depth").value = config.depth || 9;
    document.getElementById("depth-val").innerText = config.depth || 9;
    document.getElementById("play_mode").value =
      config.play_mode || "Auto-Play";
    document.getElementById("highlight_color").value =
      config.color || "#ff2a2a";
    document.getElementById("assist_delay").value = config.delay || 1800;
    document.getElementById("delay-val").innerText =
      (config.delay || 1800) + "ms";
    document.getElementById("browser_path").value = config.browser_path || "";
    document.getElementById("stockfish_path").value =
      config.stockfish_path || "";
    if (config.hotkeys) {
      document.getElementById("hotkey-next").value =
        config.hotkeys.next || "Shift + Space";
      document.getElementById("hotkey-toggle").value =
        config.hotkeys.toggle || "Alt + T";
      document.getElementById("hotkey-hide").value =
        config.hotkeys.hide || "F12";
    }
  };

  const saveAllConfig = async () => {
    const config = {
      depth: parseInt(document.getElementById("depth").value),
      play_mode: document.getElementById("play_mode").value,
      color: document.getElementById("highlight_color").value,
      delay: parseInt(document.getElementById("assist_delay").value),
      browser_path: document.getElementById("browser_path").value,
      stockfish_path: document.getElementById("stockfish_path").value,
      hotkeys: {
        next: document.getElementById("hotkey-next").value,
        toggle: document.getElementById("hotkey-toggle").value,
        hide: document.getElementById("hotkey-hide").value,
      },
    };
    await fetch("/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    return config;
  };

  document.getElementById("apply-depth").addEventListener("click", async () => {
    const newDepth = parseInt(document.getElementById("depth").value);
    await fetch("/api/set-depth", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ depth: newDepth }),
    });
    logMsg(`Stockfish depth changed to ${newDepth} (applied instantly).`);
  });

  document.getElementById("depth").addEventListener("input", (e) => {
    document.getElementById("depth-val").innerText = e.target.value;
  });
  document.getElementById("assist_delay").addEventListener("input", (e) => {
    document.getElementById("delay-val").innerText = e.target.value + "ms";
  });

  function createFileBrowser(fieldId) {
    const input = document.createElement("input");
    input.type = "file";
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (file) {
        document.getElementById(fieldId).value = file.path;
        await saveAllConfig();
        logMsg(`${fieldId} saved: ${file.path}`);
      }
    };
    input.click();
  }

  document
    .getElementById("browse-stockfish")
    .addEventListener("click", () => createFileBrowser("stockfish_path"));
  document
    .getElementById("browse-browser")
    .addEventListener("click", () => createFileBrowser("browser_path"));

  document
    .getElementById("stockfish_path")
    .addEventListener("change", saveAllConfig);
  document
    .getElementById("browser_path")
    .addEventListener("change", saveAllConfig);

  const loadAccount = async () => {
    const res = await fetch("/api/account");
    const acc = await res.json();
    document.getElementById("display-user").innerText =
      acc.username || "Not Connected";
    document.getElementById("inp-user").value = acc.username || "";
    document.getElementById("inp-pass").value = acc.pass || "";
  };

  document.getElementById("edit-acc-btn").addEventListener("click", () => {
    document.getElementById("edit-acc-form").classList.toggle("hidden");
  });

  document
    .getElementById("save-acc-btn")
    .addEventListener("click", async () => {
      const data = {
        username: document.getElementById("inp-user").value,
        pass: document.getElementById("inp-pass").value,
      };
      await fetch("/api/account", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      document.getElementById("display-user").innerText = data.username;
      document.getElementById("edit-acc-form").classList.add("hidden");
      logMsg("Account credentials updated.");
    });

  document.getElementById("btn-open").addEventListener("click", async () => {
    logMsg("Booting stealth browser and authenticating...");
    await saveAllConfig();
    const res = await fetch("/api/open", { method: "POST" });
    const data = await res.json();
    logMsg(data.message);
  });

  document.getElementById("btn-inject").addEventListener("click", async () => {
    await saveAllConfig();
    logMsg("Injecting NEMESIS payload into active tab...");
    const status = document.getElementById("status-indicator");
    status.innerText = "ATTACHED";
    status.className = "status online";
    const res = await fetch("/api/inject", { method: "POST" });
    const data = await res.json();
    logMsg(data.message);
  });

  document.getElementById("btn-stop").addEventListener("click", async () => {
    const status = document.getElementById("status-indicator");
    status.innerText = "IDLE";
    status.className = "status idle";
    const res = await fetch("/api/stop", { method: "POST" });
    const data = await res.json();
    logMsg(data.message);
  });

  document
    .getElementById("save-general")
    .addEventListener("click", async () => {
      await saveAllConfig();
      logMsg("General settings saved.");
    });

  const setupKeybindCapture = (inputId) => {
    const inputEl = document.getElementById(inputId);
    if (!inputEl) return;
    inputEl.addEventListener("keydown", (e) => {
      e.preventDefault();
      let keys = [];
      if (e.ctrlKey) keys.push("Ctrl");
      if (e.shiftKey) keys.push("Shift");
      if (e.altKey) keys.push("Alt");
      if (
        e.key !== "Control" &&
        e.key !== "Shift" &&
        e.key !== "Alt" &&
        e.key !== "Meta"
      ) {
        let keyName = e.code.replace("Key", "").replace("Digit", "");
        keys.push(keyName);
      }
      if (keys.length > 0) inputEl.value = keys.join(" + ");
    });
  };
  setupKeybindCapture("hotkey-next");
  setupKeybindCapture("hotkey-toggle");
  setupKeybindCapture("hotkey-hide");

  document.getElementById("save-binds").addEventListener("click", async () => {
    await saveAllConfig();
    logMsg("Keybinds synchronized.");
  });

  loadConfig();
  loadAccount();
});
