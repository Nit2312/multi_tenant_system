// Global variables
let adviceCount = 0;
let analysisCount = 0;
let isSystemInitialized = false;

// DOM elements
const statusIndicator = document.getElementById('statusIndicator');
const statusDot = statusIndicator.querySelector('.status-dot');
const statusText = statusIndicator.querySelector('.status-text');
const stocksCountElement = document.getElementById('stocksCount');
const bondsCountElement = document.getElementById('bondsCount');
const assetsCountElement = document.getElementById('assetsCount');
const adviceCountElement = document.getElementById('adviceCount');
const analysisCountElement = document.getElementById('analysisCount');
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const initBtn = document.getElementById('initBtn');
const loadingOverlay = document.getElementById('loadingOverlay');

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    checkSystemStatus();
    setupEventListeners();
    setupMobileSidebar();
    setupSidebarToggle();
    setupNewChat();
});

// Setup event listeners
function setupEventListeners() {
    messageInput.addEventListener('input', handleInputChange);
    messageInput.addEventListener('keypress', handleKeyPress);
}

// Handle input changes
function handleInputChange() {
    const hasText = messageInput.value.trim().length > 0;
    sendBtn.disabled = !hasText || !isSystemInitialized;
}

// Handle keyboard events
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

// Check system status
async function checkSystemStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        updateSystemStatus(data);

        if (!data.initialized) {
            initializeSystem();
        }
    } catch (error) {
        console.error('Error checking system status:', error);
        updateStatus('error', 'Connection failed');
    }
}

// Update system status
function updateSystemStatus(data) {
    isSystemInitialized = data.initialized;
    
    if (isSystemInitialized) {
        updateStatus('connected', 'Connected');
        stocksCountElement.textContent = data.stocks_count || '-';
        bondsCountElement.textContent = data.bonds_count || '-';
        assetsCountElement.textContent = data.assets_count || '-';
        if (initBtn) {
            initBtn.innerHTML = '<i class="fas fa-check"></i> System Ready';
            initBtn.disabled = true;
            initBtn.classList.add('btn-primary');
            initBtn.classList.remove('btn-secondary');
        }
    } else {
        updateStatus('disconnected', 'Not initialized');
        stocksCountElement.textContent = '-';
        bondsCountElement.textContent = '-';
        assetsCountElement.textContent = '-';
        if (initBtn) {
            initBtn.innerHTML = '<i class="fas fa-play"></i> Initialize System';
            initBtn.disabled = false;
            initBtn.classList.remove('btn-primary');
            initBtn.classList.add('btn-secondary');
        }
    }
    
    handleInputChange();
}

// Update status indicator
function updateStatus(status, message) {
    statusDot.className = 'status-dot';
    
    switch(status) {
        case 'connected':
            statusDot.classList.add('connected');
            break;
        case 'initializing':
            statusDot.classList.add('initializing');
            break;
        case 'error':
            // Keep default red color
            break;
    }
    
    statusText.textContent = message;
}

// Initialize system
async function initializeSystem() {
    if (isSystemInitialized) return;
    
    updateStatus('initializing', 'Initializing...');
    if (initBtn) {
        initBtn.disabled = true;
        initBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Initializing...';
    }
    
    try {
        const response = await fetch('/api/initialize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            updateSystemStatus({
                initialized: true,
                stocks_count: data.stocks_count,
                bonds_count: data.bonds_count,
                assets_count: data.assets_count
            });
            
            showNotification('System initialized successfully!', 'success');
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('Error initializing system:', error);
        updateStatus('error', 'Initialization failed');
        if (initBtn) {
            initBtn.disabled = false;
            initBtn.innerHTML = '<i class="fas fa-play"></i> Initialize System';
        }
        showNotification('Failed to initialize system: ' + error.message, 'error');
    }
}

function setupMobileSidebar() {
    const media = window.matchMedia('(max-width: 768px)');
    const detailsList = document.querySelectorAll('.sidebar .collapsible');

    const applyState = () => {
        if (media.matches) {
            detailsList.forEach((detail) => {
                detail.removeAttribute('open');
            });
        }
    };

    applyState();
    media.addEventListener('change', applyState);
}

