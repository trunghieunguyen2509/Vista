const reserveSelect = document.getElementById('reserve-currency-select');
const reserveRateDisplay = document.getElementById('rate-display');

function updateReserveRate() {
    const selectedOption = reserveSelect.options[reserveSelect.selectedIndex];
    const rate = parseFloat(selectedOption.dataset.rate);
    reserveRateDisplay.textContent = `1 AUD = ${rate.toFixed(4)} ${reserveSelect.value}`;
}

reserveSelect.addEventListener('change', updateReserveRate);
updateReserveRate();
