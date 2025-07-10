// Safe console logging to prevent EIO errors
function safeLog(...args) {
  try {
    console.log(...args);
  } catch (e) {
    // Ignore EIO errors from console output
  }
}

function safeWarn(...args) {
  try {
    console.warn(...args);
  } catch (e) {
    // Ignore EIO errors from console output
  }
}

function safeError(...args) {
  try {
    console.error(...args);
  } catch (e) {
    // Ignore EIO errors from console output
  }
}

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
    window.connectService = function(service) {
        // Handle all Google services
        const googleServices = ['gmail', 'google_docs', 'google_sheets', 'google_slides', 'google_drive', 'google_calendar'];
        
        if (googleServices.includes(service)) {
            // Open Pipedream Connect Link directly in the same window
            window.location.href = `/connect/${service}`;
        } else {
            showComingSoon();
        }
    }
    
    window.connectNotion = function() { showComingSoon(); }
    window.connectSlack = function() { showComingSoon(); }
    window.connectZoom = function() { showComingSoon(); }

    window.disconnectNotion = function() { disconnectService('notion'); }
    window.disconnectSlack = function() { disconnectService('slack'); }
    window.disconnectZoom = function() { disconnectService('zoom'); }

//     // Generic: For every tool marked as connected, call /api/connect_tool
//     const toolNames = ['docs', 'notion', 'slack', 'zoom']; // Add future tools here
//     toolNames.forEach(tool => {
//         if (window[tool.replace('-', '_') + 'Connected']) {
//             fetch('/api/connect_tool', {
//                 method: 'POST',
//                 headers: { 'Content-Type': 'application/json' },
//                 body: JSON.stringify({ tool_name: tool })
//             })
//             .then(res => res.json())
//             .then(data => {
//                 if (!data.success) {
//                     console.error(`Failed to connect ${tool} tool:`, data.error);
//                 }
//             })
//             .catch(err => {
//                 console.error(`Error connecting ${tool} tool:`, err);
//             });
//         }
//     });
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
        safeError('Error:', error);
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
            alert('Failed to disconnect service: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        safeError('Error during disconnect API call:', error);
        alert('An error occurred while trying to disconnect.');
    });
} 