/**
 * Enhanced ChatApp - Hauptklasse für das erweiterte Chat-System
 * @class
 */
class EnhancedChatApp {
    constructor() {
        this.username = "Benutzer";
        this.ws = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.currentLang = localStorage.getItem('chat_lang') || 'de';
        this.currentTheme = localStorage.getItem('chat_theme') || 'light';
        this.messageCount = 0;
        this.userActivity = new Map();
        this.currentRoom = 'general';
        this.typingUsers = new Set();
        this.typingTimeout = null;
        this.onlineUsers = new Set();
        this.projects = [];
        this.tickets = [];
        this.files = [];
        
        console.log('🚀 Enhanced ChatApp initializing...');
        console.log(`🌐 Language: ${this.currentLang}, Theme: ${this.currentTheme}`);
        
        this.translations = {
            de: {
                title: "Enhanced Chat System - AI Powered Collaboration",
                welcome: "Willkommen im Enhanced Chat System! 🚀",
                usernamePlaceholder: "Dein Name",
                usernameButton: "Speichern",
                messagePlaceholder: "Schreibe eine Nachricht...",
                sendButton: "Senden",
                connecting: "Verbinde...",
                connected: "Verbunden",
                disconnected: "Getrennt",
                reconnecting: "Wiederverbinden...",
                nameChanged: (name) => `✅ Dein Name wurde auf "${name}" geändert`,
                userJoined: (name) => `👋 ${name} ist dem Chat beigetreten`,
                userLeft: (name) => `👋 ${name} hat den Chat verlassen`,
                serverConnected: "✅ Mit Chat-Server verbunden",
                serverLost: "❌ Verbindung verloren. Versuche erneut...",
                errorPrefix: "❌ Fehler: ",
                languageLabel: "🌐 Sprache",
                themeLabel: "🎨 Theme",
                messageCount: (count) => `📊 Nachrichten: ${count}`,
                userCount: (count) => `👥 Benutzer online: ${count}`,
                typing: "schreibt...",
                messageTooLong: "❌ Nachricht zu lang (max. 4000 Zeichen)",
                usernameTooLong: "❌ Benutzername zu lang (max. 50 Zeichen)",
                roomCreated: "✅ Raum erfolgreich erstellt",
                projectCreated: "✅ Projekt erfolgreich erstellt",
                ticketCreated: "✅ Ticket erfolgreich erstellt",
                fileUploaded: "✅ Datei erfolgreich hochgeladen",
                aiThinking: "🤖 Denkt nach...",
                aiResponse: "🤖 AI Assistant:"
            },
            en: {
                title: "Enhanced Chat System - AI Powered Collaboration",
                welcome: "Welcome to the Enhanced Chat System! 🚀",
                usernamePlaceholder: "Your name",
                usernameButton: "Save",
                messagePlaceholder: "Type a message...",
                sendButton: "Send",
                connecting: "Connecting...",
                connected: "Connected",
                disconnected: "Disconnected",
                reconnecting: "Reconnecting...",
                nameChanged: (name) => `✅ Your name has been changed to "${name}"`,
                userJoined: (name) => `👋 ${name} joined the chat`,
                userLeft: (name) => `👋 ${name} left the chat`,
                serverConnected: "✅ Connected to chat server",
                serverLost: "❌ Connection lost. Retrying...",
                errorPrefix: "❌ Error: ",
                languageLabel: "🌐 Language",
                themeLabel: "🎨 Theme",
                messageCount: (count) => `📊 Messages: ${count}`,
                userCount: (count) => `👥 Users online: ${count}`,
                typing: "is typing...",
                messageTooLong: "❌ Message too long (max 4000 characters)",
                usernameTooLong: "❌ Username too long (max 50 characters)",
                roomCreated: "✅ Room created successfully",
                projectCreated: "✅ Project created successfully",
                ticketCreated: "✅ Ticket created successfully",
                fileUploaded: "✅ File uploaded successfully",
                aiThinking: "🤖 Thinking...",
                aiResponse: "🤖 AI Assistant:"
            }
        };
        
        this.init();
    }

