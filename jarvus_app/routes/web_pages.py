# app/routes/web_pages.py
from flask import Blueprint, render_template, session, redirect, url_for

web = Blueprint("web", __name__)

@web.route("/")
def landing():
    return render_template("landing.html")

@web.route("/home")
def home():
    if "user" not in session:
        return redirect(url_for("auth.signin"))
    return render_template("home.html", user=session["user"])

@web.route("/profile")
def profile():
    if "user" not in session:
        return redirect(url_for("auth.signin"))
    return render_template("profile.html", user=session["user"])
