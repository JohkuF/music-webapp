import os
from .main import app

if __name__ == "__main__":
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        # f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres:5432/musicApp"
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@0.0.0.0:8123/musicApp"
    )
    app.debug = True
    app.run(port=8080)
