# YouTube Analytics System

A comprehensive analytics system for YouTube channels built with Python (FastAPI) backend and Next.js frontend.

## Features

- **Multi-Channel Tracking**: Monitor multiple YouTube channels (your own and competitors)
- **Video Analytics**: Track views, likes, comments, and engagement metrics
- **Trending Detection**: Identify videos with rapid growth
- **Historical Data**: Store daily snapshots for trend analysis
- **Alert System**: Get notified when videos go viral or engagement drops
- **Multi-Key Support**: Distribute API requests across multiple YouTube API keys
- **Modern UI**: Clean, responsive interface with shadcn/ui components

## Architecture

### Backend (Python)
- **FastAPI**: Modern, fast web framework
- **SQLAlchemy/SQLModel**: ORM for database operations
- **YouTube Data API v3**: Public data access
- **APScheduler**: Background jobs for data refresh
- **Multi-key quota management**: Intelligent API key rotation

### Frontend (Next.js)
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **shadcn/ui**: High-quality UI components
- **Recharts**: Data visualization

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- YouTube Data API v3 keys ([Get them here](https://console.cloud.google.com/apis/credentials))

### Local Development

#### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Create `.env` file from example:
```bash
cp .env.example .env
```

4. Edit `.env` and add your YouTube API keys:
```env
YOUTUBE_API_KEYS=your_key_1,your_key_2,your_key_3
DATABASE_URL=sqlite:///./youtube_analytics.db
CORS_ORIGINS=http://localhost:3000
```

5. Run the backend:
```bash
python -m backend.main
```

The API will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

#### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env.local`:
```bash
cp .env.example .env.local
```

4. Edit `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

5. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Deployment

### Backend Deployment (Render.com)

1. **Create a new Web Service** on [Render.com](https://render.com)

2. **Connect your GitHub repository**

3. **Configure the service**:
   - **Name**: `youtube-analytics-api`
   - **Environment**: `Python 3`
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Add Environment Variables**:
   ```
   YOUTUBE_API_KEYS=your_key_1,your_key_2
   DATABASE_URL=sqlite:////opt/render/project/data/youtube_analytics.db
   CORS_ORIGINS=https://yourusername.github.io
   ```

5. **Add a Persistent Disk** (for SQLite database):
   - Mount path: `/opt/render/project/data`
   - Size: 1GB minimum

6. **Deploy**

Your API will be available at `https://youtube-analytics-api.onrender.com`

#### Alternative: Docker Deployment

The backend includes a `Dockerfile` for containerized deployment:

```bash
cd backend
docker build -t youtube-analytics-api .
docker run -p 8000:8000 -v $(pwd)/data:/app/data \
  -e YOUTUBE_API_KEYS=your_keys \
  youtube-analytics-api
```

Deploy the Docker container to any platform (Railway, Fly.io, AWS ECS, etc.)

### Frontend Deployment (GitHub Pages)

The project includes automatic deployment via GitHub Actions.

#### Setup GitHub Pages

1. **Enable GitHub Pages** in your repository:
   - Go to Settings → Pages
   - Source: "GitHub Actions"

2. **Add Backend URL Secret**:
   - Go to Settings → Secrets and variables → Actions
   - Add a new secret:
     - Name: `NEXT_PUBLIC_API_URL`
     - Value: `https://your-backend-url.onrender.com/api/v1`

3. **Push to main branch**:
```bash
git add .
git commit -m "Deploy to GitHub Pages"
git push origin main
```

4. The GitHub Action will automatically:
   - Build the Next.js app
   - Export static files
   - Deploy to GitHub Pages

Your frontend will be available at `https://yourusername.github.io/repositoryname`

## Usage

### Adding a Channel

1. Navigate to the "Channels" page
2. Click "Add Channel"
3. Paste any YouTube channel URL or video URL
4. Click "Import"

The system will:
- Fetch channel information
- Import recent videos (up to 50 by default)
- Create initial statistics snapshots
- Start tracking the channel

### Viewing Analytics

- **Dashboard**: Overview of all tracked channels
- **Channels**: List of all channels with details
- **Channel Details**: Click on a channel to see all videos and metrics
- **Trending**: Videos with highest growth in last 24 hours
- **Alerts**: Notifications for important events

## API Endpoints

### Channels
- `POST /api/v1/channels` - Import a channel
- `GET /api/v1/channels` - List all channels
- `GET /api/v1/channels/{id}` - Get channel details
- `POST /api/v1/channels/{id}/refresh` - Refresh channel data
- `DELETE /api/v1/channels/{id}` - Delete channel

### Videos
- `GET /api/v1/channels/{id}/videos` - List channel videos
- `GET /api/v1/videos/{id}` - Get video details
- `GET /api/v1/videos/{id}/history` - Get historical stats

### Analytics
- `GET /api/v1/channels/{id}/analytics` - Get channel analytics
- `GET /api/v1/trending/videos` - Get trending videos

### Alerts
- `POST /api/v1/alerts` - Create alert
- `GET /api/v1/alerts` - List alerts
- `GET /api/v1/alert-events` - List alert events

## YouTube API Quotas

The YouTube Data API v3 has a default quota of 10,000 units per day per key.

Common operation costs:
- List videos: 1 unit
- List channels: 1 unit
- Search: 100 units

The system implements:
- **Multi-key rotation**: Distribute requests across multiple keys
- **Quota tracking**: Monitor usage per key
- **Automatic failover**: Switch keys when quota is exceeded
- **Background updates**: Scheduled refresh to minimize API calls

## Project Structure

```
.
├── backend/                    # Python FastAPI backend
│   ├── api/                   # API routes and schemas
│   ├── api_key_manager/       # YouTube API key management
│   ├── data_ingestion/        # YouTube data fetching
│   ├── storage/               # Database models
│   ├── analytics/             # Analytics calculations
│   ├── alerts/                # Alert system
│   ├── future_ai/             # AI integration stubs
│   ├── main.py                # FastAPI application
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile             # Docker configuration
│
├── frontend/                   # Next.js frontend
│   ├── app/                   # Next.js pages (App Router)
│   ├── components/            # React components
│   ├── lib/                   # Utilities and API client
│   ├── public/                # Static assets
│   └── package.json           # Node dependencies
│
└── .github/workflows/         # GitHub Actions
    └── deploy-frontend.yml    # Frontend deployment
```

## Future Enhancements

The system includes stubs for future AI/LLM integration in `backend/future_ai/`:

- **Comment Analysis**: Sentiment analysis and topic extraction
- **Content Ideas**: AI-generated video topic suggestions
- **Script Generation**: Automated script writing
- **Auto-publishing**: Scheduled video uploads (requires OAuth)

## Troubleshooting

### Backend Issues

**Database locked error**:
- Stop all running instances
- Delete `youtube_analytics.db-journal` if it exists

**API key errors**:
- Verify keys in `.env`
- Check quota usage in Google Cloud Console
- Add more keys if needed

### Frontend Issues

**API connection errors**:
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Verify backend is running
- Check CORS settings in backend

**Build errors**:
- Delete `node_modules` and `.next`
- Run `npm install` again
- Check Node.js version (18+ required)

## License

MIT License - see LICENSE file for details