document.addEventListener("DOMContentLoaded", async function () {
    const bankSelect = document.getElementById("bank");

    try {
        const response = await fetch("/api/get-banks/");
        const data = await response.json();

        if (data.status) {
            // Clear existing options
            bankSelect.innerHTML = '<option value="">Select Bank</option>';

            // Populate dynamically
            data.banks.forEach(bank => {
                const option = document.createElement("option");
                option.value = bank.code;
                option.textContent = bank.name;
                bankSelect.appendChild(option);
            });
        } else {
            bankSelect.innerHTML = '<option value="">Error loading banks</option>';
        }
    } catch (err) {
        console.error("Error fetching banks:", err);
        bankSelect.innerHTML = '<option value="">Error loading banks</option>';
    }
});



document.addEventListener("DOMContentLoaded", function () {
    const bankSelect = document.getElementById("bank");
    const accountInput = document.getElementById("account_number");
    const accountNameDisplay = document.getElementById("account_name");

    async function verifyAccount() {
        const bankCode = bankSelect.value;
        const accountNumber = accountInput.value;

        // Only run when both are filled and account number is 10 digits
        if (bankCode && accountNumber.length === 10) {
            accountNameDisplay.textContent = "Verifying...";
            accountNameDisplay.classList.remove("text-danger");
            accountNameDisplay.classList.add("text-muted");

            try {
                const response = await fetch(`/api/verify-bank-account/?bank_code=${bankCode}&account_number=${accountNumber}`);
                const data = await response.json();

                if (data.status) {
                    accountNameDisplay.textContent = data.account_name;
                    accountNameDisplay.classList.remove("text-muted", "text-danger");
                    accountNameDisplay.classList.add("text-success");
                } else {
                    accountNameDisplay.textContent = "Invalid account details";
                    accountNameDisplay.classList.remove("text-muted", "text-success");
                    accountNameDisplay.classList.add("text-danger");
                }
            } catch (error) {
                accountNameDisplay.textContent = "Error verifying account";
                accountNameDisplay.classList.remove("text-muted", "text-success");
                accountNameDisplay.classList.add("text-danger");
            }
        }
    }

    accountInput.addEventListener("input", () => {
        if (accountInput.value.length === 10) verifyAccount();
    });

    bankSelect.addEventListener("change", () => {
        if (accountInput.value.length === 10) verifyAccount();
    });
});
