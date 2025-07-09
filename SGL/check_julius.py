import os
import requests
from dotenv import load_dotenv

load_dotenv()


def run_checks():
    API_KEY = os.getenv('JULIUS_API_KEY')
    BASE_URL = os.getenv('JULIUS_BASE_URL', 'https://api.julius.ai/v1')

    if not API_KEY:
        print("❌ JULIUS_API_KEY missing in .env")
        return

    tests = {
        "DNS Resolution": ("https://api.julius.ai", None),
        "API Endpoint": (f"{BASE_URL}/ping", {"Authorization": f"Bearer {API_KEY}"})
    }

    for name, (url, headers) in tests.items():
        try:
            r = requests.get(url, headers=headers, timeout=5)
            print(f"✅ {name}: HTTP {r.status_code} ({url})")
            if r.text: print(f"   Response: {r.text[:100]}")
        except Exception as e:
            print(f"❌ {name} failed: {str(e)}")


if __name__ == "__main__":
    run_checks()