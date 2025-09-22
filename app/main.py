# main.py
import subprocess
import threading
import time
from app.common.logger import get_logger
from app.common.custom_exception import CustomException
from dotenv import load_dotenv

logger = get_logger(__name__)
load_dotenv()  # loads GROQ_API_KEY, TAVILY_API_KEY into current env

def run_backend():
    try:
        logger.info("Starting backend service..")
        subprocess.run(
            ["uvicorn", "app.backend.api:app", "--host", "127.0.0.1", "--port", "9999"],
            check=True,
        )
    except Exception as e:
        logger.error("Problem with backend service")
        raise CustomException("Failed to start the backend", e)

def run_frontend():
    try:
        logger.info("Starting the frontend service")
        subprocess.run(["streamlit", "run", "app/frontend/ui.py"], check=True)
    except Exception as e:
        logger.error("Problem with frontend service")
        raise CustomException("Failed to start the frontend", e)

if __name__ == "__main__":
    try:
        threading.Thread(target=run_backend, daemon=True).start()
        time.sleep(2)
        run_frontend()
    except CustomException as e:
        logger.exception(f"CustomException Occurred: {str(e)}")

        