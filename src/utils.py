import os
import functools
from sqlalchemy import text
from flask import session, redirect

from .schemas import VoteSchema
from .myenums import VoteType


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
    # TODO use enum
    if result[0] == "admin":
        return True
    return False


def set_signup_state(db, status: bool):
    """
    sets the signup state on or off
    """
    sql = text("UPDATE signup_state SET allow_signup = :status1 WHERE id = 1;")
    db.session.execute(sql, {"status1": status})
    db.session.commit()

    return None


def get_signup_state(db) -> bool:
    sql = text("SELECT * FROM signup_state WHERE id = 1;")
    result = db.session.execute(sql).fetchone()
    print(result[1])
    return result[1]


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

    print("user has voted prev", res)

    if not res:
        return False
    try:
        return VoteType(res[0])
    except:
        # TODO: log error
        return VoteType.NONEVOTE
