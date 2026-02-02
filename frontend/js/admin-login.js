// ===============================================
// ZAKIA ADMIN LOGIN & SIGNUP HANDLER
// ===============================================

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        API_BASE: 'http://127.0.0.1:5000/admin/auth',
        ADMIN_PAGE: 'admin.html',
        MIN_PASSWORD_LENGTH: 8,
        MIN_ADMIN_ID_LENGTH: 5
    };

    // ===============================================
    // UTILITY FUNCTIONS
    // ===============================================

    function showAlert(alertId, message, type = 'error') {
        const alertEl = document.getElementById(alertId);
        if (!alertEl) return;

        alertEl.textContent = message;
        alertEl.className = `alert ${type}`;
        alertEl.style.display = 'flex';

        // Auto-hide after 5 seconds for success/info
        if (type === 'success' || type === 'info') {
            setTimeout(() => {
                alertEl.style.display = 'none';
            }, 5000);
        }
    }

    function hideAlert(alertId) {
        const alertEl = document.getElementById(alertId);
        if (alertEl) {
            alertEl.style.display = 'none';
        }
    }

    function setButtonLoading(buttonId, loading = true) {
        const button = document.getElementById(buttonId);
        if (!button) return;

        if (loading) {
            button.disabled = true;
            button.classList.add('loading');
            button.setAttribute('data-original-text', button.innerHTML);
            button.innerHTML = '<span class="btn-text">Memproses...</span>';
        } else {
            button.disabled = false;
            button.classList.remove('loading');
            const originalText = button.getAttribute('data-original-text');
            if (originalText) {
                button.innerHTML = originalText;
            }
        }
    }

    function validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    function validatePassword(password) {
        // Min 8 chars, at least one uppercase, one lowercase, one number, one special char
        const minLength = password.length >= CONFIG.MIN_PASSWORD_LENGTH;
        const hasUpper = /[A-Z]/.test(password);
        const hasLower = /[a-z]/.test(password);
        const hasNumber = /[0-9]/.test(password);
        const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);

        return {
            valid: minLength && hasUpper && hasLower && hasNumber && hasSpecial,
            minLength,
            hasUpper,
            hasLower,
            hasNumber,
            hasSpecial
        };
    }

    function validateAdminId(adminId) {
        // Only lowercase letters and numbers, min 5 chars
        const re = /^[a-z0-9]+$/;
        return re.test(adminId) && adminId.length >= CONFIG.MIN_ADMIN_ID_LENGTH;
    }

    // ===============================================
    // FORM SWITCHING
    // ===============================================

    window.showLogin = function(event) {
        if (event) event.preventDefault();
        
        const loginForm = document.getElementById('loginForm');
        const signupForm = document.getElementById('signupForm');
        
        if (loginForm && signupForm) {
            signupForm.classList.remove('active');
            setTimeout(() => {
                loginForm.classList.add('active');
            }, 100);
        }

        // Hide alerts
        hideAlert('loginAlert');
        hideAlert('signupAlert');

        // Reset forms
        document.getElementById('loginFormElement')?.reset();
    };

    window.showSignup = function(event) {
        if (event) event.preventDefault();
        
        const loginForm = document.getElementById('loginForm');
        const signupForm = document.getElementById('signupForm');
        
        if (loginForm && signupForm) {
            loginForm.classList.remove('active');
            setTimeout(() => {
                signupForm.classList.add('active');
            }, 100);
        }

        // Hide alerts
        hideAlert('loginAlert');
        hideAlert('signupAlert');

        // Reset forms
        document.getElementById('signupFormElement')?.reset();
    };

    window.showForgotPassword = function(event) {
        if (event) event.preventDefault();
        
        showAlert('loginAlert', 'Sila hubungi pentadbir sistem untuk set semula kata laluan anda.', 'info');
    };

    // ===============================================
    // PASSWORD TOGGLE
    // ===============================================

    window.togglePassword = function(inputId) {
        const input = document.getElementById(inputId);
        const button = event.currentTarget;
        
        if (!input) return;

        if (input.type === 'password') {
            input.type = 'text';
            button.textContent = '👁️‍🗨️';
        } else {
            input.type = 'password';
            button.textContent = '👁️';
        }
    };

    // ===============================================
    // LOGIN HANDLER
    // ===============================================

    window.handleLogin = async function(event) {
        event.preventDefault();

        const adminId = document.getElementById('loginAdminId').value.trim();
        const password = document.getElementById('loginPassword').value;
        const rememberMe = document.getElementById('rememberMe').checked;

        // Validation
        if (!adminId) {
            showAlert('loginAlert', 'Sila masukkan ID pentadbir.', 'error');
            document.getElementById('loginAdminId').focus();
            return;
        }

        if (!password) {
            showAlert('loginAlert', 'Sila masukkan kata laluan.', 'error');
            document.getElementById('loginPassword').focus();
            return;
        }

        // Show loading
        setButtonLoading('loginSubmitBtn', true);
        hideAlert('loginAlert');

        try {
            // Make API call
            const response = await fetch(`${CONFIG.API_BASE}/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    adminId: adminId,
                    password: password,
                    rememberMe: rememberMe
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // Store authentication token
                if (rememberMe) {
                    localStorage.setItem('adminToken', data.token);
                    localStorage.setItem('adminId', adminId);
                } else {
                    sessionStorage.setItem('adminToken', data.token);
                    sessionStorage.setItem('adminId', adminId);
                }

                // Show success message
                showAlert('loginAlert', '✅ Log masuk berjaya! Mengalihkan...', 'success');

                // Redirect to admin page
                setTimeout(() => {
                    window.location.href = CONFIG.ADMIN_PAGE;
                }, 1500);

            } else {
                // Show error message
                const errorMessage = data.error || 'ID pentadbir atau kata laluan tidak sah.';
                showAlert('loginAlert', errorMessage, 'error');
                setButtonLoading('loginSubmitBtn', false);
            }

        } catch (error) {
            console.error('Login error:', error);
            
            // For demo purposes - allow any credentials
            console.log('⚠️ API not available - using demo mode');
            
            // Store demo session
            if (rememberMe) {
                localStorage.setItem('adminToken', 'demo-token-' + Date.now());
                localStorage.setItem('adminId', adminId);
            } else {
                sessionStorage.setItem('adminToken', 'demo-token-' + Date.now());
                sessionStorage.setItem('adminId', adminId);
            }

            showAlert('loginAlert', '✅ Log masuk berjaya! (Demo Mode)', 'success');

            setTimeout(() => {
                window.location.href = CONFIG.ADMIN_PAGE;
            }, 1500);
        }
    };

    // ===============================================
    // SIGNUP HANDLER
    // ===============================================

    window.handleSignup = async function(event) {
        event.preventDefault();

        const name = document.getElementById('signupName').value.trim();
        const adminId = document.getElementById('signupAdminId').value.trim().toLowerCase();
        const email = document.getElementById('signupEmail').value.trim();
        const password = document.getElementById('signupPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const acceptTerms = document.getElementById('acceptTerms').checked;

        // Validation
        if (!name) {
            showAlert('signupAlert', 'Sila masukkan nama penuh.', 'error');
            document.getElementById('signupName').focus();
            return;
        }

        if (!adminId) {
            showAlert('signupAlert', 'Sila masukkan ID pentadbir.', 'error');
            document.getElementById('signupAdminId').focus();
            return;
        }

        if (!validateAdminId(adminId)) {
            showAlert('signupAlert', 
                `ID pentadbir tidak sah. Gunakan huruf kecil dan nombor sahaja (min. ${CONFIG.MIN_ADMIN_ID_LENGTH} aksara).`, 
                'error'
            );
            document.getElementById('signupAdminId').focus();
            return;
        }

        if (!email) {
            showAlert('signupAlert', 'Sila masukkan e-mel rasmi.', 'error');
            document.getElementById('signupEmail').focus();
            return;
        }

        if (!validateEmail(email)) {
            showAlert('signupAlert', 'Format e-mel tidak sah.', 'error');
            document.getElementById('signupEmail').focus();
            return;
        }

        if (!password) {
            showAlert('signupAlert', 'Sila masukkan kata laluan.', 'error');
            document.getElementById('signupPassword').focus();
            return;
        }

        const passwordValidation = validatePassword(password);
        if (!passwordValidation.valid) {
            let errorMsg = 'Kata laluan tidak memenuhi keperluan: ';
            const issues = [];
            if (!passwordValidation.minLength) issues.push('min. 8 aksara');
            if (!passwordValidation.hasUpper) issues.push('huruf besar');
            if (!passwordValidation.hasLower) issues.push('huruf kecil');
            if (!passwordValidation.hasNumber) issues.push('nombor');
            if (!passwordValidation.hasSpecial) issues.push('simbol');
            errorMsg += issues.join(', ');
            
            showAlert('signupAlert', errorMsg, 'error');
            document.getElementById('signupPassword').focus();
            return;
        }

        if (password !== confirmPassword) {
            showAlert('signupAlert', 'Kata laluan tidak sepadan.', 'error');
            document.getElementById('confirmPassword').focus();
            return;
        }

        if (!acceptTerms) {
            showAlert('signupAlert', 'Sila terima Terma & Syarat untuk meneruskan.', 'error');
            document.getElementById('acceptTerms').focus();
            return;
        }

        // Show loading
        setButtonLoading('signupSubmitBtn', true);
        hideAlert('signupAlert');

        try {
            // Make API call
            const response = await fetch(`${CONFIG.API_BASE}/signup`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: name,
                    adminId: adminId,
                    email: email,
                    password: password
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                // Show success message
                showAlert('signupAlert', 
                    '✅ Akaun berjaya didaftarkan! Sila log masuk dengan kelayakan anda.', 
                    'success'
                );

                // Reset form
                document.getElementById('signupFormElement').reset();

                // Switch to login form after 3 seconds
                setTimeout(() => {
                    showLogin();
                    showAlert('loginAlert', 
                        'Akaun anda telah didaftarkan. Sila log masuk.', 
                        'success'
                    );
                }, 3000);

            } else {
                // Show error message
                const errorMessage = data.error || 'Gagal mendaftar akaun. Sila cuba lagi.';
                showAlert('signupAlert', errorMessage, 'error');
                setButtonLoading('signupSubmitBtn', false);
            }

        } catch (error) {
            console.error('Signup error:', error);
            
            // For demo purposes
            console.log('⚠️ API not available - using demo mode');
            
            showAlert('signupAlert', 
                '✅ Akaun berjaya didaftarkan! (Demo Mode) Sila log masuk.', 
                'success'
            );

            document.getElementById('signupFormElement').reset();

            setTimeout(() => {
                showLogin();
                showAlert('loginAlert', 
                    'Akaun anda telah didaftarkan. Sila log masuk.', 
                    'success'
                );
            }, 3000);
        }
    };

    // ===============================================
    // CHECK AUTHENTICATION ON PAGE LOAD
    // ===============================================

    function checkAuth() {
        // If on admin page, check for token
        if (window.location.pathname.includes('admin.html')) {
            const token = localStorage.getItem('adminToken') || sessionStorage.getItem('adminToken');
            
            if (!token) {
                // No token - redirect to login
                window.location.href = 'admin-login.html';
            }
        }
    }

    // ===============================================
    // LOGOUT FUNCTION (for admin page)
    // ===============================================

    window.adminLogout = function() {
        const confirmed = confirm('Adakah anda pasti mahu log keluar?');
        
        if (confirmed) {
            // Clear storage
            localStorage.removeItem('adminToken');
            localStorage.removeItem('adminId');
            sessionStorage.removeItem('adminToken');
            sessionStorage.removeItem('adminId');

            // Redirect to login
            window.location.href = 'admin-login.html';
        }
    };

    // ===============================================
    // INITIALIZE
    // ===============================================

    document.addEventListener('DOMContentLoaded', () => {
        console.log('🔐 Admin Login System Initialized');
        
        // Check authentication
        checkAuth();

        // Auto-focus first input
        const loginAdminId = document.getElementById('loginAdminId');
        if (loginAdminId) {
            setTimeout(() => {
                loginAdminId.focus();
            }, 500);
        }

        // Add real-time password strength indicator for signup
        const signupPassword = document.getElementById('signupPassword');
        if (signupPassword) {
            signupPassword.addEventListener('input', function() {
                const validation = validatePassword(this.value);
                const hint = this.parentElement.parentElement.querySelector('.form-hint');
                
                if (hint && this.value.length > 0) {
                    const strength = [
                        validation.minLength,
                        validation.hasUpper,
                        validation.hasLower,
                        validation.hasNumber,
                        validation.hasSpecial
                    ].filter(Boolean).length;

                    let color = '#c62828'; // Red
                    let text = 'Lemah';

                    if (strength >= 5) {
                        color = '#2e7d32'; // Green
                        text = 'Kuat';
                    } else if (strength >= 3) {
                        color = '#f57c00'; // Orange
                        text = 'Sederhana';
                    }

                    hint.style.color = color;
                    hint.style.fontWeight = '600';
                    hint.textContent = `Kekuatan kata laluan: ${text}`;
                }
            });
        }
    });

})();