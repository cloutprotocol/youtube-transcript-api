#!/usr/bin/env python3
"""
Simple HTTP server for Hermes YouTube Transcript Viewer
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import urllib.request
import re
import os
from datetime import datetime

# Load environment variables from .env file
from pathlib import Path
import sys

# Try to load dotenv if available
try:
    from dotenv import load_dotenv
    env_path = Path('.') / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

# Initialize Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
model = None

# Only import google.generativeai if API key is available
if GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        print(f"✅ Gemini API initialized successfully")
    except ImportError:
        print("⚠️  google-generativeai package not installed. Install with: pip install google-generativeai")
        GEMINI_API_KEY = None
else:
    print("⚠️  GEMINI_API_KEY not found in environment variables")

class TranscriptHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse the URL
        parsed_path = urlparse(self.path)
        
        # Serve the HTML files
        if parsed_path.path == '/' or parsed_path.path == '/hermes.html':
            self.serve_html('hermes.html')
        elif parsed_path.path == '/history.html':
            self.serve_html('history.html')
        # Handle API requests
        elif parsed_path.path.startswith('/api/transcript/'):
            video_id = parsed_path.path.split('/')[-1]
            self.serve_transcript(video_id)
        else:
            self.send_error(404, "File not found")
    
    def do_POST(self):
        # Parse the URL
        parsed_path = urlparse(self.path)
        
        # Handle flashcard generation
        if parsed_path.path == '/api/flashcards':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            self.generate_flashcards(json.loads(post_data))
        else:
            self.send_error(404, "Endpoint not found")
    
    def serve_html(self, filename):
        try:
            with open(filename, 'rb') as file:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.send_error(404, f"{filename} not found")
    
    def get_video_metadata(self, video_id):
        """Fetch video title and metadata from YouTube"""
        try:
            # Construct YouTube URL
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Fetch the page
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                html = response.read().decode('utf-8')
            
            # Extract title using regex
            title_match = re.search(r'<title>(.*?)</title>', html)
            title = title_match.group(1) if title_match else "YouTube Video"
            
            # Clean up the title (remove " - YouTube" suffix)
            if title.endswith(" - YouTube"):
                title = title[:-10]
            
            # Try to extract channel name
            channel_match = re.search(r'"author":"([^"]+)"', html)
            channel = channel_match.group(1) if channel_match else "Unknown Channel"
            
            return {
                'title': title,
                'channel': channel,
                'video_id': video_id
            }
        except Exception as e:
            return {
                'title': f"Video {video_id}",
                'channel': "Unknown Channel",
                'video_id': video_id
            }
    
    def serve_transcript(self, video_id):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            # Get video metadata
            metadata = self.get_video_metadata(video_id)
            
            # Create API instance and fetch transcript
            api = YouTubeTranscriptApi()
            fetched_transcript = api.fetch(video_id)
            
            # Format for easier display
            formatted_transcript = []
            for entry in fetched_transcript:
                formatted_transcript.append({
                    'start': entry.start,
                    'duration': entry.duration,
                    'text': entry.text
                })
            
            response = {
                'success': True,
                'video_id': video_id,
                'title': metadata['title'],
                'channel': metadata['channel'],
                'transcript': formatted_transcript
            }
            
        except TranscriptsDisabled:
            response = {
                'success': False,
                'error': 'Transcripts are disabled for this video'
            }
        except NoTranscriptFound:
            response = {
                'success': False,
                'error': 'No transcript found for this video'
            }
        except Exception as e:
            response = {
                'success': False,
                'error': str(e)
            }
        
        self.wfile.write(json.dumps(response).encode())
    
    def generate_flashcards(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if not GEMINI_API_KEY:
            response = {
                'success': False,
                'error': 'Gemini API key not configured. Set GEMINI_API_KEY environment variable.'
            }
            self.wfile.write(json.dumps(response).encode())
            return
        
        try:
            # Extract transcript data
            transcript_entries = data.get('transcript', [])
            video_title = data.get('title', 'Unknown Video')
            video_duration = data.get('duration', 0)
            
            # Calculate total duration from transcript
            if transcript_entries:
                last_entry = transcript_entries[-1]
                video_duration = last_entry['start'] + last_entry.get('duration', 0)
            
            # Determine number of flashcards based on duration
            num_flashcards = 20 if video_duration > 1500 else 10  # 25 minutes = 1500 seconds
            
            # Prepare transcript text with timestamps
            transcript_text = ""
            for entry in transcript_entries:
                timestamp = f"[{int(entry['start'])}s]"
                transcript_text += f"{timestamp} {entry['text']}\n"
            
            # Create prompt for Gemini
            prompt = f"""Analyze this YouTube video transcript titled "{video_title}" and create {num_flashcards} multiple-choice flashcards.

TRANSCRIPT:
{transcript_text}

INSTRUCTIONS:
1. First, identify the main topic, intent, and key themes of the video
2. Extract the most important and educational points that align with the video's purpose
3. Create {num_flashcards} multiple-choice questions that test understanding of these key points
4. Each flashcard should reference a specific quote and timestamp from the transcript
5. Include 4 answer choices (A, B, C, D) with only one correct answer
6. Make wrong answers plausible but clearly incorrect based on the transcript

Return the response as a JSON object with this EXACT structure:
{{
    "video_analysis": {{
        "main_topic": "Brief description of the video's main topic",
        "key_themes": ["theme1", "theme2", "theme3"],
        "video_intent": "What the video aims to teach or communicate"
    }},
    "flashcards": [
        {{
            "question": "The question text",
            "options": {{
                "A": "First option",
                "B": "Second option", 
                "C": "Third option",
                "D": "Fourth option"
            }},
            "correct_answer": "A",
            "explanation": "Why this answer is correct",
            "timestamp": 123,
            "related_quote": "The exact quote from the transcript this question is based on"
        }}
    ]
}}

Make sure to return ONLY valid JSON, no additional text or formatting."""
            
            # Generate flashcards using Gemini
            response = model.generate_content(prompt)
            
            # Parse the response
            try:
                flashcard_data = json.loads(response.text)
                flashcard_data['success'] = True
                flashcard_data['num_flashcards'] = num_flashcards
                flashcard_data['video_duration'] = video_duration
            except json.JSONDecodeError:
                # Try to extract JSON from the response
                import re
                json_match = re.search(r'\{[\s\S]*\}', response.text)
                if json_match:
                    flashcard_data = json.loads(json_match.group())
                    flashcard_data['success'] = True
                    flashcard_data['num_flashcards'] = num_flashcards
                    flashcard_data['video_duration'] = video_duration
                else:
                    raise ValueError("Could not parse Gemini response as JSON")
            
            self.wfile.write(json.dumps(flashcard_data).encode())
            
        except Exception as e:
            response = {
                'success': False,
                'error': f'Error generating flashcards: {str(e)}'
            }
            self.wfile.write(json.dumps(response).encode())

def run_server(port=8590):
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, TranscriptHandler)
    print(f"🚀 Hermes server running on http://0.0.0.0:{port}")
    print(f"   Local: http://localhost:{port}")
    print(f"   Network: http://<your-ip>:{port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        httpd.server_close()

if __name__ == '__main__':
    run_server()