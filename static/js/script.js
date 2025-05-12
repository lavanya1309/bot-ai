document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('queryForm');
    const input = document.getElementById('queryInput');
    const chatContainer = document.getElementById('chatContainer');
    const submitBtn = document.getElementById('submitBtn');
    const newChatBtn = document.getElementById('newChatBtn'); // Get the new button

    // Function to add a message to the chat
    function addMessage(content, sender, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isError ? 'error' : ''}`;

        let messageContent = '';
        if (sender === 'user') {
            messageContent = `
                <div class="user-message">
                    <div class="avatar"><i class="fas fa-user"></i></div>
                    <div class="content">${content}</div>
                </div>
            `;
        } else {
            messageContent = `
                <div class="ai-message">
                    <div class="avatar"><i class="fas fa-robot"></i></div>
                    <div class="content">${content}</div>
                </div>
            `;
        }
        messageDiv.innerHTML = messageContent;
        chatContainer.appendChild(messageDiv);

        // Highlight any code blocks
        document.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });

        // Scroll to the new message
        messageDiv.scrollIntoView({ behavior: 'smooth' });
    }

    // Handle form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        const query = input.value.trim();
        if (!query) return;

        addMessage(query, 'user');
        input.value = '';

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

            if (!response.ok) {
                const errorText = await response.text();
                console.error('Fetch error:', response.status, errorText);
                addMessage(`Error: Failed to fetch (${response.status} - ${errorText})`, 'ai', true);
                return;
            }

            const data = await response.json();
            console.log('Response Data:', data); // Debugging

            if (data.error) {
                console.error('Backend error:', data.error);
                addMessage(`Error: ${data.error}`, 'ai', true);
                return;
            }

            if (data && data.response) {
                addMessage(data.response, 'ai', data.is_error);
            } else {
                console.error('Invalid response format:', data);
                addMessage('Error: Invalid response from AI', 'ai', true);
            }

        } catch (error) {
            console.error('Fetch error:', error);
            addMessage(`Error: ${error.message}`, 'ai', true);
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Send';
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    });

    // Handle "New Chat" button click
    newChatBtn.addEventListener('click', function() {
        chatContainer.innerHTML = '';
        input.value = '';
        chatContainer.scrollTop = 0;

        fetch('/new_chat', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                console.log('New chat acknowledged by backend:', data);
            })
            .catch(error => {
                console.error('Error clearing backend chat:', error);
            });
    });

    // Add click handlers for suggestion buttons
    document.querySelectorAll('.suggestion-btn').forEach(button => {
        button.addEventListener('click', function() {
            input.value = this.textContent;
            input.focus();
        });
    });

    // Auto-focus input on page load
    input.focus();
});
