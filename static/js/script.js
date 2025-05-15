document.addEventListener('DOMContentLoaded', function() {
    const newChatBtn = document.getElementById('newChatBtn');
    const chatContainer = document.getElementById('chatContainer');
    const queryForm = document.getElementById('queryForm');
    const queryInput = document.getElementById('queryInput');
    const submitBtn = document.getElementById('submitBtn');
    const previousChatsList = document.getElementById('previousChatsList');
    const themeToggle = document.getElementById('themeToggle');

    // Theme toggle functionality
    function initializeTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        themeToggle.checked = savedTheme === 'dark';
        updateCodeHighlightTheme(savedTheme);
    }

    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateCodeHighlightTheme(newTheme);
    }

    function updateCodeHighlightTheme(theme) {
        // Remove all highlight.js styles
        document.querySelectorAll('link[rel="stylesheet"][href*="highlight.js"]').forEach(link => {
            link.disabled = true;
            link.parentNode.removeChild(link);
        });

        // Add the appropriate theme
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = `https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/${theme === 'dark' ? 'github-dark' : 'github'}.min.css`;
        document.head.appendChild(link);

        // Re-highlight all code blocks
        document.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }

    if (themeToggle) {
        initializeTheme();
        themeToggle.addEventListener('change', toggleTheme);
    }

    // Rest of your existing code...
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
            previousChatsList.innerHTML = '';
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
                await updatePreviousChats();
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
        
        if (sender === 'user') {
            messageDiv.innerHTML = `
                <div class="user-message">
                    <div class="message-content">${message}</div>
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
                    <div class="ai-avatar"><i class="fas fa-robot"></i></div>
                    <div class="message-content">${formattedMessage}</div>
                </div>
            `;
        }
        chatContainer.appendChild(messageDiv);
        attachCopyEventListeners();
    }

    function attachCopyEventListeners() {
        const copyButtons = document.querySelectorAll('.copy-button');
        copyButtons.forEach(button => {
            button.addEventListener('click', function() {
                const code = decodeURIComponent(this.dataset.code);
                navigator.clipboard.writeText(code)
                    .then(() => {
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
                            await updatePreviousChats();
                            clearChatDisplay();
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
                            const aiDiv = document.createElement('div');
                            aiDiv.className = 'message';
                            aiDiv.innerHTML = `
                                <div class="ai-message">
                                    <div class="ai-avatar"><i class="fas fa-robot"></i></div>
                                    <div class="message-content">${item.response}</div>
                                </div>
                            `;
                            chatContainer.appendChild(aiDiv);

                            const userDiv = document.createElement('div');
                            userDiv.className = 'message';
                            userDiv.innerHTML = `
                                <div class="user-message">
                                    <div class="message-content">${item.query}</div>
                                </div>
                            `;
                            chatContainer.appendChild(userDiv);
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

    updatePreviousChats();
});
