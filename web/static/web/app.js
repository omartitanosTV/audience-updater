// Show only the schedule fields that belong to the selected frequency.
function syncScheduleFields() {
    const frequencyField = document.getElementById("id_refresh_frequency");

    if (!frequencyField) {
        return;
    }

    const frequency = frequencyField.value;

    document.querySelectorAll("[data-schedule]").forEach((element) => {
        const supportedFrequencies = element.dataset.schedule.split(" ");
        element.hidden = !supportedFrequencies.includes(frequency);
    });
}

// Require confirmation for destructive forms such as audience deletion.
document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
        if (!window.confirm(form.dataset.confirm)) {
            event.preventDefault();
        }
    });
});

// Keep the active chip style in sync with its checkbox.
document.querySelectorAll("label.chip input[type='checkbox']").forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
        checkbox.closest("label.chip").classList.toggle("on", checkbox.checked);
    });
});

const refreshFrequencyField = document.getElementById("id_refresh_frequency");
if (refreshFrequencyField) {
    refreshFrequencyField.addEventListener("change", syncScheduleFields);
    syncScheduleFields();
}
