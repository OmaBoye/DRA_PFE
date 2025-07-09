import os
from dotenv import load_dotenv


def verify_julius_connection():
    """Test if Julius AI credentials are properly configured"""
    load_dotenv()  # Load .env file

    required_vars = ['JULIUS_API_KEY', 'JULIUS_BASE_URL']
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print(f"❌ Missing in .env: {', '.join(missing)}")
        print("Please add these to your .env file")
        return False

    print("✅ .env configuration valid")
    print(f"API Key: {'*' * 12}{os.getenv('JULIUS_API_KEY')[-4:]}")
    print(f"Base URL: {os.getenv('JULIUS_BASE_URL')}")

    # Test API connectivity (optional)
    try:
        import requests
        response = requests.get(
            f"{os.getenv('JULIUS_BASE_URL')}/ping",  # Check if Julius has a ping endpoint
            headers={"Authorization": f"Bearer {os.getenv('JULIUS_API_KEY')}"}
        )
        print(f"API Connection: {'✅ Success' if response.ok else '❌ Failed'}")
    except Exception as e:
        print(f"⚠️ Connection test skipped: {str(e)}")

    return True


if __name__ == "__main__":
    verify_julius_connection()