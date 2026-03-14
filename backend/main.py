from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth import auth_router
from routes.test import router as test_router

app = FastAPI(title="PlayListPass API")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    # Dev-friendly CORS for local frontend hosts (localhost with any port).
    allow_origins=[
        "http://localhost",
        "http://127.0.0.1",
        "http://localhost:8090",
        "http://127.0.0.1:8090",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(test_router)
