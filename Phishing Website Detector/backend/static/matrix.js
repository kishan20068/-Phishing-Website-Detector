// Matrix-style animated background (red lines on black)
const canvas = document.getElementById('matrix-canvas');
const ctx = canvas.getContext('2d');

// Set canvas to full screen
function resizeMatrix() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
resizeMatrix();
window.addEventListener('resize', resizeMatrix);

const fontSize = 20;
const columns = () => Math.floor(canvas.width / fontSize);
const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&';
let drops = [];

function initDrops() {
    drops = [];
    for (let x = 0; x < columns(); x++) {
        drops[x] = Math.random() * canvas.height / fontSize;
    }
}
initDrops();
window.addEventListener('resize', initDrops);

function drawMatrix() {
    ctx.fillStyle = 'rgba(10,10,10,0.6)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.font = fontSize + "px 'Consolas', 'Courier New', monospace";
    for (let i = 0; i < drops.length; i++) {
        const text = chars[Math.floor(Math.random() * chars.length)];
        ctx.fillStyle = '#ff1744';
        ctx.fillText(text, i * fontSize, drops[i] * fontSize);
        if (Math.random() > 0.975) {
            drops[i] = 0;
        }
        drops[i] += 1;
        if (drops[i] * fontSize > canvas.height) {
            drops[i] = 0;
        }
    }
}
setInterval(drawMatrix, 50); 