    /**
     * Initialisiert die erweiterte Chat-Anwendung
     */
    async init() {
        console.log('🔄 Enhanced ChatApp initializing UI components...');
        this.applyTheme(this.currentTheme, false);
        this.bindEvents();
        this.applyTranslations();
        this.connectWebSocket();
        this.updateUserStats();
        await this.loadInitialData();
        
        console.log('✅ Enhanced ChatApp initialization complete');
    }

    /**
     * Lädt initiale Daten
     */
    async loadInitialData() {
        try {
            console.log('📥 Loading initial data...');
            
            // Lade Projekte
            const projectsResponse = await this.apiCall('/api/projects?limit=10');
            if (projectsResponse) {
                this.projects = projectsResponse.items || [];
                this.updateProjectsBadge();
            }
            
            // Lade Tickets
            const ticketsResponse = await this.apiCall('/api/tickets?limit=10');
            if (ticketsResponse) {
                this.tickets = ticketsResponse.items || [];
                this.updateTicketsBadge();
            }
            
            // Lade Dateien
            const filesResponse = await this.apiCall('/api/files?limit=10');
            if (filesResponse) {
                this.files = filesResponse.items || [];
            }
            
            // Lade System-Info
            const systemInfo = await this.apiCall('/api/info');
            if (systemInfo) {
                console.log('ℹ️ System info loaded:', systemInfo);
            }
            
            console.log('✅ Initial data loaded successfully');
        } catch (error) {
            console.error('❌ Error loading initial data:', error);
        }
    }

    /**
     * Bindet Event-Listener an UI-Elemente
     */
    bindEvents() {
        console.log('🔗 Binding event listeners...');
        
        // Benutzer-Events
        document.getElementById('setUsernameBtn').addEventListener('click', () => this.setUsername());
        document.getElementById('usernameInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.setUsername();
        });
        
        // Nachrichten-Events
        document.getElementById('messageInput').addEventListener('keypress', (e) => this.handleKeyPress(e));
        document.getElementById('messageInput').addEventListener('input', (e) => this.handleTyping(e));
        document.getElementById('sendMessageBtn').addEventListener('click', () => this.sendMessage());
        
