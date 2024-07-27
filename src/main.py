# TODO: Database add max char size
import os
import bleach
import json
import logging
from sqlalchemy import text
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects import postgresql
from werkzeug.utils import secure_filename
from flask import Flask, Response, send_file
from flask import render_template, request, session, redirect, flash, url_for, jsonify
from werkzeug.security import check_password_hash, generate_password_hash

from .schemas import VoteSchema
from .myenums import VoteType, AcceptedFileTypes
from .utils import (
    check_login,
    find_new_filename,
    is_admin,
    is_valid_song_name,
    log_user,
    set_signup_state,
    set_upload_state,
    get_signup_state,
    get_upload_state,
    get_user_likes,
    check_vote,
    setup_login,
    songs_appData,
)
from .sql_commands import (
    SQL_FILE_UPLOAD,
    SQL_SEND_MESSAGE_GENERAL,
    SQL_FETCH_MESSAGES_GENERAL,
    SQL_FETCH_MESSAGES_ON_SONG,
    SQL_INSERT_VOTE,
)

app = Flask(__name__, template_folder="templates", static_folder="static")
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

load_dotenv(".env")
app.secret_key = os.getenv("SECRET_KEY")


POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_USER = os.getenv("POSTGRES_USER")
IS_DOCKER = os.getenv("IS_DOCKER", False)

setup_login(IS_DOCKER)

postgres_uri = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres:5432/musicApp"
    if IS_DOCKER is not False
    else f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@0.0.0.0:8123/musicApp"
)

app.config["SQLALCHEMY_DATABASE_URI"] = postgres_uri

app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER")

app.config["allow_signup"] = True

# To use get_db() instead
db = SQLAlchemy(app)


@app.errorhandler(404)
def not_found_error(error):
    return "Page not found :(", 404


@app.route("/")
def index():
    if "username" in session:
        return redirect("/home")
    return render_template("index.html")


@app.route("/home")
@check_login
def home():
    songs = get_songs(13)
    likes = get_user_likes(db, session["user_id"])

    # Data to be put into appData
    appData_songs = songs_appData(songs)
    messages = get_messages()

    return render_template(
        "home.html",
        songs=songs,
        likes=likes,
        appData_songs=appData_songs,
        messages=messages,
    )


@app.route("/explore")
@check_login
def explore():
    songs = get_songs()
    likes = get_user_likes(db, session["user_id"])

    # Data to be put into appData
    appData_songs = songs_appData(songs)
    messages = get_messages()

    return render_template(
        "explore.html",
        songs=songs,
        likes=likes,
        appData_songs=appData_songs,
        messages=messages,
    )


@app.route("/library")
@check_login
def library():
    songs = get_songs(user_id=session["user_id"])
    likes = get_user_likes(db, session["user_id"])

    # Data to be put into appData
    appData_songs = songs_appData(songs)
    messages = get_messages()

    return render_template(
        "library.html",
        songs=songs,
        likes=likes,
        appData_songs=appData_songs,
        messages=messages,
    )


@app.route("/settings")
@check_login
def settings():
    admin: bool = is_admin(db, session["user_id"])
    if admin:
        return render_template(
            "settings.html",
            is_afetchMdmin=admin,
            is_upload=get_upload_state(db),
            is_signup=get_signup_state(db),
        )
    return render_template("settings.html", is_admin=admin)


@app.route("/a", methods=["POST"])
@check_login
def admin_commands():
    if is_admin(db, session["user_id"]):
        if "login-down" in request.form:
            set_signup_state(db, False)
        elif "login-up" in request.form:
            set_signup_state(db, True)
        elif "upload-down" in request.form:
            set_upload_state(db, False)
        elif "upload-up" in request.form:
            set_upload_state(db, True)

        return redirect("/settings")

    return json.dumps({"UNAUTHORIZED": True}), 401, {"ContentType": "application/json"}


@app.route("/messages", defaults={"song_id": None}, strict_slashes=False)
@app.route("/messages/<path:song_id>")
def get_messages(song_id=None):

    result = db.session.execute(SQL_FETCH_MESSAGES_ON_SONG, {"song_id": song_id})

    messages = result.fetchall()
    messages_list = [
        {
            "username": message.username,
            "song_id": message.song_id,
            "content": message.content,
        }
        for message in messages
    ]

    return messages_list


@app.route("/songs")
def get_songs(n: int | None = None, user_id: int | None = None):
    sql = """SELECT songs.*, song_metadata.*
        FROM songs
        LEFT JOIN song_metadata ON songs.id = song_metadata.song_id
        LEFT JOIN uploads u ON u.song_id = songs.id
        WHERE (:user_id IS NULL OR u.user_id = :user_id)
        ORDER BY (song_metadata.upvote - song_metadata.downvote) DESC
    """

    params = {"user_id": user_id}
    if n:
        sql += "\nLIMIT :limit"
        params["limit"] = n

    result = db.session.execute(text(sql), params)
    songs = result.fetchall()

    return songs


@app.route("/new")
def new():
    return render_template("new.html")


@app.route("/send/<path:song_id>", methods=["POST"])
def send(song_id):
    assert song_id == request.view_args["song_id"]
    song_id = bleach.clean(song_id)

    content = bleach.clean(request.form["content"])
    username = bleach.clean(session["username"])

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
        logging.info(log_user(username, "comment", song_id=song_id, content=content))

    except Exception as e:
        logging.error(f"Error executing SQL: {e}")

    result = db.session.execute(SQL_FETCH_MESSAGES_ON_SONG, {"song_id": song_id})
    messages = result.fetchall()
    # Dynamic comment loading -> music doesn't stop
    response = ""
    for message in messages:
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

    return response


