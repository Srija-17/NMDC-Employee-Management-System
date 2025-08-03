document.addEventListener("DOMContentLoaded", () => {
    console.log("Admin dashboard loaded");

    const downloadBtn = document.getElementById("downloadBtn");
    const table = document.querySelector("#results table");

    // -----------------------------
    // Download CSV
    // -----------------------------
    downloadBtn.addEventListener("click", function (e) {
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
                let data = col.innerText.replace(/,/g, ""); // remove commas
                rowData.push(`"${data}"`);
            });
            csv.push(rowData.join(","));
        });

        const csvBlob = new Blob([csv.join("\n")], { type: "text/csv" });
        const url = URL.createObjectURL(csvBlob);

        const a = document.createElement("a");
        a.href = url;
        a.download = "admin_report.csv";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    });

    // -----------------------------
    // Edit button toggle
    // -----------------------------
    const editBtn = document.getElementById("editBtn");
    const editSearchArea = document.getElementById("editSearchArea");

    if (editBtn && editSearchArea) {
        editBtn.addEventListener("click", () => {
            editSearchArea.style.display = (editSearchArea.style.display === "none" || editSearchArea.style.display === "") 
                ? "block" 
                : "none";
        });
    }

    // -----------------------------
    // Search functionality
    // -----------------------------
    const searchBtn = document.getElementById("searchBtn");
    if (searchBtn) {
        searchBtn.addEventListener("click", () => {
            const filterType = document.getElementById("filterType").value;
            const searchValue = document.getElementById("searchValue").value;

            if (!filterType || !searchValue) {
                alert("Please select a filter and enter a search value.");
                return;
            }

            // Reload with query params
            window.location.href = `/admin?filter_type=${filterType}&search_value=${encodeURIComponent(searchValue)}`;
        });
    }

    // -----------------------------
    // Save row functionality
    // -----------------------------
    const saveButtons = document.querySelectorAll(".saveRowBtn");
    saveButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            const row = btn.closest("tr");
            const cells = row.querySelectorAll("td[contenteditable='true']");
            let rowData = [];

            cells.forEach(cell => rowData.push(cell.innerText.trim()));

            console.log("Saving row:", rowData);

            // Send update to backend
            fetch("/admin/update_row", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ data: rowData })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert("Row updated successfully!");
                } else {
                    alert("Error updating row: " + (data.error || ""));
                }
            })
            .catch(err => {
                console.error(err);
                alert("Error updating row.");
            });
        });
    });

});
