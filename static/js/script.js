document.addEventListener('DOMContentLoaded', function() {
    const newChatBtn = document.getElementById('newChatBtn');
    const chatContainer = document.getElementById('chatContainer');
    const queryForm = document.getElementById('queryForm');
    const queryInput = document.getElementById('queryInput');
    const submitBtn = document.getElementById('submitBtn');
    const previousChatsList = document.getElementById('previousChatsList');

    function clearChatDisplay() {
        chatContainer.innerHTML = '';
    }

    async function updatePreviousChats() {
        try {
            const response = await fetch('/get_last_day_chats');
            if (!response.ok) {
                console.error('Error fetching previous chats:', response.status);
                return;
            }
            const chats = await response.json();
            previousChatsList.innerHTML = ''; // Clear the current list
            if (chats.length > 0) {
                chats.forEach(chat => {
                    const li = document.createElement('li');
                    li.dataset.filename = chat.filename;
                    li.className = 'previous-chat-item';
                    li.innerHTML = `${chat.summary} <span class="chat-time">(${chat.timestamp})</span>`;
                    const deleteButton = document.createElement('button');
                    deleteButton.className = 'delete-chat-btn';
                    deleteButton.dataset.filename = chat.filename;
                    deleteButton.innerHTML = '<i class="fas fa-trash-alt"></i>';
                    li.appendChild(deleteButton);
                    previousChatsList.appendChild(li);
                });
            } else {
                const li = document.createElement('li');
                li.textContent = 'No recent chats';
                previousChatsList.appendChild(li);
            }
            attachDeleteChatListeners(); // Attach listeners after updating the list
        } catch (error) {
            console.error('Error updating previous chats:', error);
        }
    }

    function attachDeleteChatListeners() {
        const deleteButtons = document.querySelectorAll('.delete-chat-btn');
        deleteButtons.forEach(button => {
            button.addEventListener('click', async function(event) {
                event.stopPropagation(); // Prevent loading the chat when delete is clicked
                const filename = this.dataset.filename;
                if (confirm(`Are you sure you want to delete chat "${filename}"?`)) {
                    try {
                        const response = await fetch('/delete_chat', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/x-www-form-urlencoded',
                            },
                            body: `filename=${encodeURIComponent(filename)}`
                        });
                        if (!response.ok) {
                            console.error('Error deleting chat:', response.status, await response.text());
                            return;
                        }
                        const data = await response.json();
                        if (data.success) {
                            await updatePreviousChats(); // Refresh the list after deletion
                        } else {
                            console.error('Error deleting chat:', data.error);
                            alert(`Error deleting chat: ${data.error}`);
                        }
                    } catch (error) {
                        console.error('Fetch error deleting chat:', error);
                        alert('Failed to delete chat.');
                    }
                }
            });
        });
    }

    newChatBtn.addEventListener('click', async function() {
        clearChatDisplay();
        queryInput.value = '';
        queryInput.focus();

        try {
            const response = await fetch('/new_chat', { method: 'POST' });
            if (!response.ok) {
                console.error('Error starting new chat:', response.status);
            }
            const data = await response.json();
            if (data.success) {
                await updatePreviousChats(); // Fetch and update the previous chats list
            }
        } catch (error) {
            console.error('Error communicating new chat to backend:', error);
        }
    });

    queryForm.addEventListener('submit', async function(event) {
        event.preventDefault();
        const query = queryInput.value.trim();
        if (query) {
            appendMessage('user', query, true); // Indicate it's the user's initial message
            queryInput.value = '';
            submitBtn.disabled = true;
            queryInput.disabled = true;
            chatContainer.scrollTop = chatContainer.scrollHeight;

            try {
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `query=${encodeURIComponent(query)}`
                });

                if (!response.ok) {
                    console.error('API error:', response.status);
                    appendMessage('ai', 'Error communicating with the AI.');
                    return;
                }

                const data = await response.json();
                if (data.is_error) {
                    appendMessage('ai', data.error);
                } else {
                    appendMessage('ai', data.response);
                }
            } catch (error) {
                console.error('Fetch error:', error);
                appendMessage('ai', 'An error occurred while processing your request.');
            } finally {
                submitBtn.disabled = false;
                queryInput.disabled = false;
                queryInput.focus();
                document.querySelectorAll('pre code').forEach((block) => {
                    hljs.highlightElement(block);
                });
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }
    });

    function appendMessage(sender, message, isUserInitial = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message';
        let contentDiv;
        let actionsDiv = '';

        if (sender === 'user') {
            actionsDiv = `
                <div class="message-actions">
                    <button class="edit-button" data-message-type="user"
