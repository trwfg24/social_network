document.addEventListener("DOMContentLoaded", function () {
  // Hiệu ứng cho menu
  const menuItems = document.querySelectorAll(".menu-item");
  menuItems.forEach((item) => {
    item.addEventListener("click", function () {
      menuItems.forEach((i) => i.classList.remove("active"));
      this.classList.add("active");
    });
  });

  // Nút đăng bài
  const postBtn = document.querySelector(".post-btn");
  const textarea = document.querySelector(".post-textarea");
  const imageInput = document.getElementById("image-upload");

  postBtn.addEventListener("click", function (event) {
    const hasText = textarea.value.trim() !== "";
    const hasImage = imageInput.files.length > 0;

    if (!hasText && !hasImage) {
      event.preventDefault(); // Chặn submit nếu rỗng cả text và ảnh
      alert("Vui lòng nhập nội dung hoặc chọn ảnh trước khi đăng!");
      return;
    }
  });

  // Hiệu ứng search
  const searchInput = document.querySelector(".search-input");
  if (searchInput) {
    searchInput.addEventListener("focus", function () {
      this.style.background = "rgba(255, 255, 255, 0.9)";
    });
    searchInput.addEventListener("blur", function () {
      this.style.background = "rgba(102, 126, 234, 0.1)";
    });
  }

  // Smooth scroll cho post mới
  const posts = document.querySelectorAll(".post");
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = "1";
          entry.target.style.transform = "translateY(0)";
        }
      });
    },
    { threshold: 0.1, rootMargin: "0px 0px -50px 0px" }
  );

  posts.forEach((post) => observer.observe(post));
});

// CSS animation
const style = document.createElement("style");
style.textContent = `
    @keyframes slideInRight {
        from { opacity: 0; transform: translateX(100%); }
        to { opacity: 1; transform: translateX(0); }
    }
`;
document.head.appendChild(style);

function likePost(button, postId) {
  if (!button) return console.error("Button is null");

  const countSpan = button.querySelector(".count");
  if (!countSpan) return console.error("Cannot find .count inside button!");

  let count = parseInt(countSpan.textContent) || 0;
  const wasLiked = button.classList.contains("liked");

  // Optimistic UI
  if (wasLiked) {
    button.classList.remove("liked");
    count--;
    button.style.transform = "scale(0.9)";
  } else {
    button.classList.add("liked");
    count++;
    button.style.transform = "scale(1.2)";
  }
  setTimeout(() => {
    button.style.transform = "scale(1)";
  }, 200);
  countSpan.textContent = count;

  fetch(`/like/${postId}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({}),
  })
    .then((res) => res.json())
    .then((data) => {
      // Chỉ cập nhật số like từ server
      if (data.likeCount !== undefined && countSpan) {
        countSpan.textContent = data.likeCount;
      }
    })
    .catch((err) => console.error("Fetch error:", err));
}

// Hàm lấy CSRF token (nếu đang dùng Django)
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + "=")) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function deletePost(postId) {
  if (!confirm("Bạn có chắc muốn xóa bài viết này?")) return;

  fetch(`/delete_post/${postId}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({}),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.status === "ok") {
        // Xóa element post khỏi DOM
        const postEl = document.getElementById(`post-${postId}`);
        if (postEl) postEl.remove();
        location.reload();
      } else {
        alert("Xóa thất bại: " + data.message);
      }
    })
    .catch((err) => console.error(err));
}

document
  .getElementById("image-upload")
  .addEventListener("change", function (e) {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = function (ev) {
        const img = document.createElement("img");
        img.src = ev.target.result;
        img.style.maxWidth = "150px";
        document.getElementById("editor").appendChild(img);
      };
      reader.readAsDataURL(file);
    }
  });

//   const form = document.querySelector("form");
//   form.addEventListener("submit", function() {
//     // Lấy text (chỉ text, bỏ thẻ <img>)
//     document.getElementById("hidden-content").value =
//         document.getElementById("editor").innerText.trim();
//   });

const form = document.getElementById("post-form");
form.addEventListener("submit", function () {
  const editor = document.getElementById("editor");

  // Lấy toàn bộ HTML từ editor
  let htmlContent = editor.innerHTML.trim();

  // Tạo temp div để lọc ảnh nếu muốn chỉ lấy text
  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = htmlContent;
  tempDiv.querySelectorAll("img").forEach((img) => img.remove());

  let textContent = tempDiv.textContent.trim();

  // Nếu không có text, gán rỗng để form vẫn submit
  if (!textContent) textContent = "";

  document.getElementById("hidden-content").value = textContent;
});

// Các hàm openModal, closeModal, closeModalOnOverlay đã được định nghĩa trong home.html
// KHÔNG định nghĩa lại ở đây để tránh duplicate!

// Submit comment - Sử dụng event delegation để tránh duplicate event listener
document.addEventListener("submit", function (e) {
  if (e.target.id === "commentForm") {
    e.preventDefault();
    const form = e.target;
    const postId = form.dataset.postId;
    const formData = new FormData(form);

    const content = formData.get("content").trim();
    const image = formData.get("image");
    if (!content && (!image || image.size === 0)) {
      alert("Vui lòng nhập nội dung hoặc chọn ảnh!");
      return;
    }
    fetch(`/add-comment/${postId}/`, {
      method: "POST",
      body: formData,
      headers: { "X-CSRFToken": formData.get("csrfmiddlewaretoken") },
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.error) {
          alert(data.error);
        } else {
          const commentsList = document.getElementById("commentsList");

          // Xóa dòng "Chưa có bình luận nào" nếu có
          const noComment = commentsList.querySelector(".no-comment");
          if (noComment) {
            noComment.remove();
          }

          // Thêm comment mới
          commentsList.insertAdjacentHTML("afterbegin", data.html);
          form.reset();
        }
      });
  }
});

function deleteComment(commentId, postId) {
  if (!confirm("Bạn có chắc chắn muốn xóa bình luận này không?")) {
    return; // hủy xóa
  }
  fetch(`/delete_comment/${commentId}/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
    },
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        // Xoá comment khỏi DOM
        let cmtElem = document.querySelector(`#comment-${data.comment_id}`);
        if (cmtElem) cmtElem.remove();

        // Update commentCount
        let countElem = document.querySelector(
          `#comment-count-${data.post_id}`
        );
        if (countElem) {
          countElem.textContent = data.commentCount;
        }
      }
    });
}
