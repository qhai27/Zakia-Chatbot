// ===============================================
// ADMIN AUTHENTICATION CHECK
// verify user is authenticated
// ===============================================

(function() {
    'use strict';

    // Check authentication immediately (synchronous)
    function checkAuthentication() {
        // Check for token in localStorage or sessionStorage
        const token = localStorage.getItem('adminToken') || sessionStorage.getItem('adminToken');
        const adminId = localStorage.getItem('adminId') || sessionStorage.getItem('adminId');
        
        // If no token found, redirect to login
        if (!token) {
            console.log('🔒 No authentication token found - redirecting to login');
            window.location.href = 'admin-login.html';
            return false;
        }

        console.log('✅ Authentication token found:', adminId);
        return true;
    }

    // Load admin info
    function loadAdminInfo() {
        const adminName = localStorage.getItem('adminName') || 
                         sessionStorage.getItem('adminName') || 
                         'Admin';
        
        const adminId = localStorage.getItem('adminId') || 
                       sessionStorage.getItem('adminId') || 
                       '';

        // Update user display when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                updateAdminDisplay(adminName, adminId);
            });
        } else {
            updateAdminDisplay(adminName, adminId);
        }
    }

    function updateAdminDisplay(name, id) {
        const adminUserNameEl = document.getElementById('adminUserName');
        if (adminUserNameEl) {
            adminUserNameEl.textContent = name;
        }

        console.log(`👤 Logged in as: ${name} (${id})`);
    }

    // Verify token with backend (optional - for production)
    async function verifyTokenWithBackend(token) {
        try {
            const response = await fetch('http://127.0.0.1:5000/admin/auth/verify', {
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
                if (data.name) {
                    localStorage.setItem('adminName', data.name);
                }
                
                return true;
            } else {
                console.log('❌ Token invalid - logging out');
                // Token is invalid - clear and redirect
                localStorage.removeItem('adminToken');
                localStorage.removeItem('adminId');
                localStorage.removeItem('adminName');
                sessionStorage.removeItem('adminToken');
                sessionStorage.removeItem('adminId');
                sessionStorage.removeItem('adminName');
                
                window.location.href = 'admin-login.html';
                return false;
            }
        } catch (error) {
            console.log('⚠️ Backend verification failed (demo mode):', error);
            // In demo mode, allow access even if backend is down
            return true;
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
                }
            }, WARNING_TIME);

            // Auto logout
            logoutTimeout = setTimeout(() => {
                alert('Sesi anda telah tamat. Sila log masuk semula.');
                
                // Clear storage
                localStorage.removeItem('adminToken');
                localStorage.removeItem('adminId');
                localStorage.removeItem('adminName');
                sessionStorage.removeItem('adminToken');
                sessionStorage.removeItem('adminId');
                sessionStorage.removeItem('adminName');

                // Redirect to login
                window.location.href = 'admin-login.html';
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

    // Initialize
    const isAuthenticated = checkAuthentication();

    if (isAuthenticated) {
        loadAdminInfo();

        // Optional: Verify token with backend in background
        const token = localStorage.getItem('adminToken') || sessionStorage.getItem('adminToken');
        if (token) {
            verifyTokenWithBackend(token);
        }

        // Optional: Setup session timeout (uncomment to enable)
        // setupSessionTimeout();

        console.log('🔐 Authentication check complete - access granted');
    }

})();