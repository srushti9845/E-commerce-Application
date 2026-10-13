// Ask for confirmation before important actions such as placing or deleting an order.
document.addEventListener("submit", function (event) {
  const form = event.target;
  const message = form.getAttribute("data-confirm");
  if (message && !window.confirm(message)) {
    event.preventDefault();
  }
});

// Fade flash messages away after a few seconds, while keeping them readable initially.
window.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".flash").forEach(function (flash) {
    window.setTimeout(function () {
      flash.classList.add("flash-hidden");
    }, 5000);
  });
});
