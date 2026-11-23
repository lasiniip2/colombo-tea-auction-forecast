const groups = JSON.parse(document.querySelector("#tea-groups").textContent);
const labels = JSON.parse(document.querySelector("#tea-options").textContent);
const fields = [...document.querySelectorAll("[data-tea-field]")];
const status = document.querySelector("#group-status");
const estimate = document.querySelector("#estimate-prices");

function updateGroup() {
  let matches = groups;
  let nextField;
  for (const field of fields) {
    const key = field.name;
    const allowed = nextField ? new Set() : new Set(matches.map(group => group[key]));
    const previous = field.value;
    const fixed = allowed.size === 1;
    const options = Object.keys(labels[key])
      .filter(value => allowed.has(value))
      .sort((a, b) => (a === "unknown") - (b === "unknown") || a.localeCompare(b));
    field.replaceChildren(...options.map(value => new Option(labels[key][value], value)));
    if (!fixed) field.prepend(new Option(field.dataset.placeholder, ""));
    field.value = fixed ? [...allowed][0] : allowed.has(previous) ? previous : "";
    const unreported = fixed && field.value === "unknown";
    field.disabled = !allowed.size;
    document.getElementById(`tea-field-${key}`).hidden = field.disabled || unreported;
    document.getElementById(`tea-hint-${key}`).hidden = !fixed || unreported;
    if (field.value) matches = matches.filter(group => group[key] === field.value);
    else if (!nextField) nextField = field;
  }
  estimate.disabled = Boolean(nextField) || matches.length !== 1;
  status.textContent = nextField ? `${nextField.dataset.placeholder} to continue.` : "Recorded quotation group matched.";
}

for (const field of fields) field.addEventListener("change", updateGroup);
updateGroup();
