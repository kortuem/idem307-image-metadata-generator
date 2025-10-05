// Image Metadata Generator - Frontend JavaScript

// State Management
const state = {
    sessionId: null,
    semanticContext: '',  // v2.0: User-provided context (e.g., "TU Delft drawing studio")
    images: [],
    captions: {},
    currentImageIndex: 0,
    uploadedFiles: []
};

// Debug Logger
const DEBUG = {
    INFO: 'info',
    SUCCESS: 'success',
    WARNING: 'warning',
    ERROR: 'error'
};

function log(level, message) {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry log-${level}`;
    logEntry.textContent = `[${timestamp}] ${level.toUpperCase()}: ${message}`;

    const debugLogs = document.getElementById('debug-logs');
    debugLogs.appendChild(logEntry);

    // Only auto-scroll if debug panel is visible AND user is near the bottom
    const debugContent = document.getElementById('debug-content');
    if (!debugContent.classList.contains('collapsed')) {
        const isNearBottom = debugLogs.scrollHeight - debugLogs.scrollTop - debugLogs.clientHeight < 100;
        if (isNearBottom) {
            debugLogs.scrollTop = debugLogs.scrollHeight;
        }
    }

    // Also log to browser console
    console.log(`[${level}] ${message}`);
}

// Theme Management
function initializeTheme() {
    // Get saved theme preference or use system preference
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = savedTheme || (systemPrefersDark ? 'dark' : 'light');

    setTheme(theme);
}

function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);

    // Update icon visibility
    const lightIcon = document.getElementById('theme-icon-light');
    const darkIcon = document.getElementById('theme-icon-dark');

    if (theme === 'dark') {
        lightIcon.style.display = 'none';
        darkIcon.style.display = 'block';
    } else {
        lightIcon.style.display = 'block';
        darkIcon.style.display = 'none';
    }
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    log(DEBUG.INFO, `Theme switched to ${newTheme} mode`);
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    log(DEBUG.INFO, 'Application initialized');
    initializeTheme();
    initializeEventListeners();
    checkAPIHealth();
});

function initializeEventListeners() {
    // Upload handlers
    const uploadInput = document.getElementById('image-upload');
    const uploadArea = document.querySelector('.upload-area');

    uploadInput.addEventListener('change', handleFileUpload);

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        uploadInput.files = files;
        handleFileUpload({ target: uploadInput });
    });

    // Clear upload
    document.getElementById('clear-upload').addEventListener('click', clearUpload);

    // Semantic context validation
    const contextInput = document.getElementById('semantic-context');
    contextInput.addEventListener('input', validateSemanticContext);
    contextInput.addEventListener('blur', validateSemanticContext);

    // Generate captions
    document.getElementById('generate-btn').addEventListener('click', generateCaptions);

    // Caption editing
    const captionTextarea = document.getElementById('caption-text');
    captionTextarea.addEventListener('input', debounce(updateCaption, 1000));
    captionTextarea.addEventListener('blur', updateCaption);

    // Navigation
    document.getElementById('prev-btn').addEventListener('click', () => navigateImage(-1));
    document.getElementById('next-btn').addEventListener('click', () => navigateImage(1));

    // Export
    document.getElementById('preview-btn').addEventListener('click', previewMetadata);
    document.getElementById('export-btn').addEventListener('click', exportZip);

    // Debug console
    document.getElementById('toggle-debug').addEventListener('click', toggleDebug);
    document.getElementById('clear-logs').addEventListener('click', clearLogs);
    document.getElementById('copy-logs').addEventListener('click', copyLogs);

    // Modal
    document.getElementById('close-modal').addEventListener('click', closeModal);
    document.getElementById('modal-close-btn').addEventListener('click', closeModal);

    // Theme toggle
    document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
}

// API Health Check
async function checkAPIHealth() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();

        if (data.status === 'healthy') {
            log(DEBUG.SUCCESS, 'API health check passed');

            // Show capacity info if available
            if (data.capacity) {
                const utilization = data.capacity.utilization_percent;
                log(DEBUG.INFO, `Server capacity: ${data.capacity.active_sessions}/${data.capacity.max_sessions} sessions (${utilization}% utilized)`);

                // Warn if getting close to capacity
                if (utilization > 80) {
                    log(DEBUG.WARNING, `Server is ${utilization}% full. You may experience delays.`);
                }
            }
        } else {
            log(DEBUG.ERROR, `API health check failed: ${data.error}`);
        }
    } catch (error) {
        log(DEBUG.ERROR, `API health check failed: ${error.message}`);
    }
}

function showCapacityError(data) {
    const message = `
        <div class="capacity-error">
            <h3>⚠️ Server Busy</h3>
            <p>${data.message}</p>
            <p><strong>Active users:</strong> ${data.active_sessions}/${data.max_sessions}</p>
            <p><strong>Suggestion:</strong> Please wait 2-3 minutes and try again.</p>
            <button onclick="location.reload()" class="btn btn-primary" style="margin-top: 1rem;">
                Retry Now
            </button>
        </div>
    `;

    // Show in alert or modal
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-warning';
    alertDiv.innerHTML = message;
    alertDiv.style.cssText = 'position: fixed; top: 20px; left: 50%; transform: translateX(-50%); z-index: 1000; max-width: 500px; padding: 2rem; background: #fff3cd; border: 2px solid #ffc107; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);';

    document.body.appendChild(alertDiv);

    log(DEBUG.ERROR, `Server at capacity: ${data.active_sessions}/${data.max_sessions} users active`);

    // Auto-remove after 10 seconds
    setTimeout(() => alertDiv.remove(), 10000);
}

// File Upload
async function handleFileUpload(event) {
    const files = Array.from(event.target.files);

    if (files.length === 0) {
        return;
    }

    log(DEBUG.INFO, `Uploading ${files.length} files...`);

    // Show upload progress
    const progressSection = document.getElementById('progress-section');
    const progressBar = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    progressSection.style.display = 'block';
    progressBar.style.width = '0%';
    progressText.textContent = 'Uploading images...';

    const formData = new FormData();
    files.forEach(file => formData.append('images', file));

    try {
        // Create XMLHttpRequest for upload progress tracking
        const xhr = new XMLHttpRequest();

        // Track upload progress
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = Math.round((e.loaded / e.total) * 100);
                progressBar.style.width = percentComplete + '%';
                progressText.textContent = `Uploading images... ${percentComplete}%`;
            }
        });

        // Convert to Promise
        const uploadPromise = new Promise((resolve, reject) => {
            xhr.addEventListener('load', () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    resolve(JSON.parse(xhr.responseText));
                } else if (xhr.status === 503) {
                    // Parse 503 response (server busy) - treat as resolved to show error
                    try {
                        resolve(JSON.parse(xhr.responseText));
                    } catch (e) {
                        reject(new Error(`Server busy (503)`));
                    }
                } else {
                    reject(new Error(`Upload failed: ${xhr.status}`));
                }
            });
            xhr.addEventListener('error', () => reject(new Error('Upload failed')));
            xhr.open('POST', '/api/upload');
            xhr.send(formData);
        });

        const data = await uploadPromise;

        // Check for capacity error (503)
        if (!data.success && data.error === 'server_busy') {
            progressSection.style.display = 'none';
            showCapacityError(data);
            return;
        }

        // Update progress to complete
        progressBar.style.width = '100%';
        progressText.textContent = 'Upload complete!';

        if (data.success) {
            state.sessionId = data.session_id;
            state.images = data.images;
            state.captions = {}; // Reset captions
            state.currentImageIndex = 0; // Reset editor index

            // Show upload info
            document.getElementById('upload-info').style.display = 'flex';
            document.getElementById('upload-count').textContent =
                `${data.total_valid} images uploaded`;

            // Initialize captions object
            data.images.forEach(img => {
                state.captions[img.filename] = {
                    text: '',
                    edited: false
                };
            });

            log(DEBUG.SUCCESS, `Uploaded ${data.total_valid} images`);

            if (data.total_rejected > 0) {
                log(DEBUG.WARNING, `${data.total_rejected} files rejected`);
                data.rejected.forEach(r => {
                    log(DEBUG.WARNING, `${r.filename}: ${r.reason}`);
                });
            }

            // Show gallery
            renderImageGrid();

            // Enable semantic context input if disabled
            document.getElementById('semantic-context').disabled = false;

            // Reset UI sections - hide editor and export until new captions are generated
            document.getElementById('editor-section').style.display = 'none';
            document.getElementById('export-section').style.display = 'none';
            document.getElementById('progress-section').style.display = 'none';

            // Reset semantic context
            document.getElementById('semantic-context').value = '';
            state.semanticContext = '';

            // Disable generate button until semantic context is entered
            document.getElementById('generate-btn').disabled = true;
        } else {
            log(DEBUG.ERROR, `Upload failed: ${data.error}`);
        }
    } catch (error) {
        log(DEBUG.ERROR, `Upload error: ${error.message}`);
    }
}

function clearUpload() {
    document.getElementById('image-upload').value = '';
    document.getElementById('upload-info').style.display = 'none';
    document.getElementById('gallery-section').style.display = 'none';
    document.getElementById('editor-section').style.display = 'none';
    document.getElementById('export-section').style.display = 'none';

    state.sessionId = null;
    state.images = [];
    state.captions = {};

    log(DEBUG.INFO, 'Upload cleared');
}

// Semantic Context Validation (v2.0)
async function validateSemanticContext() {
    const input = document.getElementById('semantic-context');
    const semanticContext = input.value.trim();
    const validationDiv = document.getElementById('context-validation');
    const generateBtn = document.getElementById('generate-btn');

    if (!semanticContext) {
        input.classList.remove('valid', 'invalid');
        validationDiv.textContent = '';
        validationDiv.className = 'validation-message';
        generateBtn.disabled = true;
        return;
    }

    try {
        const response = await fetch('/api/validate-semantic-context', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ semantic_context: semanticContext })
        });

        const data = await response.json();

        if (data.valid) {
            input.classList.add('valid');
            input.classList.remove('invalid');
            validationDiv.textContent = '✓ Valid context';
            validationDiv.className = 'validation-message success';

            state.semanticContext = semanticContext;
            generateBtn.disabled = state.images.length === 0;

            log(DEBUG.SUCCESS, `Semantic context validated: ${semanticContext}`);
        } else {
            input.classList.add('invalid');
            input.classList.remove('valid');
            validationDiv.textContent = `✗ ${data.error}`;
            validationDiv.className = 'validation-message error';

            if (data.examples) {
                validationDiv.textContent += ` (Examples: ${data.examples.slice(0, 2).join(', ')})`;
            }

            generateBtn.disabled = true;
        }
    } catch (error) {
        log(DEBUG.ERROR, `Validation error: ${error.message}`);
    }
}

// Generate Captions (one image at a time for real-time progress) - v2.0
async function generateCaptions() {
    if (!state.sessionId || !state.semanticContext) {
        log(DEBUG.ERROR, 'Missing session ID or semantic context');
        return;
    }

    const generateBtn = document.getElementById('generate-btn');
    generateBtn.disabled = true;
    generateBtn.textContent = 'Generating...';

    // Show progress section
    document.getElementById('progress-section').style.display = 'block';

    const totalImages = state.images.length;
    let processedCount = 0;
    let successCount = 0;

    log(DEBUG.INFO, `Starting caption generation for ${totalImages} images...`);

    // Get required API key from user input
    const userApiKey = document.getElementById('api-key').value.trim();

    if (!userApiKey) {
        log(DEBUG.ERROR, 'API key is required');
        alert('Please enter your Gemini API key or access code');
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate Captions';
        return;
    }

    // Process each image individually for real-time updates
    for (const imageFile of state.images) {
        const filename = imageFile.filename;

        // Update progress BEFORE processing starts
        processedCount++;
        log(DEBUG.INFO, `Processing ${filename} (${processedCount}/${totalImages})`);
        updateProgress(processedCount, totalImages);

        try {
            const requestBody = {
                session_id: state.sessionId,
                filename: filename,
                semantic_context: state.semanticContext,
                api_key: userApiKey
            };

            const response = await fetch('/api/generate-single', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();

            if (data.success) {
                // Update caption in state
                state.captions[filename] = {
                    text: data.caption,
                    edited: false
                };
                successCount++;

                log(DEBUG.SUCCESS, `✓ Generated caption for ${filename}: ${data.caption.substring(0, 80)}...`);
            } else {
                log(DEBUG.ERROR, `✗ Failed to generate caption for ${filename}: ${data.error}`);
            }

        } catch (error) {
            log(DEBUG.ERROR, `Error processing ${filename}: ${error.message}`);
        }
    }

    // All images processed
    log(DEBUG.SUCCESS, `Completed: ${successCount}/${totalImages} captions generated`);

    if (successCount > 0) {
        // Show editor and export sections
        document.getElementById('editor-section').style.display = 'block';
        document.getElementById('export-section').style.display = 'block';

        // Load first image in editor
        state.currentImageIndex = 0;
        loadImageInEditor(0);
    }

    // Re-enable button
    generateBtn.disabled = false;
    generateBtn.textContent = 'Generate Captions';

    // Hide progress after a delay
    setTimeout(() => {
        document.getElementById('progress-section').style.display = 'none';
    }, 2000);
}

function updateProgress(current, total) {
    const percentage = Math.round((current / total) * 100);
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');

    progressFill.style.width = `${percentage}%`;
    progressText.textContent = `Processing ${current} of ${total} (${percentage}%)`;
}

// Image Grid
function renderImageGrid() {
    const grid = document.getElementById('image-grid');
    grid.innerHTML = '';

    state.images.forEach((image, index) => {
        const item = document.createElement('div');
        item.className = 'image-item';
        item.dataset.index = index;

        const img = document.createElement('img');
        img.src = image.thumbnail;
        img.alt = image.filename;
        img.className = 'image-thumbnail';

        const filename = document.createElement('div');
        filename.className = 'image-filename';
        filename.textContent = image.filename;

        item.appendChild(img);
        item.appendChild(filename);

        item.addEventListener('click', () => {
            state.currentImageIndex = index;
            loadImageInEditor(index);
        });

        grid.appendChild(item);
    });

    document.getElementById('gallery-section').style.display = 'block';
}

function updateImageGridSelection() {
    const items = document.querySelectorAll('.image-item');
    items.forEach((item, index) => {
        item.classList.remove('selected');
        if (index === state.currentImageIndex) {
            item.classList.add('selected');
        }

        // Mark edited items
        const filename = state.images[index].filename;
        if (state.captions[filename] && state.captions[filename].edited) {
            item.classList.add('edited');
        }
    });
}

// Caption Editor
function loadImageInEditor(index) {
    if (index < 0 || index >= state.images.length) {
        return;
    }

    const image = state.images[index];
    const caption = state.captions[image.filename];

    // Update preview image
    document.getElementById('preview-image').src = image.thumbnail;
    document.getElementById('preview-filename').textContent = image.filename;

    // Update caption textarea
    document.getElementById('caption-text').value = caption ? caption.text : '';

    // Update edit indicator
    const indicator = document.getElementById('edit-indicator');
    if (caption && caption.edited) {
        indicator.textContent = 'Edited';
        indicator.className = 'indicator edited';
    } else {
        indicator.textContent = 'Auto-generated';
        indicator.className = 'indicator auto';
    }

    // Update character count
    updateCharCount();

    // Update navigation
    updateNavigation();

    // Update grid selection
    updateImageGridSelection();
}

function updateCaption() {
    const index = state.currentImageIndex;
    const image = state.images[index];
    const newCaption = document.getElementById('caption-text').value;

    // Update state
    state.captions[image.filename] = {
        text: newCaption,
        edited: true
    };

    // Update server
    fetch('/api/caption', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: state.sessionId,
            filename: image.filename,
            caption: newCaption
        })
    }).then(response => response.json())
      .then(data => {
          if (data.success) {
              log(DEBUG.SUCCESS, `Caption updated for ${image.filename}`);

              // Update edit indicator
              const indicator = document.getElementById('edit-indicator');
              indicator.textContent = 'Edited';
              indicator.className = 'indicator edited';

              // Update grid
              updateImageGridSelection();
          }
      })
      .catch(error => {
          log(DEBUG.ERROR, `Failed to update caption: ${error.message}`);
      });
}

function updateCharCount() {
    const textarea = document.getElementById('caption-text');
    const charCount = document.getElementById('caption-count');
    charCount.textContent = `${textarea.value.length} characters`;
}

function navigateImage(direction) {
    const newIndex = state.currentImageIndex + direction;
    if (newIndex >= 0 && newIndex < state.images.length) {
        state.currentImageIndex = newIndex;
        loadImageInEditor(newIndex);
    }
}

function updateNavigation() {
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    const navPosition = document.getElementById('nav-position');

    prevBtn.disabled = state.currentImageIndex === 0;
    nextBtn.disabled = state.currentImageIndex === state.images.length - 1;

    navPosition.textContent = `${state.currentImageIndex + 1} of ${state.images.length}`;
}

// Export
async function previewMetadata() {
    if (!state.sessionId) {
        log(DEBUG.ERROR, 'No active session');
        return;
    }

    try {
        const response = await fetch(`/api/preview/${state.sessionId}`);
        const data = await response.json();

        if (data.success) {
            document.getElementById('preview-content').textContent = data.metadata_content;
            document.getElementById('preview-modal').style.display = 'flex';

            if (data.warnings.length > 0) {
                log(DEBUG.WARNING, `Preview warnings: ${data.warnings.length} missing captions`);
                data.warnings.forEach(w => log(DEBUG.WARNING, w));
            }
        } else {
            log(DEBUG.ERROR, `Preview failed: ${data.error}`);
        }
    } catch (error) {
        log(DEBUG.ERROR, `Preview error: ${error.message}`);
    }
}

async function exportZip() {
    if (!state.sessionId) {
        log(DEBUG.ERROR, 'No active session');
        return;
    }

    log(DEBUG.INFO, 'Exporting training zip...');

    try {
        // Generate dataset name from semantic context
        const datasetName = state.semanticContext
            ? state.semanticContext.toLowerCase().replace(/\s+/g, '_')
            : 'dataset';

        const response = await fetch('/api/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                session_id: state.sessionId,
                dataset_name: datasetName
            })
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${datasetName}_training.zip`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            log(DEBUG.SUCCESS, `Exported ${datasetName}_training.zip`);
        } else {
            const data = await response.json();
            log(DEBUG.ERROR, `Export failed: ${data.error}`);
        }
    } catch (error) {
        log(DEBUG.ERROR, `Export error: ${error.message}`);
    }
}

