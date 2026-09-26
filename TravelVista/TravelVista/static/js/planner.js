/* planner.js — small UX helpers for the AI Trip Planner form */

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("planner-form");
  const submitBtn = document.getElementById("planner-submit-btn");
  if (form && submitBtn) {
    form.addEventListener("submit", () => {
      submitBtn.disabled = true;
      submitBtn.textContent = "Generating your itinerary...";
    });
  }
});
