import os
import bleach
import json
import logging
from sqlalchemy import text
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask import Flask, Response, send_file
from flask import render_template, request, session, redirect, flash, url_for, jsonify
from werkzeug.security import check_password_hash, generate_password_hash

from .schemas import VoteSchema
from .myenums import VoteType, AcceptedFileTypes
from .utils import (
    find_new_filename,
    set_signup_state,
    set_upload_state,
    get_signup_state,
    get_upload_state,
    is_song_deleted,
    get_user_likes,
    is_valid_name,
    setup_logging,
    songs_appData,
    check_login,
    check_vote,
    is_admin,
    log_user,
)
from .sql_commands import (
    SQL_VOTE_UPDATE_EXISTING_VOTE,
    SQL_VOTE_UPDATE_SONG_METADATA,
    SQL_FETCH_MESSAGES_ON_SONG,
    SQL_CHECK_USERNAME_EXISTS,
    SQL_VOTE_INSERT_NEW_VOTE,
    SQL_UPDATE_SONG_METADATA,
    SQL_GET_SONG_FILEPATH,
    SQL_GET_SONGS_DEFAULT,
    SQL_CHANGE_PUBLICITY,
    SQL_CREATE_NEW_USER,
    SQL_UPDATE_PASSWORD,
    SQL_DELETE_ACCOUNT,
    SQL_SEND_MESSAGE,
    SQL_DELETE_SONG,
    SQL_FILE_UPLOAD,
    SQL_USER_COUNT,
    SQL_LOGIN,
)

app = Flask(__name__, template_folder="templates", static_folder="static")
log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

load_dotenv(".env")
app.secret_key = os.getenv("SECRET_KEY")

POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_USER = os.getenv("POSTGRES_USER")
IS_DOCKER = os.getenv("IS_DOCKER", False)

setup_logging(IS_DOCKER)

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
    songs = get_songs(13, is_public=True)
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
    songs = get_songs(user_id=session["user_id"], is_public=None)
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
            is_admin=admin,
            is_upload=get_upload_state(db),
            is_signup=get_signup_state(db),
        )
    return render_template("settings.html", is_admin=admin)


@app.route("/a", methods=["POST", "DELETE"])
@check_login
def action_commands():
    """For handling different actions"""

    # ---------- SONG DELETION ----------
    if request.method == "DELETE" and "delete_song" in request.args:
        try:
            song_id = int(bleach.clean(request.args.get("delete_song")))
            delete_song_by_id(song_id)
        except Exception as e:
            logging.error(log_user(session["username"], e))
            return jsonify("Something went wrong", 500)

    # ---------- ADMIN CONTROLS ----------
    if request.form.get("request_type") == "admin-command" and is_admin(
        db, session["user_id"]
    ):
        if "login-down" in request.form:
            set_signup_state(db, False)
        elif "login-up" in request.form:
            set_signup_state(db, True)
        elif "upload-down" in request.form:
            set_upload_state(db, False)
        elif "upload-up" in request.form:
            set_upload_state(db, True)

        return redirect("/settings")

    # ---------- PASSWORD RESET ----------
    elif request.form.get("request_type") == "password_reset":
        try:
            _new_password = bleach.clean(request.form["password"])
            # output not used because flask renders json if used
            update_user_password(session["user_id"], session["username"], _new_password)
            flash("Password updated", "success")
            logging.info(log_user(session["username"], "Changed password"))
            return jsonify("Password changed succesfully", 200)
        except Exception as e:
            logging.error(log_user(session["username"], e))
        return redirect("/settings")

    # ---------- ACCOUNT DELETION ----------
    elif request.form.get("request_type") == "account_delete":
        try:
            return delete_user_account(session["user_id"], session["username"])
        except Exception as e:
            logging.error(log_user(session["username"], e))
        return redirect("/settings")

    # ---------- SONG PUBLIC/PRIVATE CHANGE ----------
    elif is_public := request.form.get("is_public_song"):
        is_public = {"true": True, "false": False}.get(is_public, None)
        assert is_public is not None
        try:
            return change_song_publicity(
                request.args["song_id"], session["user_id"], is_public
            )
        except Exception as e:
            logging.error(log_user(session["username"], e))
            return jsonify("Something went wrong", 500)
    return redirect("/setting")


# ********** ACTION HELPER FUNCTIONS **********
def delete_song_by_id(song_id) -> Response:
    assert isinstance(song_id, int)
    sql = SQL_DELETE_SONG
    db.session.execute(sql, {"user_id": session["user_id"], "song_id": song_id})
    db.session.commit()
    logging.info(log_user(session["username"], "Deleted song %s" % song_id))
    return jsonify("Song deleted succesfully", 200)


def update_user_password(user_id, username, _new_password) -> Response:
    hashed_password = generate_password_hash(_new_password)
    sql = SQL_UPDATE_PASSWORD
    db.session.execute(
        sql,
        {
            "hashed_password": hashed_password,
            "username": username,
            "user_id": user_id,
        },
    )
    db.session.commit()
    return jsonify("Password changed succesfully", 200)


def delete_user_account(user_id: int, username: str) -> Response:
    sql = SQL_DELETE_ACCOUNT
    db.session.execute(sql, {"username": username, "user_id": user_id})
    db.session.commit()
    logging.info(log_user(session["username"], "User deleted"))
    del session["username"]
    return redirect("/")


def change_song_publicity(song_id, user_id, is_public) -> Response:
    sql = SQL_CHANGE_PUBLICITY
    db.session.execute(
        sql,
        {
            "is_public": is_public,
            "song_id": song_id,
            "user_id": user_id,
        },
    )
    db.session.commit()
    logging.info(
        log_user(
            session["username"],
            "Changed song publicity to %s" % is_public,
            song_id=song_id,
            is_public=is_public,
        )
    )
    return jsonify("Form processed successfully", 200)


