// References
const messagesEl = document.getElementById("messages");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("sendBtn");

// Backend URL
const BACKEND_URL = "http://127.0.0.1:8000";

// Send Message Function
async function sendMessage() {
    const message = chatInput.value.trim();
    if (!message) return;

    // Display User Message
    const userMessage = document.createElement("div");
    userMessage.className = "message user";
    userMessage.textContent = message;
    messagesEl.appendChild(userMessage);

    // Clear Input
    chatInput.value = "";

    try {
        // Send API Request
        const response = await fetch(`${BACKEND_URL}/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message }),
        });

        const data = await response.json();

        // Display Beru's Response
        const beruMessage = document.createElement("div");
        beruMessage.className = "message beru";
        beruMessage.textContent = data.response;
        messagesEl.appendChild(beruMessage);
    } catch (error) {
        console.error("Error:", error);
    }
}

// Event Listeners
sendBtn.addEventListener("click", sendMessage);
chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        sendMessage();
    }
});