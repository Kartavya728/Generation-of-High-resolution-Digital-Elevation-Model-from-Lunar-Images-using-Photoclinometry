// static/js/main.js

document.addEventListener('DOMContentLoaded', () => {
    const sfsForm = document.getElementById('sfs-form');
    const submitBtn = document.getElementById('submit-btn');
    
    const progressContainer = document.getElementById('progress-container');
    const progressBar = document.getElementById('progress-bar');
    const progressPercent = document.getElementById('progress-percent');
    const progressMessage = document.getElementById('progress-message');

    const resultsContainer = document.getElementById('results-container');
    const resultsContent = document.getElementById('results-content');
    const errorMessage = document.getElementById('error-message');

    let eventSource;

    sfsForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Reset UI from previous runs
        submitBtn.disabled = true;
        submitBtn.textContent = 'Processing...';
        progressContainer.style.display = 'block';
        resultsContainer.style.display = 'none';
        errorMessage.style.display = 'none';
        updateProgress(0, 'Preparing upload...');

        const formData = new FormData(sfsForm);
        
        // Use fetch to start the SSE connection
        try {
            const response = await fetch('/run-sfs', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Server error occurred.');
            }

            // The body is a ReadableStream. We read it line by line.
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                // SSE sends messages separated by \n\n
                const lines = chunk.split('\n\n');

                for (const line of lines) {
                    if (line.trim() === '') continue;

                    if (line.startsWith('event: progress')) {
                        const dataLine = line.split('\ndata: ')[1];
                        const progressData = JSON.parse(dataLine);
                        updateProgress(progressData.percent, progressData.message);
                    } else if (line.startsWith('event: done')) {
                        const dataLine = line.split('\ndata: ')[1];
                        const resultData = JSON.parse(dataLine);
                        displayResults(resultData);
                        return; // End the loop
                    } else if (line.startsWith('event: error')) {
                        const dataLine = line.split('\ndata: ')[1];
                        const errorData = JSON.parse(dataLine);
                        displayError(errorData.error);
                        return; // End the loop
                    }
                }
            }
        } catch (error) {
            displayError(error.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Run SFS Process';
        }
    });

    function updateProgress(percent, message) {
        progressBar.style.width = `${percent}%`;
        progressPercent.textContent = `${percent}%`;
        progressMessage.textContent = message;
    }

    function displayError(message) {
        progressContainer.style.display = 'none';
        resultsContainer.style.display = 'block';
        resultsContent.style.display = 'none';
        errorMessage.style.display = 'block';
        errorMessage.textContent = `Error: ${message}`;
        console.error(message);
    }

    function displayResults(data) {
        progressContainer.style.display = 'none';
        resultsContainer.style.display = 'block';
        resultsContent.style.display = 'block';
        errorMessage.style.display = 'none';

        // Populate the results
        document.getElementById('model-viewer').src = data.model_obj_url;
        document.getElementById('depth-map-img').src = data.depth_map_png_url;
        document.getElementById('summary-text').textContent = data.summary;

        const downloadLinks = document.getElementById('download-links');
        downloadLinks.innerHTML = `
            <a href="${data.dem_tif_url}" class="download-btn" download>Download DEM (.tif)</a>
            <a href="${data.model_obj_url}" class="download-btn" download>Download 3D Model (.obj)</a>
            <a href="${data.depth_map_png_url}" class="download-btn" download>Download 2D Map (.png)</a>
            <a href="${data.surface_3d_png_url}" class="download-btn" download>Download 3D Plot (.png)</a>
        `;
    }
});