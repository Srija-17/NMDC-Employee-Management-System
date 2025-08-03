window.addEventListener('DOMContentLoaded', function () {
  const filterTypeEl = document.getElementById('filterType');
  const searchInput = document.getElementById('searchInput');
  const departmentSelect = document.getElementById('departmentSelect');
  const dateInputs = document.getElementById('dateInputs');

  // Show/hide fields based on filter
  function toggleExtraInputs() {
    searchInput.style.display = 'inline-block'; // default show
    departmentSelect.style.display = 'none';
    dateInputs.style.display = 'none';

    if (filterTypeEl.value === 'department') {
      searchInput.style.display = 'none';
      departmentSelect.style.display = 'inline-block';
    }
    else if (filterTypeEl.value === 'training_date') {
      searchInput.style.display = 'none';
      dateInputs.style.display = 'flex';
    }
    else if (filterTypeEl.value === 'due') {
      searchInput.style.display = 'none';
    }
  }

  // Event: filter change
  filterTypeEl.addEventListener('change', function () {
    toggleExtraInputs();
    if (this.value === 'due') {
      searchData();
    }
  });

  // Auto-search on department select
  departmentSelect.addEventListener('change', function () {
    if (filterTypeEl.value === 'department') {
      searchData();
    }
  });

  // Search function
  function searchData() {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/reviewer_one';

    form.appendChild(makeHidden('filter_type', filterTypeEl.value));

    if (filterTypeEl.value === 'department') {
      form.appendChild(makeHidden('search_value', departmentSelect.value));
    }
    else if (filterTypeEl.value === 'training_date') {
      form.appendChild(makeHidden('joining_date', document.getElementById('joiningDate').value));
      form.appendChild(makeHidden('completion_date', document.getElementById('completionDate').value));
    }
    else if (filterTypeEl.value !== 'due') {
      form.appendChild(makeHidden('search_value', searchInput.value));
    }

    document.body.appendChild(form);
    form.submit();
  }

  // Create hidden input
  function makeHidden(name, value) {
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = name;
    input.value = value;
    return input;
  }

  // CSV Download
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

  // Logout
  function logout() {
    window.location.href = '/logout';
  }

  document.getElementById('searchBtn').addEventListener('click', searchData);
  document.getElementById('downloadBtn').addEventListener('click', downloadCSV);
  document.getElementById('logoutBtn').addEventListener('click', logout);

  // Initial state
  toggleExtraInputs();
});
