# AI FitTrack API

A beginner-friendly REST API backend for a fitness tracking app. Users can
create a profile, log workouts and meals, track their weight over time, and
generate a personalized weekly workout plan.

Built with **Python + Flask**, using Python's built-in `sqlite3` module for
storage — no database server to install, no ORM to learn. The whole app is
one small, readable codebase.

## Features

- **User profiles** — name, age, height, weight, fitness goal, experience level, workout days/week
- **Workout tracking** — log workouts and view full history
- **Consistency badges** — track weekly workout goals, completed-week streaks, and active-day milestones
- **Meal tracking** — log meals, view full history, and see today's calorie total
- **Water tracking** — log water servings in millilitres and view today's total
- **Goal-based food ideas** — show general meal ideas matched to the profile goal
- **Instruction-based daily meal plan** — generate five meal ideas from food preferences; uses the AI provider when configured
- **Progress tracking** — log weight over time, see a start/current/change summary, and calculate BMI
- **AI workout plan** — generates a personalized weekly plan; if no AI provider is configured (or the AI call fails), it automatically falls back to a clearly-labeled sample plan instead of erroring out
- Input validation, consistent JSON response shape, and clear error messages on every endpoint

## Project structure

```
ai-fittrack-api/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── db.py                # SQLite connection + schema (creates tables on startup)
│   ├── static/index.html    # web frontend (served at /)
│   ├── routes/
│   │   ├── health.py        # GET /api/health
│   │   ├── users.py         # user profile endpoints
│   │   ├── workouts.py      # workout tracking endpoints
│   │   ├── meals.py         # meal tracking endpoints
│   │   ├── water.py         # water-intake tracking endpoints
│   │   ├── progress.py      # weight logging + progress endpoints
│   │   └── workout_plan.py  # AI workout plan endpoint
│   └── utils/
│       ├── validation.py    # input validation helpers
│       ├── responses.py     # consistent success/error JSON helpers
│       └── workout_planner.py  # AI call + rule-based sample-plan fallback
├── Procfile                 # start command for hosting (gunicorn)
├── DEPLOY.md                # how to put the app online
├── run.py                   # start the app: python run.py
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

**Requirements:** Python 3.9+

1. **Clone / download the project, then move into it:**
   ```bash
   cd ai-fittrack-api
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **(Optional) Enable real AI-generated workout plans:**
   ```bash
   cp .env.example .env
   ```
   Then open `.env` and add your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your-key-here
   ```
   Then load it before running the server, e.g. `export $(cat .env | xargs)` on
   macOS/Linux, or use a tool like `python-dotenv` if you prefer. **This step
   is entirely optional** — without a key, the workout plan endpoint still
   works and returns a clearly-labeled sample plan.

5. **Run the server:**
   ```bash
   python run.py
   ```
   The API will be available at `http://localhost:5000`. The SQLite database
   file (`fittrack.db`) is created automatically on first run — no manual
   setup needed.

6. **Try it:**
   ```bash
   curl http://localhost:5000/api/health
   ```

## Web frontend

A simple web page is included and served by the same Flask server. After
`python run.py`, open **http://localhost:5000** in your browser. You can create
a profile, log workouts, meals and weight, view progress (with a chart), and
generate a weekly plan. The page lives in `app/static/index.html` (plain HTML,
CSS and JavaScript, no build step).

## Login (authentication)

Every `/api/users/{id}/...` endpoint needs a login token, and a user can only
open their own data (`401` if no token, `403` if the token belongs to someone else).

1. **Sign up** with `POST /api/users` (send `email` and `password`, 6+ characters, plus the profile fields).
2. **Log in** with `POST /api/auth/login` and body `{"email": "...", "password": "..."}`.
3. Both return `{"success": true, "data": {"user": {...}, "token": "..."}}`.
4. Send the token on every other request as the header `Authorization: Bearer <token>`.

