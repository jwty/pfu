(function() {
    const clearBtn = document.getElementById('clear-expire');
    const expireDate = document.getElementById('expire-date');
    const expireTime = document.getElementById('expire-time');
    function updateButtonState() {
        clearBtn.disabled = !expireDate.value && !expireTime.value;
        expireDate.required = !!expireTime.value;
    }
    expireDate.addEventListener('input', updateButtonState);
    expireTime.addEventListener('input', updateButtonState);
    clearBtn.addEventListener('click', function() {
        expireDate.value = '';
        expireTime.value = '';
        updateButtonState();
    });
    updateButtonState();
})();