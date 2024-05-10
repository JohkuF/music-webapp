import os
import functools
from flask import session, redirect


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
