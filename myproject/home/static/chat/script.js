// ====================== Constants ======================
const CURRENT_USER_NAME = "{{ request.user.full_name|escapejs }}";
const CURRENT_USER_AVATAR =
  "{{ request.user.avatar.url|default_if_none:'null' }}";

let currentOtherUserId = null; // id của người đang chat cùng
let currentConversationId = null; // id cuộc trò chuyện hiện tại
let chatSocket = null;

const protocol = window.location.protocol === "https:" ? "wss" : "ws";
const chatList = document.getElementById("chatList");
const searchInput = document.querySelector(".search-input");
const searchResults = document.querySelector(".search-results");
const messageInput = document.getElementById("messageInput");

// ====================== Chọn 1 cuộc trò chuyện ======================
function selectChat(otherId, otherName, convId, otherAvatarUrl = null) {
  currentOtherUserId = otherId;
  currentConversationId = parseInt(convId, 10);

  // header
  document.getElementById("headerName").textContent = otherName;
  document.querySelector(".header-status").textContent = "Đang tải...";
  renderHeaderAvatar(otherName, otherAvatarUrl);

  // container
  const container = document.getElementById("messagesContainer");
  container.innerHTML = "<p>Đang tải tin nhắn...</p>";

  // load trạng thái
  fetchStatus(otherId);
  if (window.statusInterval) clearInterval(window.statusInterval);
  window.statusInterval = setInterval(() => fetchStatus(otherId), 2000);

  // load tin nhắn
  fetch(`/chat/messages/${currentConversationId}/`)
    .then((res) => res.json())
    .then((messages) => {
      container.innerHTML = "";
      messages.forEach((m) => {
        addMessage(m.text, m.sender_name, m.is_self, m.time, m.sender_avatar);
      });

      // Cập nhật số lượng tin nhắn chưa đọc sau khi đọc tin nhắn
      updateUnreadMessageCount();
    })
    .catch(() => {
      container.innerHTML = "<p>Lỗi khi tải tin nhắn</p>";
    });

  // WebSocket cho cuộc trò chuyện
  if (chatSocket) chatSocket.close();
  chatSocket = new WebSocket(
    `${protocol}://${window.location.host}/ws/chat/${currentConversationId}/`
  );

  chatSocket.onmessage = (e) => {
    const data = JSON.parse(e.data);
    if (data.type === "chat_message") {
      addMessage(
        data.message,
        data.sender_name,
        data.is_self ?? data.sender_id === CURRENT_USER_ID,
        data.time,
        data.avatar
      );
    }
  };

  chatSocket.onclose = () => {
    console.error("Chat socket closed unexpectedly");
  };
}

// ====================== Helper: Render avatar header ======================
function renderHeaderAvatar(name, avatarUrl) {
  const avatarDiv = document.getElementById("headerAvatar");
  avatarDiv.innerHTML = "";
  if (avatarUrl && avatarUrl !== "null") {
    const img = document.createElement("img");
    img.src = avatarUrl;
    img.alt = name;
    Object.assign(img.style, {
      width: "100%",
      height: "100%",
      objectFit: "cover",
      borderRadius: "50%",
    });
    avatarDiv.appendChild(img);
  } else {
    avatarDiv.textContent = name.charAt(0).toUpperCase();
  }
}

// ====================== Helper: Fetch status ======================
function fetchStatus(userId) {
  fetch(`/chat/status/${userId}/`)
    .then((res) => res.json())
    .then((data) => {
      document.querySelector(".header-status").textContent = data.status;
    })
    .catch(() => {
      document.querySelector(".header-status").textContent =
        "Không lấy được trạng thái";
    });
}

