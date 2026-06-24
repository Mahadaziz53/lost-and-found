**FoundBridge** — I'm in **Ask mode**, so I can't create the file on disk. Copy the README below into `lost-and-found/README.md`, or switch to **Agent mode** and ask me to add it for you.

---

```markdown
# FoundBridge

A smart **Lost & Found** web application that helps users report lost or found items and automatically matches them using AI.

Users can register, post listings with photos and descriptions, search items, and view ranked match results. The system combines **NLP**, **computer vision**, and **Google Gemini** to score how likely a lost item matches a found one.

---

## Features

- User authentication (register, login, logout)
- Report **lost** and **found** items with title, description, location, category, and optional image
- Browse lost/found listings with search and filters
- Personal dashboard with your listings and matches
- **AI-powered matching** between lost and found items
- Image analysis (color histograms, dominant colors, edge features)
- NLP tag extraction (entities, colors, keywords) via spaCy
- Gemini-generated image descriptions and pairwise match reasoning
- Admin panel for managing users and items
- Contact phone revealed only to owners or matched users

---

## Tech Stack

| Layer | Technology |
|--------|------------|
| Backend | Flask, Flask-Login, SQLAlchemy |
| Database | SQLite (local); Postgres supported via `DATABASE_URL` |
| NLP | spaCy (`en_core_web_sm`) |
| Computer Vision | OpenCV, NumPy, Pillow |
| AI | Google Gemini API |
| Frontend | Jinja2 templates, Tailwind CSS (CDN) |
| Server | Gunicorn (production) |

---

## How Matching Works

When an item is saved, the app enriches it with:

1. **Vision features** — OpenCV extracts color histograms and image metadata
2. **AI description** — Gemini describes uploaded images (if API key is set)
3. **NLP tags** — spaCy + rule-based extraction from text

Match score formula:

```
final_score = 0.35 × NLP + 0.30 × CV + 0.35 × GenAI
```

Results are shown on `/results/<item_id>` and surfaced on the user dashboard.

---

## Project Structure

```
lost-and-found/
├── app/
│   ├── __init__.py          # App factory, DB setup
│   ├── config.py            # Environment configuration
│   ├── models.py            # User, Item, Match models
│   ├── routes/              # auth, items, match, admin
│   ├── modules/             # vision, NLP, Gemini, scoring pipelines
│   ├── templates/           # HTML pages
│   └── static/              # CSS, JS, uploads
├── tests/
├── run.py                   # Local entrypoint
├── Procfile                 # Render / production start command
├── requirements.txt
└── .env                     # Local secrets (do not commit)
```

---

## Prerequisites

- Python 3.10+
- pip
- Google Gemini API key (optional; AI features disabled without it)

---

## Local Setup

### 1. Clone and enter the project

```bash
cd lost-and-found
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 4. Configure environment variables

Create a `.env` file in `lost-and-found/`:

```env
SECRET_KEY=your-secret-key-here
GEMINI_API_KEY=your-gemini-api-key
ADMIN_USERNAMES=mahad
GEMINI_MODEL=gemini-2.0-flash
```

### 5. Run the app

```bash
python run.py
```

Open **http://127.0.0.1:5000** in your browser.

Optional debug mode:

```bash
# Windows PowerShell
$env:FLASK_DEBUG="1"
python run.py
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes (production) | Flask session secret |
| `GEMINI_API_KEY` | No | Enables AI descriptions and GenAI matching |
| `GEMINI_MODEL` | No | Default: `gemini-2.0-flash` |
| `ADMIN_USERNAMES` | No | Comma-separated usernames granted admin access |
| `DATABASE_URL` | No | SQLite by default; Postgres URL for production |
| `FLASK_DEBUG` | No | Set to `1` for local debug mode |

---

## Main Routes

| Route | Description |
|-------|-------------|
| `/` | Home / landing |
| `/register` | Create account |
| `/login` | Sign in |
| `/lost-items` | Browse lost items |
| `/found-items` | Browse found items |
| `/report/lost` | Report a lost item |
| `/report/found` | Report a found item |
| `/item/<id>` | Item details |
| `/results/<id>` | Match results for an item |
| `/dashboard` | User dashboard |
| `/admin` | Admin panel |

---

## Deploy Online (Render)

> **Note:** This is a Flask backend app. Use **Render** or **Railway** — not Netlify.

1. Push the project to GitHub
2. Create a new **Web Service** on [Render](https://render.com)
3. Set **Root Directory** to `lost-and-found` (if repo root is parent folder)
4. **Build command:**
   ```bash
   pip install -r requirements.txt && python -m spacy download en_core_web_sm
   ```
5. **Start command:**
   ```bash
   gunicorn run:app --bind 0.0.0.0:$PORT --timeout 120 --workers 1
   ```
6. Add environment variables: `SECRET_KEY`, `GEMINI_API_KEY`, `ADMIN_USERNAMES`

---

## Running Tests

```bash
pytest tests/
```

---

## Limitations

- SQLite data and uploads may not persist on free cloud tiers after redeploy
- Gemini API calls add latency and require a valid API key
- First request on free hosting may be slow (cold start)

---

## Author

Mahad — Data Science student

---

## License

MIT (or update as needed)
```

---

To have this saved as `lost-and-found/README.md` automatically, switch to **Agent mode** and say: **"create the README file"**.
