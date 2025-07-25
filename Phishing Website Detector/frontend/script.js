async function checkPhishing() {
    const url = document.getElementById('urlInput').value;
    // You need to extract features from the URL here
    const features = extractFeatures(url); // Implement this function

    const response = await fetch('http://localhost:5000/predict', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({features})
    });
    const data = await response.json();
    document.getElementById('result').innerText =
        data.prediction ? "Phishing Website!" : "Legitimate Website.";
}

// Dummy feature extraction (replace with real logic)
function extractFeatures(url) {
    // Example: [length of url, count of dots, ...]
    return [url.length, (url.match(/\./g) || []).length];
} 