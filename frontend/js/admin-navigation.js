// ===============================================
// UNIFIED NAVIGATION HANDLER FOR ADMIN INTERFACE
// Handles sidebar and topbar navigation clicks,
// section visibility, and section-specific loading.
// ===============================================

(function () {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('🧭 Navigation handler initializing...');

        // Section mapping - UPDATED to include contactRequests
        const SECTION_MAP = {
            'faqs': 'faqSection',
            'reminders': 'remindersSection',
            'chatlog': 'chatlogSection',
            'contactRequests': 'contactRequestsSection',  
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

            // Stop auto-refresh on sections being left
            stopAutoRefreshOnNavigation(sectionKey);

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
            loadSectionData(sectionKey);
        }

        // Stop auto-refresh when navigating away from sections
        function stopAutoRefreshOnNavigation(targetSection) {
            // Stop ChatLog auto-refresh when leaving
            if (targetSection !== 'chatlog') {
                if (window.ChatLogOperations && window.ChatLogOperations.stopAutoRefresh) {
                    window.ChatLogOperations.stopAutoRefresh();
                }
            }

            // Stop Contact Requests auto-refresh when leaving
            if (targetSection !== 'contactRequests') {
                if (window.ContactRequestAdmin && window.ContactRequestAdmin.stopAutoRefresh) {
                    window.ContactRequestAdmin.stopAutoRefresh();
                    console.log('⏸️ Stopped Contact Requests auto-refresh');
                }
            }
        }

        // Load section-specific data
        function loadSectionData(sectionKey) {
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

                case 'contactRequests':
                    // ✅  Contact Requests section
                    console.log('📞 Loading Contact Requests section...');
                    if (window.ContactRequestAdmin) {
                        setTimeout(() => {
                            console.log('   - Calling ContactRequestAdmin.load()');
                            window.ContactRequestAdmin.load();
                            
                            console.log('   - Starting auto-refresh');
                            window.ContactRequestAdmin.startAutoRefresh();
                            
                            console.log('✅ Contact Requests section loaded');
                        }, 150);
                    } else {
                        console.error('❌ ContactRequestAdmin not found! Make sure admin-contact.js is loaded.');
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

                default:
                    console.warn(`⚠️ No loader defined for section: ${sectionKey}`);
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

            // Contact Requests count (if available)
            const pendingContacts = document.getElementById('statsPendingContacts')?.textContent || '0';
            const topbarContactsEl = document.getElementById('topbarPendingContacts');
            if (topbarContactsEl) {
                topbarContactsEl.textContent = pendingContacts;
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
        const pendingContactsEl = document.getElementById('statsPendingContacts');

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

        if (pendingContactsEl) {
            observer.observe(pendingContactsEl, { 
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
            updateStats: updateTopbarStats,
            getSectionMap: () => SECTION_MAP
        };

        console.log('✅ Navigation handler initialized with Contact Requests support');
        console.log('   Available sections:', Object.keys(SECTION_MAP));
    });
})();