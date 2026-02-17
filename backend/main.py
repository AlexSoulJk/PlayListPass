from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.auth import auth_router
from routes.test import router as test_router

app = FastAPI(title="PlayListPass API")

# --- CORS ---
origins = ["http://localhost"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app = FastAPI(title="PlayListPass API")
app.include_router(auth_router)
app.include_router(test_router)