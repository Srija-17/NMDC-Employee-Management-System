document.addEventListener("DOMContentLoaded", () => {
    const usersTable = document.getElementById("usersTable");
    const filterType = document.getElementById("filterType");
    const searchInput = document.getElementById("searchInput");
    const roleDropdown = document.getElementById("roleDropdown");
    const editBtn = document.getElementById("editBtn");
    const saveBtn = document.getElementById("saveBtn");
    const downloadBtn = document.getElementById("downloadBtn");

    if (!usersTable) return; // Only run on Manage Users page

    let isEditing = false;

    // ---- Edit ----
    editBtn.addEventListener("click", () => {
        isEditing = true;
        const rows = usersTable.querySelectorAll("tbody tr");

        rows.forEach(row => {
            const usernameCell = row.cells[1];
            const passwordCell = row.cells[2];
            const roleCell = row.cells[3];

            usernameCell.innerHTML = `<input type="text" value="${usernameCell.textContent.trim()}">`;
            passwordCell.innerHTML = `<input type="text" value="${passwordCell.textContent.trim()}">`;

            const currentRole = roleCell.textContent.trim();
            roleCell.innerHTML = `
                <select>
                    <option value="admin" ${currentRole === "admin" ? "selected" : ""}>admin</option>
                    <option value="reviewer_one" ${currentRole === "reviewer_one" ? "selected" : ""}>reviewer_one</option>
                    <option value="reviewer_two" ${currentRole === "reviewer_two" ? "selected" : ""}>reviewer_two</option>
                </select>
            `;
        });
    });

    // ---- Save ----
    saveBtn.addEventListener("click", () => {
        if (!isEditing) return alert("Click Edit first!");

        const updatedData = [];
        const rows = usersTable.querySelectorAll("tbody tr");

        rows.forEach(row => {
            const userId = row.dataset.userId;
            const username = row.cells[1].querySelector("input").value.trim();
            const password = row.cells[2].querySelector("input").value.trim();
            const role = row.cells[3].querySelector("select").value;

            updatedData.push({ user_id: userId, username, password, role });
        });

        fetch("/update_users_bulk", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(updatedData)
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                alert("Users updated successfully!");
                location.reload();
            } else {
                alert("Update failed: " + (data.message || "Unknown error"));
            }
        })
        .catch(err => console.error("Error:", err));
    });

    // ---- Download CSV (Only Manage Users table) ----
    downloadBtn.addEventListener("click", (e) => {
        e.preventDefault();
        let csv = [];
        const rows = usersTable.querySelectorAll("tr");

        rows.forEach(row => {
            const cols = row.querySelectorAll("th, td");
            let rowData = [];
            cols.forEach(col => {
                let data = col.innerText.replace(/,/g, "");
                rowData.push(`"${data}"`);
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

    // ---- Filter toggle ----
    filterType.addEventListener("change", () => {
        if (filterType.value === "role") {
            searchInput.classList.add("hidden");
            roleDropdown.classList.remove("hidden");
        } else {
            searchInput.classList.remove("hidden");
            roleDropdown.classList.add("hidden");
        }
    });

    // ---- Auto-submit on role change ----
    roleDropdown.addEventListener("change", () => {
        if (filterType.value === "role") {
            document.getElementById("searchForm").submit();
        }
    });
});
