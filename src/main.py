import os

from flask import Flask
from sqlalchemy import text
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask import render_template, request, session, redirect, flash, url_for, jsonify
from werkzeug.security import check_password_hash, generate_password_hash

from utils import check_login
from sql_commands import (
    SQL_FILE_UPLOAD,
    SQL_SEND_MESSAGE_GENERAL,
    SQL_FETCH_MESSAGES_GENERAL,
)


app = Flask(__name__, template_folder="templates")

load_dotenv(".env")
app.secret_key = os.getenv("SECRET_KEY")

POSTGRES_USER_PASSWORD = os.getenv("POSTGRES_USER_PASSWORD")
POSTGRES_USER = os.getenv("POSTGRES_USER")

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_USER_PASSWORD}@localhost:8123/app"
)

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
    songs = get_songs()
    print(songs)
    return render_template("home.html", songs=songs)


@app.route("/chat")
def chat():
    result = db.session.execute(SQL_FETCH_MESSAGES_GENERAL)
    messages = result.fetchall()
    print(messages)

    return render_template("chat.html", messages=messages, count=len(messages))


@app.route("/messages/<path:song_id>")
def messages(song_id):
    assert song_id == request.view_args["song_id"]
    print(request.path)
    print("\n\n\nID", song_id)
    sql = text(
        """SELECT users.username, messages.content
        FROM messages
        JOIN users ON messages.user_id = users.id
        WHERE messages.song_id = {};""".format(
            song_id
        )
    )

    result = db.session.execute(sql)
    messages = result.fetchall()
    messages_list = [{"username": row[0], "content": row[1]} for row in messages]

    return jsonify(messages_list)


@app.route("/songs")
def get_songs():
    sql = text("SELECT * FROM songs;")
    result = db.session.execute(sql)
    songs = result.fetchall()
    return songs


@app.route("/new")
def new():
    return render_template("new.html")


@app.route("/send/<path:song_id>", methods=["POST"])
def send(song_id):
    assert song_id == request.view_args["song_id"]
    # print(request.form)
    content = request.form["content"]
    username = session["username"]
    if song_id == 0 or song_id == None:
        SQL_SEND_MESSAGE_GENERAL
        db.session.execute(
            SQL_SEND_MESSAGE_GENERAL,
            {"username": session["username"], "content": content},
        )
        db.session.commit()
        return redirect("/chat")

    print("SONGPATH", song_id, content)

    sql = text(
        """
    INSERT INTO messages (song_id, user_id, upload_time, content)
    SELECT :song_id, id, NOW(), :content FROM users WHERE username = :username;
    """
    )

    db.session.execute(
        sql, {"username": username, "song_id": song_id, "content": content}
    )
    db.session.commit()
    print("DATA EXECUTED")
    # response_data = {"success": True, "message": "Data inserted successfully."}
    # return jsonify(response_data)

    # TODO: find better solution
    response = f"""
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

    # Experimental fetch for all the messages again

    sql = text(
        """SELECT users.username, messages.content
        FROM messages
        JOIN users ON messages.user_id = users.id
        WHERE messages.song_id = {};""".format(
            song_id
        )
    )

    result = db.session.execute(sql)
    messages = result.fetchall()

    # TODO: compine /messages and this fuggly thing to one function
    response = ""
    for message in reversed(messages):
        print(message)
        response += f"""
            <div class="card mb-4" id="messages-{song_id}">
              <div class="card-body">
                <p>{message.content}</p>
                <div class="d-flex justify-content-between">
                  <div class="d-flex flex-row align-items-center">
                    <p class="small mb-0 ms-2">{message.username}</p>
                  </div>
                </div>
              </div>
            </div>
        """

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


def allowed_file(filename):
    # TODO: Add allowed file types.
    # return '.' in filename and \
    #       filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    return True


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
        print(request.form)
        # TODO: use pydantic
        username = session["username"]
        song_name = request.form["songName"]
        song_description = request.form.get("description", None)
        if song_description == "":
            song_description = None

        if file.filename == "":
            flash("No selected file")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            db.session.execute(
                SQL_FILE_UPLOAD,
                {
                    "username": username,
                    "song_name": song_name,
                    "song_description": song_description,
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
