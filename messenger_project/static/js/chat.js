let chatSocket;
let lastMessageDate = '';

// Функция для инициализации соединения WebSocket
function initializeChat(chatType, roomName, username) {
    console.log("Инициализация чата:", chatType, roomName, username);
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsURL = `${protocol}://${window.location.host}/ws/chat/${chatType}/${roomName}/`;

    if (!chatSocket || chatSocket.readyState === WebSocket.CLOSED) {
        chatSocket = new WebSocket(wsURL);

        chatSocket.onopen = function() {
            updateConnectionStatus('CONNECTED');
            sendSystemMessage(`${username} присоединился к чату.`);
        };

        chatSocket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            console.log("Данные, полученные от сервера:", data);
            const isSystemMessage = data.username === 'System';
            const userId = data.user_id || currentUserId; 
            addMessageToChat(data.username, data.message, data.timestamp, isSystemMessage, userId);
        };

        chatSocket.onclose = function() {
            console.log('WebSocket закрыт');
            updateConnectionStatus('DISCONNECTED');
            sendSystemMessage(`${username} покинул чат.`);
            document.getElementById('open-button').disabled = false;
        };

        chatSocket.onerror = function(error) {
            console.error('Ошибка WebSocket:', error);
            updateConnectionStatus('ERROR: ошибка WebSocket');
        };
    }
}

// Функция для обновления статуса соединения
function updateConnectionStatus(status) {
    const statusElement = document.getElementById('connection-status');
    if (statusElement) {
        statusElement.innerText = status;
        statusElement.className = ''; // Сбрасываем классы статуса
        if (status === 'CONNECTED') {
            statusElement.classList.add('text-success');
        } else if (status === 'DISCONNECTED') {
            statusElement.classList.add('text-danger');
        } else if (status.startsWith('ERROR')) {
            statusElement.classList.add('text-warning');
        }
    }
}

// Функция для добавления сообщения в лог чата
function addMessageToChat(username, message, timestamp, isSystemMessage = false, userId = null) {
    const chatLog = document.getElementById('chat-log');
    const currentUserAvatar = document.getElementById('current-user-avatar').value || '/static/default_avatar.png';
    const chatType = document.getElementById('chat-type').value;
    const currentUserId = document.getElementById('current-user-id').value;

    let avatarPath;
    if (chatType === "private") {
        const otherUserAvatar = document.getElementById('other-user-avatar').value || '/static/default_avatar.png';
        avatarPath = userId == currentUserId ? currentUserAvatar : otherUserAvatar;
    } else {
        const userAvatarsJson = document.getElementById('user-avatars-json') ? document.getElementById('user-avatars-json').value : '{}';
        let userAvatars;
        try {
            userAvatars = JSON.parse(userAvatarsJson);
        } catch (e) {
            console.error("Ошибка при парсинге JSON с аватарами:", e);
            userAvatars = {};
        }
        avatarPath = userId == currentUserId ? currentUserAvatar : (userAvatars[userId] || '/static/default_avatar.png');
    }

    const currentDate = new Date(timestamp).toLocaleDateString();
    if (currentDate !== lastMessageDate) {
        const dateSeparator = document.createElement('div');
        dateSeparator.className = 'date-separator';
        dateSeparator.innerText = currentDate;
        chatLog.appendChild(dateSeparator);
        lastMessageDate = currentDate;
    }

    const messageElement = document.createElement('div');

    if (isSystemMessage) {
        messageElement.innerHTML = `
            <div class="system-message" style="text-align: center; font-style: italic;">
                ${escapeHTML(message || "Системное сообщение не указано")}
            </div>
        `;
    } else {
        const safeMessage = message !== undefined && message !== null ? message : "Сообщение недоступно";
        messageElement.innerHTML = `
            <div class="message">
                <div class="avatar">
                    <img class="avatar-image" src="${avatarPath}" alt="avatar" />
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <strong>${escapeHTML(username)}</strong>
                        <span class="message-timestamp">${new Date(timestamp).toLocaleTimeString()}</span>
                    </div>
                    <div class="message-body">${escapeHTML(safeMessage)}</div>
                </div>
            </div>
        `;
    }

    chatLog.appendChild(messageElement);
    chatLog.scrollTop = chatLog.scrollHeight; // Прокрутка вниз
}

// Привязка событий к форме и кнопкам
document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const openButton = document.getElementById('open-button');
    const closeButton = document.getElementById('close-button');
    
    const chatId = document.getElementById('chat-id').value; 
    loadPreviousMessages(chatId);

    chatForm.onsubmit = function(event) {
        event.preventDefault();
        const messageInput = document.getElementById('chat-message-input');
        const message = messageInput.value;
        const username = document.getElementById('username').value;

        if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
            chatSocket.send(JSON.stringify({
                'message': message,
                'username': username,
                'user_id': currentUserId 
            }));
            messageInput.value = '';
        } else {
            alert('Соединение не открыто. Пожалуйста, откройте соединение.');
        }
    };

    openButton.addEventListener('click', function() {
        const chatType = document.getElementById('chat-type').value;
        const roomName = document.getElementById('room-name').value;
        const username = document.getElementById('username').value;

        if (!chatSocket || chatSocket.readyState === WebSocket.CLOSED) {
            initializeChat(chatType, roomName, username);
            openButton.disabled = true;
        }
    });

    closeButton.addEventListener('click', function() {
        closeConnection();
    });
});

// Функция для закрытия соединения WebSocket
function closeConnection() {
    if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.close();
        sendSystemMessage('Соединение закрыто.');
    }
}

// Функция для отправки системного сообщения
function sendSystemMessage(message) {
    console.log("Отправка системного сообщения:", message);
    const username = 'System';
    const timestamp = new Date().toISOString();

    if (chatSocket && chatSocket.readyState === WebSocket.OPEN) {
        chatSocket.send(JSON.stringify({
            'message': message,
            'username': username,
            'timestamp': timestamp,
            'isSystemMessage': true
        }));
    } else {
        addMessageToChat(username, message, timestamp, true);
    }
}

// Функция загрузки предыдущих сообщений
function loadPreviousMessages(chatId) {
    if (!chatId) {
        console.warn("Отсутствует chatId. Пропускаем загрузку предыдущих сообщений.");
        return;
    }

    console.log("Загружаем сообщения для chat_id:", chatId);
    
    fetch(`/api/get_previous_messages?chat_id=${chatId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка загрузки предыдущих сообщений: ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            console.log("Сообщения, полученные с сервера:", data);
            data.forEach(message => {
                addMessageToChat(
                    message.sender.username,
                    message.content,
                    message.timestamp,
                    false,
                    message.sender.id 
                );
            });
        })
        .catch(error => console.error('Ошибка загрузки сообщений:', error));
}

// Экранирование HTML для защиты от XSS
function escapeHTML(unsafe) {
    if (unsafe === undefined || unsafe === null) {
        return "";
    }
    return unsafe.replace(/[&<>"']/g, function(match) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return map[match];
    });
}