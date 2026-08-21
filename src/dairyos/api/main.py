from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from datetime import date
import asyncio
import random
import json

from .database import engine, get_db
from . import models

# Automatically create tables in SQLite if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="DairyOS API")

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PYDANTIC SCHEMAS ---
class AnimalResponse(BaseModel):
    id: int
    tag: str
    name: str
    status: str
    model_config = ConfigDict(from_attributes=True)

class AIRecordCreate(BaseModel):
    cow_id: str
    bull_id: str
    date: date
    technician: str
    notes: str | None = None

# --- REST ENDPOINTS (Now Connected to DB) ---
@app.get("/api/v1/herd", response_model=list[AnimalResponse])
def get_herd(db: Session = Depends(get_db)):
    # Fetch all animals from the database
    animals = db.query(models.AnimalDB).all()
    return animals

@app.post("/api/v1/ai-records")
def create_ai_record(record: AIRecordCreate, db: Session = Depends(get_db)):
    # Save the new AI record directly to the database
    db_record = models.AIRecordDB(
        cow_id=record.cow_id,
        bull_id=record.bull_id,
        date=record.date,
        technician=record.technician,
        notes=record.notes
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    
    return {
        "status": "success", 
        "message": f"AI event recorded securely in DB for {record.cow_id}"
    }

# --- WEBSOCKETS ---
@app.websocket("/ws/thi")
async def thi_telemetry(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            temp_c = round(random.uniform(28.0, 38.0), 1)
            humidity = round(random.uniform(50.0, 85.0), 1)
            thi = round((1.8 * temp_c + 32) - ((0.55 - 0.0055 * humidity) * ((1.8 * temp_c + 32) - 58)), 1)
            
            status = "Normal"
            if thi >= 72 and thi < 79:
                status = "Mild Stress"
            elif thi >= 79 and thi < 89:
                status = "Severe Stress"
            elif thi >= 89:
                status = "Deadly"
                
            payload = {"temperature": temp_c, "humidity": humidity, "thi": thi, "status": status}
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(2)
            
    except WebSocketDisconnect:
        print("Widget disconnected")
