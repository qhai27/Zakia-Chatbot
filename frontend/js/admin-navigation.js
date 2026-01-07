// ===============================================
// UNIFIED NAVIGATION HANDLER
// Ensures only one section is visible at a time
// ===============================================

(function () {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('🧭 Navigation handler initializing...');

        // Section mapping
        const SECTION_MAP = {
            'faqs': 'faqSection',
            'reminders': 'remindersSection',
            'chatlog': 'chatlogSection',
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

            // Update active nav item
            const navItems = document.querySelectorAll('.nav-item');
            navItems.forEach(nav => {
                nav.classList.remove('active');
                if (nav.getAttribute('data-section') === sectionKey) {
                    nav.classList.add('active');
                }
            });

            // Trigger section-specific loading
            switch (sectionKey) {
                case 'faqs':
                    // FAQ section - already loaded by admin-faq.js
                    if (window.AdminAPI && window.AdminAPI.reload) {
                        window.AdminAPI.reload();
                    }
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

        // Attach navigation listeners
        function setupNavigation() {
            const navItems = document.querySelectorAll('.nav-item[data-section]');

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

        // Make navigation handler globally accessible
        window.AdminNavigation = {
            navigate: handleNavigation,
            showSection: (sectionKey) => handleNavigation(sectionKey)
        };

        console.log('✅ Navigation handler initialized');
    });
})();


