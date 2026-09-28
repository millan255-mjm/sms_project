document.addEventListener("DOMContentLoaded", function () {
  const toggle = document.getElementById("sidebarToggle");
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("sidebarOverlay");

  function closeSidebar() {
    sidebar && sidebar.classList.remove("open");
    overlay && overlay.classList.remove("show");
  }

  if (toggle && sidebar) {
    toggle.addEventListener("click", function () {
      sidebar.classList.toggle("open");
      overlay.classList.toggle("show");
    });
  }
  if (overlay) {
    overlay.addEventListener("click", closeSidebar);
  }

  // Close sidebar automatically after tapping a nav link (mobile)
  document.querySelectorAll(".nav-link").forEach(function (link) {
    link.addEventListener("click", closeSidebar);
  });
});
