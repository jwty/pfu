(function() {
    const clearBtn = document.getElementById('clear-expire');
    const setNextHourBtn = document.getElementById('set-next-hour');
    const setNextDayBtn = document.getElementById('set-next-day');
    const setNextWeekBtn = document.getElementById('set-next-week');
    const setNextMonthBtn = document.getElementById('set-next-month');
    const expireDate = document.getElementById('expire-date');
    const expireTime = document.getElementById('expire-time');

    function updateButtonState() {
        clearBtn.disabled = !expireDate.value && !expireTime.value;
        expireDate.required = !!expireTime.value;
    }

    function setExpiration(addHours, addMonths = 0) {
        let baseDate = new Date();
        if (expireDate.value) {
            // Default to current time if expireTime is empty
            const timePart = expireTime.value || `${String(baseDate.getHours()).padStart(2, '0')}:${String(baseDate.getMinutes()).padStart(2, '0')}`;
            baseDate = new Date(`${expireDate.value}T${timePart}`);
        }
        if (addHours) baseDate.setHours(baseDate.getHours() + addHours);
        if (addMonths) baseDate.setMonth(baseDate.getMonth() + addMonths);
        const outYear = baseDate.getFullYear();
        const outMonth = String(baseDate.getMonth() + 1).padStart(2, '0');
        const outDay = String(baseDate.getDate()).padStart(2, '0');
        expireDate.value = `${outYear}-${outMonth}-${outDay}`;
        const outHours = String(baseDate.getHours()).padStart(2, '0');
        const outMinutes = String(baseDate.getMinutes()).padStart(2, '0');
        expireTime.value = `${outHours}:${outMinutes}`;
        updateButtonState();
    }

    expireDate.addEventListener('input', updateButtonState);
    expireTime.addEventListener('input', updateButtonState);

    clearBtn.addEventListener('click', function() {
        expireDate.value = '';
        expireTime.value = '';
        updateButtonState();
    });
    if (setNextHourBtn) setNextHourBtn.addEventListener('click', function() { setExpiration(1); });
    if (setNextDayBtn) setNextDayBtn.addEventListener('click', function() { setExpiration(24); });
    if (setNextWeekBtn) setNextWeekBtn.addEventListener('click', function() { setExpiration(24 * 7); });
    if (setNextMonthBtn) setNextMonthBtn.addEventListener('click', function() { setExpiration(0, 1); });
    updateButtonState();
})();