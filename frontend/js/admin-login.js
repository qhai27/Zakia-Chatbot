// ===============================================
// ADMIN LOGIN & SIGNUP HANDLER
// Handles authentication for ZAKIA Admin Panel
// ===============================================

const API_BASE = 'http://127.0.0.1:5000/admin/auth';

// ===============================================
// UTILITY FUNCTIONS
// ===============================================

function showAlert(elementId, message, type = 'error') {
    const alertEl = document.getElementById(elementId);
    if (!alertEl) return;

    alertEl.className = `alert alert-${type}`;
    alertEl.textContent = message;
    alertEl.style.display = 'block';

    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            alertEl.style.display = 'none';
        }, 5000);
    }
}

function hideAlert(elementId) {
    const alertEl = document.getElementById(elementId);
    if (alertEl) {
        alertEl.style.display = 'none';
    }
}

function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const toggleIcon = document.querySelector(`[toggle="#${inputId}"]`);
    
    if (!input || !toggleIcon) return;

    if (input.type === 'password') {
        input.type = 'text';
        toggleIcon.classList.remove('fa-eye');
        toggleIcon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        toggleIcon.classList.remove('fa-eye-slash');
        toggleIcon.classList.add('fa-eye');
    }
}

function setButtonLoading(buttonId, isLoading) {
    const button = document.getElementById(buttonId);
    if (!button) return;

    if (isLoading) {
        button.disabled = true;
        button.classList.add('loading');
        const btnText = button.querySelector('.btn-text');
        if (btnText) {
            btnText.dataset.originalText = btnText.textContent;
            btnText.textContent = 'Memproses...';
        }
    } else {
        button.disabled = false;
        button.classList.remove('loading');
        const btnText = button.querySelector('.btn-text');
        if (btnText && btnText.dataset.originalText) {
            btnText.textContent = btnText.dataset.originalText;
        }
    }
}

// ===============================================
// FORM SWITCHING
// ===============================================

function showLogin(event) {
    if (event) event.preventDefault();
    
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    
    if (loginForm && signupForm) {
        signupForm.classList.remove('active');
        loginForm.classList.add('active');
    }
    
    // Clear both forms
    document.getElementById('loginFormElement')?.reset();
    hideAlert('loginAlert');
}

function showSignup(event) {
    if (event) event.preventDefault();
    
    const loginForm = document.getElementById('loginForm');
    const signupForm = document.getElementById('signupForm');
    
    if (loginForm && signupForm) {
        loginForm.classList.remove('active');
        signupForm.classList.add('active');
    }
    
    // Clear both forms
    document.getElementById('signupFormElement')?.reset();
    hideAlert('signupAlert');
}

function showForgotPassword(event) {
    if (event) event.preventDefault();
    alert('Untuk menetapkan semula kata laluan, sila hubungi pentadbir sistem.');
}

// ===============================================
// CLIENT-SIDE VALIDATION
// ===============================================

function validateAdminId(adminId) {
    if (!adminId || adminId.length < 5) {
        return {
            valid: false,
            message: 'ID pentadbir mesti sekurang-kurangnya 5 aksara'
        };
    }
    
    if (!/^[a-z0-9]+$/.test(adminId)) {
        return {
            valid: false,
            message: 'ID pentadbir hanya boleh mengandungi huruf kecil dan nombor'
        };
    }
    
    return { valid: true };
}

function validateEmail(email) {
    if (!email) {
        return {
            valid: false,
            message: 'E-mel diperlukan'
        };
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        return {
            valid: false,
            message: 'Format e-mel tidak sah'
        };
    }
    
    return { valid: true };
}

function validatePassword(password) {
    if (!password || password.length < 8) {
        return {
            valid: false,
            message: 'Kata laluan mesti sekurang-kurangnya 8 aksara'
        };
    }
    
    const hasUpper = /[A-Z]/.test(password);
    const hasLower = /[a-z]/.test(password);
    const hasDigit = /[0-9]/.test(password);
    const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);
    
    if (!hasUpper || !hasLower || !hasDigit || !hasSpecial) {
        return {
            valid: false,
            message: 'Kata laluan mesti mengandungi huruf besar, huruf kecil, nombor dan simbol'
        };
    }
    
    return { valid: true };
}