        // Navigation-Events
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => this.switchSection(e.target.closest('.nav-link').dataset.section));
        });
        
        // Raum-Events
        document.getElementById('addRoomBtn').addEventListener('click', () => this.showRoomModal());
        document.addEventListener('click', (e) => {
            if (e.target.closest('.room-item')) {
                this.switchRoom(e.target.closest('.room-item').dataset.room);
            }
        });
        
        // Sprache und Theme
        const languageSelect = document.getElementById('languageSelect');
        const themeSelect = document.getElementById('themeSelect');
        
        if (languageSelect) {
            languageSelect.value = this.currentLang;
            languageSelect.addEventListener('change', (e) => this.changeLanguage(e.target.value));
        }
        
        if (themeSelect) {
            themeSelect.value = this.currentTheme;
            themeSelect.addEventListener('change', (e) => this.applyTheme(e.target.value));
        }

        // Action-Buttons
        document.getElementById('fileUploadBtn').addEventListener('click', () => this.showUploadModal());
        document.getElementById('aiAssistantBtn').addEventListener('click', () => this.openAIAssistant());
        document.getElementById('emojiPickerBtn').addEventListener('click', () => this.toggleEmojiPicker());
        
        // Projekt- und Ticket-Buttons
        document.getElementById('createProjectBtn')?.addEventListener('click', () => this.showProjectModal());
        document.getElementById('createTicketBtn')?.addEventListener('click', () => this.showTicketModal());
        document.getElementById('uploadFileBtn')?.addEventListener('click', () => this.showUploadModal());
        
        // AI Assistant
        document.getElementById('sendAIMessageBtn')?.addEventListener('click', () => this.sendAIMessage());
        document.getElementById('aiMessageInput')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendAIMessage();
        });

        // Modal-Events
        document.querySelectorAll('.modal-close').forEach(closeBtn => {
            closeBtn.addEventListener('click', () => this.closeModals());
        });
        
        document.getElementById('modalOverlay').addEventListener('click', (e) => {
            if (e.target.id === 'modalOverlay') this.closeModals();
        });

        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                console.log('📱 Chat tab is now hidden');
            } else {
                console.log('📱 Chat tab is now visible');
                this.updateConnectionStatus();
            }
        });

        console.log('✅ Event listeners bound successfully');
    }

    /**
     * Übersetzungshilfe
     */
    t(key, ...args) {
        const langPack = this.translations[this.currentLang] || this.translations.de;
        const value = langPack[key];
        if (typeof value === 'function') {
            return value(...args);
        }
        return value || key;
    }

    /**
     * Wendet Übersetzungen auf die UI an
     */
    applyTranslations() {
        console.log(`🌐 Applying translations for language: ${this.currentLang}`);
        
        const elements = {
            'app-title': 'textContent',
            'welcomeMessage .message-content h3': 'textContent',
            'usernameInput': 'placeholder',
            'setUsernameBtn .button-text': 'textContent',
            'messageInput': 'placeholder',
            'sendMessageBtn .button-text': 'textContent',
            'languageLabel': 'textContent',
            'themeLabel': 'textContent',
            'chatTitle': 'textContent'
        };

        Object.entries(elements).forEach(([selector, prop]) => {
            const element = document.querySelector(selector);
            if (element) {
                const key = selector.split(' ').pop().replace(/[.#].*/, '');
                element[prop] = this.t(key);
            }
        });

        console.log('✅ Translations applied successfully');
    }

    /**
     * Ändert die Sprache
     */
    changeLanguage(lang) {
        console.log(`🔄 Changing language to: ${lang}`);
        this.currentLang = lang;
        localStorage.setItem('chat_lang', lang);
        this.applyTranslations();
        this.showNotification(`🌐 Sprache geändert zu ${lang}`);
        console.log(`✅ Language changed to: ${lang}`);
    }

    /**
     * Wendet das Theme an
     */
    applyTheme(theme, persist = true) {
        console.log(`🎨 Applying theme: ${theme}`);
        
        const body = document.body;
        body.classList.remove('theme-light', 'theme-dark', 'theme-contrast');
        
        if (theme === 'dark') {
            body.classList.add('theme-dark');
        } else if (theme === 'contrast') {
            body.classList.add('theme-contrast');
        } else {
            body.classList.add('theme-light');
        }
        
        this.currentTheme = theme;
        if (persist) {
            localStorage.setItem('chat_theme', theme);
            console.log(`💾 Theme saved to localStorage: ${theme}`);
        }
        
        console.log(`✅ Theme applied: ${theme}`);
    }

    /**
     * Wechselt zwischen Sektionen
     */
    switchSection(section) {
        console.log(`🔄 Switching to section: ${section}`);
        
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-section="${section}"]`).closest('.nav-item').classList.add('active');
        
        // Update content sections
        document.querySelectorAll('.content-section').forEach(sectionEl => {
            sectionEl.classList.remove('active');
        });
        document.getElementById(`${section}Section`).classList.add('active');
        
        // Section-specific initializations
        switch(section) {
            case 'projects':
                this.loadProjects();
                break;
            case 'tickets':
                this.loadTickets();
                break;
            case 'files':
                this.loadFiles();
                break;
            case 'ai':
                this.loadAIConversation();
                break;
            case 'analytics':
                this.loadAnalytics();
                break;
        }
        
        console.log(`✅ Switched to section: ${section}`);
    }

    /**
     * Wechselt den Raum
     */
    switchRoom(roomId) {
        console.log(`🔄 Switching to room: ${roomId}`);
        
        // Update room selection
        document.querySelectorAll('.room-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-room="${roomId}"]`).classList.add('active');
        
        this.currentRoom = roomId;
        
        // Update chat title
        document.getElementById('chatTitle').textContent = `${roomId.charAt(0).toUpperCase() + roomId.slice(1)} Chat`;
        
        // Load room messages
        this.loadRoomMessages(roomId);
        
        this.showNotification(`🗨️ Raum gewechselt zu: ${roomId}`);
        console.log(`✅ Switched to room: ${roomId}`);
    }

    /**
     * Setzt den Benutzernamen
     */
    setUsername() {
        const newUsername = document.getElementById('usernameInput').value.trim();
        console.log(`👤 Setting username to: ${newUsername}`);
        
        if (!newUsername) {
            this.showNotification(this.t('errorPrefix') + 'Benutzername darf nicht leer sein');
            return;
        }
        
        if (newUsername.length > 50) {
            this.showNotification(this.t('usernameTooLong'));
            return;
        }
        
        this.username = newUsername;
        document.getElementById('currentUsername').textContent = this.username;
        this.addSystemMessage(this.t('nameChanged', this.username));
        this.showNotification(`✅ Benutzername geändert zu: ${this.username}`);
        console.log(`✅ Username set to: ${this.username}`);
    }

    /**
     * Stellt WebSocket-Verbindung her
     */
    connectWebSocket() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('❌ Max reconnection attempts reached');
            this.showNotification('❌ Maximale Verbindungsversuche erreicht');
            return;
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        console.log(`🔌 Connecting to WebSocket: ${wsUrl}`);
        console.log(`🔄 Reconnect attempt: ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts}`);

        this.ws = new WebSocket(wsUrl);
        this.updateConnectionStatus('connecting');

        this.ws.onopen = () => {
            console.log('✅ WebSocket connection established');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.updateConnectionStatus('connected');
            this.addSystemMessage(this.t('serverConnected'));
            this.showNotification('✅ Mit Server verbunden');
            
            // Join current room
            this.joinRoom(this.currentRoom);
        };

        this.ws.onmessage = (event) => {
            console.log('📨 WebSocket message received:', event.data);
            try {
                const data = JSON.parse(event.data);
                this.handleIncomingMessage(data);
            } catch (error) {
                console.error('❌ Error parsing WebSocket message:', error);
            }
        };

        this.ws.onclose = (event) => {
            console.log('🔌 WebSocket connection closed:', event.code, event.reason);
            this.isConnected = false;
            this.updateConnectionStatus('disconnected');
            
            if (!event.wasClean) {
                this.reconnectAttempts++;
                const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
                console.log(`🔄 Reconnecting in ${delay}ms...`);
                this.addSystemMessage(this.t('serverLost'));
                setTimeout(() => this.connectWebSocket(), delay);
            }
        };

        this.ws.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
            this.isConnected = false;
            this.updateConnectionStatus('error');
            this.showNotification('❌ Verbindungsfehler');
        };
    }

    /**
     * Verarbeitet eingehende Nachrichten
     */
    handleIncomingMessage(data) {
        console.log(`📨 Processing message type: ${data.type}`, data);
        
        switch(data.type) {
            case 'chat_message':
                this.messageCount++;
                this.trackUserActivity(data.username);
                this.addChatMessage(data.username, data.message, data.timestamp, data.room);
                this.updateUserStats();
                break;
            case 'user_joined':
                this.addSystemMessage(this.t('userJoined', data.username));
                this.onlineUsers.add(data.username);
                this.updateOnlineUsers();
                this.showNotification(`👋 ${data.username} ist dem Chat beigetreten`);
                break;
            case 'user_left':
                this.addSystemMessage(this.t('userLeft', data.username));
                this.onlineUsers.delete(data.username);
                this.updateOnlineUsers();
                break;
            case 'user_typing':
                this.handleUserTyping(data.username, data.typing);
                break;
            case 'room_joined':
                this.addSystemMessage(`✅ Raum betreten: ${data.room}`);
                break;
            case 'room_created':
                this.addRoomToUI(data.room);
                this.showNotification(this.t('roomCreated'));
                break;
            case 'user_count':
                this.updateOnlineUsers(data.count);
                break;
            case 'ping':
                console.log('🏓 Ping received from server');
                if (this.isConnected) {
                    this.ws.send(JSON.stringify({
                        type: 'pong',
                        ping_id: data.ping_id,
                        timestamp: new Date().toISOString()
                    }));
                }
                break;
            case 'pong':
                console.log('🏓 Pong received from server');
                break;
            case 'error':
                console.error('❌ Server error:', data.message);
                this.addSystemMessage(this.t('errorPrefix') + data.message);
                this.showNotification(`❌ ${data.message}`);
                break;
            case 'ai_response':
                this.handleAIResponse(data);
                break;
            default:
                console.warn('⚠️ Unknown message type:', data.type);
        }
    }

    /**
     * Sendet eine Nachricht
     */
    sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();

        console.log(`📤 Preparing to send message: "${message.substring(0, 50)}..."`);

        if (!message) {
            console.warn('⚠️ Attempt to send empty message');
            return;
        }

        if (message.length > 4000) {
            this.showNotification(this.t('messageTooLong'));
            console.warn('❌ Message too long:', message.length);
            return;
        }

        if (this.isConnected) {
            const messageData = {
                type: 'chat_message',
                username: this.username,
                message: message,
                room: this.currentRoom,
                timestamp: new Date().toISOString()
            };

            this.ws.send(JSON.stringify(messageData));
            console.log('✅ Message sent successfully');
            messageInput.value = '';
            
            // Clear typing indicator
            this.clearTypingIndicator();
        } else {
            console.error('❌ Cannot send message - not connected');
            this.showNotification('❌ Nicht mit Server verbunden');
        }
    }

    /**
     * Handle-Tastendruck für Nachrichten
     */
    handleKeyPress(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.sendMessage();
        }
    }

    /**
     * Handle-Tippen für Typing-Indicator
     */
    handleTyping(event) {
        if (this.isConnected && event.target.value.length > 0) {
            this.sendTypingIndicator(true);
        } else {
            this.sendTypingIndicator(false);
        }
    }

    /**
     * Sendet Typing-Indicator
     */
    sendTypingIndicator(typing) {
        if (this.isConnected) {
            const typingData = {
                type: 'user_typing',
                username: this.username,
                typing: typing,
                room: this.currentRoom
            };
            this.ws.send(JSON.stringify(typingData));
        }
    }

    /**
     * Verarbeitet User-Typing
     */
    handleUserTyping(username, typing) {
        if (typing) {
            this.typingUsers.add(username);
        } else {
            this.typingUsers.delete(username);
        }
        this.updateTypingIndicator();
    }

    /**
     * Aktualisiert Typing-Indicator
     */
    updateTypingIndicator() {
        const indicator = document.getElementById('typingIndicators');
        if (!indicator) return;

        if (this.typingUsers.size > 0) {
            const users = Array.from(this.typingUsers).slice(0, 3);
            let text = '';
            
            if (users.length === 1) {
                text = `${users[0]} ${this.t('typing')}`;
            } else if (users.length === 2) {
                text = `${users[0]} und ${users[1]} ${this.t('typing')}`;
            } else {
                text = `${users.join(', ')} ${this.t('typing')}`;
            }
            
            indicator.innerHTML = `<div class="typing-indicator">${text}</div>`;
            indicator.style.display = 'block';
        } else {
            indicator.style.display = 'none';
        }
    }

    /**
     * Setzt Typing-Indicator zurück
     */
    clearTypingIndicator() {
        this.typingUsers.clear();
        this.updateTypingIndicator();
        this.sendTypingIndicator(false);
    }

    /**
     * Fügt eine Chat-Nachricht hinzu
     */
    addChatMessage(user, message, timestamp, room = 'general') {
        // Only show messages for current room
        if (room !== this.currentRoom) return;

        const messagesDiv = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message';

        const isOwnMessage = user === this.username;
        if (isOwnMessage) {
            messageDiv.classList.add('user');
        } else {
            messageDiv.classList.add('other');
        }

        const time = timestamp ? new Date(timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
        messageDiv.innerHTML = `
            <div class="message-header">
                <span class="message-username">${this.escapeHtml(user)}</span>
                <span class="message-time">${time}</span>
            </div>
            <div class="message-content">${this.escapeHtml(message)}</div>
        `;

        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        
        console.log(`💬 Message added from ${user}`);
    }

    /**
     * Fügt eine Systemnachricht hinzu
     */
    addSystemMessage(message) {
        const messagesDiv = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system';
        messageDiv.innerHTML = `<div class="message-content">${this.escapeHtml(message)}</div>`;

        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
        
        console.log(`ℹ️ System message: ${message}`);
    }

    /**
     * Aktualisiert den Verbindungsstatus
     */
    updateConnectionStatus(status) {
        const statusElements = [
            document.getElementById('connectionStatusText'),
            document.getElementById('sidebarConnectionStatus')
        ];

        const statusMap = {
            'connecting': { text: this.t('connecting'), className: 'connecting' },
            'connected': { text: this.t('connected'), className: 'connected' },
            'disconnected': { text: this.t('disconnected'), className: 'disconnected' },
            'reconnecting': { text: this.t('reconnecting'), className: 'connecting' },
            'error': { text: 'Fehler', className: 'disconnected' }
        };

        const statusInfo = statusMap[status] || statusMap.disconnected;
        
        statusElements.forEach(element => {
            if (element) {
                element.textContent = statusInfo.text;
                element.className = `status-value ${statusInfo.className}`;
            }
        });

        // Update connection bar
        const connectionBar = document.getElementById('connectionBar');
        const connectionIndicator = document.getElementById('connectionIndicator');
        
        if (connectionBar && connectionIndicator) {
            connectionBar.className = `connection-bar ${statusInfo.className}`;
            connectionIndicator.className = `status-indicator ${statusInfo.className}`;
        }

        // Update UI elements based on connection status
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendMessageBtn');

        if (messageInput) {
            messageInput.disabled = status !== 'connected';
            messageInput.placeholder = status !== 'connected' ? this.t('connecting') : this.t('messagePlaceholder');
        }
        if (sendButton) {
            sendButton.disabled = status !== 'connected';
        }

        console.log(`🔌 Connection status updated: ${status}`);
    }

    /**
     * Zeigt eine Benachrichtigung an
     */
    showNotification(message, duration = 3000) {
        const container = document.getElementById('notificationContainer') || this.createNotificationContainer();
        const notification = document.createElement('div');
        notification.className = 'notification';
        notification.textContent = message;
        
        container.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, duration);

        console.log(`🔔 Notification: ${message}`);
    }

    /**
     * Erstellt den Notification-Container
     */
    createNotificationContainer() {
        const container = document.createElement('div');
        container.id = 'notificationContainer';
        container.className = 'notification-container';
        document.body.appendChild(container);
        return container;
    }

    /**
     * Aktualisiert Benutzerstatistiken
     */
    updateUserStats() {
        const statsElement = document.getElementById('userStats');
        if (statsElement) {
            const now = new Date();
            const onlineSince = this.userOnlineSince ? 
                new Date(this.userOnlineSince).toLocaleTimeString() : 
                now.toLocaleTimeString();
            
            if (!this.userOnlineSince) {
                this.userOnlineSince = now.toISOString();
            }
            
            statsElement.innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">Nachrichten:</span>
                    <span class="stat-value" id="userMessageCount">${this.messageCount}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Online seit:</span>
                    <span class="stat-value" id="userOnlineSince">${onlineSince}</span>
                </div>
            `;
        }
    }

    /**
     * Aktualisiert Online-Benutzer
     */
    updateOnlineUsers() {
        const usersList = document.getElementById('usersList');
        const onlineCount = document.getElementById('onlineCount');
        
        if (usersList) {
            usersList.innerHTML = '';
            this.onlineUsers.forEach(user => {
                const userElement = document.createElement('div');
                userElement.className = 'user-item';
                userElement.innerHTML = `
                    <span class="user-status-indicator"></span>
                    <span class="user-name">${this.escapeHtml(user)}</span>
                `;
                usersList.appendChild(userElement);
            });
        }
        
        if (onlineCount) {
            onlineCount.textContent = this.onlineUsers.size;
        }
    }

    /**
     * Verfolgt Benutzeraktivität
     */
    trackUserActivity(username) {
        this.userActivity.set(username, Date.now());
        
        // Clean up inactive users (older than 5 minutes)
        const now = Date.now();
        for (let [user, lastActive] of this.userActivity.entries()) {
            if (now - lastActive > 5 * 60 * 1000) {
                this.userActivity.delete(user);
                this.onlineUsers.delete(user);
            }
        }
        
        this.updateOnlineUsers();
    }

    /**
     * API-Aufruf-Hilfsfunktion
     */
    async apiCall(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`❌ API call failed for ${endpoint}:`, error);
            this.showNotification(`❌ Fehler bei API-Aufruf: ${endpoint}`);
            return null;
        }
    }

    /**
     * Lädt Raum-Nachrichten
     */
    async loadRoomMessages(roomId) {
        try {
            console.log(`📥 Loading messages for room: ${roomId}`);
            const messages = await this.apiCall(`/api/messages?room_id=${roomId}&limit=50`);
            
            if (messages && messages.items) {
                const messagesDiv = document.getElementById('chatMessages');
                messagesDiv.innerHTML = ''; // Clear existing messages
                
                messages.items.forEach(msg => {
                    this.addChatMessage(msg.username, msg.message, msg.timestamp, msg.room);
                });
                
                this.messageCount = messages.items.length;
                this.updateUserStats();
            }
        } catch (error) {
            console.error(`❌ Error loading room messages:`, error);
        }
    }

    /**
     * Beitritt einem Raum
     */
    joinRoom(roomId) {
        if (this.isConnected) {
            const joinData = {
                type: 'join_room',
                room: roomId,
                username: this.username
            };
            this.ws.send(JSON.stringify(joinData));
        }
    }

    /**
     * Fügt Raum zur UI hinzu
     */
    addRoomToUI(roomData) {
        const roomsList = document.getElementById('roomsList');
        const roomElement = document.createElement('div');
        roomElement.className = 'room-item';
        roomElement.dataset.room = roomData.id;
        roomElement.innerHTML = `
            <span class="room-icon">${roomData.icon || '💬'}</span>
            <span class="room-name">${this.escapeHtml(roomData.name)}</span>
            <span class="room-members">0</span>
        `;
        roomsList.appendChild(roomElement);
    }

    /**
     * Modal-Funktionen
     */
    showRoomModal() {
        this.showModal('roomModal');
    }

    showUploadModal() {
        this.showModal('uploadModal');
    }

    showProjectModal() {
        this.showModal('projectModal');
    }

    showTicketModal() {
        this.showModal('ticketModal');
    }

    showModal(modalId) {
        document.getElementById('modalOverlay').style.display = 'flex';
        document.querySelectorAll('.modal').forEach(modal => {
            modal.style.display = 'none';
        });
        document.getElementById(modalId).style.display = 'block';
    }

    closeModals() {
        document.getElementById('modalOverlay').style.display = 'none';
        document.querySelectorAll('.modal').forEach(modal => {
            modal.style.display = 'none';
        });
    }

    /**
     * AI Assistant Funktionen
     */
    openAIAssistant() {
        this.switchSection('ai');
    }

    async sendAIMessage() {
        const input = document.getElementById('aiMessageInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Add user message to conversation
        this.addAIMessage('user', message);
        input.value = '';
        
        // Show thinking indicator
        this.addAIMessage('ai', this.t('aiThinking'), true);
        
        try {
            const response = await this.apiCall('/api/ai/ask', {
                method: 'POST',
                body: JSON.stringify({
                    question: message,
                    username: this.username,
                    use_context: true
                })
            });
            
            // Remove thinking indicator
            this.removeLastAIMessage();
            
            if (response && response.answer) {
                this.addAIMessage('ai', response.answer);
            } else {
                this.addAIMessage('ai', '❌ Keine Antwort vom AI Assistant erhalten.');
            }
        } catch (error) {
            this.removeLastAIMessage();
            this.addAIMessage('ai', '❌ Fehler bei der AI-Anfrage.');
            console.error('❌ AI request failed:', error);
        }
    }

    addAIMessage(sender, message, isThinking = false) {
        const conversation = document.getElementById('aiConversation');
        const messageDiv = document.createElement('div');
        messageDiv.className = `ai-message ${sender}-message ${isThinking ? 'thinking' : ''}`;
        messageDiv.innerHTML = `
            <div class="ai-message-content">${this.escapeHtml(message)}</div>
        `;
        conversation.appendChild(messageDiv);
        conversation.scrollTop = conversation.scrollHeight;
    }

    removeLastAIMessage() {
        const conversation = document.getElementById('aiConversation');
        const lastMessage = conversation.lastElementChild;
        if (lastMessage && lastMessage.classList.contains('thinking')) {
            conversation.removeChild(lastMessage);
        }
    }

    handleAIResponse(data) {
        this.addAIMessage('ai', data.response);
    }

    loadAIConversation() {
        // Load previous AI conversation if any
        const conversation = document.getElementById('aiConversation');
        conversation.innerHTML = '<div class="ai-message system-message">🤖 AI Assistant bereit. Stelle eine Frage!</div>';
    }

    /**
     * Projekt-Funktionen
     */
    async loadProjects() {
        try {
            const projects = await this.apiCall('/api/projects?limit=20');
            if (projects && projects.items) {
                this.projects = projects.items;
                this.renderProjects();
            }
        } catch (error) {
            console.error('❌ Error loading projects:', error);
        }
    }

    renderProjects() {
        const grid = document.getElementById('projectsGrid');
        if (!grid) return;
        
        grid.innerHTML = this.projects.map(project => `
            <div class="project-card">
                <div class="project-header">
                    <h3>${this.escapeHtml(project.name)}</h3>
                    <span class="project-status ${project.status}">${project.status}</span>
                </div>
                <p class="project-description">${this.escapeHtml(project.description || 'Keine Beschreibung')}</p>
                <div class="project-meta">
                    <span class="project-date">Erstellt: ${new Date(project.created_at).toLocaleDateString()}</span>
                    <span class="project-tickets">Tickets: ${project.ticket_count || 0}</span>
                </div>
            </div>
        `).join('');
    }

    updateProjectsBadge() {
        const badge = document.getElementById('projectsBadge');
        if (badge) {
            badge.textContent = this.projects.length;
        }
    }

    updateTicketsBadge() {
        const badge = document.getElementById('ticketsBadge');
        if (badge) {
            badge.textContent = this.tickets.length;
        }
    }

    /**
     * Weitere Funktionen für Tickets, Dateien, Analytics...
     */
    async loadTickets() {
        // Implementation for loading tickets
    }

    async loadFiles() {
        // Implementation for loading files
    }

    async loadAnalytics() {
        // Implementation for loading analytics
    }

    toggleEmojiPicker() {
        // Implementation for emoji picker
    }

    /**
     * Escaped HTML für sichere Anzeige
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize enhanced chat app when page loads
window.addEventListener('load', () => {
    console.log('🚀 Page loaded, initializing EnhancedChatApp...');
    window.chatApp = new EnhancedChatApp();
    
    const msgInput = document.getElementById('messageInput');
    if (msgInput) {
        msgInput.focus();
        console.log('🎯 Message input focused');
    }
    
    console.log('✅ EnhancedChatApp ready!');
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    console.log('👋 EnhancedChatApp closing...');
    if (window.chatApp) {
        window.chatApp.sendTypingIndicator(false);
        if (window.chatApp.ws) {
            window.chatApp.ws.close();
        }
    }
});