document.addEventListener("DOMContentLoaded", function () {
    const empIdInput = document.getElementById('emp_id');
    const empError = document.getElementById('empError');

    const trainingIdInput = document.getElementById('training_id');
    const trainingError = document.getElementById('trainingError');

    const submitBtn = document.querySelector('button[type="submit"]');

    function checkEmployee(empId) {
        if (empId.length === 0) {
            empError.style.display = "none";
            return Promise.resolve(true);
        }
        return fetch(`/check_employee/${empId}`)
            .then(res => res.json())
            .then(data => {
                if (data.exists) {
                    empError.style.display = "none";
                    return true;
                } else {
                    empError.style.display = "inline";
                    return false;
                }
            });
    }

    function checkTraining(trainingId) {
        if (trainingId.length === 0) {
            trainingError.style.display = "none";
            return Promise.resolve(true);
        }
        return fetch(`/check_training/${trainingId}`)
            .then(res => res.json())
            .then(data => {
                if (data.exists) {
                    trainingError.style.display = "none";
                    return true;
                } else {
                    trainingError.style.display = "inline";
                    return false;
                }
            });
    }

    empIdInput.addEventListener('input', async function () {
        const empValid = await checkEmployee(this.value.trim());
        const trainingValid = await checkTraining(trainingIdInput.value.trim());
        submitBtn.disabled = !(empValid && trainingValid);
    });

    trainingIdInput.addEventListener('input', async function () {
        const empValid = await checkEmployee(empIdInput.value.trim());
        const trainingValid = await checkTraining(this.value.trim());
        submitBtn.disabled = !(empValid && trainingValid);
    });
});