// ===============================================
// LOGIN HANDLER
// ===============================================

async function handleLogin(event) {
    event.preventDefault();
    
    console.log('🔐 Login attempt started...');
    
    // Get form data
    const adminId = document.getElementById('loginAdminId')?.value.trim().toLowerCase();
    const password = document.getElementById('loginPassword')?.value;
    const rememberMe = document.getElementById('rememberMe')?.checked || false;
    
    // Clear previous alerts
    hideAlert('loginAlert');
    
    // Validation
    if (!adminId || !password) {
        showAlert('loginAlert', 'Sila masukkan ID pentadbir dan kata laluan', 'error');
        return;
    }
    
    // Set loading state
    setButtonLoading('loginSubmitBtn', true);
    
    try {
        // Call login API
        const response = await fetch(`${API_BASE}/login`, {
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
            console.log('✅ Login successful');
            
            // Store authentication data
            const storage = rememberMe ? localStorage : sessionStorage;
            
            storage.setItem('adminToken', data.token);
            storage.setItem('adminId', data.admin_id);
            storage.setItem('adminName', data.name);
            storage.setItem('adminEmail', data.email);
            
            // Show success message
            showAlert('loginAlert', 'Log masuk berjaya! Mengalihkan...', 'success');
            
            // Redirect to admin panel after short delay
            setTimeout(() => {
                window.location.href = 'admin.html';
            }, 1000);
            
        } else {
            console.log('❌ Login failed:', data.error);
            showAlert('loginAlert', data.error || 'Log masuk gagal', 'error');
            setButtonLoading('loginSubmitBtn', false);
        }
        
    } catch (error) {
        console.error('❌ Login error:', error);
        showAlert('loginAlert', 'Ralat sambungan. Sila pastikan pelayan berjalan.', 'error');
        setButtonLoading('loginSubmitBtn', false);
    }
}

// ===============================================
// SIGNUP HANDLER
// ===============================================

async function handleSignup(event) {
    event.preventDefault();
    
    console.log('\n' + '='.repeat(50));
    console.log('📝 SIGNUP ATTEMPT STARTED');
    console.log('='.repeat(50));
    
    // Get form data
    const name = document.getElementById('signupName')?.value.trim();
    const adminId = document.getElementById('signupAdminId')?.value.trim().toLowerCase();
    const email = document.getElementById('signupEmail')?.value.trim().toLowerCase();
    const password = document.getElementById('signupPassword')?.value;
    const confirmPassword = document.getElementById('confirmPassword')?.value;
    const acceptTerms = document.getElementById('acceptTerms')?.checked;
    
    console.log('📋 Form Data:');
    console.log('  - Name:', name);
    console.log('  - Admin ID:', adminId);
    console.log('  - Email:', email);
    console.log('  - Password length:', password?.length || 0);
    console.log('  - Confirm password length:', confirmPassword?.length || 0);
    console.log('  - Accept terms:', acceptTerms);
    
    // Clear previous alerts
    hideAlert('signupAlert');
    
    // Validation
    console.log('\n🔍 Starting validation...');
    
    if (!name) {
        console.log('❌ Validation failed: Name is empty');
        showAlert('signupAlert', 'Sila masukkan nama penuh', 'error');
        return;
    }
    console.log(' Name validated');
    
    const adminIdCheck = validateAdminId(adminId);
    if (!adminIdCheck.valid) {
        console.log('❌ Validation failed: Admin ID -', adminIdCheck.message);
        showAlert('signupAlert', adminIdCheck.message, 'error');
        return;
    }
    console.log('✅ Admin ID validated');
    
    const emailCheck = validateEmail(email);
    if (!emailCheck.valid) {
        console.log('❌ Validation failed: Email -', emailCheck.message);
        showAlert('signupAlert', emailCheck.message, 'error');
        return;
    }
    console.log(' Email validated');
    
    const passwordCheck = validatePassword(password);
    if (!passwordCheck.valid) {
        console.log('❌ Validation failed: Password -', passwordCheck.message);
        showAlert('signupAlert', passwordCheck.message, 'error');
        return;
    }
    console.log(' Password validated');
    
    if (password !== confirmPassword) {
        console.log('❌ Validation failed: Passwords do not match');
        showAlert('signupAlert', 'Kata laluan tidak sepadan', 'error');
        return;
    }
    console.log(' Password confirmation validated');
    
    if (!acceptTerms) {
        console.log('❌ Validation failed: Terms not accepted');
        showAlert('signupAlert', 'Sila terima Terma & Syarat', 'error');
        return;
    }
    console.log(' Terms accepted');
    
    console.log('\n All validations passed!');
    
    // Set loading state
    setButtonLoading('signupSubmitBtn', true);
    
    // Prepare request data
    const requestData = {
        name: name,
        adminId: adminId,
        email: email,
        password: password
    };
    
    console.log('\n📤 Sending signup request to:', `${API_BASE}/signup`);
    console.log('📦 Request data:', {
        name: requestData.name,
        adminId: requestData.adminId,
        email: requestData.email,
        password: '***' + requestData.password.slice(-3)
    });
    
    try {
        // Call signup API
        const response = await fetch(`${API_BASE}/signup`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        console.log('\n📥 Response received:');
        console.log('  - Status:', response.status);
        console.log('  - Status Text:', response.statusText);
        console.log('  - OK:', response.ok);
        
        const data = await response.json();
        console.log('  - Response data:', data);
        
        if (response.ok && data.success) {
            console.log('\n✅ SIGNUP SUCCESSFUL!');
            console.log('  - Message:', data.message);
            console.log('  - Admin ID:', data.admin_id);
            console.log('  - Name:', data.name);
            console.log('='.repeat(50) + '\n');
            
            // Show success message
            showAlert('signupAlert', 
                `${data.message} Sila log masuk dengan kelayakan anda.`, 
                'success'
            );
            
            // Clear form
            document.getElementById('signupFormElement')?.reset();
            
            // Switch to login form after 3 seconds
            setTimeout(() => {
                console.log('🔄 Switching to login form...');
                showLogin(null);
                
                // Pre-fill admin ID in login form
                const loginAdminIdField = document.getElementById('loginAdminId');
                if (loginAdminIdField) {
                    loginAdminIdField.value = data.admin_id || adminId;
                    console.log(' Pre-filled admin ID in login form');
                }
                
                showAlert('loginAlert', 'Akaun berjaya didaftarkan. Sila log masuk.', 'success');
            }, 3000);
            
        } else {
            console.log('\n❌ SIGNUP FAILED!');
            console.log('  - Error:', data.error);
            console.log('='.repeat(50) + '\n');
            
            showAlert('signupAlert', data.error || 'Pendaftaran gagal', 'error');
            setButtonLoading('signupSubmitBtn', false);
        }
        
    } catch (error) {
        console.error('\n❌ SIGNUP ERROR!');
        console.error('  - Error:', error);
        console.error('  - Message:', error.message);
        console.error('  - Stack:', error.stack);
        console.log('='.repeat(50) + '\n');
        
        showAlert('signupAlert', 
            'Ralat sambungan. Sila pastikan pelayan berjalan di http://127.0.0.1:5000', 
            'error'
        );
        setButtonLoading('signupSubmitBtn', false);
    }
}

// ===============================================
// PAGE INITIALIZATION
// ===============================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🔐 Admin Login Page Initialized');
    
    // Check if already logged in
    const token = localStorage.getItem('adminToken') || sessionStorage.getItem('adminToken');
    if (token) {
        console.log(' Already logged in - redirecting to admin panel');
        window.location.href = 'admin.html';
        return;
    }
    
    // Setup form submissions
    const loginForm = document.getElementById('loginFormElement');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }
    
    const signupForm = document.getElementById('signupFormElement');
    if (signupForm) {
        signupForm.addEventListener('submit', handleSignup);
    }
    
    // Setup password visibility toggles
    document.querySelectorAll('.toggle-password').forEach(button => {
        button.addEventListener('click', function() {
            const inputSelector = this.getAttribute('toggle');
            const inputId = inputSelector.replace('#', '');
            togglePassword(inputId);
        });
    });
    
    console.log(' Event listeners attached');
});