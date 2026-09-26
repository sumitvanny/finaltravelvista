/* main.js — global site behaviors shared across all pages */

document.addEventListener("DOMContentLoaded", () => {
  initNavToggle();
  initFlashDismiss();
  initWishlistButtons();
  initImagePreviews();
  initThemeToggle();
  initModalCloseOnOverlay();
  initTabs();
  initStarRatingLabels();
});

function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute("content") : "";
}

function initNavToggle() {
  const toggle = document.querySelector(".nav-toggle");
  const links = document.querySelector(".nav-links");
  if (toggle && links) {
    toggle.addEventListener("click", () => links.classList.toggle("open"));
  }
}

function initFlashDismiss() {
  document.querySelectorAll(".flash").forEach((flash) => {
    const closeBtn = flash.querySelector(".flash-close");
    if (closeBtn) closeBtn.addEventListener("click", () => flash.remove());
    setTimeout(() => {
      if (flash.parentElement) flash.style.opacity = "0";
      setTimeout(() => flash.remove(), 400);
    }, 6000);
  });
}

function initWishlistButtons() {
  document.querySelectorAll(".wishlist-btn").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.preventDefault();
      const destId = btn.dataset.destinationId;
      try {
        const res = await fetch(`/wishlist/toggle/${destId}`, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": getCsrfToken(),
          },
        });
        const data = await res.json();
        if (data.success) {
          btn.classList.toggle("active", data.added);
          btn.innerHTML = data.added ? "&#9829;" : "&#9825;";
        }
      } catch (err) {
        console.error("Wishlist toggle failed", err);
      }
    });
  });
}

function initImagePreviews() {
  document.querySelectorAll("input[type=file][data-preview]").forEach((input) => {
    input.addEventListener("change", () => {
      const previewEl = document.getElementById(input.dataset.preview);
      if (!previewEl || !input.files || !input.files[0]) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        if (previewEl.tagName === "IMG") previewEl.src = e.target.result;
        else previewEl.style.backgroundImage = `url(${e.target.result})`;
      };
      reader.readAsDataURL(input.files[0]);
    });
  });
}

function initThemeToggle() {
  const toggle = document.getElementById("theme-toggle");
  const saved = window.__travelvistaTheme || "dark";
  document.documentElement.setAttribute("data-theme", saved);
  if (toggle) {
    toggle.addEventListener("click", () => {
      const current = document.documentElement.getAttribute("data-theme");
      const next = current === "light" ? "dark" : "light";
      document.documentElement.setAttribute("data-theme", next);
      window.__travelvistaTheme = next;
    });
  }
}

function initModalCloseOnOverlay() {
  document.querySelectorAll(".modal-overlay").forEach((overlay) => {
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay) overlay.classList.remove("open");
    });
  });
  document.querySelectorAll("[data-modal-open]").forEach((trigger) => {
    trigger.addEventListener("click", () => {
      const modal = document.getElementById(trigger.dataset.modalOpen);
      if (modal) modal.classList.add("open");
    });
  });
  document.querySelectorAll("[data-modal-close]").forEach((trigger) => {
    trigger.addEventListener("click", () => {
      const modal = trigger.closest(".modal-overlay");
      if (modal) modal.classList.remove("open");
    });
  });
}

function initTabs() {
  document.querySelectorAll(".tabs").forEach((tabGroup) => {
    const buttons = tabGroup.querySelectorAll(".tab-btn");
    buttons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const panelId = btn.dataset.tabTarget;
        const container = tabGroup.closest("[data-tab-container]") || document;
        buttons.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        container.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
        const target = document.getElementById(panelId);
        if (target) target.classList.add("active");
      });
    });
  });
}

function initStarRatingLabels() {
  // Purely cosmetic hover feedback handled via CSS; nothing extra needed here,
  // reserved for future enhancement (e.g. submitting rating via AJAX preview).
}

/* Simple client-side form validation helper used by multiple pages */
function validateRequiredFields(formEl) {
  let valid = true;
  formEl.querySelectorAll("[required]").forEach((field) => {
    if (!field.value || !field.value.trim()) {
      field.classList.add("input-error");
      valid = false;
    } else {
      field.classList.remove("input-error");
    }
  });
  return valid;
}
