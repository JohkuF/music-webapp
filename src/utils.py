import os
import json
import logging
import functools
from sqlalchemy import text
from flask import session, redirect

from .schemas import VoteSchema
from .myenums import VoteType


def setup_login(IS_DOCKER):
    log_path = "/logs/music-webapp.log" if IS_DOCKER else "logi.log"
    file_handler = logging.FileHandler(log_path)

    logging.basicConfig(
        level=logging.DEBUG,
        format=json.dumps(
            {
                "timestamp": "%(asctime)s",
                "level": "%(levelname)s",
                "message": "%(message)s",
            }
        ),
        handlers=[logging.StreamHandler(), file_handler],
    )


def check_login(func):
    """
    To check if the user is logged in or not. Returns to login page if not
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Check if user is logged in
        if "username" not in session:
            return redirect("/")
        return func(*args, **kwargs)

    return wrapper


def find_new_filename(path: str, filename: str) -> str:
    filename, end = os.path.splitext(filename)
    # Loop to 100 to avoid for ever loops
    for i in range(100):
        new_filename = filename + "_" + str(i) + end
        new_filepath = os.path.join(path, new_filename)
        if not os.path.exists(new_filepath):
            return new_filename
    raise FileExistsError("Filename already exists")


def is_admin(db, user_id: int) -> bool:
    """
    Check if user is admin
    """
    sql = text("SELECT users.role FROM users WHERE users.id = :user_id;")
    result = db.session.execute(sql, {"user_id": user_id}).fetchone()

    if result[0] == "admin":
        return True
    return False


def _set_state(db, status: bool, name: str):
    sql = text("UPDATE states SET allow_signup = :status WHERE state_name = :name;")
    db.session.execute(sql, {"status": status, "name": name})
    db.session.commit()


def _get_state(db, name: str):
    sql = text("SELECT * FROM states WHERE state_name = :name")
    result = db.session.execute(sql, {"name": name}).fetchone()
    return result[2]


def set_signup_state(db, status: bool):
    """
    sets the signup state on or off
    """
    _set_state(db, status, "signup")
    return None


def set_upload_state(db, status: bool):
    """
    sets the upload state on or off
    """
    _set_state(db, status, "upload")


def get_signup_state(db) -> bool:
    return _get_state(db, "signup")


def get_upload_state(db) -> bool:
    return _get_state(db, "upload")


def check_vote(db, voteModel: VoteSchema) -> VoteType | bool:
    """Check users logged vote"""

    # Check if user has already voted similarly
    sql = text(
        """SELECT vote_type FROM likes
        WHERE user_id = :user_id
        AND target_id = :song_id
        AND target_type = :target_type;"""
    )

    res = db.session.execute(
        sql,
        {
            "user_id": session["user_id"],
            "song_id": voteModel.id,
            "target_type": "song",  # TODO: add target type check
        },
    ).fetchone()

    if not res:
        return False
    try:
        return VoteType(res[0])
    except:
        # TODO: log error
        return VoteType.NONEVOTE


def get_user_likes(db, user_id: int) -> list:
    """Gets user likes on spesic songs to be shown on the frontend"""
    sql = (
        "SELECT target_id, target_type, vote_type FROM likes WHERE user_id = :user_id;"
    )
    result = db.session.execute(text(sql), params={"user_id": user_id})
    likes = result.fetchall()
    likes_list = [
        {
            "target_id": like.target_id,
            "target_type": like.target_type,
            "vote_type": like.vote_type,
        }
        for like in likes
    ]
    return likes_list


def log_user(username, message, **kwargs):
    """Helper for logging"""
    return {"username": username, "message": message, **kwargs}


def is_valid_song_name(name: str) -> bool:
    """Rules for invalid filenames"""
    if name.strip() == "":
        return False

    return True


def songs_appData(songs) -> dict:
    """Parse songs sql request to be put into appData"""
    return [{"id": song.song_id, "song_name": song.song_name} for song in songs]
