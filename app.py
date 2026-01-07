from flask import Flask, render_template, redirect, url_for, request
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = "secret-key-123"

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# مستخدم تجريبي
class User(UserMixin):
    def __init__(self, id):
        self.id = id

users = {
    "admin": {"password": "1234"}
}

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# الصفحة الرئيسية
@app.route("/")
def home():
    return render_template("index.html")

# تسجيل الدخول
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username]["password"] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for("dashboard"))

        return render_template("login.html", error="بيانات الدخول غير صحيحة")

    return render_template("login.html")

# لوحة التحكم
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user.id)

# تسجيل الخروج
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
