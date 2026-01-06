from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

# بيانات تسجيل الدخول (اختبار)
USER = "m"
PASSWORD = "m"

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        print(username, password)  # للمراجعة في اللوق

        if username == USER and password == PASSWORD:
            return redirect("/dashboard")
        else:
            return render_template("index.html", error="❌ خطأ في اسم المستخدم أو كلمة المرور")

    return render_template("index.html")


@app.route("/dashboard", methods=["GET"])
def dashboard():
    return "<h1>✅ تم تسجيل الدخول بنجاح</h1>"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
