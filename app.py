from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import uuid

app = Flask(__name__)
app.secret_key = "SECRET_KEY_123"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"


# ===================== MODELS =====================

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    balance = db.Column(db.Float, default=0.0)


class Order(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.Integer)
    service = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
    status = db.Column(db.String(50), default="قيد التنفيذ")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ===================== ROUTES =====================

@app.route("/", methods=["GET"])
def home():
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = User(
            username=request.form["username"],
            password=request.form["password"]
        )
        db.session.add(user)
        db.session.commit()
        flash("تم إنشاء الحساب بنجاح")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            username=request.form["username"],
            password=request.form["password"]
        ).first()

        if user:
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("بيانات الدخول غير صحيحة")

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/new_order", methods=["GET", "POST"])
@login_required
def new_order():
    if request.method == "POST":
        service = request.form["service"]
        quantity = int(request.form["quantity"])

        price = 0
        if service == "followers":
            price = (quantity / 1000) * 3
        if service == "likes":
            price = (quantity / 1000) * 1

        if current_user.balance < price:
            flash("رصيدك غير كافي")
            return redirect(url_for("new_order"))

        current_user.balance -= price

        order = Order(
            id=str(uuid.uuid4())[:8],
            user_id=current_user.id,
            service=service,
            quantity=quantity,
            price=price
        )

        db.session.add(order)
        db.session.commit()

        flash("تم إرسال الطلب بنجاح")
        return redirect(url_for("orders"))

    return render_template("new_order.html")


@app.route("/orders")
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).all()
    return render_template("orders.html", orders=user_orders)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=10000)
