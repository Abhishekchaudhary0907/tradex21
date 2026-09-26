import os
from dotenv import load_dotenv

load_dotenv()

GROWW_API_KEY = os.getenv("GROWW_API_KEY")
GROWW_API_SECRET = os.getenv("GROWW_API_SECRET")

if not GROWW_API_KEY:
    raise RuntimeError("GROWW_API_KEY is missing in .env")

if not GROWW_API_SECRET:
    raise RuntimeError("GROWW_API_SECRET is missing in .env")


# How frequently the bot checks positions/LTP.
POLL_INTERVAL_SECONDS = 1.0

# Your strategy rules
INITIAL_SL_POINTS = 5.0
TRAIL_TRIGGER_POINTS = 0.10
TRAIL_SL_POINTS = 3.0