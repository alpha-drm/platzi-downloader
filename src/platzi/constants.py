import random
from pathlib import Path

import platformdirs

APP_NAME = "Platzi"
SESSION_DIR = Path(platformdirs.user_data_dir(APP_NAME))
SESSION_FILE = SESSION_DIR / "state.json"  # Cookies are stored here

LOGIN_URL = "https://platzi.com/login"
LOGIN_DETAILS_URL = "https://api.platzi.com/api/v1/components/headerv2/user/"


PLATZI_URL = "https://platzi.com"
REFERER = "https://platzi.com/"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:144.0) Gecko/20100101 Firefox/144.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
]

HEADERS = {
    "User-Agent": random.choice(USER_AGENTS),
    "Referer": REFERER,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3",
    "Connection": "keep-alive",
    "Host": "mediastream.platzi.com",
    "Origin": "https://platzi.com",
}


# --- Session directory ---
SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)

# --- Cache directory ---
CACHE_DIR = SESSION_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
