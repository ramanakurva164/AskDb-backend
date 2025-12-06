from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import Base, engine
from . import models  # noqa: F401
from .routers import chat, conversations

# Create tables (dev only)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Student Assignment Chat API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://askdb-frontend.onrender.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(conversations.router)


@app.get("/")
def root():
    return {"status": "ok"}
