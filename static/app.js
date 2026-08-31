// ── DOM References ────────────────────────────────────────
const chatArea     = document.getElementById("chat-area");
const userInput    = document.getElementById("user-input");
const sendBtn      = document.getElementById("send-btn");
const progressFill = document.getElementById("progress-fill");
const fieldsCount  = document.getElementById("fields-count");
const completionOverlay = document.getElementById("completion-overlay");
const submitBtn         = document.getElementById("submit-btn");
const proceedBtn        = document.getElementById("proceed-btn");
const inputHint         = document.getElementById("input-hint");
const resetBtn          = document.getElementById("reset-btn");
const downloadBtn       = document.getElementById("download-btn");

// ── Add a message bubble to the chat ─────────────────────
function addMessage(text, role) {
    const wrapper = document.createElement("div");
    wrapper.classList.add("message", role === "user" ? "user-message" : "ai-message");

    const avatar = document.createElement("div");
    avatar.classList.add("avatar");
    avatar.textContent = role === "user" ? "You" : "GR";

    const bubble = document.createElement("div");
    bubble.classList.add("bubble");

    // Support line breaks in the reply
    text.split("\n").forEach(line => {
        if (line.trim() === "") return;
        const p = document.createElement("p");
        p.textContent = line;
        bubble.appendChild(p);
    });

    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);
    chatArea.appendChild(wrapper);

    // Scroll to latest message
    chatArea.scrollTop = chatArea.scrollHeight;
}

// ── Show typing indicator while waiting for Gemini ───────
function showTyping() {
    const wrapper = document.createElement("div");
    wrapper.classList.add("message", "ai-message", "typing-indicator");
    wrapper.id = "typing";

    const avatar = document.createElement("div");
    avatar.classList.add("avatar");
    avatar.textContent = "GR";

    const bubble = document.createElement("div");
    bubble.classList.add("bubble");
    bubble.innerHTML = `<div class="dot"></div><div class="dot"></div><div class="dot"></div>`;

    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);
    chatArea.appendChild(wrapper);
    chatArea.scrollTop = chatArea.scrollHeight;
}

function hideTyping() {
    const typing = document.getElementById("typing");
    if (typing) typing.remove();
}

// ── Update the progress bar ───────────────────────────────
function updateProgress(filled) {
    const pct = (filled / 16) * 100;
    progressFill.style.width = pct + "%";
    fieldsCount.textContent = filled;

    // Show reset button once at least 1 field is filled
    if (filled > 0) {
        resetBtn.style.display = "block";
    }

    // All 16 fields filled — hide input completely, show proceed button
    if (filled >= 16) {
        userInput.style.display = "none";
        sendBtn.style.display = "none";
        inputHint.style.display = "none";
        proceedBtn.style.display = "block";
    }
}

// ── Show completion overlay ───────────────────────────────
function showCompletion() {
    completionOverlay.style.display = "flex";
}

// ── Proceed button — shows the completion overlay ─────────
proceedBtn.addEventListener("click", () => {
    showCompletion();
});

// ── Send message to Flask backend ────────────────────────
async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    // Show user message and clear input
    addMessage(message, "user");
    userInput.value = "";
    userInput.style.height = "auto";

    // Disable input while waiting
    userInput.disabled = true;
    sendBtn.disabled = true;

    // Show typing dots
    showTyping();

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();

        hideTyping();
        addMessage(data.reply, "ai");
        updateProgress(data.filled);

    } catch (error) {
        hideTyping();
        addMessage("Sorry, something went wrong. Please try again.", "ai");
        console.error("Error:", error);
    } finally {
        // Re-enable input
        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
    }
}

// ── Submit button — save filled fields to server ─────────
submitBtn.addEventListener("click", async () => {
    try {
        const response = await fetch("/submit", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });
        const data = await response.json();

        if (data.status === "incomplete") {
            // Close overlay, re-enable chat, ask Gemini to re-collect missing fields
            completionOverlay.style.display = "none";
            userInput.style.display = "block";
            sendBtn.style.display = "flex";
            inputHint.style.display = "block";
            proceedBtn.style.display = "none";

            // Trigger Gemini to ask about missing fields
            const missingList = data.missing_fields.join(", ");
            const triggerMsg = `Please re-ask the patient about these unanswered fields: ${missingList}`;
            showTyping();
            const retryResponse = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: triggerMsg })
            });
            const retryData = await retryResponse.json();
            hideTyping();
            addMessage(data.reply, "ai");
            updateProgress(retryData.filled);
        } else {
            submitBtn.textContent = "Submitted ✓";
            submitBtn.disabled = true;

            // Show download button — triggers browser save of the JSON
            downloadBtn.style.display = "block";
            downloadBtn.addEventListener("click", () => {
                const blob = new Blob([JSON.stringify(data.filled_fields, null, 2)], { type: "application/json" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "genoroot_intake.json";
                a.click();
                URL.revokeObjectURL(url);
            }, { once: true });
        }
    } catch (error) {
        console.error("Submit error:", error);
    }
});

// ── Reset session ────────────────────────────────────────
resetBtn.addEventListener("click", async () => {
    await fetch("/reset", { method: "POST" });

    // Clear chat UI — restore only the initial greeting
    chatArea.innerHTML = `
        <div class="message ai-message" id="greeting">
          <div class="avatar">GR</div>
          <div class="bubble">
            <p>Hello! I'm here to help GenoRoot get a complete picture of your hair health before your consultation.</p>
            <p>It'll feel more like a conversation than a form — just answer naturally and we'll get through it together.</p>
            <p>Whenever you're ready, just say <strong>hi</strong> or tell me a little about what's been going on.</p>
          </div>
        </div>`;

    // Reset progress bar
    progressFill.style.width = "0%";
    fieldsCount.textContent = "0";

    // Restore input
    userInput.style.display = "block";
    sendBtn.style.display = "flex";
    inputHint.style.display = "block";
    proceedBtn.style.display = "none";
    resetBtn.style.display = "none";

    // Hide overlay if open
    completionOverlay.style.display = "none";
    submitBtn.textContent = "Submit & Confirm";
    submitBtn.disabled = false;
    downloadBtn.style.display = "none";

    userInput.focus();
});

// ── Event listeners ───────────────────────────────────────

// Send on button click
sendBtn.addEventListener("click", sendMessage);

// Send on Enter, new line on Shift+Enter
userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Auto-resize textarea as user types
userInput.addEventListener("input", () => {
    userInput.style.height = "auto";
    userInput.style.height = userInput.scrollHeight + "px";
});