@app.route("/messages", defaults={"song_id": None}, strict_slashes=False)
@app.route("/messages/<path:song_id>")
@check_login
def get_messages(song_id=None):
    result = db.session.execute(SQL_FETCH_MESSAGES_ON_SONG, {"song_id": song_id})
    messages = result.fetchall()
    return [
        {
            "username": message.username,
            "song_id": message.song_id,
            "content": message.content,
            "timestamp": message.upload_time,
        }
        for message in messages
    ]


def get_songs(
    n: int | None = None, is_public: bool | None = True, user_id: int | None = None
):
    sql = SQL_GET_SONGS_DEFAULT
    params = {"user_id": user_id, "is_public": is_public}
    if n:
        sql += "\nLIMIT :limit"
        params["limit"] = n
    result = db.session.execute(text(sql), params)
    songs = result.fetchall()
    return songs


@app.route("/send/<path:song_id>", methods=["POST"])
@check_login
def send(song_id):
    """Comment on a song route"""
    assert song_id == request.view_args["song_id"]
    song_id = bleach.clean(song_id)
    content = bleach.clean(request.form["content"])
    username = bleach.clean(session["username"])

    sql = SQL_SEND_MESSAGE
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
        timestamp = bleach.clean(
            message.upload_time.strftime("%a, %d %b %Y %H:%M:%S GMT")
        )
        response += f"""
            <div class="card mb-4" id="messages-{song_id}">
              <div class="card-body">
                <p>{content}</p>
                <div class="d-flex justify-content-between">
                    <p class="small mb-0 ms-2">{username}</p>
                    <p class="small mb-0 ms-2 text-secondary">{timestamp}</p>
                </div>
              </div>
            </div>
        """
    return response


@app.route("/login", methods=["POST"])
def login():
    username = bleach.clean(request.form["username"])
    password = bleach.clean(request.form["password"])
    sql = SQL_LOGIN
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
@check_login
def logout():
    logging.info(log_user(session["username"], "logout"))
    del session["username"]
    return redirect("/")


@app.route("/signup", methods=["POST"])
def signup():
    try:
        # Check if signup is currently closed
        if not get_signup_state(db):
            return "Signup closed by admin"

        username = bleach.clean(request.form["username"]).strip()
        if not is_valid_name(username):
            flash("Username is not valid")
            return redirect("/")

        _password = bleach.clean(request.form["password"])
        hash_pass = generate_password_hash(_password)

        # Check if first user - for admin priv
        result = db.session.execute(SQL_USER_COUNT)
        row_count = result.fetchone()[0]
        role = "admin" if row_count == 0 else "user"

        # Check if username is taken
        sql = SQL_CHECK_USERNAME_EXISTS
        result = db.session.execute(sql, {"username": username})
        user = result.fetchone()

        if user:
            return "User already exists"

        sql = SQL_CREATE_NEW_USER
        db.session.execute(
            sql, {"username": username, "password": hash_pass, "role": role}
        )
        db.session.commit()
        logging.info(log_user(username, "signup"))

    except Exception as e:
        logging.error(log_user(session["username"], e))
        return jsonify("Something went wrong", 500)
    return redirect("/")


@app.route("/v", methods=["POST"])
@check_login
def register_vote():
    """Route for votes"""
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
        sql = SQL_VOTE_INSERT_NEW_VOTE
    elif previous_vote == voteModel.type:
        return (
            json.dumps({"message": "Same vote already registered"}),
            200,
            {"ContentType": "application/json"},
        )
    else:
        # Update existing vote
        sql = SQL_VOTE_UPDATE_EXISTING_VOTE.format(
            prev_vote_type=previous_vote.value, vote_type=vote_type
        )

    sql += SQL_VOTE_UPDATE_SONG_METADATA.format(vote_type=vote_type)

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


@app.route("/upload/", methods=["GET", "POST"])
@check_login
def upload_file():

    if request.method == "POST":
        if not get_upload_state(db):
            return "Upload closed by admin"

        # check if the post request has the file part
        if "file" not in request.files:
            # TODO: flash not implemented in the frontend
            flash("No file part")
            return redirect(request.url)

        file = request.files["file"]
        username = bleach.clean(session["username"])
        song_name = bleach.clean(request.form["songName"]).strip()
        song_description = bleach.clean(request.form.get("description", None))

        _is_public = bleach.clean(request.form.get("is_public", ""))
        is_public = _is_public == "on"

        if not is_valid_name(song_name):
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

            # TODO:TODO:TODO add is_public to the query
            db.session.execute(
                SQL_FILE_UPLOAD,
                {
                    "username": username,
                    "song_name": song_name,
                    "song_description": song_description,
                    "is_public": is_public,
                    "filepath": path,
                    "filename": filename,
                },
            )
            db.session.commit()

            request.files["file"].save(os.path.join(path, filename))
            return redirect(url_for("upload_file", filename=filename))
    return render_template("/upload.html")


@app.route("/stream/<int:music_id>")
@check_login
def stream_music(music_id):

    # Check if song is deleted
    if is_song_deleted(db, music_id):
        return jsonify("Song is deleted")

    sql = SQL_GET_SONG_FILEPATH
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
    sql = SQL_UPDATE_SONG_METADATA
    db.session.execute(sql, {"song_id": music_id})
    db.session.commit()
    return send_file(filepath + filename, mimetype="audio/mp3")


if __name__ == "__main__":
    app.debug = True

    app.run(port=8080)
