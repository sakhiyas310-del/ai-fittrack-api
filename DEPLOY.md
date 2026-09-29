# Putting AI FitTrack online (Render, free plan)

The app serves both the API and the web page, so one web service is enough.

## 1. Put the code on GitHub
1. Create a new empty repository on github.com.
2. Upload the project files (the folder that contains `run.py`, `app/`, `requirements.txt`, `Procfile`).
   Do **not** upload `.venv`, `fittrack.db` or `.env` (the included `.gitignore` already skips them if you use git).

## 2. Create the web service on Render
1. Sign up at render.com (you can use your GitHub account).
2. Click **New +**, then **Web Service**, and pick your GitHub repository.
3. Fill in:
   - **Runtime / Language:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn run:app --bind 0.0.0.0:$PORT`
   - **Instance type:** Free
4. Under **Environment Variables** add `SECRET_KEY` with a long random text (for example, mash the keyboard for 40 characters). Keep it private.
5. Click **Create Web Service** and wait for the build. You get a public link like `https://your-name.onrender.com`.

Button names on Render can look slightly different; the settings above are what matter.

## Things to know
- **Data may reset.** The free plan has no permanent disk, so the SQLite file can be wiped when the service restarts or redeploys. Fine for a demo; for real users you would need a paid disk or a hosted database.
- **The first visit can be slow** after the app has been idle (free services go to sleep).
- Set your own `SECRET_KEY`. Without it the app uses a public default, and anyone could forge login tokens.
- Optional: add `ANTHROPIC_API_KEY` as another environment variable to get real AI workout plans.
