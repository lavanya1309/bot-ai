document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('queryForm');
    const input = document.getElementById('queryInput');
    const chatContainer = document.getElementById('chatContainer');
    const submitBtn = document.getElementById('submitBtn');
    const newChatBtn = document.getElementById('newChatBtn'); // Get the new button

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

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            addMessage(data.response, 'ai', data.is_error);
        } catch (error) {
            addMessage(`Error: ${error.message}`, 'ai', true);
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Send';
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    });

    // Handle "New Chat" button click
    newChatBtn.addEventListener('click', function() {
        // Clear the displayed chat messages
        chatContainer.innerHTML = '';

        // Optionally clear the input field
        input.value = '';

        // Potentially scroll to the top of the chat container
        chatContainer.scrollTop = 0;

        // --- Backend Consideration (Optional but Recommended) ---
        fetch('/new_chat', { method: 'POST' })
            .then(response => response.
