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
    if (isNaN(audVal) || audVal < 0) {
        foreignInput.value = ''; // Clear the other box
    } else {
        foreignInput.value = (audVal * rate).toFixed(2);
    }
});

foreignInput.addEventListener('input', () => {
    const rate = getRate();
    const foreignVal = parseFloat(foreignInput.value); // Parse the foreign box

    // Check if the input is empty or invalid
    if (isNaN(foreignVal) || foreignVal < 0) {
        audInput.value = ''; // Clear the AUD box
    } else {
        // Reverse calculation using division
        audInput.value = (foreignVal / rate).toFixed(2);
    }
    // 💡 Try applying the same isNaN() pattern here for foreignInput!
});


// 4. Run on load
updateRateDisplay();
select.addEventListener('change', updateRateDisplay);


// 5. Custom currency dropdown (flags)
const dropdownToggle = document.getElementById('dropdown-toggle');
const dropdownList = document.getElementById('dropdown-list');
const selectedFlag = document.getElementById('selected-flag');
const selectedLabel = document.getElementById('selected-label');

// 6. Snap the foreign amount to the nearest note denomination available,
// so customers can only request amounts we can actually hand over —
// otherwise we'd have to round up and effectively overcharge them.
function getDenominations() {
    const selectedOption = select.options[select.selectedIndex];
    try {
        return JSON.parse(selectedOption.dataset.denominations || '[]');
    } catch {
        return [];
    }
}

function snapToDenomination(amount, denominations) {
    if (!denominations.length || isNaN(amount) || amount <= 0) return amount;
    const unit = Math.min(...denominations);
    return Math.round(amount / unit) * unit;
}

function applyDenominationSnap() {
    const rate = getRate();
    const foreignVal = parseFloat(foreignInput.value);
    if (isNaN(foreignVal) || foreignVal <= 0) return;

    const snapped = snapToDenomination(foreignVal, getDenominations());
    foreignInput.value = snapped.toFixed(2);
    audInput.value = (snapped / rate).toFixed(2);
}

// Snap on blur (works whichever field the customer typed into, since
// foreignInput always holds the live-synced foreign amount by then)
foreignInput.addEventListener('blur', applyDenominationSnap);

// Safety net: re-snap right before the "Add to Cart" submit fires, in case
// the customer hits Enter without blurring the field first
document.getElementById('converter-form').addEventListener('submit', applyDenominationSnap);

dropdownToggle.addEventListener('click', () => {
    const isOpen = !dropdownList.hidden;
    dropdownList.hidden = isOpen;
    dropdownToggle.setAttribute('aria-expanded', String(!isOpen));
});

dropdownList.addEventListener('click', (e) => {
    const option = e.target.closest('.dropdown-option');
    if (!option) return;

    // Sync the hidden native select — this keeps all your existing
    // getRate()/updateRateDisplay() logic working unchanged
    select.value = option.dataset.code;
    select.dispatchEvent(new Event('change'));

    selectedFlag.src = `https://flagcdn.com/w40/${option.dataset.flag}.png`;
    selectedLabel.textContent = option.dataset.code;

    dropdownList.hidden = true;
    dropdownToggle.setAttribute('aria-expanded', 'false');
});

document.addEventListener('click', (e) => {
    if (!document.getElementById('currency-dropdown').contains(e.target)) {
        dropdownList.hidden = true;
        dropdownToggle.setAttribute('aria-expanded', 'false');
    }
});

dropdownToggle.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        dropdownList.hidden = true;
        dropdownToggle.setAttribute('aria-expanded', 'false');
    }
});
