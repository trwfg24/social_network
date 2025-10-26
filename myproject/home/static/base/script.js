document.addEventListener("DOMContentLoaded", function () {
  const dropdownIcons = document.querySelectorAll(".nav-icon.has-dropdown");

  dropdownIcons.forEach((icon) => {
    const dropdown = icon.querySelector(".dropdown");

    icon.addEventListener("click", function (e) {
      e.stopPropagation(); // Không cho click lan ra ngoài
      // Ẩn tất cả dropdown khác
      document.querySelectorAll(".dropdown").forEach((d) => {
        if (d !== dropdown) d.classList.remove("show");
      });
      // Toggle dropdown hiện tại
      dropdown.classList.toggle("show");
    });
  });

  // Click ra ngoài thì đóng
  document.addEventListener("click", function () {
    document
      .querySelectorAll(".dropdown")
      .forEach((d) => d.classList.remove("show"));
  });

  // Ẩn badge khi số lượng = 0
  const notificationBadge = document.getElementById("notification-count");
  const messageBadge = document.getElementById("message-count");

  if (notificationBadge && parseInt(notificationBadge.innerText) === 0) {
    notificationBadge.style.display = "none";
  }

  if (messageBadge && parseInt(messageBadge.innerText) === 0) {
    messageBadge.style.display = "none";
  }
});
