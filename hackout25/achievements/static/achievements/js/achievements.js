// Achievement System JavaScript

class AchievementManager {
    constructor() {
        this.apiEndpoints = {
            progress: '/achievements/api/progress/',
            notifications: '/achievements/api/notifications/',
            markRead: '/achievements/api/notifications/read/',
            track: '/achievements/api/track/',
            leaderboard: '/achievements/api/leaderboard/'
        };
        
        this.notificationQueue = [];
        this.isShowingNotification = false;
        
        this.init();
    }
    
    init() {
        // Initialize achievement system when DOM is loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupEventListeners());
        } else {
            this.setupEventListeners();
        }
        
        // Check for new notifications periodically
        this.startNotificationPolling();
    }
    
    setupEventListeners() {
        // Achievement card click handlers
        document.querySelectorAll('.achievement-card').forEach(card => {
            card.addEventListener('click', (e) => this.handleAchievementClick(e));
        });
        
        // Notification close handlers
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('notification-close')) {
                this.closeNotification(e.target.closest('.achievement-notification'));
            }
        });
        
        // Leaderboard filters
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleLeaderboardFilter(e));
        });
        
        // Track map usage when heatmap is accessed
        if (window.location.pathname.includes('/heatmap/')) {
            this.trackAction('map_view');
        }
    }
    
    async trackAction(actionType, additionalData = {}) {
        try {
            const formData = new FormData();
            formData.append('action_type', actionType);
            
            Object.keys(additionalData).forEach(key => {
                formData.append(key, additionalData[key]);
            });
            
            const response = await fetch(this.apiEndpoints.track, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
            
            if (response.ok) {
                console.log(`Action tracked: ${actionType}`);
            }
        } catch (error) {
            console.error('Error tracking action:', error);
        }
    }
    
    async checkNotifications() {
        try {
            const response = await fetch(this.apiEndpoints.notifications);
            const data = await response.json();
            
            if (data.success && data.notifications.length > 0) {
                // Add new notifications to queue
                data.notifications.forEach(notification => {
                    if (!notification.is_displayed) {
                        this.notificationQueue.push(notification);
                    }
                });
                
                // Process notification queue
                this.processNotificationQueue();
            }
        } catch (error) {
            console.error('Error checking notifications:', error);
        }
    }
    
    processNotificationQueue() {
        if (this.notificationQueue.length > 0 && !this.isShowingNotification) {
            const notification = this.notificationQueue.shift();
            this.showAchievementNotification(notification);
        }
    }
    
    showAchievementNotification(notification) {
        this.isShowingNotification = true;
        
        // Create notification element
        const notificationEl = document.createElement('div');
        notificationEl.className = 'achievement-notification';
        notificationEl.innerHTML = `
            <button class="notification-close" type="button">&times;</button>
            <div class="notification-header">
                <div class="notification-icon">${notification.achievement.icon}</div>
                <div class="notification-content">
                    <h4>Achievement Unlocked!</h4>
                    <p>${notification.achievement.name}</p>
                </div>
            </div>
            <div class="notification-meta">
                <small>${notification.achievement.tier.toUpperCase()} • +${notification.achievement.points} points</small>
            </div>
        `;
        
        // Style based on tier
        const tierColors = {
            bronze: 'linear-gradient(135deg, #CD7F32, #A0522D)',
            silver: 'linear-gradient(135deg, #C0C0C0, #A8A8A8)',
            gold: 'linear-gradient(135deg, #FFD700, #DAA520)',
            platinum: 'linear-gradient(135deg, #E5E4E2, #C0C0C0)',
            diamond: 'linear-gradient(135deg, #B9F2FF, #87CEEB)',
            legendary: 'linear-gradient(135deg, #FF69B4, #FF1493)'
        };
        
        notificationEl.style.background = tierColors[notification.achievement.tier] || tierColors.bronze;
        
        // Add to DOM
        document.body.appendChild(notificationEl);
        
        // Trigger animation
        setTimeout(() => {
            notificationEl.classList.add('show');
        }, 100);
        
        // Celebration effect
        this.triggerCelebration();
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.closeNotification(notificationEl);
        }, 5000);
        
        // Mark as displayed
        this.markNotificationAsDisplayed(notification.id);
    }
    
    closeNotification(notificationEl) {
        if (notificationEl) {
            notificationEl.style.transform = 'translateX(100%)';
            
            setTimeout(() => {
                if (notificationEl.parentNode) {
                    notificationEl.parentNode.removeChild(notificationEl);
                }
                this.isShowingNotification = false;
                
                // Process next notification in queue
                this.processNotificationQueue();
            }, 500);
        }
    }
    
    triggerCelebration() {
        // Create confetti effect
        this.createConfetti();
        
        // Play achievement sound (if enabled)
        this.playAchievementSound();
    }
    
    createConfetti() {
        const colors = ['#FFD700', '#FF69B4', '#00CED1', '#32CD32', '#FF6347'];
        const confettiCount = 50;
        
        for (let i = 0; i < confettiCount; i++) {
            const confetti = document.createElement('div');
            confetti.style.cssText = `
                position: fixed;
                width: 8px;
                height: 8px;
                background: ${colors[Math.floor(Math.random() * colors.length)]};
                top: -10px;
                left: ${Math.random() * 100}vw;
                border-radius: 50%;
                pointer-events: none;
                z-index: 10001;
                animation: confettiFall ${2 + Math.random() * 3}s linear forwards;
            `;
            
            document.body.appendChild(confetti);
            
            // Remove after animation
            setTimeout(() => {
                if (confetti.parentNode) {
                    confetti.parentNode.removeChild(confetti);
                }
            }, 5000);
        }
    }
    
    playAchievementSound() {
        // Create a simple achievement sound using Web Audio API
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            oscillator.frequency.setValueAtTime(1000, audioContext.currentTime + 0.1);
            oscillator.frequency.setValueAtTime(1200, audioContext.currentTime + 0.2);
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            
            oscillator.start();
            oscillator.stop(audioContext.currentTime + 0.5);
        } catch (error) {
            // Audio not supported or blocked
            console.log('Achievement sound not available');
        }
    }
    
    async markNotificationAsDisplayed(notificationId) {
        try {
            const formData = new FormData();
            formData.append('notification_ids', notificationId);
            
            await fetch(this.apiEndpoints.markRead, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': this.getCSRFToken()
                }
            });
        } catch (error) {
            console.error('Error marking notification as displayed:', error);
        }
    }
    
    handleAchievementClick(event) {
        const card = event.currentTarget;
        const achievementId = card.dataset.achievementId;
        
        if (achievementId) {
            // Add click animation
            card.style.transform = 'scale(0.98)';
            setTimeout(() => {
                card.style.transform = '';
            }, 150);
            
            // Navigate to achievement detail (if route exists)
            if (window.location.pathname.includes('/achievements/')) {
                window.location.href = `/achievements/achievement/${achievementId}/`;
            }
        }
    }
    
    handleLeaderboardFilter(event) {
        const btn = event.target;
        const filterType = btn.dataset.filter;
        
        // Update active state
        document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Update URL and reload
        const url = new URL(window.location);
        url.searchParams.set('type', filterType);
        window.location.href = url.toString();
    }
    
    startNotificationPolling() {
        // Check for notifications every 30 seconds
        setInterval(() => {
            this.checkNotifications();
        }, 30000);
        
        // Initial check
        setTimeout(() => {
            this.checkNotifications();
        }, 2000);
    }
    
    getCSRFToken() {
        // Get CSRF token from cookie or meta tag
        const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                     document.querySelector('meta[name=csrf-token]')?.content ||
                     this.getCookie('csrftoken');
        return token;
    }
    
    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    // Widget methods for embedding in other pages
    static async createProgressWidget(containerId) {
        try {
            const response = await fetch('/achievements/api/progress/');
            const data = await response.json();
            
            if (data.success) {
                const container = document.getElementById(containerId);
                if (container) {
                    container.innerHTML = AchievementManager.generateProgressWidgetHTML(data.data);
                }
            }
        } catch (error) {
            console.error('Error creating progress widget:', error);
        }
    }
    
    static generateProgressWidgetHTML(userData) {
        return `
            <div class="user-progress-widget">
                <div class="widget-header">
                    <h5>🏆 Your Progress</h5>
                    <div class="level-display">Level ${userData.level}</div>
                </div>
                
                <div class="progress-section">
                    <div class="progress-label">
                        <span class="progress-title">Achievements</span>
                        <span class="progress-value">${userData.achievements_unlocked}/${userData.total_achievements}</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${userData.completion_percentage}%"></div>
                    </div>
                </div>
                
                <div class="progress-section">
                    <div class="progress-label">
                        <span class="progress-title">Points</span>
                        <span class="progress-value">${userData.total_points}</span>
                    </div>
                </div>
                
                <div class="progress-section">
                    <div class="progress-label">
                        <span class="progress-title">Current Streak</span>
                        <span class="progress-value">${userData.streak_current} days 🔥</span>
                    </div>
                </div>
                
                <div class="widget-footer">
                    <small>Rank #${userData.user_rank} • ${userData.next_level_points} pts to next level</small>
                </div>
            </div>
        `;
    }
    
    static async createMiniLeaderboard(containerId, type = 'points', limit = 5) {
        try {
            const response = await fetch(`/achievements/api/leaderboard/?type=${type}&limit=${limit}`);
            const data = await response.json();
            
            if (data.success) {
                const container = document.getElementById(containerId);
                if (container) {
                    container.innerHTML = AchievementManager.generateLeaderboardHTML(data.leaderboard, type);
                }
            }
        } catch (error) {
            console.error('Error creating mini leaderboard:', error);
        }
    }
    
    static generateLeaderboardHTML(leaderboard, type) {
        const typeLabels = {
            points: 'Points',
            reports: 'Reports',
            achievements: 'Achievements'
        };
        
        const header = typeLabels[type] || 'Score';
        
        let html = `
            <div class="mini-leaderboard">
                <h6>🏆 Top ${header}</h6>
                <div class="leaderboard-list">
        `;
        
        leaderboard.forEach((entry, index) => {
            const rankClass = index < 3 ? `rank-${index + 1}` : '';
            html += `
                <div class="mini-leaderboard-row ${rankClass}">
                    <span class="mini-rank">#${entry.rank}</span>
                    <span class="mini-user">${entry.username}</span>
                    <span class="mini-score">${entry.score}</span>
                </div>
            `;
        });
        
        html += `
                </div>
                <div class="leaderboard-footer">
                    <a href="/achievements/leaderboard/" class="view-full-link">View Full Leaderboard →</a>
                </div>
            </div>
        `;
        
        return html;
    }
}

