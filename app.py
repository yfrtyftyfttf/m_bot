from flask import Flask, render_template, request, redirect, session
from flask_cors import CORS
import telebot
from telebot import types
import uuid

# ===== الإعدادات =====
TOKEN = "7465926974:AAHzPv067I1ser4kExbRt5Hzj9R3Ma5Xjik"
ADMIN_ID = "6695916631"
ADMIN_PIN = "11110000"

SERVICE_PRICES = {
    "Followers": 3,
    "Likes": 1,
    "Views": 3,
    "Comments": 3
}

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
app.secret_key = "secret123"
CORS(app)

users = {}
orders = {}
admin_unlocked = False

# ===== الموقع =====

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        if u not in users:
            users[u] = {"password": p, "balance": 0, "orders": []}

        if users[u]["password"] == p:
            session["user"] = u
            return redirect("/dashboard")

    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template(
        "dashboard.html",
        user=session["user"],
        balance=users[session["user"]]["balance"]
    )


@app.route("/services")
def services():
    if "user" not in session:
        return redirect("/")
    return render_template("services.html")


@app.route("/create_order", methods=["POST"])
def create_order():
    if "user" not in session:
        return redirect("/")

    service = request.form["service"]
    qty = int(request.form["qty"])
    link = request.form["link"]

    price = SERVICE_PRICES.get(service, 3)
    cost = round((qty / 1000) * price, 2)

    user = session["user"]
    if users[user]["balance"] < cost:
        return "رصيد غير كافي"

    users[user]["balance"] -= cost
    order_id = str(uuid.uuid4())[:8]

    orders[order_id] = {
        "user": user,
        "service": service,
        "qty": qty,
        "link": link,
        "cost": cost,
        "status": "pending"
    }

    users[user]["orders"].append(order_id)

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🔄 قيد التنفيذ", callback_data=f"ord_proc_{order_id}"),
        types.InlineKeyboardButton("✅ تم التنفيذ", callback_data=f"ord_done_{order_id}")
    )

    bot.send_message(
        ADMIN_ID,
        f"🚀 طلب جديد\n"
        f"🆔 {order_id}\n"
        f"👤 {user}\n"
        f"📦 {service}\n"
        f"🔢 {qty}\n"
        f"💰 {cost}$\n"
        f"🔗 {link}",
        reply_markup=markup
    )

    return redirect("/dashboard")


@app.route("/support", methods=["GET", "POST"])
def support():
    if request.method == "POST":
        bot.send_message(
            ADMIN_ID,
            f"🆘 دعم فني\n"
            f"👤 {request.form['username']}\n"
            f"🆔 {request.form['order_id']}\n"
            f"{request.form['message']}"
        )
        return redirect("/dashboard")

    return render_template("support.html")


# ===== البوت =====

@bot.message_handler(commands=["start"])
def start_bot(message):
    if str(message.from_user.id) != ADMIN_ID:
        return
    bot.send_message(message.chat.id, "🔐 أرسل رمز الدخول")
    bot.register_next_step_handler(message, check_pin)


def check_pin(message):
    global admin_unlocked
    if message.text == ADMIN_PIN:
        admin_unlocked = True
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("👑 لوحة الأدمن", "🔒 قفل")
        bot.send_message(message.chat.id, "✅ تم الفتح", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "❌ رمز خطأ")


@bot.message_handler(func=lambda m: m.text == "👑 لوحة الأدمن")
def admin_panel(message):
    if not admin_unlocked:
        return
    bot.send_message(message.chat.id, "🆔 أرسل رقم الطلب:")
    bot.register_next_step_handler(message, get_order)


def get_order(message):
    oid = message.text
    if oid not in orders:
        bot.send_message(message.chat.id, "❌ غير موجود")
        return

    o = orders[oid]
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("❌ إلغاء", callback_data=f"cancel_{oid}"),
        types.InlineKeyboardButton("💰 إعادة رصيد", callback_data=f"refund_{oid}"),
        types.InlineKeyboardButton("✅ تم", callback_data=f"done_{oid}")
    )

    bot.send_message(
        message.chat.id,
        f"🆔 {oid}\n📦 {o['service']}\n🔢 {o['qty']}\n💰 {o['cost']}$\n🔄 {o['status']}",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda c: True)
def actions(call):
    if not admin_unlocked:
        return

    action, oid = call.data.split("_")
    o = orders[oid]
    user = o["user"]

    if action == "cancel":
        o["status"] = "cancelled"
    elif action == "refund":
        users[user]["balance"] += o["cost"]
        o["status"] = "refunded"
    elif action == "done":
        o["status"] = "completed"

    bot.edit_message_text("✅ تم", call.message.chat.id, call.message.message_id)


if __name__ == "__main__":
    from threading import Thread
    Thread(target=bot.infinity_polling).start()
    app.run(host="0.0.0.0", port=5000)
