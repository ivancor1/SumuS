document.getElementById('signupForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const form = e.target;
    const errorMessage = document.getElementById('errorMessage');
    
    // Basic validation
    const password = form.password.value;
    const confirmPassword = form.confirm_password.value;
    
    if (password !== confirmPassword) {
        errorMessage.textContent = 'Passwords do not match';
        return;
    }
    
    try {
        const response = await fetch('/signup', {
            method: 'POST',
            body: new FormData(form)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            errorMessage.textContent = data.error;
            return;
        }
        
        // Success - redirect to login or dashboard
        alert('Account created successfully!');
        window.location.href = '/';
        
    } catch (error) {
        errorMessage.textContent = 'An error occurred. Please try again.';
        console.error('Error:', error);
    }
}); 