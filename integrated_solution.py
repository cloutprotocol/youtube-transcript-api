"""
Integrated solution for existing YouTube transcript application
This modifies your existing server code to use client-side fetching
"""

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
import os

class HybridTranscriptFetcher:
    """
    Hybrid approach: Try server-side first, fallback to client-side
    """
    
    def __init__(self):
        # Try to use proxy if credentials are available
        proxy_username = os.environ.get('WEBSHARE_PROXY_USERNAME')
        proxy_password = os.environ.get('WEBSHARE_PROXY_PASSWORD')
        
        if proxy_username and proxy_password:
            self.api = YouTubeTranscriptApi(
                proxy_config=WebshareProxyConfig(
                    proxy_username=proxy_username,
                    proxy_password=proxy_password,
                )
            )
        else:
            self.api = YouTubeTranscriptApi()
    
    def fetch_transcript(self, video_id, languages=['en']):
        """
        Try to fetch transcript server-side first
        Returns dict with either transcript data or client-side fetch instruction
        """
        try:
            # Try server-side fetch
            transcript = self.api.fetch(video_id, languages=languages)
            return {
                'success': True,
                'method': 'server',
                'data': transcript.to_raw_data(),
                'language': transcript.language,
                'language_code': transcript.language_code,
                'is_generated': transcript.is_generated
            }
        except Exception as e:
            # If blocked, return client-side fetch instruction
            if 'blocked' in str(e).lower() or 'ip' in str(e).lower():
                return {
                    'success': False,
                    'method': 'client',
                    'error': str(e),
                    'instruction': 'fetch_client_side',
                    'video_id': video_id,
                    'fetcher_url': '/api/get-fetcher-code'
                }
            else:
                # Other errors
                return {
                    'success': False,
                    'method': 'server',
                    'error': str(e)
                }

# Example Flask/FastAPI endpoint
def transcript_endpoint(video_url: str):
    """
    Modified endpoint that handles both server and client fetching
    """
    fetcher = HybridTranscriptFetcher()
    
    # Extract video ID from URL
    import re
    match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', video_url)
    if not match:
        return {'error': 'Invalid YouTube URL'}
    
    video_id = match.group(1)
    result = fetcher.fetch_transcript(video_id)
    
    if result['success']:
        # Server-side fetch worked
        return result
    elif result.get('instruction') == 'fetch_client_side':
        # Need client-side fetch
        return {
            'require_client_fetch': True,
            'video_id': video_id,
            'fetcher_script': get_client_fetcher_script(),
            'message': 'Please use client-side fetching due to IP restrictions'
        }
    else:
        # Other error
        return result

def get_client_fetcher_script():
    """Return minified version of client fetcher"""
    return '''
    // Minified client fetcher
    class YTF{async gv(u){const r=/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/;
    const m=u.match(r);return m?m[1]:null}async ft(u){try{const v=await this.gv(u);
    if(!v)throw new Error('Invalid URL');const r=await fetch(`https://www.youtube.com/watch?v=${v}`);
    const h=await r.text();const p=h.match(/var ytInitialPlayerResponse = ({.+?});/);
    if(!p)throw new Error('No player response');const d=JSON.parse(p[1]);
    const t=d?.captions?.playerCaptionsTracklistRenderer?.captionTracks||[];
    if(!t.length)throw new Error('No captions');const c=t.find(x=>x.languageCode==='en')||t[0];
    const x=await fetch(c.baseUrl);const xml=await x.text();
    const parser=new DOMParser();const doc=parser.parseFromString(xml,'text/xml');
    const texts=doc.getElementsByTagName('text');const trans=[];
    for(let i=0;i<texts.length;i++){const e=texts[i];
    trans.push({text:e.textContent.replace(/&amp;/g,'&').replace(/&lt;/g,'<').replace(/&gt;/g,'>'),
    start:parseFloat(e.getAttribute('start')),duration:parseFloat(e.getAttribute('dur'))});}
    return{success:true,videoId:v,transcript:trans,language:c.name.simpleText};}
    catch(e){return{success:false,error:e.message};}}}
    '''

# React/Frontend integration example
REACT_COMPONENT = '''
import React, { useState } from 'react';

function TranscriptFetcher() {
    const [transcript, setTranscript] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchTranscript = async (videoUrl) => {
        setLoading(true);
        setError(null);
        
        try {
            // First try server-side
            const response = await fetch('/api/transcript', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ video_url: videoUrl })
            });
            
            const data = await response.json();
            
            if (data.require_client_fetch) {
                // Need to fetch client-side
                const fetcher = new Function(data.fetcher_script + '; return new YTF();')();
                const result = await fetcher.ft(videoUrl);
                
                if (result.success) {
                    setTranscript(result.transcript);
                    
                    // Send back to server for processing/storage
                    await fetch('/api/save-transcript', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(result)
                    });
                } else {
                    setError(result.error);
                }
            } else if (data.success) {
                // Server-side fetch worked
                setTranscript(data.data);
            } else {
                setError(data.error);
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            {/* Your UI here */}
        </div>
    );
}
'''