// ====================== Add message UI ======================
function addMessage(
  text,
  senderName,
  isSelf = false,
  time = null,
  senderAvatarUrl = null
) {
  const messagesContainer = document.getElementById("messagesContainer");
  const messageTime =
    time ||
    new Date().toLocaleTimeString("vi-VN", {
      hour: "2-digit",
      minute: "2-digit",
    });

  let avatarHtml = "";
  if (!isSelf) {
    avatarHtml =
      senderAvatarUrl && senderAvatarUrl !== "null"
        ? `<img src="${senderAvatarUrl}" alt="${senderName}"
                       style="width:32px;height:32px;border-radius:50%;object-fit:cover;">`
        : senderName.charAt(0).toUpperCase();
  }

  const html = isSelf
    ? `
        <div class="message sent">
            <div class="message-content">${text}</div>
        </div>
        <div class="message-time" style="text-align: right; margin-right: 12px;">${messageTime}</div>
    `
    : `
        <div class="message received">
            <div class="message-avatar">${avatarHtml}</div>
            <div class="message-content">${text}</div>
        </div>
        <div class="message-time" style="text-align: left; margin-left: 44px;">${messageTime}</div>
    `;
  messagesContainer.innerHTML += html;
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// ====================== Send message ======================
function sendMessage() {
  const messageText = messageInput.value.trim();
  if (!chatSocket || !messageText) return;

  chatSocket.send(
    JSON.stringify({
      message: messageText,
      avatar: CURRENT_USER_AVATAR,
    })
  );

  messageInput.value = "";
  messageInput.style.height = "auto";
}

// ====================== Input events ======================
messageInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

messageInput.addEventListener("input", function () {
  this.style.height = "auto";
  this.style.height = Math.min(this.scrollHeight, 80) + "px";
});

// ====================== Search user ======================
searchInput.addEventListener("input", function () {
  const keyword = this.value.trim();
  if (!keyword) {
    searchResults.innerHTML = "";
    return;
  }

  fetch(`/chat/search-users/?q=${encodeURIComponent(keyword)}`)
    .then((res) => res.json())
    .then((users) => {
      searchResults.innerHTML = "";
      users.forEach((user) => {
        const item = document.createElement("div");
        item.className = "search-item";

        const avatarHtml = user.avatar
          ? `<img src="${user.avatar}" alt="${user.name}"
                        style="width:32px;height:32px;border-radius:50%;object-fit:cover;">`
          : user.name.charAt(0).toUpperCase();

        item.innerHTML = `
                <div class="avatar">${avatarHtml}</div>
                <div class="name">${user.name}</div>
            `;

        item.onclick = () =>
          openOrSelectConversation(user.id, user.name, user.avatar);
        searchResults.appendChild(item);
      });
    });
});

// ====================== Open or create conversation ======================
function openOrSelectConversation(userId, userName, userAvatar = null) {
  const existingItem = Array.from(chatList.children).find(
    (item) => parseInt(item.dataset.userId, 10) === userId
  );

  if (existingItem) {
    const convId = parseInt(existingItem.dataset.convId, 10);
    selectChat(userId, userName, convId, userAvatar);
  } else {
    fetch(`/chat/get-or-create-conversation/${userId}/`)
      .then((res) => res.json())
      .then((data) => {
        const convId = parseInt(data.id, 10);
        const newItem = document.createElement("div");
        newItem.className = "chat-item";
        newItem.dataset.userId = userId;
        newItem.dataset.convId = convId;
        newItem.onclick = () =>
          selectChat(userId, userName, convId, userAvatar);

        const avatarHtml = userAvatar
          ? `<img src="${userAvatar}" alt="${userName}"
                           style="width:40px;height:40px;border-radius:50%;object-fit:cover;">`
          : userName.charAt(0).toUpperCase();

        newItem.innerHTML = `
                    <div class="avatar">${avatarHtml}</div>
                    <div class="chat-info">
                        <div class="chat-name">${userName}</div>
                        <div class="chat-bottom">
                            <div class="chat-preview">(Chưa có tin nhắn)</div>
                            <div class="chat-time"></div>
                        </div>
                    </div>
                `;
        chatList.prepend(newItem);

        selectChat(userId, userName, convId);
      });
  }

  searchResults.innerHTML = "";
  searchInput.value = "";
}
// ====================== User Socket (để update danh sách chat) ======================
const notifSocket = new WebSocket(
  `${protocol}://${window.location.host}/ws/notifications/`
);

notifSocket.onmessage = (e) => {
  const data = JSON.parse(e.data);
  if (data.type === "chat_list_update") {
    updateChatListPreview(
      data.conv_id,
      data.last_text,
      data.time,
      data.sender_id
    );
  } else if (data.type === "new_message") {
    // Cập nhật badge số tin nhắn chưa đọc
    const messageCountSpan =
      window.parent.document.getElementById("message-count");
    if (messageCountSpan) {
      messageCountSpan.innerText = data.unread_count;
    }
  }
};

notifSocket.onclose = () => {
  console.error("Notification socket closed unexpectedly");
};

// ====================== Update chat list preview ======================
function updateChatListPreview(convId, lastText, time, senderId) {
  const chatItem = document.querySelector(
    `.chat-item[data-conv-id="${convId}"]`
  );
  if (!chatItem) return;

  const preview = chatItem.querySelector(".chat-preview");
  if (preview) {
    preview.innerHTML =
      senderId === CURRENT_USER_ID
        ? `<span class="sender-label">Bạn:</span> ${lastText}`
        : lastText;
  }

  const timeDiv = chatItem.querySelector(".chat-time");
  if (timeDiv) {
    timeDiv.textContent = time;
  }

  // Đưa hội thoại lên đầu danh sách
  chatList.prepend(chatItem);
}

function confirmDeleteConversation() {
  if (!currentConversationId) {
    alert("Chưa chọn cuộc trò chuyện nào!");
    return;
  }

  if (confirm("Bạn có chắc muốn xóa cuộc trò chuyện này?")) {
    fetch(`/delete-conversation/${currentConversationId}/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCSRFToken(), // cần CSRF token nếu Django view yêu cầu
      },
    })
      .then((res) => {
        if (res.ok) {
          alert("Đã xóa cuộc trò chuyện.");
          // reload lại trang hoặc xóa item trong chat list
          location.reload();
        } else {
          alert("Lỗi khi xóa cuộc trò chuyện.");
        }
      })
      .catch(() => {
        alert("Không thể kết nối tới server.");
      });
  }
}

function getCSRFToken() {
  const name = "csrftoken=";
  const decodedCookie = decodeURIComponent(document.cookie);
  const ca = decodedCookie.split(";");
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === " ") {
      c = c.substring(1);
    }
    if (c.indexOf(name) === 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}

// ====================== Update unread message count ======================
function updateUnreadMessageCount() {
  fetch("/chat/unread-count/")
    .then((res) => res.json())
    .then((data) => {
      const messageCountSpan =
        window.parent.document.getElementById("message-count");
      if (messageCountSpan) {
        messageCountSpan.innerText = data.unread_count;
      }
    })
    .catch((err) => console.error("Error updating unread count:", err));
}
