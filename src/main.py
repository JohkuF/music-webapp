# TODO: Database add max char size
import os
import enum
import bleach
import logging
from flask import Flask, Response, send_file
from sqlalchemy import text
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask import render_template, request, session, redirect, flash, url_for, jsonify
from werkzeug.security import check_password_hash, generate_password_hash


from .utils import check_login, find_new_filename
from .sql_commands import (
    SQL_FILE_UPLOAD,
    SQL_SEND_MESSAGE_GENERAL,
    SQL_FETCH_MESSAGES_GENERAL,
    SQL_FETCH_MESSAGES_ON_SONG,
)


class AcceptedFileTypes(enum.Enum):
    MP3 = "audio/mpeg"
    FLAC = "audio/flac"
    OGG = "audio/ogg"


app = Flask(__name__, template_folder="templates", static_folder="static")
# TODO: check if compressions if good tradeoff
# from flask_compress import Compress

load_dotenv(".env")
app.secret_key = os.getenv("SECRET_KEY")

POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_USER = os.getenv("POSTGRES_USER")
IS_DOCKER = os.getenv("IS_DOCKER", False)

postgres_uri = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres:5432/musicApp"
    if IS_DOCKER is not False
    else f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@0.0.0.0:8123/musicApp"
)

app.config["SQLALCHEMY_DATABASE_URI"] = postgres_uri

app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER")


db = SQLAlchemy(app)


@app.route("/")
def index():
    if "username" in session:
        return redirect("/home")
    return render_template("index.html")


@app.route("/home")
@check_login
def home():
    songs = get_songs(17)
    return render_template("home.html", songs=songs)


@app.route("/messages/<path:song_id>")
def messages(song_id):
    assert song_id == request.view_args["song_id"]
    result = db.session.execute(SQL_FETCH_MESSAGES_ON_SONG, {"song_id": song_id})
    messages = result.fetchall()
    messages_list = [{"username": row[0], "content": row[1]} for row in messages]

    return jsonify(messages_list)


@app.route("/songs")
def get_songs(n: int | None = None):
    sql = text(
        """SELECT * FROM songs
           LEFT JOIN song_metadata
           ON songs.id = song_metadata.song_id;"""
    )
    result = db.session.execute(sql)
    songs = result.fetchall()
    if n:
        return songs[:n]
    return songs


@app.route("/new")
def new():
    return render_template("new.html")


@app.route("/send/<path:song_id>", methods=["POST"])
def send(song_id):
    assert song_id == request.view_args["song_id"]
    song_id = bleach.clean(song_id)

    content = request.form["content"]
    username = session["username"]

    sql = text(
        """INSERT INTO messages (song_id, user_id, upload_time, content)
    SELECT :song_id, id, NOW(), :content FROM users WHERE username = :username;
    """
    )

    try:
        db.session.execute(
            sql, {"username": username, "song_id": song_id, "content": content}
        )
        db.session.commit()
    except Exception as e:
        logging.error(f"Error executing SQL: {e}")

    result = db.session.execute(SQL_FETCH_MESSAGES_ON_SONG, {"song_id": song_id})
    messages = result.fetchall()
    # TODO: compine /messages and this fuggly thing to one function
    # Dynamic comment loading -> music doesn't stop
    response = ""
    for message in reversed(messages):
        content = bleach.clean(message.content)
        username = bleach.clean(message.username)
        response += f"""
            <div class="card mb-4" id="messages-{song_id}">
              <div class="card-body">
                <p>{content}</p>
                <div class="d-flex justify-content-between">
                  <div class="d-flex flex-row align-items-center">
                    <p class="small mb-0 ms-2">{username}</p>
                  </div>
                </div>
              </div>
            </div>
        """
    logging.warning(response)

    return response


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
    # TODO Bleach username
    username = request.form["username"]
    # Check if username is taken
    sql = text("SELECT id, password FROM users WHERE username=:username")
    result = db.session.execute(sql, {"username": username})
    user = result.fetchone()
    if user:
        return "User already exists"

    hash_pass = generate_password_hash(request.form["password"])

    sql = text(
        "INSERT INTO users (username, password, role) VALUES (:username, :password, 'user')"
    )
    db.session.execute(sql, {"username": username, "password": hash_pass})
    db.session.commit()

    return redirect("/")


def allowed_file(filetype):
    return filetype in [ftype.value for ftype in AcceptedFileTypes]
    # mime = magic.Magic(mime=True)
    # file_type = mime.from_buffer(filename.read())
    # return file_type in [ftype.value for ftype in AcceptedFileTypes]


# TODO: add api admin command to turn of uploads
@app.route("/upload/", methods=["GET", "POST"])
@check_login
def upload_file():

    if request.method == "POST":
        print("POST")
        # check if the post request has the file part
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)

        file = request.files["file"]

        # TODO: use pydantic
        username = session["username"]
        song_name = request.form["songName"]
        song_description = request.form.get("description", None)

        # TODO don't accept empty name
        if song_description == "":
            song_description = None

        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)

        if file and allowed_file(file.content_type):
            filename = secure_filename(file.filename)
            path = app.config["UPLOAD_FOLDER"]

            filepath = os.path.join(path, filename)
            if os.path.exists(filepath):
                filename = find_new_filename(path, filename)

            db.session.execute(
                SQL_FILE_UPLOAD,
                {
                    "username": username,
                    "song_name": song_name,
                    "song_description": song_description,
                    "filepath": path,
                    "filename": filename,
                },
            )
            db.session.commit()

            # TODO: check if file already exists.
            request.files["file"].save(os.path.join(path, filename))
            # TODO: -maybe useless redirect - Anyway its wrong
            return redirect(url_for("upload_file", filename=filename))

    print("NO POST")
    return render_template("/upload.html")


@app.route("/stream/<int:music_id>")
@check_login
def stream_music(music_id):
    # TODO: add better logging for music streaming

    sql = text(
        """
        SELECT filepath, filename FROM uploads
        WHERE song_id = :song_id;
        """
    )
    result = db.session.execute(sql, {"song_id": music_id})
    filepath, filename = result.fetchone()

    if not filepath or not filename:
        # TODO propper error handling
        return "Naah"

    return send_file(filepath + filename, mimetype="audio/mp3")
    # TODO: Use this for radio feature
    """
    # @stream_with_context
    def generate():
        count = 1

        with open(filepath + filename, "rb") as fwaw:
            data = fwaw.read(1024 // 2)
            while data:
                yield data
                data = fwaw.read(1024 // 2)


    response = Response(generate(), mimetype="audio/mp3")
    response.headers["X-Accel-Buffering"] = "no"
    # response.headers["X-Accel-Buffering"] = "yes"
    response.iter_chunk_size = 1024 // 2  # * 1024  # 1MB chunks

    # Check if the client supports range requests
    if "Range" in request.headers:
        response.status_code = 206  # Partial Content
    else:
        response.status_code = 200  # OK

    return response
    """


if __name__ == "__main__":
    app.debug = True

    app.run(port=8080)
