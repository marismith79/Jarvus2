// Profile page functionality
document.addEventListener('DOMContentLoaded', function() {
    // Handle basic info form submission
    const basicInfoForm = document.getElementById('basic-info-form');
    if (basicInfoForm) {
        basicInfoForm.addEventListener('submit', handleProfileUpdate);
    }

    // Handle name input changes
    const nameInput = document.getElementById('name');
    if (nameInput) {
        let debounceTimer;
        nameInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                handleProfileUpdate(new Event('submit'));
            }, 500); // Wait 500ms after user stops typing
        });
    }

    // Connection handling
    window.connectGmail = function() { window.location.href = '/connect/gmail'; }
    window.connectNotion = function() { showComingSoon(); }
    window.connectSlack = function() { showComingSoon(); }
    window.connectZoom = function() { showComingSoon(); }

    window.disconnectGmail = function() { disconnectService('gmail'); }
    window.disconnectNotion = function() { disconnectService('notion'); }
    window.disconnectSlack = function() { disconnectService('slack'); }
    window.disconnectZoom = function() { disconnectService('zoom'); }
});

function handleProfileUpdate(e) {
    e.preventDefault();
    
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    
    fetch('/api/update_profile', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            name: name,
            email: email
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the welcome message
            document.querySelector('.profile-hero h1').textContent = `Welcome! ${name}`;
            // Only show alert if it was a form submission (not a name input change)
            if (e.type === 'submit') {
                alert('Profile updated successfully!');
            }
        } else {
            alert(data.error || 'Failed to update profile');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating your profile');
    });
}

function showComingSoon() {
    const popup = document.getElementById('comingSoonPopup');
    popup.classList.add('show');
    setTimeout(() => {
        popup.classList.remove('show');
    }, 2000); // Hide after 2 seconds
}

function disconnectService(service) {
    fetch(`/disconnect/${service}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            window.location.reload();
        } else {
            alert('Failed to disconnect service.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while trying to disconnect.');
    });
} 