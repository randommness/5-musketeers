# Pet Guardian 😺
For AI-GNITION 2026 Hackathon

Built by: **YM fanclub ❤️**

# Accessing our website
Our website is live and accessible at https://ym-fanclub-pet-guardian.vercel.app/

You will be redirected into the login page. As this is a public repository, please reach out to the team for demo credentials!

_Please note we aren't able to place demo credentials publicly as it will trigger a security alert on Google._

😺🐶 **Built with love by pet lovers, for pet lovers.**

# Technical stack: API and website set-up

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

## Opening the website HTML files
Right now, the HTML file is connected to the live API from Railway. 

If not in the `frontend` folder yet, run:
```bash
cd frontend
```

Once at folder, run
```bash
python -m http.server 5500
```

Then access the landing page (index.html) at http://localhost:5500/index.html (you can change the page itself based on which HTML file you wish to access)