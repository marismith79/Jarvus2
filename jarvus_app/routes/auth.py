from flask import Blueprint, render_template, request, redirect, url_for, session

auth = Blueprint("auth", __name__)

@auth.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # TODO: Replace with real authentication
        if username == "admin" and password == "secure":
            session["user"] = username
            return redirect(url_for("web.home"))

        return render_template("signin.html", error="Invalid credentials.")

    return render_template("signin.html")

@auth.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("auth.signin"))
