# Intelligent Search Visualizer - Deployment Starter

This repository contains the web application starter code and deployment configuration for the Search Visualizer project. It provides an empty frontend and backend setup so students can test local execution and cloud deployment prior to implementing search algorithms.

---

## Directory Structure

```text
.
├── app.py                      # Flask web server and routing endpoints
├── data_fetcher.py             # Script to fetch geocoding & road distance data
├── templates/
│   └── index.html              # Map frontend interface (Leaflet.js)
├── requirements.txt            # Python dependencies
├── Procfile                    # Deployment process configuration (Render/Gunicorn)
└── README.md                   # Setup and deployment instructions
```

---

## Local Development

### 1. Set Up Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Generate Map Data
Run `data_fetcher.py` to retrieve geocoding and road distance data for locations in your chosen USA region:
```bash
python data_fetcher.py
```
This generates `map_data.json` containing city coordinates and road graph distances.

### 4. Run the Web Application
```bash
python app.py
```
Open a web browser and go to `http://127.0.0.1:5000`.

---

## Deployment to Render

Follow these steps to deploy your application to Render:

### Step 1: Push Code to GitHub
Ensure all files are committed and pushed to your repository:
```bash
git add .
git commit -m "Deployment setup"
git push origin main
```

### Step 2: Create a Web Service
1. Log in to Render (https://render.com).
2. Click **New +** and select **Web Service**.
3. Connect your project repository.

### Step 3: Configure Settings
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`
- **Instance Type:** `Free`

### Step 4: Verify Deployment
1. Click **Deploy Web Service**.
2. Once the build completes, open your provided live URL (e.g., `https://<your-app-name>.onrender.com`).
3. Verify that the map and controls render properly.
