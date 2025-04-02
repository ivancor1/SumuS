document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const form = e.target;
    const errorMessage = document.getElementById('errorMessage');
    
    try {
        const response = await fetch('/login', {
            method: 'POST',
            body: new FormData(form)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            errorMessage.textContent = data.error;
            return;
        }
        
        // Success - redirect to dashboard
        alert('Logged in successfully!');
        window.location.href = '/dashboard';
        
    } catch (error) {
        errorMessage.textContent = 'An error occurred. Please try again.';
        console.error('Error:', error);
    }
}); 