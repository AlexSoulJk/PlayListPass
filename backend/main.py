from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth import router as auth_router

app = FastAPI(
    title="PlayListPass API",
    description="Backend API for music aggregator",
    version="0.1.0"
)

# --- CORS (Чтобы фронт с localhost:8090 мог стучаться) ---
origins = [
    "http://localhost",
    "http://localhost:8090",
    "http://127.0.0.1:8090",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Подключаем роуты ---
app.include_router(auth_router)

@app.get("/")
async def root():
    return {"status": "ok", "service": "PlayListPass Backend"}