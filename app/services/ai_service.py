import json
import logging
from typing import Any
from ..config import settings

logger = logging.getLogger(__name__)

def _demo_plan(data: dict[str, Any]) -> dict[str, Any]:
    goal, intensity = data["goal"], data["intensity"]
    level = {"low": "beginner-friendly", "medium": "moderate", "high": "challenging"}[intensity]
    focus = {
        "weight loss": ["Full body + brisk cardio","Lower body + intervals","Upper body + cardio","Active recovery","Full body circuit","Cardio + core","Rest & mobility"],
        "muscle gain": ["Upper body strength","Lower body strength","Active recovery","Push strength","Pull strength","Legs + core","Rest & mobility"],
        "general wellness": ["Full body mobility","Light strength","Cardio & breathing","Mobility","Full body strength","Fun cardio","Rest & reflection"],
        "flexibility": ["Full body mobility","Hips & hamstrings","Shoulders & spine","Yoga-inspired flow","Lower-body mobility","Full-body stretch","Rest"],
        "endurance": ["Easy cardio","Intervals","Strength + cardio","Tempo cardio","Recovery cardio","Long easy session","Rest"],
    }[goal]
    days = []
    for i, title in enumerate(focus, 1):
        if title == "Rest":
            warmup, main, cooldown = "5 min easy breathing and gentle mobility.", ["Rest day. Optional easy walk for 15–20 minutes."], "Gentle stretching only."
        elif "recovery" in title.lower() or "Rest &" in title:
            warmup, main, cooldown = "5–8 min easy walking and joint circles.", ["20–30 min easy walking","10 min mobility flow"], "5 min relaxed stretching."
        elif any(x in title.lower() for x in ["cardio","interval","tempo"]):
            warmup, main, cooldown = "5–10 min brisk walk + dynamic mobility.", ["20–30 min cardio at a sustainable pace","6 × 30 sec faster efforts with 60 sec easy recovery"], "5–10 min easy walking and calf/hip stretches."
        else:
            warmup, main, cooldown = "5–10 min brisk walk + dynamic mobility.", ["Squat or chair squat — 3 × 10–12","Push-up or incline push-up — 3 × 8–12","Row/band row — 3 × 10–12","Glute bridge — 3 × 12–15","Plank — 3 × 20–40 sec"], "5–8 min easy stretching."
        days.append({"day":f"Day {i}","focus":title,"level":level,"warmup":warmup,"main_workout":main,"cooldown":cooldown})
    return {"title":f"7-Day {goal.title()} Plan","summary":f"A {intensity}-intensity plan designed around {goal}.","days":days,"safety":"Start gradually, use controlled technique, and stop if you feel sharp pain, dizziness, or unusual symptoms."}

def _demo_tip(goal: str) -> str:
    return {
        "weight loss":"Build meals around vegetables, a protein source, whole-food carbohydrates, and water. Sustainable habits matter more than extreme restriction.",
        "muscle gain":"Include a protein-rich food in each main meal and eat enough total energy to support training and recovery.",
        "general wellness":"Stay hydrated, include varied whole foods, and aim for consistent sleep and regular movement.",
        "flexibility":"Hydrate normally and include protein and nutrient-dense foods to support recovery from mobility work.",
        "endurance":"For longer sessions, combine carbohydrates for training fuel with protein after exercise and keep hydration consistent.",
    }.get(goal, "Stay hydrated, eat varied whole foods, and prioritize consistent recovery.")

def _gemini_client():
    if not settings.google_api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=settings.google_api_key)
    except Exception as exc:
        logger.warning("Gemini client unavailable: %s", exc)
        return None

def _extract_json(text: str):
    cleaned = text.strip().replace("```json","").replace("```","").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        a, b = cleaned.find("{"), cleaned.rfind("}")
        if a >= 0 and b > a:
            try: return json.loads(cleaned[a:b+1])
            except json.JSONDecodeError: return None
    return None

def generate_workout_gemini(data: dict[str, Any]) -> dict[str, Any]:
    client = _gemini_client()
    if not client: return _demo_plan(data)
    prompt = f"""
You are FitBuddy, a cautious fitness-planning assistant.
Create a safe, practical 7-day workout plan for:
Name: {data['username']}; Age: {data['age']}; Weight kg: {data['weight']};
Goal: {data['goal']}; Intensity: {data['intensity']}.
Return ONLY valid JSON with keys title, summary, days, safety.
days must contain exactly 7 objects with day, focus, level, warmup, main_workout (array of strings), cooldown.
Do not diagnose disease or prescribe treatment. Include recovery and safety guidance.
"""
    try:
        response = client.models.generate_content(model=settings.gemini_workout_model, contents=prompt)
        result = _extract_json(getattr(response, "text", "") or "")
        if isinstance(result, dict) and isinstance(result.get("days"), list) and len(result["days"]) == 7:
            return result
    except Exception as exc:
        logger.exception("Gemini workout generation failed: %s", exc)
    return _demo_plan(data)

def generate_nutrition_tip_with_flash(goal: str) -> str:
    client = _gemini_client()
    if not client: return _demo_tip(goal)
    prompt = f'Give one concise, practical nutrition or recovery tip for the fitness goal "{goal}". Keep it general wellness guidance, not medical advice. Maximum 80 words.'
    try:
        response = client.models.generate_content(model=settings.gemini_tip_model, contents=prompt)
        tip = (getattr(response, "text", "") or "").strip()
        if tip: return tip
    except Exception as exc:
        logger.exception("Gemini tip generation failed: %s", exc)
    return _demo_tip(goal)

def update_workout_plan(original_plan: dict[str, Any], data: dict[str, Any], feedback: str) -> dict[str, Any]:
    client = _gemini_client()
    if not client:
        updated = json.loads(json.dumps(original_plan))
        updated["summary"] = f"{updated.get('summary','')} Feedback applied: {feedback}"
        return updated
    prompt = f"""
Revise this existing 7-day fitness plan according to the user's feedback.
User: age={data['age']}, weight={data['weight']} kg, goal={data['goal']}, intensity={data['intensity']}.
Feedback: {feedback}
Existing plan:
{json.dumps(original_plan, indent=2)}
Return ONLY valid JSON with the same schema and exactly 7 days. Do not diagnose disease or prescribe medical treatment.
"""
    try:
        response = client.models.generate_content(model=settings.gemini_workout_model, contents=prompt)
        result = _extract_json(getattr(response, "text", "") or "")
        if isinstance(result, dict) and isinstance(result.get("days"), list) and len(result["days"]) == 7:
            return result
    except Exception as exc:
        logger.exception("Gemini plan update failed: %s", exc)
    updated = json.loads(json.dumps(original_plan))
    updated["summary"] = f"{updated.get('summary','')} Feedback applied: {feedback}"
    return updated