// CSS for confetti animation
const confettiCSS = `
@keyframes confettiFall {
    0% {
        transform: translateY(-100vh) rotate(0deg);
        opacity: 1;
    }
    100% {
        transform: translateY(100vh) rotate(720deg);
        opacity: 0;
    }
}

.mini-leaderboard {
    background: white;
    border-radius: 10px;
    padding: 15px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.mini-leaderboard h6 {
    margin: 0 0 15px 0;
    color: #333;
    font-weight: 600;
}

.mini-leaderboard-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #f0f0f0;
}

.mini-leaderboard-row:last-child {
    border-bottom: none;
}

.mini-rank {
    font-weight: bold;
    width: 30px;
}

.mini-user {
    flex: 1;
    margin: 0 10px;
}

.mini-score {
    font-weight: 600;
    color: var(--primary-color);
}

.rank-1 .mini-rank { color: var(--achievement-gold); }
.rank-2 .mini-rank { color: var(--achievement-silver); }
.rank-3 .mini-rank { color: var(--achievement-bronze); }

.leaderboard-footer {
    margin-top: 15px;
    text-align: center;
}

.view-full-link {
    color: var(--primary-color);
    text-decoration: none;
    font-size: 0.9rem;
    font-weight: 500;
}

.view-full-link:hover {
    text-decoration: underline;
}

.widget-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
}

.widget-header h5 {
    margin: 0;
    color: #333;
    font-weight: 600;
}

.level-display {
    background: var(--primary-color);
    color: white;
    padding: 4px 10px;
    border-radius: 15px;
    font-size: 0.8rem;
    font-weight: 600;
}

.widget-footer {
    margin-top: 15px;
    text-align: center;
}

.widget-footer small {
    color: #666;
}
`;

// Inject confetti CSS
const style = document.createElement('style');
style.textContent = confettiCSS;
document.head.appendChild(style);

// Global utility functions
window.AchievementUtils = {
    // Show achievement popup manually
    showAchievement: function(achievementData) {
        if (window.achievementManager) {
            window.achievementManager.showAchievementNotification(achievementData);
        }
    },
    
    // Track custom actions
    trackAction: function(actionType, data = {}) {
        if (window.achievementManager) {
            window.achievementManager.trackAction(actionType, data);
        }
    },
    
    // Create progress widget in any container
    createProgressWidget: function(containerId) {
        AchievementManager.createProgressWidget(containerId);
    },
    
    // Create mini leaderboard
    createMiniLeaderboard: function(containerId, type = 'points', limit = 5) {
        AchievementManager.createMiniLeaderboard(containerId, type, limit);
    }
};

// Initialize achievement manager when script loads
window.addEventListener('DOMContentLoaded', function() {
    window.achievementManager = new AchievementManager();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AchievementManager;
}
