import os
import json
import logging
from .main import app

if __name__ == "__main__":
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        # f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres:5432/musicApp"
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@0.0.0.0:8123/musicApp"
    )
    app.debug = True

    logging.basicConfig(
        level=logging.DEBUG,
        format=json.dumps(
            {
                "timestamp": "%(asctime)s",
                "level": "%(levelname)s",
                "message": "%(message)s",
            }
        ),
        handlers=[logging.StreamHandler()],
    )

    app.run(port=8080)
