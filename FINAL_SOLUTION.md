# Final Solution: YouTube Transcript API on Cloud Servers

## The Problem
- YouTube blocks requests from cloud server IPs (AWS, Google Cloud, Coolify, etc.)
- Client-side fetching doesn't work due to CORS restrictions
- Free solutions are not reliable

## The Solution: Webshare Proxy

### 1. Sign up for Webshare
1. Go to [Webshare](https://www.webshare.io/?referral_code=w0xno53eb50g)
2. Create an account
3. Purchase a "Residential" proxy package (NOT "Proxy Server" or "Static Residential")
   - Minimum package (~$7/month) should be sufficient for light usage

### 2. Get Your Proxy Credentials
1. Go to [Proxy Settings](https://dashboard.webshare.io/proxy/settings)
2. Find your:
   - **Proxy Username** (looks like: `username-rotate`)
   - **Proxy Password** (a generated string)

### 3. Configure Coolify Environment Variables
Add these to your Coolify service:
```
WEBSHARE_PROXY_USERNAME=your-proxy-username
WEBSHARE_PROXY_PASSWORD=your-proxy-password
PORT=8590
GEMINI_API_KEY=your-gemini-key (optional, for flashcards)
```

### 4. Deploy
Deploy the application with the updated files:
- `hermes_server.py` - Now includes proxy support
- `hermes.html` - Uses server-side fetching
- Other files remain unchanged

## How It Works
1. User enters YouTube URL
2. Frontend requests transcript from your server
3. Server uses Webshare proxy to fetch from YouTube
4. YouTube sees residential IP (not blocked)
5. Transcript returned to user

## Why This Approach
- **Client-side fetching is impossible** due to CORS (browsers block cross-origin requests to YouTube)
- **Direct server fetching fails** because YouTube blocks cloud IPs
- **Webshare provides rotating residential proxies** that YouTube won't block
- **Cost-effective** (~$7/month for basic usage)

## Testing
After deployment, test with any YouTube video:
```
http://your-coolify-domain:8590
```

Enter a YouTube URL and it should fetch transcripts successfully.

## Alternative Free Options (Not Recommended)
1. **Run locally** - Use residential internet, not cloud
2. **User-provided proxy** - Let users configure their own proxies
3. **Browser extension** - Bypass CORS with an extension

These are less reliable and require more user setup.

## Troubleshooting
If you still see errors:
1. Check proxy credentials are correct
2. Ensure environment variables are set in Coolify
3. Check server logs for specific error messages
4. Test proxy credentials directly with Webshare's test tools