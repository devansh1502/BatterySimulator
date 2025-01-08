from src.api import app
from database.db import configure_database

if __name__ == "__main__":
    configure_database()
    app.run(port=8080)