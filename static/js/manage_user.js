document.addEventListener("DOMContentLoaded", () => {
    const filterType = document.getElementById("filterType");
    const searchInput = document.getElementById("searchInput");
    const roleDropdown = document.getElementById("roleDropdown");

    // Toggle between username input and role dropdown
    filterType.addEventListener("change", () => {
        if (filterType.value === "role") {
            searchInput.classList.add("hidden");
            roleDropdown.classList.remove("hidden");
        } else {
            searchInput.classList.remove("hidden");
            roleDropdown.classList.add("hidden");
        }
    });

    // Auto-submit form when role changes
    roleDropdown.addEventListener("change", () => {
        if (filterType.value === "role") {
            document.getElementById("searchForm").submit();
        }
    });
});
