from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy import Column, Float, String, Integer
import smtplib


# function to send email from a Gmail account
def send_email(user, pwd, recipient, subject, body):

    FROM = user
    TO = recipient if isinstance(recipient, list) else [recipient]
    SUBJECT = subject
    TEXT = body

    # Prepare actual message
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(user, pwd)
        server.sendmail(FROM, TO, message)
        server.close()
        print('Successfully sent mail')
    except Exception as e:
        print("Failed to send mail: ", e)


# function to pretty print a dictionary
def prettifyGasDict(d):
    res = '\nGas -> Value\n'
    for gas, value in d.items():
        res += '\n{} -> {}'.format(gas, value)
    return res


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
SQLALCHEMY_DATABASE_URL = 'sqlite+pysqlite:///./db.sqlite3'
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
    CO2 = Column(Float, nullable=False)
    Toluene = Column(Float, nullable=False)
    NH4 = Column(Float, nullable=False)
    Acetone = Column(Float, nullable=False)
    H2 = Column(Float, nullable=False)
    LPG = Column(Float, nullable=False)
    CH4 = Column(Float, nullable=False)
    CO = Column(Float, nullable=False)
    Alcohol = Column(Float, nullable=False)
    Date_Time = Column(String, nullable=False)


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
    query = db.query(SensorValueDB).order_by(
        SensorValueDB.Date_Time.desc()).limit(15).all()
    return query[::-1]


def create_sensor_value(db: Session, sensorValue: SensorValue):
    db_value = SensorValueDB(**sensorValue.dict())
    db.add(db_value)
    db.commit()
    db.refresh(db_value)

    return db_value


# Routes for interacting with the API
@app.post('/values/', response_model=SensorValue)
def create_values_endpoint(sensorValue: SensorValue, db: Session = Depends(get_db)):

    # add new values to DB
    db_value = create_sensor_value(db, sensorValue)

    allGasValues = sensorValue.dict()

    # remove the Date_Time entry since it is not a gas
    allGasValues.pop('Date_Time')

    # filter incoming values to find the gases that breached a threshold of 50
    breachedGasValues = {
        k: v for (k, v) in allGasValues.items() if v > 50}

    # send mail in case gases have breached thresholds
    if len(breachedGasValues) > 0:
        emailUser = 'arduinoiaqmonitor@gmail.com'
        emailPassword = open('password-for-email', 'r').readline()
        emailRecipients = ['gautham.is17@bmsce.ac.in',
                           'anannya.is17@bmsce.ac.in', 'arvindhs.is17@bmsce.ac.in']
        emailSubject = 'IAQ Monitor Alert'
        emailBody = 'Your IAQ Monitor detected threshold breaches for one or more gases. Please find the associated report below.\n\n' + \
            prettifyGasDict(breachedGasValues)
        print(emailBody)
        send_email(emailUser,
                   emailPassword, emailRecipients, emailSubject, emailBody)

    return db_value


@app.get('/values/', response_model=List[SensorValue])
def get_values_endpoint(db: Session = Depends(get_db)):
    return get_all_sensor_values(db)


@app.get('/latestValues/', response_model=List[SensorValue])
def get_values_last_fifteen_entries_endpoint(db: Session = Depends(get_db)):
    return get_last_sensor_values(db)


@app.get('/')
async def root():
    return {'instructions': ['GET /values => gets all the sensor values', 'GET /latestValues => gets the last 15 entries', 'POST /values => adds a supplied sensor value to the database']}
