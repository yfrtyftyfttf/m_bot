from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

# بيانات تجريبية (بعدها نربطها بالبوت)
USER = "admin"
PASSWORD = "1234"

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == USER and password == PASSWORD:
            return redirect(url_for("dashboard"))
        else:
            return render_template("index.html", error="❌ بيانات الدخول غير صحيحة")

    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return "<h1>✅ تم تسجيل الدخول بنجاح</h1>"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
