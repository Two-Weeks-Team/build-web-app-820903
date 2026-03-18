from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from models import create_all
from routes import router, seed_demo_data


app = FastAPI(title="Build Web App API", version="1.0.0")

@app.middleware("http")
async def normalize_api_prefix(request: Request, call_next):
    if request.scope.get("path", "").startswith("/api/"):
        request.scope["path"] = request.scope["path"][4:] or "/"
    return await call_next(request)

app.include_router(router)


@app.on_event("startup")
def on_startup():
    create_all()
    seed_demo_data()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def root():
    html = """
    <html>
      <head>
        <title>Build Web App API</title>
        <style>
          body { background:#0b1020; color:#e5e7eb; font-family: Inter, Arial, sans-serif; margin:0; }
          .wrap { max-width: 980px; margin: 40px auto; padding: 24px; }
          .card { background:#121a2f; border:1px solid #263252; border-radius:12px; padding:20px; margin-bottom:16px; }
          h1 { margin-top:0; color:#93c5fd; }
          a { color:#a7f3d0; text-decoration:none; }
          code { color:#fde68a; }
          ul { line-height:1.8; }
        </style>
      </head>
      <body>
        <div class="wrap">
          <div class="card">
            <h1>Build Web App — Meal Prep Planning API</h1>
            <p>Turn a messy meal-prep goal into a structured brief, weekly board, grocery basket, prep workflow, and saved snapshots.</p>
          </div>

          <div class="card">
            <h2>Endpoints</h2>
            <ul>
              <li><code>GET /health</code> — API health status</li>
              <li><code>POST /plan</code> and <code>POST /api/plan</code> — build a meal plan artifact (AI-native)</li>
              <li><code>POST /insights</code> and <code>POST /api/insights</code> — generate rebalance insights (AI-native)</li>
              <li><code>POST /rebalance</code> and <code>POST /api/rebalance</code> — deterministic live constraint rebalance</li>
              <li><code>GET /snapshots</code> and <code>GET /api/snapshots</code> — list saved prep snapshots</li>
              <li><code>GET /snapshots/{id}</code> and <code>GET /api/snapshots/{id}</code> — open a saved artifact</li>
            </ul>
          </div>

          <div class="card">
            <h2>Tech Stack</h2>
            <ul>
              <li>FastAPI 0.115.0 + Uvicorn 0.30.0</li>
              <li>SQLAlchemy 2.0.35 (sync) + PostgreSQL/SQLite compatible</li>
              <li>DigitalOcean Serverless Inference via <code>httpx</code> (model: anthropic-claude-4.6-sonnet)</li>
            </ul>
            <p><a href="/docs">OpenAPI Docs</a> · <a href="/redoc">ReDoc</a></p>
          </div>
        </div>
      </body>
    </html>
    """
    return HTMLResponse(content=html)
