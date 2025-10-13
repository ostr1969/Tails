// existing-jobs.js
function fetchElasticsearchStats() {
    fetch('/_elasticsearch_statistics')
        .then(response => response.json())
        .then(data => {
            // Update the DOM with Elasticsearch statistics
            displayElasticsearchStats(data);
        })
        .catch(error => {
            console.error('Error fetching Elasticsearch statistics:', error);
        });
}

function displayElasticsearchStats(stats) {
    const dashboardContainer = document.getElementById('elasticsearchDashboard');
    dashboardContainer.innerHTML = '';  // Clear existing content

    // Display total number of documents
    const totalDocumentsContainer = document.createElement('div');
    totalDocumentsContainer.innerHTML = `<h3>Total Number of Documents: ${stats.total_documents}</h3>`;
    dashboardContainer.appendChild(totalDocumentsContainer);

    // Display total number of documents with content
    const totalDocumentsWithContentContainer = document.createElement('div');
    totalDocumentsWithContentContainer.innerHTML = `<h3>Total Number of Documents with Content: ${stats.total_documents_with_content}</h3>`;
    dashboardContainer.appendChild(totalDocumentsWithContentContainer);

    // Display file extensions table
    const fileExtensionsTableContainer = document.createElement('div');
    const fileExtensionsTable = document.createElement('table');
    fileExtensionsTable.className = 'file-extensions-table';
    fileExtensionsTableContainer.appendChild(fileExtensionsTable);

    // Create table header
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    headerRow.innerHTML = '<th>File Extension</th><th>Count</th>';
    thead.appendChild(headerRow);
    fileExtensionsTable.appendChild(thead);

    // Create table body
    const tbody = document.createElement('tbody');
    stats.file_extensions.forEach(fileExtension => {
        const row = document.createElement('tr');
        row.innerHTML = `<td>${fileExtension.extension}</td><td>${fileExtension.count}</td>`;
        tbody.appendChild(row);
    });
    fileExtensionsTable.appendChild(tbody);

    dashboardContainer.appendChild(fileExtensionsTableContainer);
}

// Fetch Elasticsearch statistics initially
fetchElasticsearchStats();

// Refresh Elasticsearch statistics every 5 seconds (adjust as needed)
setInterval(fetchElasticsearchStats, 5000);
