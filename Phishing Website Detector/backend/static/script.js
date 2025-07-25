const API_KEY = 'mysecretkey123'; // Must match backend

const tips = [
    "Check for HTTPS and a valid certificate.",
    "Beware of URLs with lots of subdomains or numbers.",
    "Never click suspicious links in emails.",
    "Look for spelling mistakes in the URL.",
    "Legitimate sites rarely ask for sensitive info via popups.",
    "Hover over links to preview the real URL.",
    "Be cautious of urgent or threatening language."
];

let history = [];
let lastResult = null;

function setExampleUrl() {
    const dropdown = document.getElementById('exampleDropdown');
    const urlInput = document.getElementById('urlInput');
    urlInput.value = dropdown.value;
}

async function checkPhishing() {
    const url = document.getElementById('urlInput').value;
    if (!url) return;
    const resultDiv = document.getElementById('result');
    resultDiv.className = 'result-area';
    resultDiv.innerHTML = '<span class="spinner"></span> Checking...';
    const response = await fetch('/predict', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'x-api-key': API_KEY
        },
        body: JSON.stringify({url})
    });
    const data = await response.json();
    let verdict, summary, icon, areaClass;
    if (data.prediction) {
        verdict = "<span class='phishing'>Phishing Website!</span>";
        summary = "<span class='summary-phishing'>⚠️ Warning: This site is likely a phishing attempt!</span>";
        icon = "<span class='icon-phishing'>🚫</span>";
        areaClass = 'phishing-bg';
    } else {
        verdict = "<span class='legit'>Legitimate Website.</span>";
        summary = "<span class='summary-legit'>✅ This site is safe.</span>";
        icon = "<span class='icon-legit'>✔️</span>";
        areaClass = 'legit-bg';
    }
    const confidence = `Confidence: ${(data.confidence * 100).toFixed(1)}%`;
    const explanation = `Reason: ${data.explanation}`;
    resultDiv.className = `result-area ${areaClass}`;
    resultDiv.innerHTML = `${icon} ${verdict}<br>${summary}<br>${confidence}<br>${explanation}`;
    // Store last result for feedback (not used now)
    lastResult = {url, prediction: data.prediction};
    // Add to history
    history.unshift({url, verdict: data.prediction ? 'Phishing' : 'Legitimate', confidence: (data.confidence * 100).toFixed(1), explanation: data.explanation});
    if (history.length > 10) history.pop();
    renderHistory();
    // Show random tip
    document.getElementById('tip').innerText = tips[Math.floor(Math.random() * tips.length)];
}

function renderHistory() {
    const table = document.getElementById('history');
    if (!table) return;
    table.innerHTML = '<tr><th>URL</th><th>Result</th><th>Confidence</th><th>Reason</th></tr>' +
        history.map(h => `<tr><td>${h.url}</td><td>${h.verdict}</td><td>${h.confidence}%</td><td>${h.explanation}</td></tr>`).join('');
}

async function showHistoryModal() {
    const modal = document.getElementById('historyModal');
    modal.style.display = 'block';
    // Fetch full history from backend
    const response = await fetch('/history');
    const data = await response.json();
    // Render
    const table = document.getElementById('history');
    table.innerHTML = '<tr><th>Time</th><th>URL</th><th>Confidence</th><th>Reason</th></tr>' +
        data.map(h => `<tr><td>${h.timestamp}</td><td>${h.url}</td><td>${h.confidence}</td><td>${h.explanation}</td></tr>`).join('');
}

function closeHistoryModal() {
    const modal = document.getElementById('historyModal');
    modal.style.display = 'none';
}

// Close modal when clicking outside content
window.onclick = function(event) {
    const modal = document.getElementById('historyModal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
}

function resetAll() {
    document.getElementById('urlInput').value = '';
    document.getElementById('result').innerHTML = '';
    document.getElementById('result').className = 'result-area';
    document.getElementById('tip').innerText = '';
    document.getElementById('exampleDropdown').selectedIndex = 0;
}

// Dark mode toggle
function toggleDarkMode() {
    document.body.classList.toggle('dark');
} 