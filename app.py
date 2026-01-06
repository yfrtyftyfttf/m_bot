from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "secret_key_123"  # أي شي، بس لا تتركه فاضي

# بيانات تسجيل الدخول (تجربة)
USERNAME = "admin"
PASSWORD = "1234"


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == USERNAME and password == PASSWORD:
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            return render_template("index.html", error="❌ معلومات الدخول غير صحيحة")

    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    return f"""
    <h1>👋 أهلاً {session['user']}</h1>
    <p>تم تسجيل الدخول بنجاح ✅</p>
    <a href="/logout">تسجيل الخروج</a>
    """


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
