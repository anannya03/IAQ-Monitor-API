# IAQ Monitor API

**_REST API written in FastAPI for reading sensor values from an Arduino Uno based Indoor Air Quality monitoring system_**

## Endpoints

- GET `/values` => gets all the sensor values stored in the database.
- GET `/latestValues` => gets the last 15 values from the database.
- POST `/values` => adds sensor values from the supplied body to the database.

## Resources

- [SQLAlchemy](https://www.sqlalchemy.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
