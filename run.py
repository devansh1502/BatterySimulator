from database.db import configure_database
from src.api import app

if __name__ == "__main__":
    configure_database()
    app.run(host="0.0.0.0", port=8080, debug=True)
