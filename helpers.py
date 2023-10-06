import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps
from cs50 import SQL

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
            ("%", "~p"), ("#", "~h"), ("/", "~s"), ('"', "''"),]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"


def isint(num):
    try:
        int(num)
        return True
    except ValueError:
        return False


def isfloat(num):
    try:
        float(num)
        return True
    except ValueError:
        return False


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def update_store_balance(amount_change, user):
    # Retrieve current store_balance of user from database
    store_balance = db.execute(
        "SELECT store_balance FROM users WHERE user_id=?", user
    )
    
    # Calculate new store balance
    new_store_balance = store_balance[0]["store_balance"] + amount_change
    
    # Update store_balance of user to database
    db.execute(
        "UPDATE users SET store_balance=? WHERE user_id=?", new_store_balance, user
    )
    
    # Update store_balance of user in session
    session["store_bal"] = new_store_balance
    return True


def log_into_trans_seller(datetime, type, amount, user, remark):
    db.execute(
        "INSERT INTO transactions_seller (datetime, type, amount, user_id, remark) \
            VALUES (?, ?, ?, ?, ?)",
        datetime, type, amount, user, remark,
    )
    return True

