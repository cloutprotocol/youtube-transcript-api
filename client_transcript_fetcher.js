// Client-side YouTube transcript fetcher
// This runs in the user's browser, using their IP address

class YouTubeTranscriptFetcher {
    constructor() {
        this.baseUrl = 'https://www.youtube.com';
    }

    async getVideoId(url) {
        const regex = /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/;
        const match = url.match(regex);
        return match ? match[1] : null;
    }

    async fetchTranscript(videoUrl) {
        try {
            const videoId = await this.getVideoId(videoUrl);
            if (!videoId) {
                throw new Error('Invalid YouTube URL');
            }

            // First, get the video page to extract initial data
            const videoPageUrl = `${this.baseUrl}/watch?v=${videoId}`;
            const response = await fetch(videoPageUrl);
            const html = await response.text();

            // Extract the initial player response
            const ytInitialPlayerResponse = this.extractYtInitialPlayerResponse(html);
            if (!ytInitialPlayerResponse) {
                throw new Error('Could not extract player response');
            }

            // Get caption tracks
            const captionTracks = this.getCaptionTracks(ytInitialPlayerResponse);
            if (!captionTracks || captionTracks.length === 0) {
                throw new Error('No captions available for this video');
            }

            // Get the first available caption track (usually English)
            const captionTrack = captionTracks.find(track => 
                track.languageCode === 'en' || track.languageCode === 'en-US'
            ) || captionTracks[0];

            // Fetch the actual transcript
            const transcriptResponse = await fetch(captionTrack.baseUrl);
            const transcriptXml = await transcriptResponse.text();
            
            // Parse the transcript
            const transcript = this.parseTranscript(transcriptXml);
            
            return {
                success: true,
                videoId: videoId,
                language: captionTrack.name.simpleText,
                languageCode: captionTrack.languageCode,
                transcript: transcript
            };
            
        } catch (error) {
            return {
                success: false,
                error: error.message
            };
        }
    }

    extractYtInitialPlayerResponse(html) {
        const regex = /var ytInitialPlayerResponse = ({.+?});/;
        const match = html.match(regex);
        if (match) {
            try {
                return JSON.parse(match[1]);
            } catch (e) {
                console.error('Failed to parse ytInitialPlayerResponse');
            }
        }
        return null;
    }

    getCaptionTracks(playerResponse) {
        try {
            return playerResponse?.captions?.playerCaptionsTracklistRenderer?.captionTracks || [];
        } catch (e) {
            return [];
        }
    }

    parseTranscript(xml) {
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(xml, 'text/xml');
        const textElements = xmlDoc.getElementsByTagName('text');
        
        const transcript = [];
        for (let i = 0; i < textElements.length; i++) {
            const element = textElements[i];
            const text = element.textContent
                .replace(/&amp;/g, '&')
                .replace(/&lt;/g, '<')
                .replace(/&gt;/g, '>')
                .replace(/&quot;/g, '"')
                .replace(/&#39;/g, "'");
            
            transcript.push({
                text: text,
                start: parseFloat(element.getAttribute('start')),
                duration: parseFloat(element.getAttribute('dur'))
            });
        }
        
        return transcript;
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = YouTubeTranscriptFetcher;
}