// ===============================================
// UNIFIED NAVIGATION HANDLER FOR ADMIN INTERFACE
// ===============================================

(function () {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('🧭 Navigation handler initializing...');

        // Section mapping
        const SECTION_MAP = {
            'faqs': 'faqSection',
            'reminders': 'remindersSection',
            'chatlog': 'chatlogSection',
            'livechat': 'livechatSection',
            'analytics': 'analyticsSection'
        };

        // Initialize: Hide all sections except FAQ
        function initializeSections() {
            const allSections = document.querySelectorAll('.content-section');
            allSections.forEach(section => {
                section.style.display = 'none';
                section.classList.remove('active');
            });

            // Show FAQ section by default
            const faqSection = document.getElementById('faqSection');
            if (faqSection) {
                faqSection.style.display = 'block';
                faqSection.classList.add('active');
            }

            console.log('✅ Sections initialized - FAQ section shown by default');
        }

        // Navigation handler
        function handleNavigation(sectionKey) {
            console.log(`🧭 Navigating to: ${sectionKey}`);

            // Hide ALL sections first
            const allSections = document.querySelectorAll('.content-section');
            allSections.forEach(section => {
                section.style.display = 'none';
                section.classList.remove('active');
            });

            // Show the selected section
            const sectionId = SECTION_MAP[sectionKey];
            if (sectionId) {
                const targetSection = document.getElementById(sectionId);
                if (targetSection) {
                    targetSection.style.display = 'block';
                    targetSection.classList.add('active');
                    console.log(`✅ Showing section: ${sectionId}`);
                } else {
                    console.error(`❌ Section not found: ${sectionId}`);
                }
            } else {
                console.error(`❌ Unknown section key: ${sectionKey}`);
            }

            // Update active nav item (works for both sidebar and topbar)
            const navItems = document.querySelectorAll('.nav-item, .topbar-nav-item');
            navItems.forEach(nav => {
                nav.classList.remove('active');
                if (nav.getAttribute('data-section') === sectionKey) {
                    nav.classList.add('active');
                }
            });

            // Close mobile nav if open
            const topbarNav = document.getElementById('topbarNav');
            if (topbarNav && topbarNav.classList.contains('mobile-open')) {
                topbarNav.classList.remove('mobile-open');
            }

            // Trigger section-specific loading
            switch (sectionKey) {
                case 'faqs':
                    // FAQ section - already loaded by admin-faq.js
                    if (window.AdminAPI && window.AdminAPI.reload) {
                        window.AdminAPI.reload();
                    }
                    // Update topbar stats
                    updateTopbarStats();
                    break;
                case 'reminders':
                    // Reminders section
                    if (window.ReminderOperations && window.ReminderOperations.load) {
                        setTimeout(() => {
                            window.ReminderOperations.load();
                        }, 100);
                    }
                    break;
                case 'chatlog':
                    // ChatLog section
                    if (window.ChatLogOperations && window.ChatLogOperations.load) {
                        setTimeout(() => {
                            window.ChatLogOperations.load();
                            if (window.ChatLogOperations.startAutoRefresh) {
                                window.ChatLogOperations.startAutoRefresh();
                            }
                        }, 100);
                    }
                    break;
                case 'livechat':
                    if (window.LiveChatAdmin && window.LiveChatAdmin.load) {
                        setTimeout(() => {
                            window.LiveChatAdmin.load();
                        }, 150);
                    }
                    break;
                case 'analytics':
                    // Analytics section
                    if (window.AnalyticsOperations && window.AnalyticsOperations.loadDashboard) {
                        setTimeout(() => {
                            window.AnalyticsOperations.loadDashboard('month');
                        }, 300);
                    }
                    break;
            }
        }

        // Update topbar stats (syncs with sidebar stats)
        function updateTopbarStats() {
            // FAQ count
            const totalFaqs = document.getElementById('totalFaqs')?.textContent || '0';
            const topbarFaqsEl = document.getElementById('topbarTotalFaqs');
            if (topbarFaqsEl) {
                topbarFaqsEl.textContent = totalFaqs;
            }

            // Chat logs count
            const totalLogs = document.getElementById('totalChatLogs')?.textContent || '0';
            const topbarLogsEl = document.getElementById('topbarTotalChatLogs');
            if (topbarLogsEl) {
                topbarLogsEl.textContent = totalLogs;
            }
        }

        // Attach navigation listeners
        function setupNavigation() {
            // Select both sidebar nav items AND topbar nav items
            const navItems = document.querySelectorAll('.nav-item[data-section], .topbar-nav-item[data-section]');

            navItems.forEach(item => {
                // Remove any existing listeners by cloning
                const newItem = item.cloneNode(true);
                item.parentNode.replaceChild(newItem, item);

                // Add new listener
                newItem.addEventListener('click', (e) => {
                    e.preventDefault();
                    e.stopPropagation();

                    const section = newItem.getAttribute('data-section');
                    if (section) {
                        handleNavigation(section);
                    }
                });
            });

            console.log(`✅ Navigation listeners attached to ${navItems.length} nav items`);
        }

        // Initialize on page load
        initializeSections();
        setupNavigation();

        // Setup stat sync (update topbar when sidebar stats change)
        const observer = new MutationObserver(() => {
            updateTopbarStats();
        });

        const totalFaqsEl = document.getElementById('totalFaqs');
        const totalLogsEl = document.getElementById('totalChatLogs');

        if (totalFaqsEl) {
            observer.observe(totalFaqsEl, { 
                childList: true, 
                characterData: true, 
                subtree: true 
            });
        }

        if (totalLogsEl) {
            observer.observe(totalLogsEl, { 
                childList: true, 
                characterData: true, 
                subtree: true 
            });
        }

        // Initial stats sync
        updateTopbarStats();

        // Make navigation handler globally accessible
        window.AdminNavigation = {
            navigate: handleNavigation,
            showSection: (sectionKey) => handleNavigation(sectionKey),
            updateStats: updateTopbarStats
        };

        console.log('✅ Navigation handler initialized');
    });
})();