Example (PowerShell):
```powershell
$login = Invoke-RestMethod -Method Post -Uri http://localhost:5000/api/auth/login -ContentType "application/json" -Body '{"email":"alex@example.com","password":"secret123"}'
Invoke-RestMethod -Uri http://localhost:5000/api/users/1/workouts -Headers @{Authorization = "Bearer " + $login.data.token}
```
Tokens last 7 days and are signed with the `SECRET_KEY` environment variable (see `.env.example`).
Accounts created before login existed have no email or password, so they cannot log in; sign up again.

## Response format

Every response is JSON with a `success` flag.

**Success:**
```json
{ "success": true, "data": { ... } }
```

**Error:**
```json
{ "success": false, "error": "A clear description of what went wrong." }
```

## API Reference

### Health check

`GET /api/health`

```json
{ "success": true, "data": { "status": "ok", "service": "AI FitTrack API" } }
```

---

### Create a user profile (sign up)

`POST /api/users`

Also send `email` and `password` (6+ characters). The response is `{"user": {...}, "token": "..."}`; the examples below show the profile fields only.

Request body:
```json
{
  "name": "Alex Rivera",
  "age": 28,
  "height_cm": 175,
  "weight_kg": 75,
  "fitness_goal": "build_muscle",
  "experience_level": "beginner",
  "workout_days_per_week": 4
}
```

- `fitness_goal`: one of `lose_weight`, `build_muscle`, `endurance`, `general_fitness`
- `experience_level`: one of `beginner`, `intermediate`, `advanced`
- `workout_days_per_week`: whole number, 1–7

Response `201`:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Alex Rivera",
    "age": 28,
    "height_cm": 175.0,
    "weight_kg": 75.0,
    "fitness_goal": "build_muscle",
    "experience_level": "beginner",
    "workout_days_per_week": 4,
    "created_at": "2026-09-27 10:29:05"
  }
}
```

Error example (`400`, missing/invalid fields):
```json
{ "success": false, "error": "Missing required field(s): age, height_cm." }
```

---

### Get a user profile

`GET /api/users/{id}`

Response `200`: same shape as the create response.
Response `404` if the user doesn't exist:
```json
{ "success": false, "error": "User with id 999 not found." }
```

---

### Log a workout

`POST /api/users/{id}/workouts`

Request body:
```json
{
  "exercise_name": "Bench Press",
  "duration_minutes": 45,
  "date": "2026-09-27",
  "notes": "Felt strong"
}
```
`notes` is optional. `date` must be `YYYY-MM-DD`.

Response `201`:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "user_id": 1,
    "exercise_name": "Bench Press",
    "duration_minutes": 45,
    "date": "2026-09-27",
    "notes": "Felt strong",
    "created_at": "2026-09-27 10:29:16"
  }
}
```

---

### Get workout history

`GET /api/users/{id}/workouts`

Response `200` — most recent first:
```json
{
  "success": true,
  "data": [
    { "id": 1, "user_id": 1, "exercise_name": "Bench Press", "duration_minutes": 45, "date": "2026-09-27", "notes": "Felt strong", "created_at": "..." },
    { "id": 2, "user_id": 1, "exercise_name": "Running", "duration_minutes": 30, "date": "2026-09-25", "notes": null, "created_at": "..." }
  ]
}
```

---

### Delete a workout

`DELETE /api/users/{id}/workouts/{workout_id}` returns `{"success": true, "data": {"deleted_id": 1}}`,
or `404` if that workout does not exist for this user.

---

### Log a meal

`POST /api/users/{id}/meals`

Request body:
```json
{
  "food_name": "Grilled chicken salad",
  "calories": 450,
  "date": "2026-09-27",
  "notes": "Lunch"
}
```

Response `201`: same shape as the request, plus `id`, `user_id`, `created_at`.

---

### Get meal history

`GET /api/users/{id}/meals`

Response `200` — most recent first, same list shape as workout history.

---

### Delete a meal

`DELETE /api/users/{id}/meals/{meal_id}` works the same way as deleting a workout.

---

### Log water

`POST /api/users/{id}/water`

Request body:
```json
{
  "amount_ml": 250,
  "date": "2026-09-29",
  "notes": "After breakfast"
}
```

