# 5-musketeers
For AI-GNITION 2026 Hackathon

How to set up the API

## First time set up
If you don't have a virtual environment, set it up by running the following in your terminal.
```bash
python -m venv .venv
```

Ensure you activate the virtual environment each time you open a new terminal.
```bash
.\.venv\Scripts\Activate.ps1
```

Ensure to install all packages in `requirements.txt`, by running the following
```bash
python -m pip install -r requirements.txt
```

Once done, execute `uvicorn` to start the API.
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
You will see the Swagger UI at http://127.0.0.1:8000/docs where you can interact with.

## Starting the API
Instantiate your virtual environment, then execute 
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Opening the HTML file and connecting to the API
The API's access is controlled by the `ALLOWED_ORIGINS` environment key in .env to ensure authorised access. Right now, it only accepts calls from Vercel (where website is deployed), and from a local path. In a separate terminal, run the following.

Right now, the HTML file is connected to the live API from Railway. Please change the API Base URL to `http://127.0.0.1:8000` before continuing

If not in the data_frontend folder yet, run:
```bash
cd data_frontend
```

Once at folder, run
```bash
python -m http.server 5500
```

Then access the HTML file at http://localhost:5500/index.html (or whichever HTML file you wish to access)