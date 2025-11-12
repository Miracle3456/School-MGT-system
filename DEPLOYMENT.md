# Render Deployment Configuration

## Environment Variables Required on Render:

Set these in your Render dashboard under "Environment" tab:

```
SECRET_KEY=your-secret-key-here-generate-new-one
DEBUG=False
ALLOWED_HOSTS=your-app.onrender.com
DATABASE_URL=(automatically set by Render PostgreSQL)
PYTHON_VERSION=3.13.7
```

## Deployment Steps:

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Configure for Render deployment"
   git push origin main
   ```

2. **On Render Dashboard:**
   - Create New Web Service
   - Connect your GitHub repository
   - Configure:
     - **Build Command:** `./build.sh`
     - **Start Command:** `gunicorn school_system.wsgi:application`
     - **Environment Variables:** Add the variables listed above

3. **Create PostgreSQL Database:**
   - Create a new PostgreSQL database on Render
   - Copy the Internal Database URL
   - Add as `DATABASE_URL` environment variable to your web service

4. **After First Deploy:**
   - Open the Render Shell from dashboard
   - Run: `python manage.py createsuperuser`
   - Run: `python manage.py update_ids` (to format existing student/teacher IDs)

## Static Files:
- Whitenoise handles static files automatically
- CSS and assets are served from `/staticfiles/`

## Database:
- Uses PostgreSQL in production (Render managed)
- Uses SQLite locally for development

## Important Notes:
- Never commit `.env` or database credentials
- Keep `DEBUG=False` in production
- Generate a new SECRET_KEY for production
- Database migrations run automatically on each deploy via `build.sh`
