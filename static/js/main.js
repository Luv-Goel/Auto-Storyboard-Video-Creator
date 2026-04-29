document.addEventListener('DOMContentLoaded', () => {
    /* Log to verify script initialization */
    console.log('Video Creator script initialized');

    const form = document.getElementById('upload-form');
    const audioInput = document.getElementById('audio');
    const fileNameDisplay = document.getElementById('file-name-display');
    const dropZone = document.getElementById('drop-zone');
    const generateBtn = document.getElementById('generate-btn');
    const btnText = generateBtn.querySelector('.btn-text');
    const loaderDots = generateBtn.querySelector('.loader-dots');
    
    const statusCard = document.getElementById('status-card');
    const progressBar = document.getElementById('progress-bar');
    const statusText = document.getElementById('status-text');
    
    const resultCard = document.getElementById('result-card');
    const resetBtnElement = document.getElementById('reset-btn');
    const videoPlayer = document.getElementById('video-player');
    const downloadLink = document.getElementById('download-link');

    const useDefaultBtn = document.getElementById('use-default-btn');
    const subtitlesCheckbox = document.getElementById('subtitles');
    const subtitleOptions = document.getElementById('subtitle-options');
    let useDefault = false;

    /* File input change listener */
    audioInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            fileNameDisplay.textContent = e.target.files[0].name;
            useDefault = false;
        }
    });

    /* Use default button listener */
    useDefaultBtn.addEventListener('click', (e) => {
        console.log('Use default clicked');
        e.preventDefault();
        e.stopPropagation();
        audioInput.value = '';
        fileNameDisplay.textContent = 'Using Default Earth Narration';
        useDefault = true;
    });

    /* Subtitles toggle listener */
    subtitlesCheckbox.addEventListener('change', (e) => {
        subtitleOptions.classList.toggle('hidden', !e.target.checked);
    });

    /* Drag and drop listeners */
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            audioInput.files = e.dataTransfer.files;
            fileNameDisplay.textContent = e.dataTransfer.files[0].name;
        }
    });

    /* Form submission listener */
    form.addEventListener('submit', async (e) => {
        console.log('Form submitted');
        e.preventDefault();
        
        const formData = new FormData(form);
        
        /* Show loading state */
        btnText.classList.add('hidden');
        loaderDots.classList.remove('hidden');
        generateBtn.disabled = true;
        
        try {
            const response = await fetch('/generate', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            if (data.job_id) {
                startPolling(data.job_id);
            } else {
                alert('Failed to start generation: ' + (data.error || 'Unknown error'));
                resetGenerateButtonState();
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred during submission');
            resetGenerateButtonState();
        }
    });

    function resetGenerateButtonState() {
        btnText.classList.remove('hidden');
        loaderDots.classList.add('hidden');
        generateBtn.disabled = false;
    }

    function startPolling(jobId) {
        form.parentElement.classList.add('hidden');
        statusCard.classList.remove('hidden');
        const progressPercent = document.getElementById('progress-percent');
        
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/status/${jobId}`);
                const data = await response.json();
                
                if (progressBar) progressBar.style.width = `${data.progress}%`;
                if (progressPercent) progressPercent.textContent = `${data.progress}%`;
                statusText.textContent = data.status;
                
                if (data.status.includes('Completed') || data.status === 'completed') {
                    clearInterval(pollInterval);
                    showResult(data.output_url);
                } else if (data.status === 'failed' || data.status.includes('failed')) {
                    clearInterval(pollInterval);
                    statusText.textContent = 'Error: ' + data.error;
                    statusText.classList.add('error');
                    resetBtnElement.classList.remove('hidden');
                }
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, 2000);
    }

    /* Reset button listener */
    if (resetBtnElement) {
        resetBtnElement.addEventListener('click', () => {
            location.reload();
        });
    }

    function showResult(videoUrl) {
        statusCard.classList.add('hidden');
        resultCard.classList.remove('hidden');
        videoPlayer.src = videoUrl;
        downloadLink.href = videoUrl;
    }
});
