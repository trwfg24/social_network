const postForm = document.getElementById('postForm');

if (postForm) {
    postForm.addEventListener('submit', function(e) {
        const content = document.getElementById('postContent').value.trim();
        const image = document.getElementById('image-upload').files.length;

        if (!content && image === 0) {
            e.preventDefault(); // Chặn gửi form
            alert('Vui lòng nhập nội dung hoặc chọn ảnh trước khi đăng!');
            return;
        }
    });
}



// Like post functionality
function likePost(button, postId) {
    const countSpan = button.querySelector('.count');
    let count = parseInt(countSpan.textContent);
    const wasLiked = button.classList.contains('liked');

    // 1) UI phản ứng ngay (optimistic UI)
    if (wasLiked) {
        button.classList.remove('liked');
        count--;
        button.style.transform = 'scale(0.9)';
    } else {
        button.classList.add('liked');
        count++;
        button.style.transform = 'scale(1.2)';
    }
    setTimeout(() => { button.style.transform = 'scale(1)'; }, 200);
    countSpan.textContent = count;

    // 2) Gọi API Django để xử lý Like & gửi notification
    fetch(`/like/${postId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "liked") {
            button.classList.add('liked');
        } else if (data.status === "unliked") {
            button.classList.remove('liked');
        }
        // Cập nhật số like từ server
        button.querySelector('.count').textContent = data.likeCount;
    })
    .catch(err => console.error("Fetch error:", err));
}

// Hàm lấy CSRF token (nếu đang dùng Django)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}



// Comment functionality
function commentPost(button) {
    const post = button.closest('.post');
    const author = post.querySelector('.post-author').textContent;
    alert(`Tính năng bình luận cho bài viết của ${author} sẽ được phát triển trong phiên bản tiếp theo!`);
}



// Navigation
function showTab(tab) {
    alert(`Chuyển đến tab: ${tab}`);
}

// Initialize animations
document.addEventListener('DOMContentLoaded', function() {
    // Floating animation for avatar
    const avatar = document.querySelector('.avatar');
    setInterval(() => {
        if (!avatar.matches(':hover')) {
            avatar.style.transform = 'translateY(-5px)';
            setTimeout(() => {
                avatar.style.transform = 'translateY(0)';
            }, 1000);
        }
    }, 4000);

    // Auto-focus on post composer when clicked
    const textarea = document.getElementById('postContent');
    const composer = document.querySelector('.post-composer');
    

});







document.querySelector('.stats').addEventListener('click', function() {
    document.getElementById('friendsModal').style.display = 'block';
    document.body.style.overflow = 'hidden';
});

// Đóng modal khi bấm nút close
function closeFriendsModal() {
    document.getElementById('friendsModal').style.display = 'none';
    document.body.style.overflow = 'auto';
}

function deletePost(postId) {
    if (!confirm("Bạn có chắc muốn xóa bài viết này?")) return;

    fetch(`/delete_post/${postId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'ok') {
            // Xóa element post khỏi DOM
            const postEl = document.getElementById(`post-${postId}`);
            if (postEl) postEl.remove();
            location.reload();
        } else {
            alert('Xóa thất bại: ' + data.message);
        }
    })
    .catch(err => console.error(err));
}




function showFriendsList() {
    const modal = document.getElementById('friendsModal');
    const friendsList = document.getElementById('friendsList');
    
    // Clear existing content
    friendsList.innerHTML = '';
    
    // Populate friends list
    friendsData.forEach(friend => {
        const friendItem = document.createElement('div');
        friendItem.className = 'friend-item';
        friendItem.innerHTML = `
            <div class="friend-avatar">${friend.initials}</div>
            <div class="friend-info">
                <div class="friend-name">${friend.name}</div>
                <div class="friend-status ${friend.status}">
                    ${friend.status === 'online' ? '🟢 Đang hoạt động' : '⚫ Không hoạt động'}
                </div>
            </div>
        `;
        
        friendItem.addEventListener('click', () => {
            alert(`Nhấn vào ${friend.name}`);
        });
        
        friendsList.appendChild(friendItem);
    });
    
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden'; // Prevent background scroll
}

function closeFriendsModal() {
    const modal = document.getElementById('friendsModal');
    modal.style.display = 'none';
    document.body.style.overflow = 'auto'; // Restore scroll
}

// Close modal when clicking outside of it
window.addEventListener('click', function(event) {
    const modal = document.getElementById('friendsModal');
    if (event.target === modal) {
        closeFriendsModal();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeFriendsModal();
    }
});

// Animation khi trang load
window.addEventListener('load', function() {
    const profileBox = document.querySelector('.profile-box');
    profileBox.style.animationDelay = '0.2s';
});




function openEditProfileModal() {
    document.getElementById('editProfileModal').style.display = 'block';
    document.body.style.overflow = 'hidden'; // khóa scroll nền nếu muốn
}

function closeEditProfileModal() {
    document.getElementById('editProfileModal').style.display = 'none';
    document.body.style.overflow = 'auto'; // mở scroll nền lại
}

// Đóng modal khi click ra ngoài modal-content
window.addEventListener('click', function(event) {
    const modal = document.getElementById('editProfileModal');
    if (event.target === modal) {
        closeEditProfileModal();
    }
});

// Đóng modal khi nhấn ESC
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        closeEditProfileModal();
    }
});
