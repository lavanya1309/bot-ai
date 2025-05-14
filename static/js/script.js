// static/js/script.js
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
                attachDeleteEventListeners(); // Attach listeners after updating the list
            } catch (error) {
                console.error('Error updating previous chats:', error);
            }
        }

        function attachDeleteEventListeners() {
            const deleteButtons = document.querySelectorAll('.delete-chat-btn');
            deleteButtons.forEach(button => {
                button.addEventListener('click', async function(event) {
                    event.stopPropagation(); // Prevent loading the chat when delete is clicked
                    const filename = this.dataset.filename;
                    if (confirm(`Are you sure you want to delete chat: ${filename}?`)) {
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
                                alert('Error deleting chat.');
                                return;
                            }
                            const data = await response.json();
                            if (data.success) {
                                await updatePreviousChats(); // Refresh the list after deletion
                            } else {
                                alert(data.error);
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
                appendMessage('user', query);
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

        function appendMessage(sender, message) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message';
            let contentDiv;
            if (sender === 'user') {
                const userContent = `<div class="content">${message}</div>`;
                const editButton = `<div class="edit-button-container"><button class="edit-button" data-message-type="user" data-message-text="${encodeURIComponent(message)}"><i class="fas fa-edit"></i></button></div>`;
                messageDiv.innerHTML = `
                    <div class="user-message">
                        <div class="avatar"><i class="fas fa-user"></i></div>
                        ${userContent}
                        ${editButton}
                    </div>
                `;
            } else if (sender === 'ai') {
                let formattedMessage = message;
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
                        <div class="copy-button-container">
                            <button class="copy-answer-btn" data-text="${message.replace(/<[^>]*>?/gm, '').trim()}"><i class="fas fa-copy"></i> Copy</button>
                        </div>
                    </div>
                `;
            }
            chatContainer.appendChild(messageDiv);
            attachCopyEventListeners();
            attachEditEventListeners();
        }

        function attachCopyEventListeners() {
            const copyButtons = document.querySelectorAll('.copy-button, .copy-answer-btn');
            copyButtons.forEach(button => {
                button.addEventListener('click', function() {
                    const textToCopy = this.dataset.code ? decodeURIComponent(this.dataset.code) : this.dataset.text;
                    const originalText = this.innerHTML;
                    navigator.clipboard.writeText(textToCopy)
                        .then(() => {
                            this.innerHTML = 'Copied!';
                            setTimeout(() => {
                                this.innerHTML = originalText;
                            }, 1500);
                        })
                        .catch(err => {
                            console.error('Failed to copy text: ', err);
                            this.textContent = 'Error';
                            setTimeout(() => {
                                this.innerHTML = originalText;
                            }, 1500);
                        });
                });
            });
        }

        function attachEditEventListeners() {
            const editButtons = document.querySelectorAll('.edit-button');
            editButtons.forEach(button => {
                button.addEventListener('click', function() {
                    const messageDiv = this.closest('.message');
                    const contentDiv = messageDiv.querySelector('.user-message .content');
                    const originalText = decodeURIComponent(this.dataset.messageText);
                    contentDiv.innerHTML = `
                        <textarea class="edit-textarea">${originalText}</textarea>
                        <div class="edit-controls">
                            <button class="save-edit-btn">Save</button>
                            <button class="cancel-edit-btn">Cancel</button>
                        </div>
                    `;
                    const textarea = contentDiv.querySelector('.edit-textarea');
                    textarea.focus();

                    const saveButton = contentDiv.querySelector('.save-edit-btn');
                    const cancelButton = contentDiv.querySelector('.cancel-edit-btn');

                    saveButton.addEventListener('click', function() {
                        const newText = textarea.value.trim();
                        if (newText) {
                            contentDiv.innerHTML = newText + `<div class="edit-button-container"><button class="edit-button" data-message-type="user" data-message-text="${encodeURIComponent(newText)}"><i class="fas fa-edit"></i></button></div>`;
                            // Optionally, you might want to resend the edited query to the bot
                        } else {
                            contentDiv.innerHTML = originalText + `<div class="edit-button-container"><button class="edit-button" data-message-type="user" data-message-text="${encodeURIComponent(originalText)}"><i class="fas fa-edit"></i></button></div>`;
                        }
                        attachEditEventListeners(); // Re-attach listeners after editing
                    });

                    cancelButton.addEventListener('click', function() {
                        contentDiv.innerHTML = originalText + `<div class="edit-button-container"><button class="edit-button" data-message-type="user" data-message-text="${encodeURIComponent(originalText)}"><i class="fas fa-edit"></i></button></div>`;
                        attachEditEventListeners(); // Re-attach listeners after canceling
                    });
                });
            });
        }

        if (previousChatsList) {
            previousChatsList.addEventListener('click', async function(event) {
                const listItem = event.target.closest('.previous-chat-item');
                if (listItem && !event.target.classList.contains('delete-chat-btn') && !event.target.closest('.delete-chat-btn')) {
                    const filename = listItem.dataset.filename;
                    try {
                        const response = await fetch('/load_chat', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/x-www-form-urlencoded',
                            },
                            body: `filename=${encodeURIComponent(filename)}`
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
                                        <div class="edit-button-container">
                                            <button class="edit-button" data-message-type="user" data-message-text="${encodeURIComponent(item.query)}"><i class="fas fa-edit"></i></button>
                                        </div>
                                    </div>
                                    <div class="ai-message">
                                        <div class="avatar"><i class="fas fa-robot"></i></div>
                                        <div class="content">${item.response}</div>
                                        <div class="copy-button-container">
                                            <button class="copy-answer-btn" data-text="${item.response.replace(/<[^>]*>?/gm, '').trim()}"><i class="fas fa-copy"></i> Copy</button>
                                        </div>
                                    </div>
                                `;
                                chatContainer.appendChild(messageDiv);
                            });
                            document.querySelectorAll('pre code').forEach((block) => {
                                hljs.highlightElement(block);
                            });
                            chatContainer.scrollTop = chatContainer.scrollHeight;
                            attachCopyEventListeners();
                            attachEditEventListeners();
                        } else {
                            console.error('Error loading chat:', data.error);
                        }
                    } catch (error) {
                        console.error('Fetch error loading chat:', error);
                    }
                }
            });
        }

        attachDeleteEventListeners(); // Initial attachment for delete buttons
        // Initial load of previous chats is handled by the template
    });
