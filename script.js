// HealthLink - Smart Hospital Appointment & Wellness Alert System

// Form validation
document.addEventListener('DOMContentLoaded', function() {
    // Password confirmation validation for registration
    const registerForm = document.querySelector('form[action="/register"]');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            const password = document.getElementById('password').value;
            if (password.length < 6) {
                alert('Password must be at least 6 characters long');
                e.preventDefault();
                return;
            }
        });
    }

    // Appointment date validation
    const appointmentForm = document.querySelector('form[action="/appointment"]');
    if (appointmentForm) {
        appointmentForm.addEventListener('submit', function(e) {
            const appointmentDate = new Date(document.getElementById('appointment_date').value);
            const now = new Date();

            if (appointmentDate <= now) {
                alert('Please select a future date and time for your appointment');
                e.preventDefault();
                return;
            }
        });
    }

    // Vitals form validation
    const vitalsForm = document.querySelector('form[action="/vitals"]');
    if (vitalsForm) {
        vitalsForm.addEventListener('submit', function(e) {
            const bloodPressure = document.getElementById('blood_pressure').value;
            const heartRate = document.getElementById('heart_rate').value;
            const temperature = document.getElementById('temperature').value;
            const weight = document.getElementById('weight').value;

            // Basic validation
            if (bloodPressure && !/^\d{2,3}\/\d{2,3}$/.test(bloodPressure)) {
                alert('Blood pressure should be in format: systolic/diastolic (e.g., 120/80)');
                e.preventDefault();
                return;
            }

            if (heartRate && (heartRate < 30 || heartRate > 200)) {
                alert('Heart rate should be between 30 and 200 bpm');
                e.preventDefault();
                return;
            }

            if (temperature && (temperature < 95 || temperature > 110)) {
                alert('Temperature should be between 95°F and 110°F');
                e.preventDefault();
                return;
            }

            if (weight && (weight < 50 || weight > 500)) {
                alert('Weight should be between 50 and 500 lbs');
                e.preventDefault();
                return;
            }
        });
    }

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.style.display = 'none';
            }, 300);
        }, 5000);
    });
});

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

function showLoading(button) {
    const originalText = button.textContent;
    button.textContent = 'Processing...';
    button.disabled = true;

    return function() {
        button.textContent = originalText;
        button.disabled = false;
    };
}