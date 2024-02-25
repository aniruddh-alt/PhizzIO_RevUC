document.addEventListener("DOMContentLoaded", function() {
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendButton = document.getElementById("send-button");

    sendButton.addEventListener("click", () => {
        const userMessage = userInput.value;
        if (!userMessage) return;

        // Display user message
        chatBox.innerHTML += `<div class="message user-message">${userMessage}</div>`;

        // Send user message to the server
        fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `user_input=${userMessage}`,
        })
        .then(response => response.json())
        .then(data => {
            const botResponse = data.bot_response;
            // Display bot response
            chatBox.innerHTML += `<div class="message bot-message">${botResponse}</div>`;
        });

        // Clear the input field
        userInput.value = "";
    });
});