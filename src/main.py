import os
from dotenv import load_dotenv
import functools
from flask import Flask
from flask import render_template, request, session, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy

from sqlalchemy import text
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder="templates")

load_dotenv(".env")
app.secret_key = os.getenv("SECRET_KEY")

POSTGRES_USER_PASSWORD = os.getenv("POSTGRES_USER_PASSWORD")
POSTGRES_USER = os.getenv("POSTGRES_USER")


app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_USER_PASSWORD}@localhost:8123/music-app"
)

app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER")


db = SQLAlchemy(app)


def check_login(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Check if user is logged in
        if "username" not in session:
            return redirect("/")
        return func(*args, **kwargs)

    return wrapper


@app.route("/")
def index():
    if "username" in session:
        return redirect("/home")
    return render_template("index.html")


@app.route("/home")
@check_login
def home():
    return render_template("home.html")


@app.route("/chat")
def chat():
    result = db.session.execute(text("SELECT content FROM messages"))
    messages = result.fetchall()

    return render_template("chat.html", messages=messages, count=len(messages))


@app.route("/new")
def new():
    return render_template("new.html")


@app.route("/send", methods=["POST"])
def send():
    content = request.form["content"]
    sql = text("INSERT INTO messages (content) VALUES (:content)")
    db.session.execute(sql, {"content": content})
    db.session.commit()
    return redirect("/chat")


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    sql = text("SELECT id, password FROM users WHERE username=:username")
    result = db.session.execute(sql, {"username": username})
    user = result.fetchone()
    if not user:
        return "User not found"

    if check_password_hash(user[1], password):
        session["username"] = username

    return redirect("/home")


@app.route("/logout", methods=["POST"])
def logout():
    del session["username"]
    return redirect("/")


@app.route("/signup", methods=["POST"])
def signup():
    username = request.form["username"]
    # Check if username is taken
    sql = text("SELECT id, password FROM users WHERE username=:username")
    result = db.session.execute(sql, {"username": username})
    user = result.fetchone()
    if user:
        return "User already exists"

    hash_pass = generate_password_hash(request.form["password"])

    sql = text("INSERT INTO users (username, password) VALUES (:username, :password)")
    db.session.execute(sql, {"username": username, "password": hash_pass})
    db.session.commit()

    return redirect("/")


def allowed_file(filename):
    # TODO: Add allowed file types.
    # return '.' in filename and \
    #       filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    return True


def insert_into_uploads(username: str, filepath: str, filename: str):

    sql = text(
        """
        with user_data AS (
	        SELECT id FROM users WHERE username = 'johku'
        )
        INSERT INTO uploads (user_id, upload_time, filepath, filename)
        VALUES ((SELECT id from user_data), NOW()::TIMESTAMP, 'data/', 'test.txt');
        """
    )


@app.route("/upload/", methods=["GET", "POST"])
def upload_file():

    if request.method == "POST":
        print("POST")
        # check if the post request has the file part
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)

        file = request.files["file"]
        print(request.form)
        # TODO: use pydantic
        username = session["username"]
        songName = request.form["songName"]
        description = request.form.get("description", None)
        if description == "":
            description = None

        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            sql = text(
                """
                with user_data AS (
                SELECT id FROM users WHERE username = (:username)
                )
                INSERT INTO uploads (
                    user_id,
                    upload_time,
                    song_name,
                    song_description,
                    filepath,
                    filename
                    )
                    VALUES (
                    (SELECT id from user_data),
                    NOW()::TIMESTAMP,
                    (:songName),
                    (:description),
                    (:filepath),
                    (:filename)
                );
            """
            )
            db.session.execute(
                sql,
                {
                    "username": username,
                    "songName": songName,
                    "description": description,
                    "filepath": app.config["UPLOAD_FOLDER"],
                    "filename": filename,
                },
            )
            db.session.commit()

            # TODO: check if file already exists.

            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            return redirect(url_for("upload_file", filename=filename))

    print("NO POST")
    return render_template("/upload.html")


if __name__ == "__main__":
    app.debug = True

    app.run(port=8080)
