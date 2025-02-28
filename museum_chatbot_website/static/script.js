let step = 0;
let booking = {};

function addMessage(sender, text) {
    const chatBox = document.getElementById('chat-box');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ' + (sender === 'You' ? 'user-message' : 'bot-message');
    messageDiv.textContent = `${sender}: ${text}`;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;

    // Check if the response includes a PDF download link
    if (sender === 'Bot' && text.includes("Click 'Download Ticket'")) {
        const pdfPathMatch = text.match(/ticket_[A-Z0-9]+\.pdf/);
        if (pdfPathMatch) {
            const pdfPath = pdfPathMatch[0];
            const downloadLink = document.createElement('a');
            downloadLink.href = `/download_ticket/${pdfPath}`;
            downloadLink.textContent = 'Download Ticket';
            downloadLink.className = 'download-link';
            downloadLink.download = pdfPath;  // Ensure the file is downloaded with the correct name
            messageDiv.appendChild(document.createElement('br'));
            messageDiv.appendChild(downloadLink);
        }
    }
}

function sendMessage() {
    const input = document.getElementById('user-input');
    const message = input.value.trim();
    if (!message) return;

    addMessage('You', message);
    input.value = '';

    fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message, step: step, booking: booking })
    })
    .then(response => response.json())
    .then(data => {
        addMessage('Bot', data.response);
        step = data.step;
        booking = data.booking || {};
        if (data.pdf_path) {
            // Optionally trigger download programmatically (uncomment if needed)
            // const downloadUrl = `/download_ticket/${data.pdf_path}`;
            // window.location.href = downloadUrl;
        }
    })
    .catch(error => console.error('Error:', error));
}

// Send message on Enter key
document.getElementById('user-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

// Add CSS for the download link
const style = document.createElement('style');
style.textContent = `
    .download-link {
        color: #007bff;
        text-decoration: underline;
        cursor: pointer;
    }
    .download-link:hover {
        color: #0056b3;
    }
`;
document.head.appendChild(style);

// Initial message
fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: '', step: 0 })
})
.then(response => response.json())
.then(data => addMessage('Bot', data.response))
.catch(error => console.error('Error:', error));