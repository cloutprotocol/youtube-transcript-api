"""
Client-side YouTube transcript fetching solution
This avoids IP blocking by fetching transcripts from the user's browser
"""

from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# HTML template with embedded JavaScript for client-side fetching
CLIENT_SIDE_FETCHER = '''
<!DOCTYPE html>
<html>
<head>
    <title>YouTube Transcript Fetcher</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .error { color: red; }
        .success { color: green; }
        #transcript { background: #f4f4f4; padding: 15px; border-radius: 5px; margin-top: 20px; }
        .snippet { margin: 5px 0; padding: 5px; background: white; border-radius: 3px; }
        .timestamp { color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <h1>YouTube Transcript Fetcher</h1>
    <div id="app">
        <input type="text" id="videoUrl" placeholder="Enter YouTube URL" style="width: 400px; padding: 5px;">
        <button onclick="fetchTranscript()">Get Transcript</button>
        <div id="status"></div>
        <div id="transcript"></div>
    </div>

    <script>
        // Inject the client-side fetcher code here
        ''' + open('client_transcript_fetcher.js', 'r').read() + '''
        
        const fetcher = new YouTubeTranscriptFetcher();
        
        async function fetchTranscript() {
            const videoUrl = document.getElementById('videoUrl').value;
            const statusDiv = document.getElementById('status');
            const transcriptDiv = document.getElementById('transcript');
            
            statusDiv.innerHTML = '<p>Fetching transcript...</p>';
            transcriptDiv.innerHTML = '';
            
            const result = await fetcher.fetchTranscript(videoUrl);
            
            if (result.success) {
                statusDiv.innerHTML = '<p class="success">Transcript fetched successfully!</p>';
                
                // Display the transcript
                let html = `<h3>Transcript (${result.language})</h3>`;
                result.transcript.forEach(snippet => {
                    const time = formatTime(snippet.start);
                    html += `<div class="snippet">
                        <span class="timestamp">[${time}]</span> ${snippet.text}
                    </div>`;
                });
                transcriptDiv.innerHTML = html;
                
                // Send to server if needed
                sendToServer(result);
            } else {
                statusDiv.innerHTML = `<p class="error">Error: ${result.error}</p>`;
            }
        }
        
        function formatTime(seconds) {
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        }
        
        async function sendToServer(transcriptData) {
            // Send the transcript to your server for processing/storage
            try {
                const response = await fetch('/api/save-transcript', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(transcriptData)
                });
                const data = await response.json();
                console.log('Saved to server:', data);
            } catch (error) {
                console.error('Failed to save to server:', error);
            }
        }
    </script>
</body>
</html>
'''

# API endpoint for client-side fetching
@app.route('/api/client-fetch')
def client_fetch():
    """Serve the client-side fetching page"""
    return render_template_string(CLIENT_SIDE_FETCHER)

# API endpoint to receive transcripts from client
@app.route('/api/save-transcript', methods=['POST'])
def save_transcript():
    """Save transcript data sent from client"""
    data = request.json
    
    # Process the transcript data here
    # You can save to database, process it, etc.
    
    return jsonify({
        'status': 'success',
        'message': 'Transcript saved',
        'videoId': data.get('videoId')
    })

# Alternative: Pure API approach
@app.route('/api/get-fetcher-code')
def get_fetcher_code():
    """Return the JavaScript code for client-side fetching"""
    with open('client_transcript_fetcher.js', 'r') as f:
        code = f.read()
    
    return jsonify({
        'code': code,
        'usage': '''
            const fetcher = new YouTubeTranscriptFetcher();
            const result = await fetcher.fetchTranscript(videoUrl);
        '''
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)