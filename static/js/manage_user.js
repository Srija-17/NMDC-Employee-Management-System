document.addEventListener("DOMContentLoaded", () => {
    console.log("Manage Users loaded");

    const editBtn = document.getElementById("editBtn");
    const saveBtn = document.getElementById("saveBtn");
    const table = document.querySelector("#usersTable");
    const downloadBtn = document.getElementById("downloadBtn");

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

        fetch("/update_users_bulk", {
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

    // Download only visible table rows
    if (downloadBtn) {
        downloadBtn.addEventListener("click", (e) => {
            e.preventDefault();
            if (!table || table.querySelectorAll("tbody tr").length === 0) {
                alert("No data to download!");
                return;
            }

            let csv = [];

            // Table header
            let headerRow = [];
            table.querySelectorAll("thead th").forEach(th => {
                headerRow.push(`"${th.innerText.trim()}"`);
            });
            csv.push(headerRow.join(","));

            // Only visible rows
            table.querySelectorAll("tbody tr").forEach(row => {
                let rowData = [];
                row.querySelectorAll("td").forEach(col => {
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

            // Create CSV
            const csvBlob = new Blob([csv.join("\n")], { type: "text/csv" });
            const url = URL.createObjectURL(csvBlob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "manage_users_filtered.csv";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        });
    }
});