Use `GET /api/users/{id}/water` to view water history or
`DELETE /api/users/{id}/water/{entry_id}` to remove an entry. The app shows
the amount logged today and does not prescribe a daily water target.

---

### Generate a full-day meal plan

`POST /api/users/{id}/meal-plan`

Request body:
```json
{
  "instructions": "South Indian vegetarian, no eggs; include idli and avoid peanuts."
}
```

The response includes breakfast, snacks, lunch, and dinner. With
`ANTHROPIC_API_KEY` configured, the plan follows the submitted instructions
using the AI provider. Without it, the app labels and returns a limited sample
plan; the fallback only recognizes common vegetarian/non-vegetarian and egg
preferences.

---

### Log a weight entry

`POST /api/users/{id}/weight`

Request body:
```json
{ "weight_kg": 73.5, "date": "2026-09-27" }
```

This also updates the user's current profile weight to this value.

Response `201`:
```json
{
  "success": true,
  "data": { "id": 2, "user_id": 1, "weight_kg": 73.5, "date": "2026-09-27", "created_at": "..." }
}
```

---

### Get progress

`GET /api/users/{id}/progress`

Response `200`:
```json
{
  "success": true,
  "data": {
    "history": [
      { "id": 1, "user_id": 1, "weight_kg": 75.0, "date": "2026-09-01", "created_at": "..." },
      { "id": 2, "user_id": 1, "weight_kg": 73.5, "date": "2026-09-27", "created_at": "..." }
    ],
    "summary": {
      "starting_weight_kg": 75.0,
      "current_weight_kg": 73.5,
      "change_kg": -1.5,
      "entries_logged": 2
    }
  }
}
```

---

### Generate a weekly workout plan

`POST /api/users/{id}/workout-plan`

No request body needed — the plan is built from the user's stored profile.

- If `ANTHROPIC_API_KEY` is set and the AI call succeeds, the plan is
  AI-generated (`"source": "ai"`).
- Otherwise — including if the AI call fails for any reason — a
  rule-based sample plan is returned instead (`"source": "sample"`), so
  this endpoint **never fails outright**.

Response `200` (no AI configured):
```json
{
  "success": true,
  "data": {
    "user_id": 1,
    "source": "sample",
    "is_ai_generated": false,
    "plan": {
      "days": [
        { "day": "Monday", "focus": "Push (Chest/Shoulders/Triceps)", "exercises": [
          { "name": "Push-ups", "sets": 3, "reps": "8-12" },
          { "name": "Shoulder Press", "sets": 3, "reps": "10-12" },
          { "name": "Tricep Dips", "sets": 3, "reps": "10-12" }
        ] },
        { "day": "Tuesday", "focus": "Pull (Back/Biceps)", "exercises": [ ... ] },
        { "day": "Wednesday", "focus": "Legs", "exercises": [ ... ] },
        { "day": "Thursday", "focus": "Push (Chest/Shoulders/Triceps)", "exercises": [ ... ] },
        { "day": "Friday", "focus": "Rest", "exercises": [] },
        { "day": "Saturday", "focus": "Rest", "exercises": [] },
        { "day": "Sunday", "focus": "Rest", "exercises": [] }
      ]
    }
  }
}
```

## Error handling

All validation errors return `400` with a message naming the exact problem.
Requests for a user that doesn't exist return `404`. Unknown routes return
`404`, wrong HTTP methods return `405`, and unexpected server errors return
`500` — all in the same `{"success": false, "error": "..."}` shape.

## Notes on design choices (why things are built this way)

- **Plain `sqlite3` instead of an ORM**: keeps every SQL query visible and
  readable, with zero extra dependencies to install — good for learning and
  for small projects.
- **Blueprints per resource**: each feature (users, workouts, meals,
  progress, workout plan) lives in its own file, so the codebase stays easy
  to navigate as it grows.
- **AI fallback by design, not as an afterthought**: `workout_planner.py`
  always returns a usable plan. It only ever tries the AI path if a key is
  configured, and any failure (missing key, network error, bad response)
  is caught and silently replaced with the sample plan.
