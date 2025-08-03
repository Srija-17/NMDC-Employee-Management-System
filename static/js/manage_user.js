document.addEventListener("DOMContentLoaded", () => {
    console.log("Manage Users loaded");

    const editBtn = document.getElementById("editBtn");
    const saveBtn = document.getElementById("saveBtn");
    const table = document.querySelector("#usersTable");
    const downloadBtn = document.getElementById("downloadBtn");

    const filterType = document.getElementById("filterType");
    const searchInput = document.getElementById("searchInput");
    const roleDropdown = document.getElementById("roleDropdown");

    // Show correct search box based on selected filter on load
    if (filterType.value === "role") {
        searchInput.style.display = "none";
        roleDropdown.style.display = "inline-block";
    } else {
        searchInput.style.display = "inline-block";
        roleDropdown.style.display = "none";
    }

    // Switch between search input and role dropdown instantly
    filterType.addEventListener("change", () => {
        if (filterType.value === "role") {
            searchInput.style.display = "none";
            roleDropdown.style.display = "inline-block";
            searchInput.value = ""; // clear text search when switching
        } else {
            searchInput.style.display = "inline-block";
            roleDropdown.style.display = "none";
            roleDropdown.value = ""; // clear role selection
        }
    });

    // Toggle edit mode
    editBtn.addEventListener("click", () => {
        const inputs = table.querySelectorAll("input, select");
        inputs.forEach(input => input.disabled = false);
        saveBtn.disabled = false;
        editBtn.disabled = true;
    });

    // Save changes
    saveBtn.addEventListener("click", () => {
        const rows = table.querySelectorAll("tbody tr");
        let updatedData = [];

        rows.forEach(row => {
            const cells = row.querySelectorAll("td");
            updatedData.push({
                user_id: cells[0].innerText.trim(),
                username: cells[1].querySelector("input").value.trim(),
                password: cells[2].querySelector("input").value.trim(),
                role: cells[3].querySelector("select").value
            });
        });

        fetch("/update_users", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(updatedData)
        })
        .then(res => res.json())
        .then(data => {
            alert(data.message || "Changes saved successfully");
            location.reload();
        })
        .catch(err => console.error(err));
    });

    // Download table as CSV
    if (downloadBtn) {
        downloadBtn.addEventListener("click", (e) => {
            e.preventDefault();
            if (!table) {
                alert("No data to download!");
                return;
            }

            let csv = [];
            const rows = table.querySelectorAll("tr");

            rows.forEach(row => {
                const cols = row.querySelectorAll("th, td");
                let rowData = [];
                cols.forEach(col => {
                    if (col.querySelector("input")) {
                        rowData.push(`"${col.querySelector("input").value}"`);
                    } else if (col.querySelector("select")) {
                        rowData.push(`"${col.querySelector("select").value}"`);
                    } else {
                        rowData.push(`"${col.innerText.trim()}"`);
                    }
                });
                csv.push(rowData.join(","));
            });

            const csvBlob = new Blob([csv.join("\n")], { type: "text/csv" });
            const url = URL.createObjectURL(csvBlob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "manage_users.csv";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        });
    }
});
