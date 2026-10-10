# Activation of local API:
# 1) Activate your virtual environment (.venv) 
# 2) Run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
# 3) Once it's up, you can access the Swagger UI at http://127.0.0.1:8000/docs

import logging
import sys

# truststore uses the Windows OS certificate store — only needed for local dev on Windows.
# On Linux (Railway), certifi below handles SSL instead, so truststore is skipped.
if sys.platform == "win32":
    import truststore
    truststore.inject_into_ssl()

from app.api import create_app
import uvicorn

import certifi, os
os.environ["CURL_CA_BUNDLE"] = certifi.where()
os.environ["SSL_CERT_FILE"] = certifi.where()

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = create_app()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
