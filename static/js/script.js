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
                    li.innerHTML = `${chat.summary} <span class="chat-time">(${chat.timestamp})</span>
                                    <button class="delete-chat-btn" data-filename="${chat.filename}">
                                        <i class="fas fa-trash-alt"></i> Delete
                                    </button>`;
                    previousChatsList.appendChild(li);
                });
            } else {
                const li = document.createElement('li');
                li.textContent = 'No recent chats';
                previousChatsList.appendChild(li);
            }
        } catch (error) {
            console.error('Error updating previous chats:', error);
        }
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
            console.log("User query submitted:", query); // Debugging line
            appendMessage('user', query);
            queryInput.value = '';
            submitBtn.disabled = true;
            queryInput.disabled = true;
            chatContainer.scrollTop = chatContainer.scrollHeight;

            try {
                console.log("Sending query to /ask..."); // Debugging line
                const response = await fetch('/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `query=${encodeURIComponent(query)}`
                });

                console.log("Response received from /ask:", response); // Debugging line

                if (!response.ok) {
                    console.error('API error:', response.status);
                    const errorText = await response.text();
                    console.error('API error text:', errorText);
                    appendMessage('ai', `Error communicating with the AI: ${response.status} - ${errorText}`);
                    return;
                }

                const data = await response.json();
                console.log("JSON data from /ask:", data); // Debugging line

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

    function appendMessage(sender, message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message';
        let contentDiv;
        if (sender === 'user') {
            messageDiv.innerHTML = `
                <div class="user-message">
                    <div class="avatar"><i class="fas fa-user"></i></div>
                    <div class="content">${message}</div>
                </div>
            `;
        } else if (sender === 'ai') {
            let formattedMessage = message;
            // Find all code blocks and add a copy button
            formattedMessage = formattedMessage.replace(/<div class="code-block"><pre><code class="([^"]*)">([\s\S]*?)<\/code><\/pre><\/div>/g, (match, language, code) => {
                const escapedCode = code.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
                return `
                    <div class="code-block">
                        <pre><code class="${language}">${code}</code></pre>
                        <button class="copy-button" data-code="${encodeURIComponent(escapedCode)}"><i class="fas fa-copy"></i> Copy</button>
                    </div>
                `;
            });
            messageDiv.innerHTML = `
                <div class="ai-message">
                    <div class="avatar"><i class="fas fa-robot"></i></div>
                    <div class="content">${formattedMessage}</div>
                </div>
            `;
        }
        chatContainer.appendChild(messageDiv);
        // After appending the message, attach event listeners to the new copy buttons
        attachCopyEventListeners();
    }

    function attachCopyEventListeners() {
        const copyButtons = document.querySelectorAll('.copy-button');
        copyButtons.forEach(button => {
            button.addEventListener('click', function() {
                const code = decodeURIComponent(this.dataset.code);
                navigator.clipboard.writeText(code)
                    .then(() => {
                        // Optional: Provide visual feedback (e.g., change button text briefly)
                        this.textContent = 'Copied!';
                        setTimeout(() => {
                            this.innerHTML = '<i class="fas fa-copy"></i> Copy';
                        }, 1500);
                    })
                    .catch(err => {
                        console.error('Failed to copy text: ', err);
                        this.textContent = 'Error';
                        setTimeout(() => {
                            this.innerHTML = '<i class="fas fa-copy"></i> Copy';
                        }, 1500);
                    });
            });
        });
    }

    if (previousChatsList) {
        previousChatsList.addEventListener('click', async function(event) {
            const loadItem = event.target.closest('.previous-chat-item');
            const deleteButton = event.target.closest('.delete-chat-btn');

            if (deleteButton) {
                const filenameToDelete = deleteButton.dataset.filename;
                if (confirm(`Are you sure you want to delete the chat: ${filenameToDelete}?`)) {
                    try {
                        const response = await fetch('/delete_chat', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/x-www-form-urlencoded',
                            },
                            body: `filename=${encodeURIComponent(filenameToDelete)}`
                        });
                        if (!response.ok) {
                            console.error('Error deleting chat:', response.status, await response.text());
                            alert('Error deleting chat.');
                            return;
                        }
                        const data = await response.json();
                        if (data.success) {
                            await updatePreviousChats(); // Reload the previous chats list
                            clearChatDisplay(); // Optionally clear the main chat area
                        } else {
                            console.error('Error deleting chat:', data.error);
                            alert(`Error deleting chat: ${data.error}`);
                        }
                    } catch (error) {
                        console.error('Fetch error deleting chat:', error);
                        alert('Failed to delete chat.');
                    }
                }
            } else if (loadItem) {
                const filenameToLoad = loadItem.dataset.filename;
                try {
                    const response = await fetch('/load_chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: `filename=${encodeURIComponent(filenameToLoad)}`
                    });
                    if (!response.ok) {
                        console.error('Error loading chat:', response.status, await response.text());
                        return;
                    }
                    const data = await response.json();
                    if (data.success) {
                        chatContainer.innerHTML = '';
                        data.conversation.forEach(item => {
                            const messageDiv = document.createElement('div');
                            messageDiv.className = 'message';
                            messageDiv.innerHTML = `
                                <div class="user-message">
                                    <div class="avatar"><i class="fas fa-user"></i></div>
                                    <div class="content">${item.query}</div>
                                </div>
                                <div class="ai-message">
                                    <div class="avatar"><i class="fas fa-robot"></i></div>
                                    <div class="content">${item.response}</div>
                                </div>
                            `;
                            chatContainer.appendChild(messageDiv);
                        });
                        document.querySelectorAll('pre code').forEach((block) => {
                            hljs.highlightElement(block);
                        });
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                    } else {
                        console.error('Error loading chat:', data.error);
                    }
                } catch (error) {
                    console.error('Fetch error loading chat:', error);
                }
            }
        });
    }

    // Initial load of previous chats
    updatePreviousChats();
});
