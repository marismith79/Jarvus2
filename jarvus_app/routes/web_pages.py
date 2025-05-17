# app/routes/web_pages.py
from flask import Blueprint, render_template, session, redirect, url_for

web = Blueprint("web", __name__)

@web.route("/")
def landing():
    return render_template("landing.html", session=session)

@web.route("/profile")
def profile():
    if "user" not in session:
        return redirect(url_for("auth.signin"))
    
    # Extract user data to pass to template
    user_data = session["user"]
    return render_template("profile.html", user=user_data)
