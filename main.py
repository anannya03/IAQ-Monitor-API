from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy import Column, Float, String, Integer

app = FastAPI()

# Allow CORS for requests from certain origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Establish connection with SQLite

SQLALCHEMY_DATABASE_URL = 'sqlite+pysqlite:///./db.sqlite3:'
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create Table

class SensorValueDB(Base):
    __tablename__ = 'sensor_values'

    id = Column(Integer, primary_key=True, index=True)
    CO2 = Column(Float, nullable = False)
    Toluene = Column(Float, nullable = False)
    NH4 = Column(Float, nullable = False)
    Acetone = Column(Float, nullable = False)
    H2 = Column(Float, nullable = False)
    LPG = Column(Float, nullable = False)
    CH4 = Column(Float, nullable = False)
    CO = Column(Float, nullable = False)
    Alcohol = Column(Float, nullable = False)
    Date_Time = Column(String, nullable = False)

Base.metadata.create_all(bind=engine)

# Pydantic class - For validation 

class SensorValue(BaseModel):
    CO2: float
    Toluene: float
    NH4: float
    Acetone: float
    H2: float
    LPG: float
    CH4: float
    CO: float
    Alcohol: float
    Date_Time: str

    class Config:
        orm_mode = True

def get_all_sensor_values(db: Session):
    return db.query(SensorValueDB).all()

def get_last_sensor_values(db: Session):
    return db.query(SensorValueDB).limit(15).all()

def create_sensor_value(db: Session, sensorValue: SensorValue):
    db_value = SensorValueDB(**sensorValue.dict())
    db.add(db_value)
    db.commit()
    db.refresh(db_value)

    return db_value

# Routes for interacting with the API

@app.post('/values/', response_model=SensorValue)
def create_values_endpoint(sensorValue: SensorValue, db: Session = Depends(get_db)):
    db_value = create_sensor_value(db, sensorValue)
    return db_value

@app.get('/values/', response_model=List[SensorValue])
def get_values_endpoint(db: Session = Depends(get_db)):
    return get_all_sensor_values(db)

@app.get('/lastValues/', response_model=List[SensorValue])
def get_values_last_fifteen_entries_endpoint(db: Session = Depends(get_db)):
    return get_last_sensor_values(db)

@app.get('/')
async def root():
    return {'message': '1. Add /values to the endpoint to get all the entries \n\t 2. Add /lastValues to the endpoint to get last 15 entries \n\t'}
