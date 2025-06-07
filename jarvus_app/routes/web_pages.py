# app/routes/web_pages.py
from flask import Blueprint, render_template, session, url_for, redirect
from flask_login import login_required, current_user

web = Blueprint("web", __name__)

@web.route("/")
def landing():
    return render_template("landing.html")

@web.route("/profile")
@login_required
def profile():
    return render_template("profile.html")

@web.route("/chatbot")
@login_required
def chatbot():
    return render_template("chatbot.html")

@web.route("/flow-builder")
@login_required
def flow_builder():
    if "user" not in session:
        return redirect(url_for("auth.signin"))
    
    return render_template("flow_builder.html", session=session)

@web.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("auth.signin"))
    
    return render_template("dashboard.html", session=session)