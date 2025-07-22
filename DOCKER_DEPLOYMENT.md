# Docker Deployment Guide for Hermes

## Quick Start

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd youtube-transcript-api
```

### 2. Set up environment variables
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Build and run with Docker Compose
```bash
docker-compose up -d
```

### 4. Access the application
Open your browser to: http://localhost:8888

## Deployment to Coolify

### Method 1: Using Docker Compose

1. In Coolify, create a new service
2. Select "Docker Compose" as the deployment method
3. Point to your repository
4. Coolify will automatically detect the `docker-compose.yml` file
5. Add your environment variable:
   - Key: `GEMINI_API_KEY`
   - Value: Your Gemini API key

### Method 2: Using Dockerfile

1. In Coolify, create a new service
2. Select "Dockerfile" as the deployment method
3. Point to your repository
4. Set the port to `8888`
5. Add your environment variable:
   - Key: `GEMINI_API_KEY`
   - Value: Your Gemini API key

## Environment Variables

- `GEMINI_API_KEY`: Required for flashcard generation. Get your key from [Google AI Studio](https://makersuite.google.com/app/apikey)

## Features

- YouTube transcript fetching
- AI-powered flashcard generation
- Local storage for saved videos
- History tracking
- Export functionality

## Notes

- The application stores data in the browser's localStorage
- Data is device and browser specific
- Use the backup feature to export your data

## Troubleshooting

### Container won't start
Check logs: `docker-compose logs hermes`

### Can't access the application
- Ensure port 8888 is not in use: `lsof -i :8888`
- Check if container is running: `docker ps`

### Flashcards not generating
- Verify GEMINI_API_KEY is set correctly
- Check logs for API errors