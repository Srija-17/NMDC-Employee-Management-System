window.addEventListener('DOMContentLoaded', function () {

  document.querySelector('.menu-btn').addEventListener('click', function () {
  document.querySelector('.menu-content').classList.toggle('hidden');
});

  function toggleExtraInputs() {
    const filter = document.getElementById('filterType').value;
    document.getElementById('departmentSelect').classList.add('hidden');
    document.getElementById('dateInputs').classList.add('hidden');

    if (filter === 'department') {
      document.getElementById('departmentSelect').classList.remove('hidden');
    } else if (filter === 'training_date') {
      document.getElementById('dateInputs').classList.remove('hidden');
    }
  }

  document.getElementById('filterType').addEventListener('change', function () {
  const filter = this.options[this.selectedIndex].text;
  const searchInput = document.getElementById('searchInput');

  if (this.value !== 'department' && this.value !== 'training_date') {
    searchInput.placeholder = `Search by ${filter}...`;
    searchInput.classList.remove('hidden');
  } else {
    searchInput.placeholder = '';
    searchInput.classList.add('hidden');
  }

  toggleExtraInputs(); // now it's safe to call because it's in scope
});

  function searchData() {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/reviewer_one';

    const filterType = document.getElementById('filterType').value;
    const filterInput = document.createElement('input');
    filterInput.type = 'hidden';
    filterInput.name = 'filter_type';
    filterInput.value = filterType;
    form.appendChild(filterInput);

    if (filterType === 'department') {
      const dept = document.getElementById('departmentSelect').value;
      form.appendChild(makeHidden('search_value', dept));
    } else if (filterType === 'training_date') {
      const jd = document.getElementById('joiningDate').value;
      const cd = document.getElementById('completionDate').value;
      form.appendChild(makeHidden('joining_date', jd));
      form.appendChild(makeHidden('completion_date', cd));
    } else {
      const val = document.getElementById('searchInput').value;
      form.appendChild(makeHidden('search_value', val));
    }

    document.body.appendChild(form);
    form.submit();
  }

  function makeHidden(name, value) {
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = name;
    input.value = value;
    return input;
  }

  function downloadCSV() {
    const rows = [...document.querySelectorAll("table tbody tr")].map(row =>
      [...row.querySelectorAll("td")].map(td => td.innerText)
    );

    if (rows.length === 0) {
      alert("No data to download.");
      return;
    }

    const headers = [...document.querySelectorAll("table thead th")].map(th => th.innerText);
    const data = rows.map(row => Object.fromEntries(headers.map((key, i) => [key, row[i]])));

    fetch('/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ results: data })
    }).then(res => res.blob()).then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'results.csv';
      a.click();
      window.URL.revokeObjectURL(url);
    });
  }

  function logout() {
    window.location.href = '/logout';
  }
  function logout() {
    window.location.href = "/logout";
  }

  document.getElementById('searchBtn').addEventListener('click', searchData);
  document.getElementById('downloadBtn').addEventListener('click', downloadCSV);
  document.getElementById('logoutBtn').addEventListener('click', logout);
});
document.addEventListener("DOMContentLoaded", function () {
    const filterType = document.getElementById("filterType");
    const searchInput = document.getElementById("searchInput");
    const extraFilters = document.getElementById("extraFilters");

    filterType.addEventListener("change", function () {
        if (this.value === "due") {
            searchInput.style.display = "none";  // Hide search box
            extraFilters.style.display = "none"; // Hide extra filters
        } else {
            searchInput.style.display = "inline-block"; // Show search box
            extraFilters.style.display = "block";       // Show extra filters
        }
    });
});
