document.addEventListener('DOMContentLoaded', function() {
    const spinner = document.getElementById('spinner');
    const goButton = document.getElementById('goButton');
    const searchBox = document.getElementById('searchBox');
    const dropdown = document.getElementById('dropdown');
    const insightButton = document.getElementById('insightButton');
    const modal = document.getElementById('modal');
    const closeModal = document.getElementById('closeModal');
    const modalContent = document.getElementById('modalContent');

    // Clear the text area on page reload
    searchBox.value = '';

    searchBox.addEventListener('input', function() {
        if (this.value.trim() !== '') {
            goButton.disabled = false;
        } else {
            goButton.disabled = true;
        }
    });

    goButton.addEventListener('click', function() {
        const selectedOption = dropdown.value;
        const searchText = searchBox.value;
        const url = `/search?${selectedOption}=${encodeURIComponent(searchText)}`;

        // Show spinner and disable inputs
        spinner.classList.remove('hidden');
        goButton.disabled = true;
        searchBox.disabled = true;
        dropdown.disabled = true;

        fetch(url)
            .then(response => response.json())
            .then(data => {
                const tableBody = document.getElementById('resultsTable').querySelector('tbody');
                tableBody.innerHTML = '';

                data.forEach(item => {
                    const row = document.createElement('tr');
                    row.classList.add('border-b', 'border-gray-200', 'hover:bg-gray-100'); // Add Tailwind classes to rows

                    // Add checkbox cell
                    const checkboxCell = document.createElement('td');
                    checkboxCell.classList.add('p-2', 'text-center', 'border-r', 'border-gray-200');
                    const checkbox = document.createElement('input');
                    checkbox.type = 'checkbox';
                    checkbox.addEventListener('change', function() {
                        const checkboxes = document.querySelectorAll('#resultsTable tbody input[type="checkbox"]');
                        const checkedCount = Array.from(checkboxes).filter(checkbox => checkbox.checked).length;
                        if (checkedCount >= 2) {
                            insightButton.classList.remove('hidden');
                        } else {
                            insightButton.classList.add('hidden');
                        }
                    });
                    checkboxCell.appendChild(checkbox);
                    row.appendChild(checkboxCell);

                    const columns = [
                        'Incident ID', 'Job Name', 'Work Details', 'Notes', 'Summary',
                        'Reported Date', 'Resolved Date', 'Resolution', 'Submit Date',
                        'Submitter Name', 'Submitter', 'Status', 'Assignee',
                        'Assigned Group', 'Flag', 'MQ', 'job', 'done'
                    ];
                    columns.forEach(column => {
                        const cell = document.createElement('td');
                        cell.textContent = item[column];
                        cell.classList.add('p-2', 'text-center', 'border-r', 'border-gray-200'); // Add Tailwind classes to cells
                        row.appendChild(cell);
                    });
                    tableBody.appendChild(row);
                });

                // Hide spinner and enable inputs
                spinner.classList.add('hidden');
                goButton.disabled = false;
                searchBox.disabled = false;
                dropdown.disabled = false;
            })
            .catch(error => {
                console.error('Error:', error);
                // Hide spinner and enable inputs in case of error
                spinner.classList.add('hidden');
                goButton.disabled = false;
                searchBox.disabled = false;
                dropdown.disabled = false;
            });
    });

    insightButton.addEventListener('click', function() {
        const checkboxes = document.querySelectorAll('#resultsTable tbody input[type="checkbox"]');
        const resolutions = [];
        checkboxes.forEach((checkbox, index) => {
            if (checkbox.checked) {
                const row = checkbox.closest('tr');
                const resolutionCell = row.children[8]; // Assuming 'Resolution' is the 9th column (index 8)
                resolutions.push(resolutionCell.textContent);
            }
        });

        // Show spinner
        spinner.classList.remove('hidden');

        // Send selected values to the '/insight' endpoint
        const url = `/insight?resolutions=${encodeURIComponent(resolutions.join(','))}`;
        fetch(url, { method: 'GET' })
            .then(response => response.json())
            .then(data => {
                console.log('Insight Response:', data);
                // Hide spinner
                spinner.classList.add('hidden');

                // Show modal with resolutions
                modalContent.textContent = data.resolutions;
                modal.classList.remove('hidden');
            })
            .catch(error => {
                console.error('Error:', error);
                // Hide spinner in case of error
                spinner.classList.add('hidden');
            });
    });

    closeModal.addEventListener('click', function(event) {
        event.stopPropagation(); // Prevent the modal click event from firing
        modal.classList.add('hidden');
    });

    modal.addEventListener('click', function(event) {
        if (event.target !== closeModal && !closeModal.contains(event.target)) {
            const text = modalContent.textContent;
            navigator.clipboard.writeText(text).then(() => {
                alert('Text copied to clipboard');
            }).catch(err => {
                console.error('Failed to copy text: ', err);
            });
        }
    });
});