window.addEventListener('DOMContentLoaded', function () {
    const filterType = document.getElementById('filterType');
    const searchInput = document.getElementById('searchInput');
    const departmentSelect = document.getElementById('departmentSelect');
    const dateInputs = document.getElementById('dateInputs');

    filterType.addEventListener('change', function () {
      searchInput.classList.remove('hidden');
      departmentSelect.classList.add('hidden');
      dateInputs.classList.add('hidden');

      if (this.value === 'department') {
        searchInput.classList.add('hidden');
        departmentSelect.classList.remove('hidden');
      }
      else if (this.value === 'training_date') {
        searchInput.classList.add('hidden');
        dateInputs.classList.remove('hidden');
      }
      else if (this.value === 'due') {
        searchInput.classList.add('hidden');
        document.getElementById('searchForm').submit();
      }
    });

    // Navigation menu toggle (scoped for each nav menu)
const navMenu = document.querySelector('.nav-menu');
if(navMenu){
    const menuBtn = navMenu.querySelector('.menu-btn');
    const menuContent = navMenu.querySelector('.menu-content');
    if(menuBtn && menuContent){
        menuBtn.addEventListener('click', function () {
            menuContent.classList.toggle('hidden');
        });
    }
}

    // Download table data as CSV
    const downloadBtn = document.getElementById('downloadBtn');
    if(downloadBtn){
        downloadBtn.addEventListener('click', function (e) {
          e.preventDefault();

          const table = document.querySelector("#results table");
          if (!table) {
            alert("No data to download.");
            return;
          }

          let csv = [];
          const rows = table.querySelectorAll("tr");

          rows.forEach(row => {
            const cols = row.querySelectorAll("th, td");
            const rowData = [];
            cols.forEach(col => rowData.push('"' + col.innerText.replace(/"/g, '""') + '"'));
            csv.push(rowData.join(","));
          });

          const blob = new Blob([csv.join("\n")], { type: "text/csv" });
          const url = window.URL.createObjectURL(blob);

          const a = document.createElement("a");
          a.setAttribute("href", url);
          a.setAttribute("download", "results.csv");
          a.click();
          window.URL.revokeObjectURL(url);
        });
    }
});
