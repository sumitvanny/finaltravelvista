/* dashboard.js — notification read-state + small dashboard interactions */

document.addEventListener("DOMContentLoaded", () => {
  initNotificationMarkRead();
  initMarkAllRead();
});

function csrfHeader() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute("content") : "";
}

function initNotificationMarkRead() {
  document.querySelectorAll(".notif-item[data-notification-id]").forEach((item) => {
    item.addEventListener("click", async () => {
      if (!item.classList.contains("unread")) return;
      const id = item.dataset.notificationId;
      try {
        await fetch(`/notifications/mark-read/${id}`, {
          method: "POST",
          headers: { "X-CSRFToken": csrfHeader() },
        });
        item.classList.remove("unread");
        updateBellCount(-1);
      } catch (err) {
        console.error("Failed to mark notification read", err);
      }
    });
  });
}

function initMarkAllRead() {
  const btn = document.getElementById("mark-all-read-btn");
  if (!btn) return;
  btn.addEventListener("click", async () => {
    try {
      await fetch("/notifications/mark-all-read", {
        method: "POST",
        headers: { "X-CSRFToken": csrfHeader() },
      });
      document.querySelectorAll(".notif-item.unread").forEach((el) => el.classList.remove("unread"));
      const bell = document.querySelector(".notif-count");
      if (bell) bell.remove();
    } catch (err) {
      console.error("Failed to mark all notifications read", err);
    }
  });
}

function updateBellCount(delta) {
  const bell = document.querySelector(".notif-count");
  if (!bell) return;
  const current = parseInt(bell.textContent, 10) || 0;
  const next = Math.max(current + delta, 0);
  if (next === 0) bell.remove();
  else bell.textContent = next;
}
