# app/routes/web_pages.py
from flask import Blueprint, render_template
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
    return render_template("flow_builder.html")

@web.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")