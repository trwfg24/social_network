document.addEventListener('DOMContentLoaded', function() {
    const signUpButton = document.getElementById('signUp');
    const signInButton = document.getElementById('signIn');
    const container = document.getElementById('container');
    const signUpForm = document.getElementById('signUpForm');
    const signInForm = document.getElementById('signInForm');

    // Toggle between sign up and sign in
    signUpButton.addEventListener('click', () => {
        container.classList.add("right-panel-active");
    });

    signInButton.addEventListener('click', () => {
        container.classList.remove("right-panel-active");
    });

    document.querySelectorAll('input').forEach(input => {
        input.addEventListener('input', () => {
            const messageBox = document.querySelector('.messages');
            if (messageBox) {
                messageBox.style.display = 'none';
            }
        });
    });

    function validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    function validatePassword(password) {
        return password.length >= 6;
    }

    // --- Sign Up Form Validation trước khi submit ---
    signUpForm.addEventListener('submit', function(e) {
        const username = document.getElementById('signUpUsername').value;
        const name = document.getElementById('signUpName').value;
        const email = document.getElementById('signUpEmail').value;
        const password = document.getElementById('signUpPassword').value;
        const confirmPassword = document.getElementById('signUpConfirmPassword').value;

        if (!username.trim()) {
            e.preventDefault();
            showMessage('signUpMessage', 'Vui lòng nhập tên tài khoản', 'error');
            return;
        }
        if (username.length < 3) {
            e.preventDefault();
            showMessage('signUpMessage', 'Tên tài khoản phải có ít nhất 3 ký tự', 'error');
            return;
        }
        if (!name.trim()) {
            e.preventDefault();
            showMessage('signUpMessage', 'Vui lòng nhập họ và tên', 'error');
            return;
        }
        if (!validateEmail(email)) {
            e.preventDefault();
            showMessage('signUpMessage', 'Email không hợp lệ', 'error');
            return;
        }
        if (!validatePassword(password)) {
            e.preventDefault();
            showMessage('signUpMessage', 'Mật khẩu phải có ít nhất 6 ký tự', 'error');
            return;
        }
        if (password !== confirmPassword) {
            e.preventDefault();
            showMessage('signUpMessage', 'Mật khẩu xác nhận không khớp', 'error');
            return;
        }
        // Nếu qua hết validate thì form sẽ submit lên backend, backend xử lý đăng ký
    });

    // --- Sign In Form Validation trước khi submit ---
    signInForm.addEventListener('submit', function(e) {
        const username = document.getElementById('signInUsername').value;
        const password = document.getElementById('signInPassword').value;

        if (!username.trim()) {
            e.preventDefault();
            showMessage('signInMessage', 'Vui lòng nhập tài khoản hoặc email', 'error');
            return;
        }
        if (!password.trim()) {
            e.preventDefault();
            showMessage('signInMessage', 'Vui lòng nhập mật khẩu', 'error');
            return;
        }
        // Nếu hợp lệ thì form gửi POST lên backend để xử lý đăng nhập
    });
    
    // --- Xóa message khi người dùng bắt đầu nhập ---
    const inputs = document.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            const form = this.closest('form');
            const messageId = form.id === 'signUpForm' ? 'signUpMessage' : 'signInMessage';
            const msgDiv = document.getElementById(messageId);
            if (msgDiv) {
                msgDiv.style.display = 'none';
                msgDiv.textContent = '';
            }
        });
    });

    // --- Các handler khác giữ nguyên (social login, forgot password, password strength indicator) ---

    document.querySelectorAll('.social').forEach(social => {
        social.addEventListener('click', function(e) {
            e.preventDefault();
            const platform = this.textContent.includes('📘') ? 'Facebook' :
                             this.textContent.includes('🌐') ? 'Google' : 'LinkedIn';
            alert(`Đăng nhập với ${platform} (Demo)`);
        });
    });

    document.querySelector('.forgot-password').addEventListener('click', function(e) {
        e.preventDefault();
        const email = prompt('Nhập email để khôi phục mật khẩu:');
        if (email && validateEmail(email)) {
            alert(`Đã gửi link khôi phục mật khẩu đến ${email}`);
        } else if (email) {
            alert('Email không hợp lệ');
        }
    });

    document.getElementById('signUpPassword').addEventListener('input', function(e) {
        const password = e.target.value;
        const strength = password.length >= 8 && /[A-Z]/.test(password) && /[0-9]/.test(password) ? 'mạnh' :
                         password.length >= 6 ? 'trung bình' : 'yếu';
        const color = strength === 'mạnh' ? '#4caf50' : strength === 'trung bình' ? '#ff9800' : '#f44336';
        e.target.style.borderColor = color;
    });

});
