# src/dairyos/api/auth.py
"""Simple login that returns a static token."""
from fastapi import APIRouter

router = APIRouter()

@router.post("/login")
def login():
    return {"access_token": "static-token", "token_type": "bearer"}
