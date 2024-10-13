// main.js

document.addEventListener('DOMContentLoaded', function() {
    // Function to confirm coin claiming
    function confirmCoinClaim(event) {
        const confirmMessage = 'Are you sure you want to claim coins for this account?';
        if (!confirm(confirmMessage)) {
            event.preventDefault();
        }
    }

    // Add click event listeners to all "Claim Coins" buttons
    const claimButtons = document.querySelectorAll('.btn-claim-coins');
    claimButtons.forEach(button => {
        button.addEventListener('click', confirmCoinClaim);
    });

    // Function to toggle password visibility
    function togglePasswordVisibility() {
        const passwordInput = document.querySelector('input[type="password"]');
        const toggleButton = document.querySelector('.toggle-password');
        
        if (passwordInput && toggleButton) {
            toggleButton.addEventListener('click', function() {
                const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
                passwordInput.setAttribute('type', type);
                this.textContent = type === 'password' ? 'Show' : 'Hide';
            });
        }
    }

    // Call the toggle password function
    togglePasswordVisibility();
});