@app.route("/login", methods=["POST"])
def login():

    username = bleach.clean(request.form["username"])
    password = bleach.clean(request.form["password"])

    sql = text("SELECT id, password FROM users WHERE username=:username")
    result = db.session.execute(sql, {"username": username})
    user = result.fetchone()

    if not user:
        return "User not found"

    # Add user_id to jwt token
    session["user_id"] = user[0]

    if check_password_hash(user[1], password):
        session["username"] = username
        logging.info(log_user(username, "login"))

    return redirect("/home")


@app.route("/logout", methods=["POST"])
def logout():
    logging.info(log_user(session["username"], "logout"))
    del session["username"]
    return redirect("/")


@app.route("/signup", methods=["POST"])
def signup():
    # Check if signup is currently closed
    if not get_signup_state(db):
        return "Signup closed by admin"

    username = bleach.clean(request.form["username"])
    _password = bleach.clean(request.form["password"])
    hash_pass = generate_password_hash(_password)

    # Check if username is taken
    sql = text("SELECT id, password FROM users WHERE username=:username")
    result = db.session.execute(sql, {"username": username})
    user = result.fetchone()

    if user:
        return "User already exists"

    sql = text(
        "INSERT INTO users (username, password, role) VALUES (:username, :password, 'user')"
    )

    db.session.execute(sql, {"username": username, "password": hash_pass})
    db.session.commit()

    logging.info(log_user(username, "signup"))

    return redirect("/")


# @app.route("/q", methods=["POST"])
# @check_login
# def query_info():
#
#    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


@app.route("/v", methods=["POST"])
@check_login
def register_vote():
    d = json.loads(request.data)
    # Validate the model
    validatedModel = VoteSchema(**d)

    # Check if request is for voting
    if validatedModel.type in VoteType:
        return process_voting(validatedModel)

    return json.dumps({"success": True}), 200, {"ContentType": "application/json"}


def process_voting(voteModel: VoteSchema) -> str:
    """Process voting (upvote/downvote)"""

    user_id = session["user_id"]
    target_id = voteModel.id
    vote_type = voteModel.type.value

    # Check if user's vote is already counted in song_metadata
    previous_vote = check_vote(db, voteModel)

    if not previous_vote:
        # Insert new vote
        sql = """
        -- Insert to likes
        INSERT INTO likes (user_id, target_id, target_type, vote_type)
        VALUES (:user_id, :target_id, :target_type, :vote_type);

        """
    elif previous_vote == voteModel.type:
        return (
            json.dumps({"message": "Same vote already registered"}),
            200,
            {"ContentType": "application/json"},
        )
    else:
        # Update existing vote
        sql = """
        -- Update likes
        UPDATE likes
        SET vote_type = :vote_type
        WHERE user_id = :user_id AND target_id = :target_id AND target_type = 'song';

        -- Adjust song_metadata for the old vote
        UPDATE song_metadata
        SET {prev_vote_type} = {prev_vote_type} - 1
        WHERE song_id = :target_id;

        """.format(
            prev_vote_type=previous_vote.value, vote_type=vote_type
        )

    sql += """
        -- Update song_metadata with the new vote
        UPDATE song_metadata
        SET {vote_type} = {vote_type} + 1
        WHERE song_id = :target_id;
        """.format(
        vote_type=vote_type
    )

    params = {
        "user_id": user_id,
        "target_id": target_id,
        "target_type": "song",
        "vote_type": vote_type,
    }

    try:
        db.session.execute(text(sql), params=params)
        db.session.commit()

        return json.dumps({"success": True}), 200, {"ContentType": "application/json"}
    except Exception as e:
        logging.error(e)
        return (
            json.dumps({"success": False, "error": str(e)}),
            500,
            {"ContentType": "application/json"},
        )


def allowed_file(filetype):
    return filetype in [ftype.value for ftype in AcceptedFileTypes]
    # mime = magic.Magic(mime=True)
    # file_type = mime.from_buffer(filename.read())
    # return file_type in [ftype.value for ftype in AcceptedFileTypes]


@app.route("/upload/", methods=["GET", "POST"])
@check_login
def upload_file():

    if request.method == "POST":
        if not get_upload_state(db):
            return "Upload closed by admin"

        # check if the post request has the file part
        if "file" not in request.files:
            flash("No file part")
            return redirect(request.url)

        file = request.files["file"]

        username = bleach.clean(session["username"])
        song_name = bleach.clean(request.form["songName"]).strip()
        song_description = bleach.clean(request.form.get("description", None))

        if not is_valid_song_name(song_name):
            return "Song name is not valid"

        # TODO don't accept empty name
        if song_description == "":
            song_description = None

        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)

        if file and allowed_file(file.content_type):
            filename = secure_filename(file.filename)
            path = app.config["UPLOAD_FOLDER"]

            # Check if filename already exists
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

            request.files["file"].save(os.path.join(path, filename))
            # TODO: -maybe useless redirect - Anyway its wrong
            return redirect(url_for("upload_file", filename=filename))
    return render_template("/upload.html")


@app.route("/stream/<int:music_id>")
@check_login
def stream_music(music_id):

    sql = text(
        """
        SELECT filepath, filename FROM uploads
        WHERE song_id = :song_id;
        """
    )
    result = db.session.execute(sql, {"song_id": music_id})
    filepath, filename = result.fetchone()

    # Add . if not docker -> dev env
    if not IS_DOCKER:
        filepath = os.getcwd()
        filename = "/data/" + filename

    if not filepath or not filename:

        err_msg = "Song not found " + filename
        logging.error(err_msg)

        return (
            json.dumps({"success": False, "error": err_msg}),
            500,
            {"ContentType": "application/json"},
        )

    logging.info(log_user(session["username"], "Streaming song", song_name=filename))

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
