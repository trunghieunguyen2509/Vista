const select = document.getElementById('currency-select');
const rateDisplay = document.getElementById('rate-display');
const amountInput = document.getElementById('amount-input');
const audEquivalent = document.getElementById('aud-equivalent');
const dropdownToggle = document.getElementById('dropdown-toggle');
const dropdownList = document.getElementById('dropdown-list');
const selectedFlag = document.getElementById('selected-flag');
const selectedLabel = document.getElementById('selected-label');

function updateRateDisplay() {
    const selectedOption = select.options[select.selectedIndex];
    const rate = parseFloat(selectedOption.dataset.rate);
    rateDisplay.textContent = `1 AUD = ${rate.toFixed(4)} ${select.value}`;
}

function updateAudEquivalent() {
    const selectedOption = select.options[select.selectedIndex];
    const rate = parseFloat(selectedOption.dataset.rate);
    const amount = parseFloat(amountInput.value);

    if (isNaN(amount) || amount < 0 || isNaN(rate) || rate <= 0) {
        audEquivalent.textContent = '≈ $0.00 AUD';
        return;
    }

    audEquivalent.textContent = `≈ $${(amount / rate).toFixed(2)} AUD`;
}

select.addEventListener('change', updateRateDisplay);
select.addEventListener('change', updateAudEquivalent);
amountInput.addEventListener('input', updateAudEquivalent);
updateRateDisplay();
updateAudEquivalent();

dropdownToggle.addEventListener('click', () => {
    const isOpen = !dropdownList.hidden;
    dropdownList.hidden = isOpen;
    dropdownToggle.setAttribute('aria-expanded', String(!isOpen));
});

dropdownList.addEventListener('click', (e) => {
    const option = e.target.closest('.dropdown-option');
    if (!option) return;

    select.value = option.dataset.code;
    select.dispatchEvent(new Event('change'));

    selectedFlag.src = `https://flagcdn.com/w40/${option.dataset.flag}.png`;
    selectedLabel.textContent = `${option.dataset.code} - ${option.dataset.name}`;

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
    const amount = parseFloat(amountInput.value);
    if (isNaN(amount) || amount <= 0) return;

    const snapped = snapToDenomination(amount, getDenominations());
    amountInput.value = snapped.toFixed(2);
    updateAudEquivalent();
}

amountInput.addEventListener('blur', applyDenominationSnap);
document.getElementById('reserve-add-form').addEventListener('submit', applyDenominationSnap);
