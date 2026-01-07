from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import uuid

app = Flask(__name__)
app.secret_key = "SUPER_SECRET_KEY"

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# ===== بيانات وهمية =====
USERS = {
    "admin": {"password": "1234", "balance": 100}
}

ORDERS = []

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# ===== Routes =====

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        if u in USERS and USERS[u]["password"] == p:
            login_user(User(u))
            return redirect("/dashboard")
    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", balance=USERS[current_user.id]["balance"])

@app.route("/services")
@login_required
def services():
    return render_template("services.html")

@app.route("/order", methods=["POST"])
@login_required
def order():
    service = request.form["service"]
    qty = int(request.form["qty"])

    prices = {
        "followers": 3,
        "likes": 1
    }

    cost = (qty / 1000) * prices[service]

    if USERS[current_user.id]["balance"] >= cost:
        USERS[current_user.id]["balance"] -= cost
        order_id = str(uuid.uuid4())[:8]
        ORDERS.append({
            "id": order_id,
            "service": service,
            "qty": qty,
            "status": "قيد التنفيذ"
        })
    return redirect("/orders")

@app.route("/orders")
@login_required
def orders():
    return render_template("orders.html", orders=ORDERS)

@app.route("/support")
@login_required
def support():
    return render_template("support.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
