document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".delete-btn").forEach(btn => {
        btn.addEventListener("click", function (event) {
            if (!confirm("Are you sure you want to delete this employee?")) {
                event.preventDefault();
            }
        });
    });
});
