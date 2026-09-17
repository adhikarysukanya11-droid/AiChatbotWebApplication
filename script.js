// ---------------- Dark mode ----------------
const themeToggle = document.getElementById("theme-toggle");

function applyTheme(theme) {
  document.body.classList.toggle("dark", theme === "dark");
  if (themeToggle) themeToggle.textContent = theme === "dark" ? "☀️" : "🌙";
}

const savedTheme = localStorage.getItem("novachat-theme") || "light";
applyTheme(savedTheme);

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    const next = document.body.classList.contains("dark") ? "light" : "dark";
    applyTheme(next);
    localStorage.setItem("novachat-theme", next);
  });
}

// ---------------- Chat page logic ----------------
const messagesEl = document.getElementById("messages");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const clearBtn = document.getElementById("clear-history");

function addMessage(role, text) {
  const row = document.createElement("div");
  row.className = `msg-row ${role}`;

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  bubble.textContent = text;

  row.appendChild(bubble);
  messagesEl.appendChild(row);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return bubble;
}

function addTypingBubble() {
  const row = document.createElement("div");
  row.className = "msg-row bot";

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble typing";
  bubble.innerHTML = `
    <span class="typing-dot"></span>
    <span class="typing-dot"></span>
    <span class="typing-dot"></span>
  `;

  row.appendChild(bubble);
  messagesEl.appendChild(row);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return row;
}

async function loadHistory() {
  if (!messagesEl) return;
  try {
    const res = await fetch("/api/history");
    const data = await res.json();
    if (data.history && data.history.length) {
      data.history.forEach((m) => addMessage(m.role === "user" ? "user" : "bot", m.text));
    } else {
      addMessage("bot", "Hey! What can I help with?");
    }
  } catch (err) {
    addMessage("bot", "Hey! What can I help with?");
  }
}

async function sendMessage(text) {
  addMessage("user", text);
  const typingRow = addTypingBubble();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const data = await res.json();
    typingRow.remove();
    addMessage("bot", data.reply || "Sorry, something went wrong.");
  } catch (err) {
    typingRow.remove();
    addMessage("bot", "Hmm, I couldn't reach the server. Is Flask running?");
  }
}

if (chatForm) {
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;
    chatInput.value = "";
    sendMessage(text);
  });

  loadHistory();
}

if (clearBtn) {
  clearBtn.addEventListener("click", async () => {
    await fetch("/api/history/clear", { method: "POST" });
    messagesEl.innerHTML = "";
    addMessage("bot", "Chat cleared. Say hi!");
  });
}
