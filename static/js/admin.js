document.addEventListener("DOMContentLoaded", () => {
    console.log("Admin dashboard loaded");

    const downloadBtn = document.getElementById("downloadBtn");
    const table = document.querySelector("#results table");

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

        // Create a blob and download link
        const csvBlob = new Blob([csv.join("\n")], { type: "text/csv" });
        const url = URL.createObjectURL(csvBlob);

        const a = document.createElement("a");
        a.href = url;
        a.download = "admin_report.csv";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    });
});
