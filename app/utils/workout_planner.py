"""
Workout plan generation.

If an AI provider (Anthropic's Claude API) is configured via the
ANTHROPIC_API_KEY environment variable, this module asks the model to
generate a personalized weekly plan based on the user's profile.

If no API key is configured, or the AI call fails for any reason, it
falls back to a clearly-labeled sample plan built from simple rules, so
the endpoint always returns something useful instead of failing.
"""

import json
import os

AI_SYSTEM_PROMPT = (
    "You are a certified fitness coach. Generate a safe, beginner-friendly "
    "weekly workout plan based on the user's profile. Respond ONLY with "
    "valid JSON (no markdown, no commentary) matching this exact shape:\n"
    '{"days": [{"day": "Monday", "focus": "Upper Body", '
    '"exercises": [{"name": "Push-ups", "sets": 3, "reps": "10-12"}]}]}\n'
    "Include one entry for every requested workout day, plus rest days "
    "labeled with an empty exercises list and focus 'Rest'. Keep the plan "
    "realistic for the user's stated experience level."
)


def _build_user_prompt(user):
    return (
        f"Profile:\n"
        f"- Age: {user['age']}\n"
        f"- Height: {user['height_cm']} cm\n"
        f"- Weight: {user['weight_kg']} kg\n"
        f"- Goal: {user['fitness_goal']}\n"
        f"- Experience level: {user['experience_level']}\n"
        f"- Workout days per week: {user['workout_days_per_week']}\n"
        f"Generate a 7-day weekly plan (including rest days)."
    )


def _call_ai_provider(user):
    """
    Calls the Anthropic API to generate a plan. Returns a parsed dict on
    success, or raises an exception on any failure (missing key, network
    error, bad response, etc.) -- callers should catch and fall back.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("No AI provider configured (ANTHROPIC_API_KEY not set).")

    import urllib.request

    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1500,
        "system": AI_SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": _build_user_prompt(user)}],
    }
    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode("utf-8"))

    text = "".join(
        block.get("text", "") for block in result.get("content", []) if block.get("type") == "text"
    )
    text = text.strip()
    # Strip markdown code fences if the model added them despite instructions.
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json\n", "", 1) if text.startswith("json\n") else text

    return json.loads(text)


def _sample_plan(user):
    """
    A simple, rule-based fallback plan. Not AI-generated -- used when no
    AI provider is configured or the AI call fails for any reason.
    """
    goal_focus = {
        "lose_weight": ["Full Body + Cardio", "Cardio + Core", "Full Body Strength"],
        "build_muscle": ["Push (Chest/Shoulders/Triceps)", "Pull (Back/Biceps)", "Legs"],
        "endurance": ["Cardio Intervals", "Steady-State Cardio", "Full Body + Core"],
        "general_fitness": ["Full Body Strength", "Cardio + Mobility", "Full Body Strength"],
    }
    focuses = goal_focus.get(user["fitness_goal"], goal_focus["general_fitness"])

    beginner_sets = 3 if user["experience_level"] == "beginner" else 4

    sample_exercise_sets = {
        "Full Body + Cardio": [
            {"name": "Bodyweight Squats", "sets": beginner_sets, "reps": "12-15"},
            {"name": "Push-ups", "sets": beginner_sets, "reps": "8-12"},
            {"name": "Brisk Walk or Jog", "sets": 1, "reps": "20 minutes"},
        ],
        "Cardio + Core": [
            {"name": "Jumping Jacks", "sets": beginner_sets, "reps": "30 seconds"},
            {"name": "Plank", "sets": beginner_sets, "reps": "20-30 seconds"},
            {"name": "Bicycle Crunches", "sets": beginner_sets, "reps": "15 per side"},
        ],
        "Full Body Strength": [
            {"name": "Bodyweight Squats", "sets": beginner_sets, "reps": "12-15"},
            {"name": "Push-ups", "sets": beginner_sets, "reps": "8-12"},
            {"name": "Bent-over Rows (light weight/band)", "sets": beginner_sets, "reps": "10-12"},
        ],
        "Push (Chest/Shoulders/Triceps)": [
            {"name": "Push-ups", "sets": beginner_sets, "reps": "8-12"},
            {"name": "Shoulder Press", "sets": beginner_sets, "reps": "10-12"},
            {"name": "Tricep Dips", "sets": beginner_sets, "reps": "10-12"},
        ],
        "Pull (Back/Biceps)": [
            {"name": "Bent-over Rows", "sets": beginner_sets, "reps": "10-12"},
            {"name": "Bicep Curls", "sets": beginner_sets, "reps": "10-12"},
            {"name": "Superman Holds", "sets": beginner_sets, "reps": "10"},
        ],
        "Legs": [
            {"name": "Bodyweight Squats", "sets": beginner_sets, "reps": "12-15"},
            {"name": "Lunges", "sets": beginner_sets, "reps": "10 per leg"},
            {"name": "Calf Raises", "sets": beginner_sets, "reps": "15-20"},
        ],
        "Cardio Intervals": [
            {"name": "Sprint Intervals", "sets": 6, "reps": "30 seconds on / 60 seconds off"},
        ],
        "Steady-State Cardio": [
            {"name": "Jog, Cycle, or Swim", "sets": 1, "reps": "30-40 minutes"},
        ],
        "Cardio + Mobility": [
            {"name": "Brisk Walk or Jog", "sets": 1, "reps": "20 minutes"},
            {"name": "Dynamic Stretching", "sets": 1, "reps": "10 minutes"},
        ],
    }

    week_days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    workout_days_count = min(user["workout_days_per_week"], 7)

    days = []
    focus_index = 0
    for i, day_name in enumerate(week_days):
        if i < workout_days_count:
            focus = focuses[focus_index % len(focuses)]
            focus_index += 1
            days.append(
                {
                    "day": day_name,
                    "focus": focus,
                    "exercises": sample_exercise_sets.get(focus, []),
                }
            )
        else:
            days.append({"day": day_name, "focus": "Rest", "exercises": []})

    return {"days": days}


def generate_workout_plan(user):
    """
    Returns a tuple: (plan_dict, source) where source is "ai" or "sample".

    Always succeeds -- if the AI call fails for any reason, it silently
    falls back to the rule-based sample plan rather than raising.
    """
    try:
        plan = _call_ai_provider(user)
        if isinstance(plan, dict) and "days" in plan:
            return plan, "ai"
        raise ValueError("AI response did not match expected format.")
    except Exception:
        return _sample_plan(user), "sample"
