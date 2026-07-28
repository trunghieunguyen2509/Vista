// 1. Get DOM Elements
const audInput = document.getElementById('aud-input');
const foreignInput = document.getElementById('foreign-input');
const select = document.getElementById('currency-select');
const rateDisplay = document.getElementById('rate-display');

// 2. Helper Functions
function getRate() {
    const selectedOption = select.options[select.selectedIndex];
    return parseFloat(selectedOption.dataset.rate);
}

function updateRateDisplay() {
    const rate = getRate();
    const code = select.value;
    rateDisplay.textContent = `1 AUD = ${rate.toFixed(4)} ${code}`;
}

// 3. Event Listeners (with NaN protection)
audInput.addEventListener('input', () => {
    const rate = getRate();
    const audVal = parseFloat(audInput.value);


    // Check if the input is empty or invalid
    if (isNaN(audVal || audVal < 0)) {
        foreignInput.value = ''; // Clear the other box
    } else {
        foreignInput.value = (audVal * rate).toFixed(2);
    }
});

foreignInput.addEventListener('input', () => {
    const rate = getRate();
    const foreignVal = parseFloat(foreignInput.value); // Parse the foreign box

    // Check if the input is empty or invalid
    if (isNaN(foreignVal)) {
        audInput.value = ''; // Clear the AUD box
    } else {
        // Reverse calculation using division
        audInput.value = (foreignVal / rate).toFixed(2);
    }
    // 💡 Try applying the same isNaN() pattern here for foreignInput!
});

select.addEventListener('change', () => {
    updateRateDisplay();
    if (audInput.value) {
        audInput.dispatchEvent(new Event('input'));
    }
});

// 4. Run on load
updateRateDisplay();