// Modal
function closeModal() {
    document.getElementById('preview-modal').style.display = 'none';
}

// Debug Console
function toggleDebug() {
    const content = document.getElementById('debug-content');
    const toggleBtn = document.getElementById('toggle-debug');

    if (content.classList.contains('collapsed')) {
        content.classList.remove('collapsed');
        toggleBtn.textContent = '▼';
    } else {
        content.classList.add('collapsed');
        toggleBtn.textContent = '▶';
    }
}

function clearLogs() {
    document.getElementById('debug-logs').innerHTML = '';
    log(DEBUG.INFO, 'Logs cleared');
}

function copyLogs() {
    const logs = document.getElementById('debug-logs').innerText;
    navigator.clipboard.writeText(logs).then(() => {
        log(DEBUG.SUCCESS, 'Logs copied to clipboard');
    }).catch(error => {
        log(DEBUG.ERROR, `Failed to copy logs: ${error.message}`);
    });
}

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Keyboard shortcuts (optional enhancement)
document.addEventListener('keydown', (e) => {
    // Only if editor is visible
    if (document.getElementById('editor-section').style.display === 'none') {
        return;
    }

    // Ignore if typing in textarea
    if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') {
        return;
    }

    if (e.key === 'ArrowLeft') {
        e.preventDefault();
        navigateImage(-1);
    } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        navigateImage(1);
    }
});
