import os
from dotenv import load_dotenv
load_dotenv()

print("DEBUG (direct):", os.environ.get("SAFETY_API_KEY"))