function setupSidebarToggle() {
    const toggle = document.querySelector('.sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    if (!toggle || !sidebar) return;
    toggle.addEventListener('click', function() {
        sidebar.classList.toggle('open');
    });
}

function setupNewChat() {
    const btn = document.querySelector('.new-chat-btn');
    if (!btn) return;
    btn.addEventListener('click', function() {
        const chatMessages = document.getElementById('chatMessages');
        if (!chatMessages) return;
        chatMessages.innerHTML = '';
        const welcome = document.createElement('div');
        welcome.className = 'welcome-message';
        welcome.innerHTML = `
            <div class="welcome-icon"><i class="fas fa-coins"></i></div>
            <h2>Intelligent Investment Guidance</h2>
            <p>Get expert insights on value investing, portfolio management, market analysis, and wealth building strategies based on time-tested principles of successful investors.</p>
            <div class="welcome-suggestions">
                <button type="button" class="suggestion-chip" onclick="sendExampleMessage('What are key principles of value investing?')">Value investing principles</button>
                <button type="button" class="suggestion-chip" onclick="sendExampleMessage('How do you identify undervalued stocks?')">Find undervalued stocks</button>
                <button type="button" class="suggestion-chip" onclick="sendExampleMessage('What are common mistakes new investors make?')">Common investor mistakes</button>
            </div>
        `;
        chatMessages.appendChild(welcome);
        messageInput.focus();
    });
}

// Send message
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || !isSystemInitialized) return;
    
    // Add user message to chat
    addMessage(message, 'user');
    messageInput.value = '';
    handleInputChange();
    
    // Update counters
    adviceCount++;
    analysisCount++;
    updateCounters();
    
    // Show loading
    showLoading(true);
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message
            })
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.error || `HTTP ${response.status} ${response.statusText}`);
        }
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Add AI response to chat (pass question for Verify answer)
        addMessage(data.response, 'assistant', data.sources || [], false, data.retrieval_metrics, message);
        
    } catch (error) {
        console.error('Error sending message:', error);
        addMessage('Sorry, I encountered an error: ' + error.message, 'assistant', [], true);
    } finally {
        showLoading(false);
    }
}

// Send example message
function sendExampleMessage(message) {
    messageInput.value = message;
    handleInputChange();
    sendMessage();
}

// Add message to chat
function addMessage(content, sender, sources = [], isError = false, retrievalMetrics = null, question = null) {
    const welcomeMessage = chatMessages.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'message-avatar';
    avatarDiv.innerHTML = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';
    if (isError) {
        bubbleDiv.style.background = '#fef2f2';
        bubbleDiv.style.color = '#991b1b';
        bubbleDiv.style.borderColor = '#fecaca';
    }
    
    const formattedContent = formatAIResponse(content);
    bubbleDiv.innerHTML = formattedContent;
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = getCurrentTime();
    
    contentDiv.appendChild(bubbleDiv);
    contentDiv.appendChild(timeDiv);
    
    if (sources && sources.length > 0) {
        const sourcesDiv = createSourcesSection(sources);
        contentDiv.appendChild(sourcesDiv);
    }
    
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Format AI response for better readability
function formatAIResponse(content) {
    // Convert markdown-like formatting to HTML
    let formatted = content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')  // Bold text
        .replace(/\*(.*?)\*/g, '<em>$1</em>')              // Italic text
        .replace(/CaseID:\s*(\w+)/g, '<span class="case-id">CaseID: $1</span>')
        .replace(/Job_Name:\s*([^,\n]+)/g, '<span class="job-name">Job Name: $1</span>')
        .replace(/•\s+(.+)/g, '<li>$1</li>')               // Bullet points
        .replace(/(\d+\.\s+.+)/g, '<li>$1</li>')           // Numbered lists
        .replace(/\n\n/g, '</p><p>')                      // Paragraph breaks
        .replace(/\n/g, '<br>');                           // Line breaks
    
    // Wrap in paragraph tags
    if (!formatted.startsWith('<p>')) {
        formatted = '<p>' + formatted;
    }
    if (!formatted.endsWith('</p>')) {
        formatted = formatted + '</p>';
    }
    
    // Convert list items to proper HTML lists
    formatted = formatted.replace(/(<li>.*?<\/li>)/gs, function(match) {
        return match.replace(/<p>(.*?)<\/p>/g, '$1');
    });
    
    // Group consecutive list items
    formatted = formatted.replace(/(<li>.*?<\/li>\s*)+/gs, '<ul>$&</ul>');
    
    return formatted;
}

// Create expandable sources section
function createSourcesSection(sources) {
    const sourcesDiv = document.createElement('div');
    sourcesDiv.className = 'sources';
    
    const sourcesHeader = document.createElement('div');
    sourcesHeader.className = 'sources-header';
    sourcesHeader.innerHTML = `
        <div class="sources-header-left">
            <i class="fas fa-file-alt"></i>
            <span>📄 Source Documents (${sources.length})</span>
        </div>
        <i class="fas fa-chevron-down expand-icon"></i>
    `;
    
    const sourcesContent = document.createElement('div');
    sourcesContent.className = 'sources-content';
    
    sources.forEach((source, index) => {
        const sourceItem = document.createElement('div');
        sourceItem.className = 'source-item';
        
        const sourceMeta = document.createElement('div');
        sourceMeta.className = 'source-meta';
        
        // Handle different source types
        if (source.type === 'case_record') {
            sourceMeta.innerHTML = `
                <strong>CaseID:</strong> ${source.case_id} | 
                <strong>Job Name:</strong> ${source.job_name}
            `;
        } else if (source.type === 'pdf_document') {
            sourceMeta.innerHTML = `
                <strong>PDF:</strong> ${source.filename}
            `;
        } else {
            sourceMeta.innerHTML = `
                <strong>Source:</strong> ${JSON.stringify(source.metadata || {})}
            `;
        }
        
        const sourceContent = document.createElement('div');
        sourceContent.className = 'source-content';
        
        // Format source content better
        const content = source.content
            .replace(/Problem:\s*/i, '<strong>Problem:</strong> ')
            .replace(/Resolution:\s*/i, '<br><strong>Resolution:</strong> ');
        sourceContent.innerHTML = content;
        
        sourceItem.appendChild(sourceMeta);
        sourceItem.appendChild(sourceContent);
        sourcesContent.appendChild(sourceItem);
    });
    
    // Add toggle functionality
    sourcesHeader.addEventListener('click', function() {
        const isExpanded = sourcesContent.classList.contains('expanded');
        
        if (isExpanded) {
            sourcesContent.classList.remove('expanded');
            sourcesHeader.classList.remove('expanded');
        } else {
            sourcesContent.classList.add('expanded');
            sourcesHeader.classList.add('expanded');
        }
    });
    
    sourcesDiv.appendChild(sourcesHeader);
    sourcesDiv.appendChild(sourcesContent);
    
    return sourcesDiv;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Get current time
function getCurrentTime() {
    const now = new Date();
    return now.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit'
    });
}

