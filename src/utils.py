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
