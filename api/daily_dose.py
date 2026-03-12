"""
Daily Dose — 200-day journey from the books in the data folder (finance & marketing).
One short teaching per day, grounded in retrieved book content, applicable to day-to-day life.
Same topic for everyone on the same calendar day; optional MongoDB caching.
"""

import argparse
import os
import json
from datetime import date, datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

JOURNEY_START = date(2026, 3, 7)
JOURNEY_DAYS = 200

_TOPICS_CACHE = None
_MONGO_CLIENT = None
_MONGO_DB = None


def _topics_path():
    p = Path(__file__).resolve().parent / "daily_topics.json"
    if not p.exists():
        p = Path.cwd() / "api" / "daily_topics.json"
    return p


def load_topics():
    """Load 200 topics from api/daily_topics.json. Cached in memory."""
    global _TOPICS_CACHE
    if _TOPICS_CACHE is not None:
        return _TOPICS_CACHE
    path = _topics_path()
    if not path.exists():
        raise FileNotFoundError(f"Topics file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    topics = data if isinstance(data, list) else data.get("topics", [])
    by_day = {int(t["day"]): t for t in topics if "day" in t}
    _TOPICS_CACHE = by_day
    return _TOPICS_CACHE


def date_to_day(d: date) -> int:
    """Map a calendar date to journey day 1–200. Wraps after 200 days."""
    delta = (d - JOURNEY_START).days
    if delta < 0:
        delta = 0
    return (delta % JOURNEY_DAYS) + 1


def get_topic(day: int):
    """Get topic dict for journey day (1–200)."""
    day = ((day - 1) % JOURNEY_DAYS) + 1
    topics = load_topics()
    return topics.get(day)


def _get_mongo():
    """Lazy connect to MongoDB if MONGODB_URI is set."""
    global _MONGO_CLIENT, _MONGO_DB
    if _MONGO_CLIENT is not None:
        return _MONGO_DB
    uri = os.getenv("MONGODB_URI")
    if not uri:
        return None
    try:
        from pymongo import MongoClient
        _MONGO_CLIENT = MongoClient(uri)
        db_name = os.getenv("MONGODB_DB", "multi_tenant")
        _MONGO_DB = _MONGO_CLIENT[db_name]
        return _MONGO_DB
    except Exception:
        return None


def get_cached_dose(day: int) -> dict | None:
    """Return cached dose for journey day if available."""
    db = _get_mongo()
    if db is None:
        return None
    try:
        doc = db.daily_doses.find_one({"day": day})
        if not doc:
            return None
        doc.pop("_id", None)
        return doc
    except Exception:
        return None


def set_cached_dose(day: int, payload: dict):
    """Cache a dose for journey day."""
    db = _get_mongo()
    if db is None:
        return
    try:
        payload = dict(payload)
        payload["day"] = day
        payload["updated_at"] = datetime.utcnow().isoformat()
        db.daily_doses.update_one(
            {"day": day},
            {"$set": payload},
            upsert=True,
        )
    except Exception:
        pass


def get_dose_for_day(
    day: int,
    for_date: date | None = None,
    generate_message_cb=None,
) -> dict:
    """
    Get the full dose for journey day (1–200): topic + message (cached or generated).
    generate_message_cb(topic_dict) -> str should generate teaching from books when not cached.
    """
    if for_date is None:
        for_date = date.today()
    topic = get_topic(day)
    if not topic:
        return {
            "day": day,
            "title": "Unknown",
            "source": "Finance & Marketing",
            "theme": "",
            "question": "",
            "message": "Topic not found for this day.",
            "date": for_date.isoformat(),
            "journey_start": JOURNEY_START.isoformat(),
            "today_day": date_to_day(date.today()),
            "cached": False,
        }

    cached = get_cached_dose(day)
    if cached and cached.get("message"):
        out = dict(cached)
        out["date"] = for_date.isoformat()
        out["journey_start"] = JOURNEY_START.isoformat()
        out["today_day"] = date_to_day(date.today())
        out["cached"] = True
        return out

    if not generate_message_cb:
        from api.app import initialize_rag_system, generate_daily_dose_message
        success, _ = initialize_rag_system()
        if not success:
            return {
                "day": day,
                "title": topic.get("title", ""),
                "source": topic.get("source", "Finance & Marketing"),
                "theme": topic.get("theme", ""),
                "question": topic.get("question", ""),
                "message": "RAG system not initialized. Start the server and try again.",
                "date": for_date.isoformat(),
                "journey_start": JOURNEY_START.isoformat(),
                "today_day": date_to_day(date.today()),
                "cached": False,
            }
        generate_message_cb = generate_daily_dose_message

    message = generate_message_cb(topic)
    source = topic.get("source", "Finance & Marketing")
    payload = {
        "day": day,
        "title": topic.get("title", ""),
        "source": source,
        "theme": topic.get("theme", ""),
        "question": topic.get("question", ""),
        "message": message,
    }
    set_cached_dose(day, payload)

    return {
        **payload,
        "date": for_date.isoformat(),
        "journey_start": JOURNEY_START.isoformat(),
        "today_day": date_to_day(date.today()),
        "cached": False,
    }


def list_topics():
    """Return list of all 200 topics (no message generation)."""
    topics = load_topics()
    return [topics.get(d) for d in range(1, JOURNEY_DAYS + 1) if topics.get(d)]


def main():
    parser = argparse.ArgumentParser(
        description="Daily Dose — 200-day journey from finance & marketing books"
    )
    parser.add_argument("--day", type=int, default=None, help="Journey day 1–200 (default: today)")
    parser.add_argument("--list", action="store_true", help="List all 200 topics")
    args = parser.parse_args()

    if args.list:
        for t in list_topics():
            if t:
                print(f"Day {t['day']}: {t.get('title', '')} ({t.get('theme', '')})")
        return

    day = args.day
    if day is None:
        day = date_to_day(date.today())
    else:
        day = ((day - 1) % JOURNEY_DAYS) + 1

    dose = get_dose_for_day(day)
    print(json.dumps(dose, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
