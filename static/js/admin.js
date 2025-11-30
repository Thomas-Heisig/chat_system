// admin.js - Admin Dashboard JavaScript
// Handles settings, RAG, database, users, monitoring, and integrations

class AdminDashboard {
    constructor() {
        this.currentSettings = {};
        this.initEventListeners();
        this.loadInitialData();
    }

    initEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => this.switchSection(e.target.closest('.nav-link').dataset.section));
        });

        // Settings tabs
        document.querySelectorAll('.settings-tab').forEach(tab => {
            tab.addEventListener('click', (e) => this.switchSettingsTab(e.target.dataset.settingsTab));
        });

        // Settings actions
        document.getElementById('saveSettingsBtn')?.addEventListener('click', () => this.saveSettings());
        document.getElementById('resetSettingsBtn')?.addEventListener('click', () => this.resetSettings());
        document.getElementById('exportSettingsBtn')?.addEventListener('click', () => this.exportSettings());

        // AI temperature slider
        document.getElementById('aiTemperature')?.addEventListener('input', (e) => {
            document.getElementById('tempValue').textContent = e.target.value;
        });

        // Database actions
        document.getElementById('dbTestConnectionBtn')?.addEventListener('click', () => this.testDbConnection());
        document.getElementById('dbBackupBtn')?.addEventListener('click', () => this.createDbBackup());
        document.getElementById('dbOptimizeBtn')?.addEventListener('click', () => this.optimizeDb());

        // RAG actions
        document.getElementById('ragTestBtn')?.addEventListener('click', () => this.testRagPipeline());
        document.getElementById('ragFileInput')?.addEventListener('change', (e) => this.uploadRagDocument(e));

        // Logs
        document.getElementById('refreshLogsBtn')?.addEventListener('click', () => this.loadLogs());
        document.getElementById('logLevelFilter')?.addEventListener('change', () => this.loadLogs());
        document.getElementById('logSearch')?.addEventListener('input', () => this.loadLogs());

        // Sessions
        document.getElementById('cleanupSessionsBtn')?.addEventListener('click', () => this.cleanupSessions());
    }

    switchSection(sectionName) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
        document.querySelector(`[data-section="${sectionName}"]`)?.closest('.nav-item')?.classList.add('active');

        // Update content sections
        document.querySelectorAll('.content-section').forEach(section => section.classList.remove('active'));
        const targetSection = document.getElementById(`${sectionName}Section`);
        if (targetSection) {
            targetSection.classList.add('active');
            this.loadSectionData(sectionName);
        }
    }

    switchSettingsTab(tabName) {
        document.querySelectorAll('.settings-tab').forEach(tab => tab.classList.remove('active'));
        document.querySelector(`[data-settings-tab="${tabName}"]`)?.classList.add('active');

        document.querySelectorAll('.settings-panel').forEach(panel => panel.classList.remove('active'));
        document.getElementById(`${tabName}SettingsPanel`)?.classList.add('active');
    }

    async loadSectionData(sectionName) {
        switch (sectionName) {
            case 'settings':
                await this.loadSettings();
                break;
            case 'rag':
                await this.loadRagStatus();
                break;
            case 'database':
                await this.loadDbStatus();
                break;
            case 'users':
                await this.loadUsers();
                break;
            case 'monitoring':
                await this.loadMonitoringData();
                break;
            case 'integrations':
                await this.loadIntegrations();
                break;
        }
    }

    async loadInitialData() {
        await this.loadSettings();
    }

    // Settings Management
    async loadSettings() {
        try {
            const response = await fetch('/api/settings');
            const data = await response.json();
            this.currentSettings = data.settings;
            this.populateSettingsForm();
            this.showToast('Einstellungen geladen', 'success');
        } catch (error) {
            console.error('Failed to load settings:', error);
            this.showToast('Fehler beim Laden der Einstellungen', 'error');
        }
    }

    populateSettingsForm() {
        const s = this.currentSettings;

        // General
        if (s.general) {
            document.getElementById('appName').value = s.general.app_name || '';
            document.getElementById('debugMode').checked = s.general.debug_mode || false;
            document.getElementById('logLevel').value = s.general.log_level || 'INFO';
        }

        // AI
        if (s.ai) {
            document.getElementById('aiEnabled').checked = s.ai.enabled || false;
            document.getElementById('ollamaUrl').value = s.ai.ollama_url || '';
            document.getElementById('defaultModel').value = s.ai.default_model || 'llama2';
            document.getElementById('aiTemperature').value = s.ai.temperature || 0.7;
            document.getElementById('tempValue').textContent = s.ai.temperature || 0.7;
            document.getElementById('maxTokens').value = s.ai.max_tokens || 1000;
            document.getElementById('autoRespond').checked = s.ai.auto_respond || false;
        }

        // Security
        if (s.security) {
            document.getElementById('rateLimitEnabled').checked = s.security.rate_limit_enabled || false;
            document.getElementById('rateLimitRequests').value = s.security.rate_limit_requests || 100;
            document.getElementById('rateLimitWindow').value = s.security.rate_limit_window || 60;
            document.getElementById('corsOrigins').value = (s.security.cors_origins || []).join('\n');
        }

        // Features
        if (s.features) {
            document.getElementById('projectManagement').checked = s.features.project_management || false;
            document.getElementById('ticketSystem').checked = s.features.ticket_system || false;
            document.getElementById('fileUpload').checked = s.features.file_upload || false;
            document.getElementById('userAuthentication').checked = s.features.user_authentication || false;
            document.getElementById('websocketEnabled').checked = s.features.websocket_enabled || false;
        }

        // UI
        if (s.ui) {
            document.getElementById('uiTheme').value = s.ui.theme || 'light';
            document.getElementById('uiLanguage').value = s.ui.language || 'de';
            document.getElementById('showTimestamps').checked = s.ui.show_timestamps !== false;
            document.getElementById('enableSound').checked = s.ui.enable_sound !== false;
            document.getElementById('enableNotifications').checked = s.ui.enable_notifications !== false;
        }
    }

    async saveSettings() {
        try {
            // Collect settings from form
            const settings = {
                general: {
                    app_name: document.getElementById('appName').value,
                    debug_mode: document.getElementById('debugMode').checked,
                    log_level: document.getElementById('logLevel').value
                },
                ai: {
                    enabled: document.getElementById('aiEnabled').checked,
                    ollama_url: document.getElementById('ollamaUrl').value,
                    default_model: document.getElementById('defaultModel').value,
                    temperature: parseFloat(document.getElementById('aiTemperature').value),
                    max_tokens: parseInt(document.getElementById('maxTokens').value),
                    auto_respond: document.getElementById('autoRespond').checked
                },
                security: {
                    rate_limit_enabled: document.getElementById('rateLimitEnabled').checked,
                    rate_limit_requests: parseInt(document.getElementById('rateLimitRequests').value),
                    rate_limit_window: parseInt(document.getElementById('rateLimitWindow').value),
                    cors_origins: document.getElementById('corsOrigins').value.split('\n').filter(Boolean)
                },
                features: {
                    project_management: document.getElementById('projectManagement').checked,
                    ticket_system: document.getElementById('ticketSystem').checked,
                    file_upload: document.getElementById('fileUpload').checked,
                    user_authentication: document.getElementById('userAuthentication').checked,
                    websocket_enabled: document.getElementById('websocketEnabled').checked
                },
                ui: {
                    theme: document.getElementById('uiTheme').value,
                    language: document.getElementById('uiLanguage').value,
                    show_timestamps: document.getElementById('showTimestamps').checked,
                    enable_sound: document.getElementById('enableSound').checked,
                    enable_notifications: document.getElementById('enableNotifications').checked
                }
            };

            // Save each category
            for (const [category, values] of Object.entries(settings)) {
                await fetch(`/api/settings/${category}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(values)
                });
            }

            this.showToast('Einstellungen gespeichert', 'success');
        } catch (error) {
            console.error('Failed to save settings:', error);
            this.showToast('Fehler beim Speichern', 'error');
        }
    }

    async resetSettings() {
        if (confirm('Alle Einstellungen auf Standardwerte zurücksetzen?')) {
            try {
                await fetch('/api/settings/reset', { method: 'POST' });
                await this.loadSettings();
                this.showToast('Einstellungen zurückgesetzt', 'success');
            } catch (error) {
                console.error('Failed to reset settings:', error);
                this.showToast('Fehler beim Zurücksetzen', 'error');
            }
        }
    }

    async exportSettings() {
        try {
            const response = await fetch('/api/settings/export');
            const data = await response.json();
            
            const blob = new Blob([data.settings_json], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'chat_system_settings.json';
            a.click();
            URL.revokeObjectURL(url);
            
            this.showToast('Einstellungen exportiert', 'success');
        } catch (error) {
            console.error('Failed to export settings:', error);
            this.showToast('Fehler beim Exportieren', 'error');
        }
    }

    // RAG Management
    async loadRagStatus() {
        try {
            const response = await fetch('/api/rag/status');
            const data = await response.json();
            
            document.getElementById('ragStatus').textContent = data.enabled ? 'Aktiv' : 'Inaktiv';
            document.getElementById('ragStatus').className = `status-indicator ${data.enabled ? 'healthy' : ''}`;
            document.getElementById('ragProvider').textContent = data.provider || 'ChromaDB';
            document.getElementById('ragDocCount').textContent = data.provider_stats?.document_count || 0;

            // Populate settings
            document.getElementById('ragEnabled').checked = data.enabled;
            document.getElementById('vectorDbProvider').value = data.provider || 'chromadb';
        } catch (error) {
            console.error('Failed to load RAG status:', error);
        }
    }

    async testRagPipeline() {
        const query = document.getElementById('ragTestQuery').value;
        if (!query) {
            this.showToast('Bitte Suchbegriff eingeben', 'warning');
            return;
        }

        try {
            const response = await fetch('/api/rag/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });
            const data = await response.json();

            const resultsContainer = document.getElementById('ragTestResults');
            if (data.results_count === 0) {
                resultsContainer.innerHTML = '<p class="no-results">Keine Ergebnisse gefunden</p>';
            } else {
                resultsContainer.innerHTML = data.results.map(r => `
                    <div class="result-item">
                        <div class="result-score">Score: ${r.score.toFixed(2)}</div>
                        <div class="result-content">${r.document.content.substring(0, 200)}...</div>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('RAG test failed:', error);
            this.showToast('RAG Test fehlgeschlagen', 'error');
        }
    }

    async uploadRagDocument(event) {
        const files = event.target.files;
        if (!files.length) return;

        for (const file of files) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('metadata', JSON.stringify({ filename: file.name }));

            try {
                await fetch('/api/rag/documents/upload', {
                    method: 'POST',
                    body: formData
                });
                this.showToast(`${file.name} hochgeladen`, 'success');
            } catch (error) {
                console.error('Upload failed:', error);
                this.showToast(`Fehler bei ${file.name}`, 'error');
            }
        }
        await this.loadRagStatus();
    }

    // Database Management
    async loadDbStatus() {
        try {
            const response = await fetch('/api/database/status');
            const data = await response.json();

            document.getElementById('dbStatus').textContent = data.status === 'healthy' ? 'Verbunden' : 'Fehler';
            document.getElementById('dbStatus').className = `status-indicator ${data.status === 'healthy' ? 'healthy' : 'error'}`;
            document.getElementById('dbType').textContent = data.database_type || 'SQLite';
            
            // Load stats
            const statsResponse = await fetch('/api/database/stats');
            const stats = await statsResponse.json();
            
            document.getElementById('dbSize').textContent = `${(stats.statistics?.database_size_bytes / 1024 / 1024).toFixed(2)} MB`;
            document.getElementById('dbTableCount').textContent = stats.statistics?.table_count || 0;

            // Populate stats table
            const statsTable = document.getElementById('dbStatsTable');
            if (stats.statistics?.tables) {
                statsTable.innerHTML = Object.entries(stats.statistics.tables).map(([table, count]) => `
                    <div class="stat-row">
                        <span class="table-name">${table}</span>
                        <span class="table-count">${count} Einträge</span>
                    </div>
                `).join('');
            }

            // Load backups
            const backupsResponse = await fetch('/api/database/backups');
            const backups = await backupsResponse.json();
            const backupsList = document.getElementById('dbBackupsList');
            if (backups.backups?.length) {
                backupsList.innerHTML = backups.backups.map(b => `
                    <div class="backup-item">
                        <span class="backup-name">${b.name}</span>
                        <span class="backup-date">${new Date(b.created_at).toLocaleString()}</span>
                        <span class="backup-size">${(b.size_bytes / 1024).toFixed(2)} KB</span>
                    </div>
                `).join('');
            } else {
                backupsList.innerHTML = '<p class="no-data">Keine Backups vorhanden</p>';
            }
        } catch (error) {
            console.error('Failed to load DB status:', error);
        }
    }

    async testDbConnection() {
        try {
            const response = await fetch('/api/database/test-connection', { method: 'POST' });
            const data = await response.json();
            
            if (data.status === 'connected') {
                this.showToast('Verbindung erfolgreich', 'success');
            } else {
                this.showToast('Verbindung fehlgeschlagen', 'error');
            }
        } catch (error) {
            console.error('Connection test failed:', error);
            this.showToast('Test fehlgeschlagen', 'error');
        }
    }

    async createDbBackup() {
        try {
            const response = await fetch('/api/database/backup', { method: 'POST' });
            const data = await response.json();
            
            if (data.status === 'success') {
                this.showToast('Backup erstellt', 'success');
                await this.loadDbStatus();
            }
        } catch (error) {
            console.error('Backup failed:', error);
            this.showToast('Backup fehlgeschlagen', 'error');
        }
    }

    async optimizeDb() {
        try {
            const response = await fetch('/api/database/optimize', { method: 'POST' });
            const data = await response.json();
            
            if (data.status === 'optimized') {
                this.showToast('Datenbank optimiert', 'success');
            }
        } catch (error) {
            console.error('Optimization failed:', error);
            this.showToast('Optimierung fehlgeschlagen', 'error');
        }
    }

    // Monitoring
    async loadMonitoringData() {
        try {
            const response = await fetch('/api/admin/system-info');
            const data = await response.json();

            document.getElementById('cpuUsage').textContent = `${data.resources?.cpu_percent || 0}%`;
            document.getElementById('memoryUsage').textContent = `${data.resources?.memory_percent || 0}%`;
            document.getElementById('diskUsage').textContent = `${data.resources?.disk_percent || 0}%`;

            await this.loadLogs();
        } catch (error) {
            console.error('Failed to load monitoring data:', error);
        }
    }

    async loadLogs() {
        try {
            const level = document.getElementById('logLevelFilter')?.value || '';
            const search = document.getElementById('logSearch')?.value || '';
            
            const params = new URLSearchParams({ limit: 100 });
            if (level) params.append('level', level);
            if (search) params.append('search', search);

            const response = await fetch(`/api/admin/logs?${params}`);
            const data = await response.json();

            const container = document.getElementById('logsContainer');
            if (data.logs?.length) {
                container.innerHTML = data.logs.map(log => `<div class="log-entry">${log}</div>`).join('');
                container.scrollTop = container.scrollHeight;
            } else {
                container.innerHTML = '<p class="no-data">Keine Logs gefunden</p>';
            }
        } catch (error) {
            console.error('Failed to load logs:', error);
        }
    }

    // Users
    async loadUsers() {
        try {
            const response = await fetch('/api/admin/users');
            const data = await response.json();
            
            const container = document.getElementById('usersList');
            if (data.users?.length) {
                container.innerHTML = data.users.map(u => `
                    <div class="user-item">
                        <span class="user-name">${u.username}</span>
                        <span class="user-role">${u.role}</span>
                    </div>
                `).join('');
            } else {
                container.innerHTML = '<p class="no-data">Keine Benutzer gefunden</p>';
            }

            // Load sessions
            const sessionsResponse = await fetch('/api/admin/sessions');
            const sessions = await sessionsResponse.json();
            document.getElementById('activeSessions').textContent = sessions.active_sessions || 0;
        } catch (error) {
            console.error('Failed to load users:', error);
        }
    }

    async cleanupSessions() {
        try {
            await fetch('/api/admin/sessions/cleanup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ max_age_hours: 24 })
            });
            this.showToast('Sessions bereinigt', 'success');
            await this.loadUsers();
        } catch (error) {
            console.error('Session cleanup failed:', error);
            this.showToast('Bereinigung fehlgeschlagen', 'error');
        }
    }

    // Integrations
    async loadIntegrations() {
        // Load webhook and integration status
        // Implementation would go here
    }

    // Utility
    showToast(message, type = 'info') {
        const container = document.getElementById('notificationContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `notification ${type}`;
        toast.innerHTML = `
            <span class="notification-icon">${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span>
            <span class="notification-message">${message}</span>
        `;
        container.appendChild(toast);

        setTimeout(() => toast.remove(), 3000);
    }
}

// Initialize admin dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.adminDashboard = new AdminDashboard();
});
