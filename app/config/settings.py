from dotenv import load_dotenv
import os 

load_dotenv()

class Settings:
    GROQ_API_KEY= os.getenv("GROQ_API_KEY")
    TRAVILY_API_KEY=os.getenv("TRAVILY_API_KEY")

    ALLOWED_MODEL_NAMES=[
        "llama-3.3-70b-versatile","llama-3.1-8b-instant"
    ]

settings=Settings()