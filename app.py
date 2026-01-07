from flask import Flask, request, jsonify, render_template, redirect, session
from flask_cors import CORS
import telebot
from telebot import types
import uuid

# ================== إعدادات ==================
TOKEN = "7465926974:AAHzPv067I1ser4kExbRt5Hzj9R3Ma5Xjik"
ADMIN_ID = "6695916631"
ADMIN_PIN = "8888"

PRICE_FOLLOWERS = 3.0   # لكل 1000
PRICE_LIKES = 1.0       # لكل 1000

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
app.secret_key = "SECRET_KEY_123"
CORS(app)

# ================== قواعد بيانات مؤقتة ==================
users = {}
orders = {}
admin_unlocked = False

# ================== دوال مساعدة ==================
def calc_price(service, qty):
    if service == "followers":
        return (qty / 1000) * PRICE_FOLLOWERS
    if service == "likes":
        return (qty / 1000) * PRICE_LIKES
    return 0

# ================== الموقع ==================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        for uid, user in users.items():
            if user["username"] == u and user["password"] == p:
                session["uid"] = uid
                return redirect("/dashboard")

        uid = str(uuid.uuid4())[:8]
        users[uid] = {
            "username": u,
            "password": p,
            "balance": 0.0,
            "telegram_id": None,
            "orders": []
        }
        session["uid"] = uid
        return redirect("/dashboard")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "uid" not in session:
        return redirect("/")
    u = users[session["uid"]]
    return render_template("dashboard.html", balance=u["balance"])


@app.route("/services", methods=["GET", "POST"])
def services():
    if "uid" not in session:
        return redirect("/")
    if request.method == "POST":
        service = request.form["service"]
        qty = int(request.form["qty"])
        uid = session["uid"]

        cost = calc_price(service, qty)
        if users[uid]["balance"] < cost:
            return "رصيد غير كافي"

        users[uid]["balance"] -= cost
        oid = str(uuid.uuid4())[:8]

        orders[oid] = {
            "user": uid,
            "service": service,
            "qty": qty,
            "cost": cost,
            "status": "pending"
        }

        users[uid]["orders"].append(oid)

        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ تم التنفيذ", callback_data=f"done_{oid}"),
            types.InlineKeyboardButton("❌ إلغاء + إعادة", callback_data=f"cancel_{oid}")
        )

        bot.send_message(
            ADMIN_ID,
            f"🚀 طلب جديد\n"
            f"🆔 {oid}\n"
            f"👤 {uid}\n"
            f"📦 {service}\n"
            f"🔢 {qty}\n"
            f"💵 {cost}$",
            reply_markup=markup
        )

        tg = users[uid]["telegram_id"]
        if tg:
            bot.send_message(tg, f"📦 تم إنشاء طلبك رقم {oid}")

        return redirect("/orders")

    return render_template("services.html")


@app.route("/orders")
def orders_page():
    if "uid" not in session:
        return redirect("/")
    uid = session["uid"]
    user_orders = []
    for oid in users[uid]["orders"]:
        o = orders[oid]
        user_orders.append({
            "id": oid,
            "service": o["service"],
            "qty": o["qty"],
            "status": o["status"]
        })
    return render_template("orders.html", orders=user_orders)


@app.route("/support", methods=["GET", "POST"])
def support():
    if "uid" not in session:
        return redirect("/")
    if request.method == "POST":
        msg = request.form["message"]
        uid = session["uid"]
        bot.send_message(ADMIN_ID, f"🎧 دعم فني\n👤 {uid}\n📩 {msg}")
        return "تم الإرسال"
    return render_template("support.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================== ربط تلغرام ==================
@bot.message_handler(commands=["start"])
def start(msg):
    bot.send_message(
        msg.chat.id,
        f"👋 أهلاً\n"
        f"ارسل ID حسابك من الموقع للربط"
    )

@bot.message_handler(func=lambda m: len(m.text) == 8)
def link_tg(msg):
    for uid in users:
        if uid == msg.text:
            users[uid]["telegram_id"] = msg.chat.id
            bot.send_message(msg.chat.id, "✅ تم ربط الحساب")
            return

# ================== لوحة الأدمن ==================
@bot.message_handler(commands=["admin"])
def admin(msg):
    bot.send_message(msg.chat.id, "🔐 اكتب رمز الأدمن")

@bot.message_handler(func=lambda m: m.text == ADMIN_PIN)
def unlock(msg):
    global admin_unlocked
    if msg.chat.id == ADMIN_ID:
        admin_unlocked = True
        bot.send_message(msg.chat.id, "✅ تم فتح لوحة الأدمن")

@bot.callback_query_handler(func=lambda c: True)
def callbacks(call):
    data = call.data.split("_")
    oid = data[1]

    if data[0] == "done":
        orders[oid]["status"] = "completed"
        uid = orders[oid]["user"]
        tg = users[uid]["telegram_id"]
        if tg:
            bot.send_message(tg, f"🎉 طلبك {oid} اكتمل")
        bot.edit_message_text("✅ تم التنفيذ", call.message.chat.id, call.message.message_id)

    if data[0] == "cancel":
        uid = orders[oid]["user"]
        users[uid]["balance"] += orders[oid]["cost"]
        orders[oid]["status"] = "cancelled"
        tg = users[uid]["telegram_id"]
        if tg:
            bot.send_message(tg, f"❌ تم إلغاء الطلب {oid} وإعادة الرصيد")
        bot.edit_message_text("❌ تم الإلغاء", call.message.chat.id, call.message.message_id)

# ================== تشغيل ==================
if __name__ == "__main__":
    from threading import Thread
    Thread(target=bot.infinity_polling).start()
    app.run(host="0.0.0.0", port=5000)
