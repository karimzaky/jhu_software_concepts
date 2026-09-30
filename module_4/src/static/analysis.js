"use strict";

const buttons = [
    document.querySelector('[data-testid="pull-data-btn"]'),
    document.querySelector('[data-testid="update-analysis-btn"]'),
];

const message = document.createElement("p");
message.setAttribute("role", "status");
message.setAttribute("aria-live", "polite");
document.querySelector(".header-actions").appendChild(message);

for (const button of buttons) {
    button.form.addEventListener("submit", async (event) => {
        event.preventDefault();

        const previousStates = buttons.map((item) => item.disabled);
        buttons.forEach((item) => { item.disabled = true; });
        message.textContent = "Processing request…";

        try {
            const response = await fetch(button.form.action, {
                method: "POST",
                headers: { "Accept": "application/json" },
            });
            const data = await response.json();

            if (response.status === 409 && data.busy) {
                message.textContent =
                    "A data pull is running. Please wait before trying again.";
            } else if (!response.ok || !data.ok) {
                message.textContent =
                    "The request failed. Check the application log for details.";
            } else {
                window.location.assign("/analysis");
            }
        } catch (error) {
            message.textContent =
                "Unable to reach the application. Please try again.";
        } finally {
            buttons.forEach((item, index) => {
                item.disabled = previousStates[index];
            });
        }
    });
}
