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
                if (confirm('Are you sure you want to delete this chat?')) {
                    try {
                        const response = await fetch('/delete_chat', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/x-www-form-urlencoded',
                            },
                            body: `filename=${encodeURIComponent(filename)}`
                        });
                        if (!response.ok) {
                            console.error('Error deleting chat:', response.status);
                            return;
                        }
                        const data = await response.json();
                        if (data.success) {
                            await updatePreviousChats(); // Reload the list of chats
                            clearChatDisplay(); // Optionally clear the chat area
                        } else {
                            console.error('Error deleting chat:', data.error);
                            alert('Failed to delete chat.');
                        }
                    } catch (error) {
                        console.error('Fetch error deleting chat:', error);
                        alert('An error occurred while deleting the chat.');
                    }
                }
            });
        });

        const copyButtons = document.querySelectorAll('.copy-button, .copy-answer-btn');
        copyButtons.forEach(button => {
            button.addEventListener('click', function() {
                let textToCopy = '';
                if (this.dataset.code) {
                    textToCopy = decodeURIComponent(this.dataset.code);
                } else if (this.dataset.text) {
                    textToCopy = this.dataset.text;
                }

                console.log('Attempting to copy:', textToCopy); // Keep this for debugging

                if (navigator.clipboard && navigator.clipboard.writeText) {
                    navigator.clipboard.writeText(textToCopy)
                        .then(() => {
                            console.log('Text copied to clipboard successfully!');
                            this.textContent = 'Copied!'; // Simple visual feedback
                            setTimeout(() => {
                                this.innerHTML = '<i class="fas fa-copy"></i> Copy'; // Revert text
                            }, 1500);
                        })
                        .catch(err => {
                            console.error('Failed to copy text: ', err);
                            this.textContent = 'Error'; // Indicate an error
                            setTimeout(() => {
                                this.innerHTML = '<i class="fas fa-copy"></i> Copy'; // Revert text
                            }, 1500);
                        });
                } else {
                    console.error('Clipboard API not available in this browser.');
                    alert('Clipboard API not available. Please copy manually.');
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
            messageDiv.innerHTML = `
                <div class="user-message">
                    <div class="avatar"><i class="fas fa-user"></i></div>
                    ${userContent}
                </div>
            `;
        } else if (sender === 'ai') {
            let formattedMessage = message;
            formattedMessage = formattedMessage.replace(/<div class="code-block"><pre><code class="([^"]*)">([\s\S]*?)<\/code><\/pre><\/div>/g, (match, language, code) => {
                constescapedCode = code.replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&amp;/g, '&');
                return `
                    <div class="code-block">
                        <pre><code class="${language}">${code}</code></pre>
                        <button class="copy-button" data-code="${encodeURIComponent(escapedCode)}"><i class="fas fa-copy"></i> Copy</button>
                    </div>
                `;
            });
            console.log("Raw AI Message:", message);
            messageDiv.innerHTML = `
                <div class="ai-message">
                    <div class="avatar"><i class="fas fa-robot"></i></div>
                    <div class="content">${formattedMessage}</div>
                    <div class="copy-button-container">
                        <button class="copy-answer-btn" data-text="${message.replace(/<[^>]*>?/gm, '').trim()}"><i class="fas fa-copy"></i> Copy</button>
                    </div>
                </div>
            `;
            // Attach event listeners IMMEDIATELY after the buttons are added to the DOM
            const copyButtons = messageDiv.querySelectorAll('.copy-button, .copy-answer-btn');
            copyButtons.forEach(button => {
                button.addEventListener('click', function() {
                    let textToCopy = '';
                    if (this.dataset.code) {
                        textToCopy = decodeURIComponent(this.dataset.code);
                    } else if (this.dataset.text) {
                        textToCopy = this.dataset.text;
                    }

                    console.log('Attempting to copy (inline):', textToCopy);

                    if (navigator.clipboard && navigator.clipboard.writeText) {
                        navigator.clipboard.writeText(textToCopy)
                            .then(() => {
                                console.log('Text copied to clipboard successfully! (inline)');
                                this.textContent = 'Copied!';
                                setTimeout(() => {
                                    this.innerHTML = '<i class="fas fa-copy"></i> Copy';
                                }, 1500);
                            })
                            .catch(err => {
                                console.error('Failed to copy text (inline): ', err);
                                this.textContent = 'Error';
                                setTimeout(() => {
                                    this.innerHTML = '<i class="fas fa-copy"></i> Copy';
                                }, 1500);
                            });
                    } else {
                        console.error('Clipboard API not available in this browser. (inline)');
                        alert('Clipboard API not available. Please copy manually.');
                    }
                });
            });
        }
        chatContainer.appendChild(messageDiv);
        // We are now attaching the listeners directly, so no need for a separate call here
        // attachCopyEventListeners();
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
                            // Attach listeners after loading previous chat messages as well
                            const copyButtons = messageDiv.querySelectorAll('.copy-button, .copy-answer-btn');
                            copyButtons.forEach(button => {
                                button.addEventListener('click', function() {
                                    let textToCopy = '';
                                    if (this.dataset.code) {
                                        textToCopy = decodeURIComponent(this.dataset.code);
                                    } else if (this.dataset.text) {
                                        textToCopy = this.dataset.text;
                                    }

                                    console.log('Attempting to copy (load chat):', textToCopy);

                                    if (navigator.clipboard && navigator.clipboard.writeText) {
                                        navigator.clipboard.writeText(textToCopy)
                                            .then(() => {
                                                console.log('Text copied to clipboard successfully! (load chat)');
                                                this.textContent = 'Copied!';
                                                setTimeout(() => {
                                                    this.innerHTML = '<i class="fas fa-copy"></i> Copy';
                                                }, 1500);
                                            })
                                            .catch(err => {
                                                console.error('Failed to copy text (load chat): ', err);
                                                this.textContent = 'Error';
                                                setTimeout(() => {
                                                    this.innerHTML = '<i class="fas fa-copy"></i> Copy';
                                                }, 1500);
                                            });
                                    } else {
                                        console.error('Clipboard API not available in this browser. (load chat)');
                                        alert('Clipboard API not available. Please copy manually.');
                                    }
                                });
                            });
                        });
                        document.querySelectorAll('pre code').forEach((block) => {
                            hljs.highlightElement(block);
                        });
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                        // No need for separate attachCopyEventListeners here now
                    } else {
                        console.error('Error loading chat:', data.error);
                    }
                } catch (error) {
                    console.error('Fetch error loading chat:', error);
                }
            }
        });
    }

    updatePreviousChats(); // Initial load of previous chats
});
