document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('queryForm');
    const input = document.getElementById('queryInput');
    const chatContainer = document.getElementById('chatContainer');
    const submitBtn = document.getElementById('submitBtn');

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        const query = input.value.trim();
        if (!query) return;

        // Add user message to chat
        addMessage(query, 'user');
        input.value = '';

        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending';

        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `query=${encodeURIComponent(query)}`
            });

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            addMessage(data.response, 'ai', data.is_error);
        } catch (error) {
            addMessage(`Error: ${error.message}`, 'ai', true);
        } finally {
            // Reset button state
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Send';

            // Scroll to bottom
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    });

    // Add click handlers for suggestion buttons
    document.querySelectorAll('.suggestion-btn').forEach(button => {
        button.addEventListener('click', function() {
            input.value = this.textContent;
            input.focus();
        });
    });

    // Function to add a message to the chat
    function addMessage(content, sender, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isError ? 'error' : ''}`;

        if (sender === 'user') {
            messageDiv.innerHTML = `
                <div class="user-message">
                    <div class="avatar"><i class="fas fa-user"></i></div>
                    <div class="content">${content}</div>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="ai-message">
                    <div class="avatar"><i class="fas fa-robot"></i></div>
                    <div class="content">${content}</div>
                </div>
            `;
        }

        chatContainer.appendChild(messageDiv);

        // Highlight any code blocks
        document.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });

        // Scroll to the new message
        messageDiv.scrollIntoView({ behavior: 'smooth' });
    }

    // Auto-focus input on page load
    input.focus();
});
