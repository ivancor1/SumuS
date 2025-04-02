document.addEventListener('DOMContentLoaded', function() {
    const profileForm = document.getElementById('profileForm');
    const profilePicture = document.getElementById('profilePicture');
    const profilePreview = document.getElementById('profilePreview');
    const errorMessage = document.getElementById('errorMessage');

    // Preview profile picture before upload
    profilePicture.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            // Validate file type
            const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
            if (!validTypes.includes(file.type)) {
                errorMessage.textContent = 'Please select a valid image file (jpg, jpeg, png, or gif)';
                profilePicture.value = '';
                return;
            }
            
            // Preview image
            const reader = new FileReader();
            reader.onload = function(e) {
                profilePreview.src = e.target.result;
            }
            reader.readAsDataURL(file);
        }
    });

    // Handle form submission
    profileForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        errorMessage.textContent = ''; // Clear any previous error
        
        try {
            const formData = new FormData(profileForm);
            
            // Log form data for debugging
            console.log("Form data being sent:");
            for (let pair of formData.entries()) {
                console.log(pair[0] + ': ' + pair[1]);
            }
            
            const response = await fetch('/profile/update', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            console.log("Server response:", data);  // Log the server response
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to update profile');
            }
            
            // Success
            alert('Profile updated successfully!');
            setTimeout(() => {
                window.location.replace(data.redirect || '/dashboard');
            }, 100);
            
        } catch (error) {
            console.error('Error details:', error);
            errorMessage.textContent = error.message || 'An error occurred. Please try again.';
        }
    });
}); 