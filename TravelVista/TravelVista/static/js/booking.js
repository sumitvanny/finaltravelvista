/* booking.js — live price calculation on the booking page */

document.addEventListener("DOMContentLoaded", () => {
  const passengersInput = document.getElementById("passengers");
  const pricePerPersonEl = document.getElementById("price-per-person-data");
  const totalDisplay = document.getElementById("total-amount-display");

  if (!passengersInput || !pricePerPersonEl || !totalDisplay) return;
  const pricePerPerson = parseFloat(pricePerPersonEl.dataset.price || "0");

  function recalc() {
    const passengers = Math.max(parseInt(passengersInput.value, 10) || 1, 1);
    const total = passengers * pricePerPerson;
    totalDisplay.textContent = "$" + total.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  passengersInput.addEventListener("input", recalc);
  recalc();
});
