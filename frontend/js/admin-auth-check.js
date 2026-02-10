// ===============================================
// ADMIN AUTHENTICATION CHECK
// Verify user is authenticated before accessing admin panel
// ===============================================

(function() {
    'use strict';

    const API_BASE = 'http://127.0.0.1:5000/admin/auth';

    // Check authentication immediately (synchronous)
    function checkAuthentication() {
        // Check for token in localStorage or sessionStorage
        const token = localStorage.getItem('adminToken') || sessionStorage.getItem('adminToken');
        const adminId = localStorage.getItem('adminId') || sessionStorage.getItem('adminId');
        
        // If no token found, redirect to login
        if (!token) {
            console.log('🔒 No authentication token found - redirecting to login');
            redirectToLogin();
            return false;
        }

        console.log('✅ Authentication token found:', adminId);
        return true;
    }

    // Redirect to login page
    function redirectToLogin() {
        // Clear any stored data
        clearAuthData();
        
        // Redirect to login
        window.location.href = 'admin-login.html';
    }

    // Clear authentication data
    function clearAuthData() {
        localStorage.removeItem('adminToken');
        localStorage.removeItem('adminId');
        localStorage.removeItem('adminName');
        localStorage.removeItem('adminEmail');
        sessionStorage.removeItem('adminToken');
        sessionStorage.removeItem('adminId');
        sessionStorage.removeItem('adminName');
        sessionStorage.removeItem('adminEmail');
    }

    // Load admin info
    function loadAdminInfo() {
        const adminName = localStorage.getItem('adminName') || 
                         sessionStorage.getItem('adminName') || 
                         'Admin';
        
        const adminId = localStorage.getItem('adminId') || 
                       sessionStorage.getItem('adminId') || 
                       '';

        const adminEmail = localStorage.getItem('adminEmail') || 
                          sessionStorage.getItem('adminEmail') || 
                          '';

        // Update user display when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                updateAdminDisplay(adminName, adminId, adminEmail);
            });
        } else {
            updateAdminDisplay(adminName, adminId, adminEmail);
        }
    }

    function updateAdminDisplay(name, id, email) {
        // Update username in topbar
        const adminUserNameEl = document.getElementById('adminUserName');
        if (adminUserNameEl) {
            adminUserNameEl.textContent = name;
        }

        // Update admin ID if element exists
        const adminIdEl = document.getElementById('adminIdDisplay');
        if (adminIdEl) {
            adminIdEl.textContent = id;
        }

        // Update email if element exists
        const adminEmailEl = document.getElementById('adminEmailDisplay');
        if (adminEmailEl) {
            adminEmailEl.textContent = email;
        }

        console.log(`👤 Logged in as: ${name} (${id})`);
    }

    // Verify token with backend
    async function verifyTokenWithBackend(token) {
        try {
            const response = await fetch(`${API_BASE}/verify`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ token: token })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                console.log('✅ Token verified with backend');
                
                // Update stored admin info
                const storage = localStorage.getItem('adminToken') ? localStorage : sessionStorage;
                
                if (data.name) {
                    storage.setItem('adminName', data.name);
                }
                if (data.admin_id) {
                    storage.setItem('adminId', data.admin_id);
                }
                if (data.email) {
                    storage.setItem('adminEmail', data.email);
                }
                
                // Update display
                updateAdminDisplay(data.name, data.admin_id, data.email);
                
                return true;
            } else {
                console.log('❌ Token invalid:', data.error);
                
                // Show notification before redirect
                showTokenExpiredNotification(data.error);
                
                // Token is invalid - redirect to login
                setTimeout(() => {
                    redirectToLogin();
                }, 2000);
                
                return false;
            }
        } catch (error) {
            console.warn('⚠️ Backend verification failed:', error.message);
            
            // In case backend is down, allow access but log warning
            // This prevents lockout if backend is temporarily unavailable
            console.log('⚠️ Proceeding in offline mode - backend unavailable');
            return true;
        }
    }

    // Show token expired notification
    function showTokenExpiredNotification(message) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #fee2e2;
            color: #991b1b;
            padding: 1rem 1.5rem;
            border-radius: 0.5rem;
            border-left: 4px solid #ef4444;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            z-index: 10000;
            max-width: 400px;
            animation: slideIn 0.3s ease-out;
        `;
        notification.textContent = message || 'Sesi anda telah tamat. Mengalihkan ke halaman log masuk...';
        document.body.appendChild(notification);
    }

    // Setup logout functionality
    function setupLogout() {
        // Wait for DOM to be ready
        const attachLogoutListener = () => {
            const logoutBtn = document.getElementById('logoutBtn');
            if (logoutBtn) {
                logoutBtn.addEventListener('click', async (e) => {
                    e.preventDefault();
                    
                    const confirmed = confirm('Adakah anda pasti untuk log keluar?');
                    if (!confirmed) return;
                    
                    console.log('🚪 Logging out...');
                    
                    // Get token
                    const token = localStorage.getItem('adminToken') || sessionStorage.getItem('adminToken');
                    
                    // Call logout API
                    try {
                        await fetch(`${API_BASE}/logout`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ token: token })
                        });
                        console.log('✅ Logout successful');
                    } catch (error) {
                        console.warn('⚠️ Logout API call failed:', error);
                    }
                    
                    // Clear local data and redirect
                    redirectToLogin();
                });
                
                console.log('✅ Logout button listener attached');
            }
        };

        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', attachLogoutListener);
        } else {
            attachLogoutListener();
        }
    }

    // Session timeout warning (optional)
    function setupSessionTimeout() {
        const WARNING_TIME = 25 * 60 * 1000; // 25 minutes
        const SESSION_TIME = 30 * 60 * 1000; // 30 minutes

        let warningTimeout;
        let logoutTimeout;

        function resetTimers() {
            clearTimeout(warningTimeout);
            clearTimeout(logoutTimeout);

            // Show warning before logout
            warningTimeout = setTimeout(() => {
                const continueSession = confirm(
                    'Sesi anda akan tamat dalam 5 minit. Klik OK untuk teruskan.'
                );
                
                if (continueSession) {
                    resetTimers();
                    
                    // Optionally refresh token here
                    const token = localStorage.getItem('adminToken') || sessionStorage.getItem('adminToken');
                    if (token) {
                        verifyTokenWithBackend(token);
                    }
                }
            }, WARNING_TIME);

            // Auto logout
            logoutTimeout = setTimeout(() => {
                alert('Sesi anda telah tamat. Sila log masuk semula.');
                redirectToLogin();
            }, SESSION_TIME);
        }

        // Reset timers on user activity
        const events = ['mousedown', 'keydown', 'scroll', 'touchstart'];
        events.forEach(event => {
            document.addEventListener(event, resetTimers, true);
        });

        // Start initial timers
        resetTimers();

        console.log('⏰ Session timeout monitoring active (30 minutes)');
    }

    // Initialize authentication check
    function initialize() {
        console.log('🔐 Initializing authentication check...');
        
        const isAuthenticated = checkAuthentication();

        if (isAuthenticated) {
            loadAdminInfo();
            setupLogout();

            // Verify token with backend in background
            const token = localStorage.getItem('adminToken') || sessionStorage.getItem('adminToken');
            if (token) {
                verifyTokenWithBackend(token);
            }

            // Optional: Setup session timeout (uncomment to enable)
            // setupSessionTimeout();

            console.log('🔓 Authentication check complete - access granted');
        } else {
            console.log('🔒 Authentication failed - access denied');
        }
    }

    // Make auth functions globally accessible
    window.AdminAuth = {
        checkAuth: checkAuthentication,
        logout: redirectToLogin,
        verifyToken: verifyTokenWithBackend,
        clearData: clearAuthData,
        getToken: () => localStorage.getItem('adminToken') || sessionStorage.getItem('adminToken'),
        getAdminId: () => localStorage.getItem('adminId') || sessionStorage.getItem('adminId'),
        getAdminName: () => localStorage.getItem('adminName') || sessionStorage.getItem('adminName')
    };

    // Run initialization
    initialize();

})();