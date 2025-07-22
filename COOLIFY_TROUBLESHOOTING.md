# Coolify Deployment Troubleshooting

## Common Issues

### 1. "Cannot connect to server" Error

If you see this error when trying to fetch transcripts, check:

#### A. Server Port Configuration
- Coolify should expose port 8590 (or whatever PORT env var you set)
- Check your Coolify service configuration for exposed ports
- The Dockerfile already has `EXPOSE 8590`

#### B. Environment Variables
- Ensure PORT is set correctly (default: 8590)
- Check if GEMINI_API_KEY is set (optional, only for flashcards)

#### C. Test Server Connectivity
1. Open your browser's developer console (F12)
2. Go to Network tab
3. Try accessing: `https://your-coolify-domain/api/health`
4. You should see a JSON response with `{"status": "ok"}`

### 2. HTTPS/SSL Issues

If your Coolify deployment uses HTTPS (recommended):
- All API calls should work automatically with relative paths
- If you see "Mixed Content" errors, ensure all resources use HTTPS

### 3. CORS Issues

The server already includes CORS headers (`Access-Control-Allow-Origin: *`), but if you still have issues:
- Check browser console for CORS errors
- Ensure Coolify isn't adding conflicting headers

## Quick Debug Steps

1. **Check if server is running:**
   ```bash
   curl https://your-coolify-domain/api/health
   ```

2. **Check browser console:**
   - Press F12 → Console tab
   - Look for specific error messages
   - Check Network tab for failed requests

3. **Verify files are served:**
   - Can you access the main page?
   - Try: `https://your-coolify-domain/hermes.html`

4. **Test the client fetcher:**
   ```bash
   curl https://your-coolify-domain/api/client-fetcher.js
   ```

## Coolify-Specific Settings

Make sure in your Coolify service configuration:

1. **Port Mapping:**
   - Container Port: 8590
   - Or use PORT environment variable

2. **Health Check:**
   - Path: `/api/health`
   - Expected Response: 200 OK

3. **Environment Variables:**
   ```
   PORT=8590
   GEMINI_API_KEY=your-key-here (optional)
   ```

## Still Having Issues?

1. Check Coolify logs for the container
2. SSH into the container and check if the process is running
3. Verify the start.sh script has execute permissions
4. Check if all files were copied correctly during build