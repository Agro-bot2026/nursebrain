import os
from dotenv import load_dotenv
load_dotenv()

GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_LOCATION = os.getenv("GCP_LOCATION", "us")
DOCUMENTAI_PROCESSOR_ID = os.getenv("DOCUMENTAI_PROCESSOR_ID")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")

APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "dev-secret")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nursebrain.db")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
BASE_URL = os.getenv("BASE_URL", "https://nursebrain.charly-tricks.dev")

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
MAIL_FROM = os.getenv("MAIL_FROM", "NurseBrain <nursebrain@charly-tricks.dev>")

ADMIN_USER = os.getenv('ADMIN_USER', 'charly.tricks.00@gmail.com')

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
if GOOGLE_APPLICATION_CREDENTIALS:
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GOOGLE_APPLICATION_CREDENTIALS
