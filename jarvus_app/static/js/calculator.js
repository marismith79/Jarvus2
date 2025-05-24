const DEGREE_WEIGHTS = {
    'PhD/PsyD': 1.43046357616,
    'LCSW/LMSW': 1,
    'LPC': 0.97350993377,
    'LMFT': 1.09933774834,
    'LMHC': 0.96688741721
};

const INSURANCE_WEIGHTS = {
    'BCBS': 0.94,               // 108 / 115
    'Aetna': 1.00,              // 115 / 115
    'Cigna': 0.79,              //  91 / 115
    'UnitedHealthcare': 0.92,   // 106 / 115
    'Humana': 0.83,             //  96 / 115
    'Kaiser': 0.89,             // 102 / 115
    'Anthem': 0.88,             // 101 / 115
    'Medicaid': 0.90,           // 103 / 115
    'Medicare': 0.82            //  94 / 115
};

const SERVICE_WEIGHTS = {
    'SimplePractice': 0.03,
    'Ensora Health': 0.03,
    'Sessions Health': 0.03,
    'Tebra': 0.03,
    'SonderMind': 0.03,
    'Private Biller': 0.08
};

const STATE_FACTOR = {
    'AL': 0.88,'AK': 1.02,'AZ': 1.00,'AR': 0.87,'CA': 1.12,
    'CO': 1.16,'CT': 1.06,'DE': 0.98,'FL': 0.88,'GA': 0.96,
    'HI': 1.11,'ID': 0.92,'IL': 1.01,'IN': 0.92,'IA': 0.98,
    'KS': 0.90,'KY': 0.89,'LA': 0.91,'ME': 1.01,'MD': 1.05,
    'MA': 1.00,'MI': 0.93,'MN': 0.98,'MS': 0.87,'MO': 0.91,
    'MT': 0.90,'NE': 0.90,'NV': 0.96,'NH': 1.08,'NJ': 1.09,
    'NM': 0.91,'NY': 1.11,'NC': 0.93,'ND': 0.89,'OH': 0.91,
    'OK': 0.89,'OR': 1.07,'PA': 0.94,'RI': 1.05,'SC': 0.94,
    'SD': 0.88,'TN': 0.92,'TX': 0.90,'UT': 0.94,'VT': 1.01,
    'VA': 0.95,'WA': 1.02,'WV': 0.89,'WI': 0.92,'WY': 0.92,
};

function calculateSavings() {
    const degree = document.getElementById('degree').value;
    const clientsPerWeek = parseInt(document.getElementById('clientsPerWeek').value);
    const sessionRate = parseFloat(document.getElementById('sessionRate').value);
    const state = document.getElementById('state').value;
    const paymentType = document.getElementById('paymentType').value;
    const insurance = document.getElementById('insurance').value;
    const service = document.getElementById('service').value;

    // Calculate base savings
    let savings = sessionRate;

    // Apply degree weight
    savings *= DEGREE_WEIGHTS[degree];

    // Apply client volume factor
    savings *= (clientsPerWeek * 52);

    // Apply payment type factor
    if (paymentType === 'insurance') {
        savings *= 0.65; // Insurance reimbursement factor
        savings *= INSURANCE_WEIGHTS[insurance];
    } else {
        savings *= 1.0; // Out of network factor
    }

    // Apply service weight
    savings *= SERVICE_WEIGHTS[service];

    // Apply state factor
    savings *= STATE_FACTOR[state];

    // Subtract from the cost of Jarvus
    savings -= 10*52;

    // Update the display
    const savingsDisplay = document.getElementById('savingsDisplay');
    savingsDisplay.textContent = `$${Math.round(savings).toLocaleString()} per year`;
}

// Initialize the calculator
document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners to all form inputs
    const inputs = document.querySelectorAll('#calculatorForm input, #calculatorForm select');
    inputs.forEach(input => {
        input.addEventListener('change', calculateSavings);
        input.addEventListener('input', calculateSavings);
    });

    // Add specific listener for range input to update the display value
    const rangeInput = document.getElementById('clientsPerWeek');
    const rangeValue = document.getElementById('clientsPerWeekValue');
    rangeInput.addEventListener('input', function() {
        rangeValue.textContent = this.value;
    });

    // Add listener for payment type to show/hide insurance field
    const paymentType = document.getElementById('paymentType');
    const insuranceGroup = document.getElementById('insuranceGroup');
    
    function toggleInsuranceField() {
        if (paymentType.value === 'outOfNetwork') {
            insuranceGroup.style.display = 'none';
            document.getElementById('insurance').required = false;
        } else {
            insuranceGroup.style.display = 'flex';
            document.getElementById('insurance').required = true;
        }
    }

    paymentType.addEventListener('change', function() {
        toggleInsuranceField();
        calculateSavings();
    });

    // Initial setup
    toggleInsuranceField();
    calculateSavings();
}); 