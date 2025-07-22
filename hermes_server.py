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

class TranscriptHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse the URL
        parsed_path = urlparse(self.path)
        
        # Serve the HTML file
        if parsed_path.path == '/' or parsed_path.path == '/hermes.html':
            self.serve_html()
        # Handle API requests
        elif parsed_path.path.startswith('/api/transcript/'):
            video_id = parsed_path.path.split('/')[-1]
            self.serve_transcript(video_id)
        else:
            self.send_error(404, "File not found")
    
    def serve_html(self):
        try:
            with open('hermes.html', 'rb') as file:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(file.read())
        except FileNotFoundError:
            self.send_error(404, "hermes.html not found")
    
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

def run_server(port=8888):
    server_address = ('', port)
    httpd = HTTPServer(server_address, TranscriptHandler)
    print(f"🚀 Hermes server running on http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
        httpd.server_close()

if __name__ == '__main__':
    run_server()