// =========================
// ZAKIA CHATBOT SCRIPT
// =========================

document.addEventListener("DOMContentLoaded", () => {
  const minimizeBtn = document.querySelector(".minimize-btn");
  const chatbox = document.querySelector(".chatbox");
  const dateChip = document.getElementById("dateChip");

  // Minimize toggle
  minimizeBtn.addEventListener("click", () => {
    const minimized = chatbox.classList.toggle("minimized");
    minimizeBtn.textContent = minimized ? "+" : "−";
  });

  // Display localized Malay date
  if (dateChip) {
    const now = new Date();
    const options = { weekday: "long", year: "numeric", month: "long", day: "numeric" };
    const dateText = now.toLocaleDateString("ms-MY", options);
    dateChip.textContent = dateText.charAt(0).toUpperCase() + dateText.slice(1);
  }

  // Chat functionality
  const textarea = document.getElementById("userInput");
  const sendBtn = document.getElementById("sendBtn");
  const messages = document.getElementById("messages");

  function sendMessage() {
    const text = textarea.value.trim();
    if (!text) return;

    const userMsg = document.createElement("div");
    userMsg.className = "msg user";
    userMsg.innerHTML = `<div class="bubble user-bubble">${text}</div>`;
    messages.appendChild(userMsg);

    textarea.value = "";
    textarea.style.height = "38px";
    messages.scrollTop = messages.scrollHeight;
  }

  sendBtn.addEventListener("click", sendMessage);
  textarea.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
});
