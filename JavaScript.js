// Configuration
const API_ENDPOINT = 'http://localhost:5000/api/submit-patient-data';

// DOM Elements
const patientForm = document.getElementById('patientForm');
const submitBtn = document.getElementById('submitBtn');
const messageContainer = document.getElementById('messageContainer');
const bodyPartPhotoInput = document.getElementById('bodyPartPhoto');
const medicalReportsInput = document.getElementById('medicalReports');
const photoPreview = document.getElementById('photoPreview');
const reportPreview = document.getElementById('reportPreview');

// File storage
let selectedPhotos = [];
let selectedReports = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    setupFilePreview();
});

// Setup Event Listeners
function setupEventListeners() {
    patientForm.addEventListener('submit', handleFormSubmit);
    
    // Phone number formatting
    const phoneInput = document.getElementById('phone');
    phoneInput.addEventListener('input', formatPhoneNumber);
}

// Setup File Preview
function setupFilePreview() {
    bodyPartPhotoInput.addEventListener('change', (e) => {
        handleFileSelection(e, 'photos');
    });

    medicalReportsInput.addEventListener('change', (e) => {
        handleFileSelection(e, 'reports');
    });
}

// Handle File Selection
function handleFileSelection(event, type) {
    const files = Array.from(event.target.files);
    const maxFiles = 5;
    const maxSize = 5 * 1024 * 1024; // 5MB

    if (type === 'photos') {
        if (selectedPhotos.length + files.length > maxFiles) {
            showMessage(`You can only upload up to ${maxFiles} photos`, 'error');
            return;
        }

        files.forEach(file => {
            if (file.size > maxSize) {
                showMessage(`File ${file.name} is too large. Max size is 5MB`, 'error');
                return;
            }

            if (!file.type.startsWith('image/')) {
                showMessage(`File ${file.name} is not an image`, 'error');
                return;
            }

            selectedPhotos.push(file);
            createPreview(file, 'photos');
        });
    } else if (type === 'reports') {
        if (selectedReports.length + files.length > maxFiles) {
            showMessage(`You can only upload up to ${maxFiles} reports`, 'error');
            return;
        }

        files.forEach(file => {
            if (file.size > maxSize) {
                showMessage(`File ${file.name} is too large. Max size is 5MB`, 'error');
                return;
            }

            selectedReports.push(file);
            createPreview(file, 'reports');
        });
    }

    // Clear the input value to allow re-selection of the same file
    event.target.value = '';
}

// Create Preview
function createPreview(file, type) {
    const previewContainer = type === 'photos' ? photoPreview : reportPreview;
    const fileArray = type === 'photos' ? selectedPhotos : selectedReports;
    
    const previewItem = document.createElement('div');
    previewItem.className = 'preview-item';
    
    if (file.type.startsWith('image/')) {
        const img = document.createElement('img');
        const reader = new FileReader();
        
        reader.onload = (e) => {
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
        
        previewItem.appendChild(img);
    } else {
        // For PDFs, show a placeholder
        const placeholder = document.createElement('div');
        placeholder.style.cssText = 'display: flex; align-items: center; justify-content: center; height: 100%; background: #f3f4f6; font-size: 12px; text-align: center; padding: 8px;';
        placeholder.textContent = file.name;
        previewItem.appendChild(placeholder);
    }
    
    // Add remove button
    const removeBtn = document.createElement('button');
    removeBtn.className = 'remove-btn';
    removeBtn.innerHTML = '×';
    removeBtn.type = 'button';
    removeBtn.onclick = () => {
        const index = fileArray.indexOf(file);
        if (index > -1) {
            fileArray.splice(index, 1);
        }
        previewItem.remove();
    };
    
    previewItem.appendChild(removeBtn);
    previewContainer.appendChild(previewItem);
}

// Format Phone Number
function formatPhoneNumber(e) {
    let value = e.target.value.replace(/\D/g, '');
    if (value.length > 15) {
        value = value.slice(0, 15);
    }
    e.target.value = value;
}

// Handle Form Submit
async function handleFormSubmit(event) {
    event.preventDefault();
    
    // Validate form
    if (!patientForm.checkValidity()) {
        showMessage('Please fill in all required fields', 'error');
        return;
    }

    // Show loading state
    setLoadingState(true);
    
    try {
        // Create FormData object
        const formData = new FormData();
        
        // Add all form fields
        const formElements = patientForm.elements;
        for (let element of formElements) {
            if (element.type === 'checkbox') {
                formData.append(element.name, element.checked);
            } else if (element.type !== 'file' && element.name) {
                formData.append(element.name, element.value);
            }
        }
        
        // Add photos
        selectedPhotos.forEach((photo, index) => {
            formData.append(`photo_${index}`, photo);
        });
        
        // Add reports
        selectedReports.forEach((report, index) => {
            formData.append(`report_${index}`, report);
        });
        
        // Add metadata
        formData.append('submissionTime', new Date().toISOString());
        formData.append('photoCount', selectedPhotos.length);
        formData.append('reportCount', selectedReports.length);
        
        // Send to server
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showMessage('✅ Patient information submitted successfully! Our team will review your case shortly.', 'success');
            
            // Reset form after successful submission
            setTimeout(() => {
                resetForm();
            }, 2000);
        } else {
            throw new Error(result.error || 'Submission failed');
        }
        
    } catch (error) {
        console.error('Error submitting form:', error);
        showMessage(`❌ Error: ${error.message}. Please try again or contact support.`, 'error');
    } finally {
        setLoadingState(false);
    }
}

// Set Loading State
function setLoadingState(isLoading) {
    const btnText = submitBtn.querySelector('.btn-text');
    const btnLoader = submitBtn.querySelector('.btn-loader');
    
    if (isLoading) {
        submitBtn.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline-block';
        patientForm.classList.add('loading');
    } else {
        submitBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
        patientForm.classList.remove('loading');
    }
}

// Show Message
function showMessage(message, type) {
    messageContainer.textContent = message;
    messageContainer.className = type;
    messageContainer.style.display = 'block';
    
    // Auto-hide success messages after 5 seconds
    if (type === 'success') {
        setTimeout(() => {
            messageContainer.style.display = 'none';
        }, 5000);
    }
    
    // Scroll to message
    messageContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Reset Form
function resetForm() {
    patientForm.reset();
    selectedPhotos = [];
    selectedReports = [];
    photoPreview.innerHTML = '';
    reportPreview.innerHTML = '';
    messageContainer.style.display = 'none';
}

// Handle offline status
window.addEventListener('offline', () => {
    showMessage('⚠️ You are offline. Please check your internet connection.', 'error');
});

window.addEventListener('online', () => {
    showMessage('✅ You are back online!', 'success');
});

// Prevent form resubmission on page refresh
if (window.history.replaceState) {
    window.history.replaceState(null, null, window.location.href);
}