// Update counters
function updateCounters() {
    adviceCountElement.textContent = adviceCount;
    analysisCountElement.textContent = analysisCount;
}

// Show/hide loading overlay
function showLoading(show) {
    if (show) {
        loadingOverlay.classList.add('active');
    } else {
        loadingOverlay.classList.remove('active');
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 0.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        z-index: 1001;
        animation: slideIn 0.3s ease-out;
        max-width: 400px;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(100%);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideOut {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
`;
document.head.appendChild(style);

// Auto-refresh status every 30 seconds
setInterval(checkSystemStatus, 30000);

// Dashboard password protection
function promptDashboardPassword() {
    const password = prompt('Enter password to access Analytics Dashboard:');
    if (password === null) return; // User cancelled
    
    // Verify password with backend
    verifyDashboardPassword(password);
}

async function verifyDashboardPassword(password) {
    try {
        const response = await fetch('/api/verify-dashboard-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ password: password })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Store session token and redirect
            sessionStorage.setItem('dashboard_token', data.token);
            window.open(`/dashboard?token=${data.token}`, '_blank');
        } else {
            alert('Invalid password. Access denied.');
        }
    } catch (error) {
        console.error('Password verification failed:', error);
        alert('Error verifying password. Please try again.');
    }
}

// Theme switching functionality
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    
    // Update theme icon
    const themeIcon = document.getElementById('themeIcon');
    if (themeIcon) {
        themeIcon.className = theme === 'dark' ? 'fas fa-sun theme-icon' : 'fas fa-moon theme-icon';
        
        // Add rotation animation
        themeIcon.classList.add('rotating');
        setTimeout(() => {
            themeIcon.classList.remove('rotating');
        }, 300);
    }
    
    // Update dashboard theme if it exists
    const dashboardLink = document.querySelector('a[href="/dashboard"]');
    if (dashboardLink && dashboardLink.href) {
        const dashboardUrl = new URL(dashboardLink.href);
        dashboardUrl.searchParams.set('theme', theme);
        dashboardLink.href = dashboardUrl.toString();
    }
}
