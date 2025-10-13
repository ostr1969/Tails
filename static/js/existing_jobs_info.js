// existing-jobs.js
function fetchAndDisplayExistingJobs() {
    // Fetch job information from the JSON endpoint
    fetch('/_existing_jobs')  // Replace '/jobs_json' with the actual URL of your JSON endpoint
        .then(response => response.json())
        .then(data => {
            // Update the DOM with the fetched job information
            displayExistingJobs(data);
        })
        .catch(error => {
            console.error('Error fetching job information:', error);
        });
}

function displayExistingJobs(jobs) {
    const existingJobsContainer = document.getElementById('existingJobs');

    // Clear existing content
    existingJobsContainer.innerHTML = '';


    // Display information about existing jobs in a table
    if (jobs && jobs.length > 0) {
        const table = document.createElement('table');
        table.className = 'job-table';  // Apply a class for styling
        existingJobsContainer.appendChild(table);

        // Create table header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        const headerNames = ['Task Name', 'Task Directory', 'Files Indexed'];  // Adjust column names as needed

        headerNames.forEach(headerName => {
            const th = document.createElement('th');
            th.textContent = headerName;
            headerRow.appendChild(th);
        });

        thead.appendChild(headerRow);
        table.appendChild(thead);

        // Create table body
        const tbody = document.createElement('tbody');

        jobs.forEach(job => {
            const row = document.createElement('tr');

            const cell1 = document.createElement('td');
            cell1.textContent = job.name;  // Assuming 'name' is the property in your job JSON
            row.appendChild(cell1);

            const cell2 = document.createElement('td');
            cell2.textContent = job.directory;  // Adjust property as needed
            row.appendChild(cell2);

            const cell3 = document.createElement('td');
            cell3.textContent = job.indexed_files;  // Adjust property as needed
            row.appendChild(cell3);

            const cell4 = document.createElement('td');
            cell4.innerHTML = "<button onclick=\"deleteJob('" + job.name + "')\">Delete</button>";  // Adjust property as needed
            row.appendChild(cell4);

            tbody.appendChild(row);
        });

        table.appendChild(tbody);
    } else {
        // Display a message if no jobs are available
        existingJobsContainer.textContent = 'No jobs available.';
    }
}

function deleteJob(jobId) {
    // You can perform an AJAX request to the server to delete the job
    // For simplicity, I'm just displaying an alert here
    if (confirm("Are you sure you want to delete this job?")) {
        // Perform the deletion (you may use fetch or another method)
        fetch('/delete_job/' + jobId);
        alert("Job deleted: " + jobId);
        location.reload();
    }
}
// Fetch and display job information initially
fetchAndDisplayExistingJobs();

// Refresh job information every 5 seconds
setInterval(fetchAndDisplayExistingJobs, 5000);
