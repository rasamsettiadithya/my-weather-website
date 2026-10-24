// Frontend sends the checked city names as JSON. The backend compares only those cities.

const button = document.querySelector("#check-weather");
const status = document.querySelector("#status");
const requestJson = document.querySelector("#request-json");
const responseJson = document.querySelector("#response-json");
const callTableBody = document.querySelector("#call-table tbody");
const cards = document.querySelectorAll(".city-card");
const cityInputs = document.querySelectorAll("input[name='city']");
const onLocalhost = location.hostname === "127.0.0.1" || location.hostname === "localhost";
const backendUrl = onLocalhost ? "http://127.0.0.1:8001/weather" : "/weather";

button.addEventListener("click", showWeather);
for (const input of cityInputs) {
    input.addEventListener("change", showRequest);
}
showRequest();

function selectedCities() {
    return Array.from(cityInputs)
        .filter(function (input) { return input.checked; })
        .map(function (input) { return input.value; });
}

function requestPayload() {
    return { cities: selectedCities() };
}

function showRequest() {
    requestJson.textContent = JSON.stringify(requestPayload(), null, 2);
    renderCallTable(null);
}

function cellText(text) {
    const cell = document.createElement("td");
    cell.textContent = text;
    return cell;
}

function cellJson(value) {
    const cell = document.createElement("td");
    const block = document.createElement("pre");
    block.textContent = typeof value === "string" ? value : JSON.stringify(value, null, 2);
    cell.appendChild(block);
    return cell;
}

function addRow(call, protocol, method, request, response) {
    const row = document.createElement("tr");
    row.appendChild(cellText(call));
    row.appendChild(cellText(protocol));
    row.appendChild(cellText(method));
    row.appendChild(cellJson(request));
    row.appendChild(cellJson(response));
    callTableBody.appendChild(row);
}

function renderCallTable(data) {
    const payload = requestPayload();
    callTableBody.replaceChildren();
    addRow(
        "Frontend calling backend",
        "HTTP",
        "POST",
        payload,
        data ? {
            requested: data.requested,
            cities: data.cities,
            result: data.result
        } : "Not sent yet"
    );

    const upstream = data && data.openMeteo ? data.openMeteo : [];
    if (!upstream.length) {
        addRow("Backend calling Open-Meteo", "HTTPS", "GET", "Sent after you check the weather", "Not sent yet");
        return;
    }
    for (const call of upstream) {
        addRow(call.call, call.protocol, call.method, call.request, call.response);
    }
}

async function showWeather() {
    const payload = requestPayload();

    button.disabled = true;
    status.textContent = "";
    status.classList.remove("is-result");
    showRequest();
    responseJson.textContent = "Waiting for the backend...";

    try {
        const response = await fetch(backendUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        responseJson.textContent = JSON.stringify(data, null, 2);
        if (response.ok) {
            renderCallTable(data);
        }
        if (!response.ok) {
            throw new Error(data.error || "Weather request failed");
        }

        const returned = {};
        for (const city of data.cities) {
            returned[city.id] = city.temperature;
        }

        for (const card of cards) {
            const temperature = returned[card.id];
            const slot = card.querySelector(".weather-slot");
            if (temperature === undefined) {
                card.classList.add("is-hidden");
                slot.innerHTML = "<p class=\"placeholder\">Weather shows here after you check.</p>";
                continue;
            }
            card.classList.remove("is-hidden");
            slot.innerHTML = ""
                + "<p class=\"temperature\">" + temperature + "°</p>"
                + "<p class=\"condition\">Current temperature</p>";
        }

        status.textContent = data.result;
        status.classList.add("is-result");
        document.querySelector(".call-preview").scrollIntoView({ behavior: "smooth", block: "nearest" });
    } catch (error) {
        status.textContent = error.message || "Weather could not be loaded. Check your connection and try again.";
    } finally {
        button.disabled = false;
    }
}
