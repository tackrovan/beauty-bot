#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ربات فروش محصولات آرایشی تلگرام - با پنل ادمین
"""

import logging
import json
import os
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ==================== تنظیمات ====================
BOT_TOKEN = "8887060569:AAFQ9Cl51B_2TxSjJbPIRGx6iCxBZvxW85g"
ADMIN_ID = 88831711

# ==================== فایل ذخیره محصولات ====================
PRODUCTS_FILE = "products.json"

def load_products():
    """بارگذاری محصولات از فایل"""
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # محصولات پیش‌فرض
    default = {
        "p1": {
            "name": "کرم مرطوب‌کننده",
            "price": 150000,
            "description": "کرم مرطوب‌کننده قوی مناسب برای انواع پوست\n✅ حاوی ویتامین E\n✅ ضد آفتاب SPF30\n✅ مناسب پوست حساس",
            "emoji": "✨"
        },
        "p2": {
            "name": "رژ لب ماندگار",
            "price": 85000,
            "description": "رژ لب با ماندگاری ۱۲ ساعته\n✅ رنگ‌های متنوع\n✅ مرطوب‌کننده\n✅ بدون پاک‌شدن با آب",
            "emoji": "💄"
        },
        "p3": {
            "name": "ریمل حجم‌دهنده",
            "price": 120000,
            "description": "ریمل ضد آب با افکت حجم‌دهنده\n✅ ضد آب\n✅ بدون خش\n✅ فرمول تقویت‌کننده مژه",
            "emoji": "👁️"
        },
        "p4": {
            "name": "سرم ویتامین C",
            "price": 280000,
            "description": "سرم روشن‌کننده پوست با ویتامین C\n✅ ضد لک\n✅ ضد پیری\n✅ روشن‌کننده طبیعی",
            "emoji": "🌟"
        },
        "p5": {
            "name": "پودر کانسیلر",
            "price": 95000,
            "description": "کانسیلر فول‌کاور با ماندگاری بالا\n✅ پوشش کامل\n✅ سبک روی پوست\n✅ مناسب انواع رنگ پوست",
            "emoji": "💎"
        },
    }
    save_products(default)
    return default

def save_products(products):
    """ذخیره محصولات در فایل"""
    with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

# ==================== متغیرهای سراسری ====================
user_carts = {}
user_orders = {}

# ==================== مراحل گفتگو ====================
WAITING_ADDRESS, WAITING_PHONE, WAITING_NAME = range(3)
ADMIN_ADD_NAME, ADMIN_ADD_PRICE, ADMIN_ADD_DESC, ADMIN_ADD_EMOJI = range(10, 14)
ADMIN_EDIT_NAME, ADMIN_EDIT_PRICE, ADMIN_EDIT_DESC = range(20, 23)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ==================== توابع کمکی ====================

def format_price(price: int) -> str:
    return f"{price:,} تومان"

def get_cart(user_id: int) -> dict:
    if user_id not in user_carts:
        user_carts[user_id] = {}
    return user_carts[user_id]

def cart_total(user_id: int) -> int:
    cart = get_cart(user_id)
    PRODUCTS = load_products()
    total = 0
    for product_id, qty in cart.items():
        if product_id in PRODUCTS:
            total += PRODUCTS[product_id]["price"] * qty
    return total

def cart_summary(user_id: int) -> str:
    cart = get_cart(user_id)
    PRODUCTS = load_products()
    if not cart:
        return "سبد خرید شما خالی است 🛒"
    text = "🛒 *سبد خرید شما:*\n\n"
    for product_id, qty in cart.items():
        if product_id in PRODUCTS:
            p = PRODUCTS[product_id]
            subtotal = p["price"] * qty
            text += f"{p['emoji']} {p['name']}\n"
            text += f"   تعداد: {qty} × {format_price(p['price'])} = {format_price(subtotal)}\n\n"
    text += f"─────────────────\n"
    text += f"💰 *جمع کل: {format_price(cart_total(user_id))}*"
    return text

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# ==================== هندلرهای کاربر ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [KeyboardButton("🛍️ مشاهده محصولات")],
        [KeyboardButton("🛒 سبد خرید"), KeyboardButton("📦 سفارش‌های من")],
        [KeyboardButton("📞 پشتیبانی"), KeyboardButton("ℹ️ درباره ما")]
    ]
    if is_admin(user.id):
        keyboard.append([KeyboardButton("⚙️ پنل ادمین")])
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"سلام {user.first_name} عزیز! 👋\n\n"
        f"به فروشگاه آرایشی نیکا خوش آمدید! 💄✨\n\n"
        f"از منوی زیر انتخاب کنید:",
        reply_markup=reply_markup
    )

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    PRODUCTS = load_products()
    keyboard = []
    for product_id, product in PRODUCTS.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{product['emoji']} {product['name']} - {format_price(product['price'])}",
                callback_data=f"product_{product_id}"
            )
        ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🛍️ *محصولات ما:*\n\nبرای مشاهده جزئیات روی محصول کلیک کنید:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    PRODUCTS = load_products()
    product_id = query.data.replace("product_", "")
    if product_id not in PRODUCTS:
        await query.edit_message_text("محصول یافت نشد!")
        return
    product = PRODUCTS[product_id]
    keyboard = [
        [InlineKeyboardButton("➕ افزودن به سبد", callback_data=f"add_{product_id}")],
        [InlineKeyboardButton("🔙 بازگشت به لیست", callback_data="back_to_list")]
    ]
    await query.edit_message_text(
        f"{product['emoji']} *{product['name']}*\n\n"
        f"{product['description']}\n\n"
        f"💰 قیمت: *{format_price(product['price'])}*",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("✅ به سبد خرید اضافه شد!")
    PRODUCTS = load_products()
    product_id = query.data.replace("add_", "")
    user_id = query.from_user.id
    cart = get_cart(user_id)
    cart[product_id] = cart.get(product_id, 0) + 1
    product = PRODUCTS[product_id]
    keyboard = [
        [
            InlineKeyboardButton("➕ یکی دیگه", callback_data=f"add_{product_id}"),
            InlineKeyboardButton("🛒 سبد خرید", callback_data="view_cart")
        ],
        [InlineKeyboardButton("🔙 بازگشت به لیست", callback_data="back_to_list")]
    ]
    await query.edit_message_text(
        f"✅ *{product['name']}* به سبد خرید اضافه شد!\n\n"
        f"تعداد در سبد: {cart[product_id]}\n"
        f"جمع کل: {format_price(cart_total(user_id))}",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def view_cart_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    cart = get_cart(user_id)
    if not cart:
        await query.edit_message_text("سبد خرید شما خالی است 🛒")
        return
    keyboard = [
        [InlineKeyboardButton("✅ ثبت سفارش", callback_data="checkout")],
        [InlineKeyboardButton("🗑️ خالی کردن سبد", callback_data="clear_cart")],
        [InlineKeyboardButton("🛍️ ادامه خرید", callback_data="back_to_list")]
    ]
    await query.edit_message_text(
        cart_summary(user_id),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cart = get_cart(user_id)
    if not cart:
        await update.message.reply_text("سبد خرید شما خالی است 🛒\n\nبرای خرید روی «مشاهده محصولات» کلیک کنید.")
        return
    keyboard = [
        [InlineKeyboardButton("✅ ثبت سفارش", callback_data="checkout")],
        [InlineKeyboardButton("🗑️ خالی کردن سبد", callback_data="clear_cart")],
        [InlineKeyboardButton("🛍️ ادامه خرید", callback_data="back_to_list")]
    ]
    await update.message.reply_text(
        cart_summary(user_id),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def clear_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("سبد خرید خالی شد!")
    user_carts[query.from_user.id] = {}
    await query.edit_message_text("🗑️ سبد خرید خالی شد.")

async def back_to_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    PRODUCTS = load_products()
    keyboard = []
    for product_id, product in PRODUCTS.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{product['emoji']} {product['name']} - {format_price(product['price'])}",
                callback_data=f"product_{product_id}"
            )
        ])
    await query.edit_message_text(
        "🛍️ *محصولات ما:*\n\nبرای مشاهده جزئیات روی محصول کلیک کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ==================== فرآیند ثبت سفارش ====================

async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if not get_cart(user_id):
        await query.edit_message_text("سبد خرید شما خالی است!")
        return
    await query.edit_message_text(
        "📝 *ثبت سفارش*\n\n"
        "لطفاً نام و نام خانوادگی خود را وارد کنید:",
        parse_mode="Markdown"
    )
    return WAITING_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_name'] = update.message.text
    await update.message.reply_text("📞 لطفاً شماره موبایل خود را وارد کنید:\n(مثال: 09123456789)")
    return WAITING_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    if not phone.startswith("09") or len(phone) != 11:
        await update.message.reply_text("⚠️ شماره موبایل اشتباه است. دوباره وارد کنید:")
        return WAITING_PHONE
    context.user_data['order_phone'] = phone
    await update.message.reply_text("🏠 لطفاً آدرس کامل خود را وارد کنید:\n(استان، شهر، خیابان، پلاک)")
    return WAITING_ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data['order_address'] = update.message.text
    cart = get_cart(user_id)
    total = cart_total(user_id)
    PRODUCTS = load_products()
    import time
    order_id = f"ORD{int(time.time())}"
    user_orders[order_id] = {
        "user_id": user_id,
        "name": context.user_data.get('order_name'),
        "phone": context.user_data.get('order_phone'),
        "address": context.user_data.get('order_address'),
        "items": dict(cart),
        "total": total,
        "status": "در انتظار بررسی"
    }
    order_text = f"✅ *سفارش شما با موفقیت ثبت شد!*\n\n"
    order_text += f"📋 کد سفارش: `{order_id}`\n\n"
    order_text += cart_summary(user_id) + "\n\n"
    order_text += f"👤 نام: {context.user_data.get('order_name')}\n"
    order_text += f"📞 تلفن: {context.user_data.get('order_phone')}\n"
    order_text += f"🏠 آدرس: {context.user_data.get('order_address')}\n\n"
    order_text += f"💰 *جمع کل: {format_price(total)}*\n\n"
    order_text += "🔔 پس از بررسی سفارش، با شما تماس خواهیم گرفت."
    await update.message.reply_text(order_text, parse_mode="Markdown")
    admin_text = f"🔔 *سفارش جدید!*\n\n"
    admin_text += f"📋 کد: `{order_id}`\n"
    admin_text += f"👤 {context.user_data.get('order_name')}\n"
    admin_text += f"📞 {context.user_data.get('order_phone')}\n"
    admin_text += f"🏠 {context.user_data.get('order_address')}\n\n"
    for product_id, qty in cart.items():
        if product_id in PRODUCTS:
            p = PRODUCTS[product_id]
            admin_text += f"• {p['name']} × {qty}\n"
    admin_text += f"\n💰 جمع: {format_price(total)}"
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"خطا در ارسال به ادمین: {e}")
    user_carts[user_id] = {}
    return ConversationHandler.END

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ فرآیند سفارش لغو شد.")
    return ConversationHandler.END

# ==================== پنل ادمین ====================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ شما دسترسی ادمین ندارید!")
        return
    keyboard = [
        [InlineKeyboardButton("📦 لیست محصولات", callback_data="admin_list")],
        [InlineKeyboardButton("➕ افزودن محصول جدید", callback_data="admin_add")],
        [InlineKeyboardButton("📋 لیست سفارشات", callback_data="admin_orders")],
    ]
    await update.message.reply_text(
        "⚙️ *پنل مدیریت*\n\nچه کاری می‌خواهید انجام دهید؟",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def admin_list_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    PRODUCTS = load_products()
    keyboard = []
    for product_id, product in PRODUCTS.items():
        keyboard.append([
            InlineKeyboardButton(
                f"{product['emoji']} {product['name']} - {format_price(product['price'])}",
                callback_data=f"admin_edit_{product_id}"
            )
        ])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")])
    await query.edit_message_text(
        "📦 *لیست محصولات*\n\nبرای ویرایش یا حذف روی محصول کلیک کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def admin_edit_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    PRODUCTS = load_products()
    product_id = query.data.replace("admin_edit_", "")
    context.user_data['editing_product_id'] = product_id
    product = PRODUCTS[product_id]
    keyboard = [
        [InlineKeyboardButton("✏️ ویرایش نام", callback_data=f"admin_edit_name_{product_id}")],
        [InlineKeyboardButton("💰 ویرایش قیمت", callback_data=f"admin_edit_price_{product_id}")],
        [InlineKeyboardButton("📝 ویرایش توضیحات", callback_data=f"admin_edit_desc_{product_id}")],
        [InlineKeyboardButton("🗑️ حذف محصول", callback_data=f"admin_delete_{product_id}")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="admin_list")],
    ]
    await query.edit_message_text(
        f"*{product['emoji']} {product['name']}*\n\n"
        f"قیمت: {format_price(product['price'])}\n\n"
        f"توضیحات: {product['description']}\n\n"
        f"چه چیزی را ویرایش کنید؟",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def admin_delete_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    product_id = query.data.replace("admin_delete_", "")
    PRODUCTS = load_products()
    if product_id in PRODUCTS:
        name = PRODUCTS[product_id]['name']
        del PRODUCTS[product_id]
        save_products(PRODUCTS)
        await query.edit_message_text(f"✅ محصول *{name}* حذف شد.", parse_mode="Markdown")
    else:
        await query.edit_message_text("محصول یافت نشد!")

async def admin_start_edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = query.data.replace("admin_edit_name_", "")
    context.user_data['editing_product_id'] = product_id
    context.user_data['editing_field'] = 'name'
    await query.edit_message_text("✏️ نام جدید محصول را بنویسید:")
    return ADMIN_EDIT_NAME

async def admin_start_edit_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = query.data.replace("admin_edit_price_", "")
    context.user_data['editing_product_id'] = product_id
    context.user_data['editing_field'] = 'price'
    await query.edit_message_text("💰 قیمت جدید را به تومان بنویسید (فقط عدد):\nمثال: 150000")
    return ADMIN_EDIT_PRICE

async def admin_start_edit_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    product_id = query.data.replace("admin_edit_desc_", "")
    context.user_data['editing_product_id'] = product_id
    context.user_data['editing_field'] = 'description'
    await query.edit_message_text("📝 توضیحات جدید محصول را بنویسید:")
    return ADMIN_EDIT_DESC

async def admin_save_edit_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_id = context.user_data.get('editing_product_id')
    PRODUCTS = load_products()
    if product_id and product_id in PRODUCTS:
        PRODUCTS[product_id]['name'] = update.message.text
        save_products(PRODUCTS)
        await update.message.reply_text(f"✅ نام محصول به *{update.message.text}* تغییر یافت!", parse_mode="Markdown")
    return ConversationHandler.END

async def admin_save_edit_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_id = context.user_data.get('editing_product_id')
    try:
        new_price = int(update.message.text.replace(",", "").replace("،", ""))
        PRODUCTS = load_products()
        if product_id and product_id in PRODUCTS:
            PRODUCTS[product_id]['price'] = new_price
            save_products(PRODUCTS)
            await update.message.reply_text(f"✅ قیمت به *{format_price(new_price)}* تغییر یافت!", parse_mode="Markdown")
    except:
        await update.message.reply_text("⚠️ عدد اشتباه است. لطفاً فقط عدد وارد کنید.")
    return ConversationHandler.END

async def admin_save_edit_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    product_id = context.user_data.get('editing_product_id')
    PRODUCTS = load_products()
    if product_id and product_id in PRODUCTS:
        PRODUCTS[product_id]['description'] = update.message.text
        save_products(PRODUCTS)
        await update.message.reply_text("✅ توضیحات محصول بروزرسانی شد!")
    return ConversationHandler.END

# ==================== افزودن محصول جدید ====================

async def admin_start_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    context.user_data['new_product'] = {}
    await query.edit_message_text("➕ *افزودن محصول جدید*\n\nنام محصول را بنویسید:", parse_mode="Markdown")
    return ADMIN_ADD_NAME

async def admin_add_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_product']['name'] = update.message.text
    await update.message.reply_text("💰 قیمت محصول را به تومان بنویسید (فقط عدد):\nمثال: 150000")
    return ADMIN_ADD_PRICE

async def admin_add_get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text.replace(",", "").replace("،", ""))
        context.user_data['new_product']['price'] = price
        await update.message.reply_text("📝 توضیحات محصول را بنویسید:")
        return ADMIN_ADD_DESC
    except:
        await update.message.reply_text("⚠️ فقط عدد وارد کنید. دوباره امتحان کنید:")
        return ADMIN_ADD_PRICE

async def admin_add_get_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_product']['description'] = update.message.text
    await update.message.reply_text("😊 ایموجی محصول را بفرستید:\nمثال: 💄 یا ✨ یا 🌟")
    return ADMIN_ADD_EMOJI

async def admin_add_get_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['new_product']['emoji'] = update.message.text
    PRODUCTS = load_products()
    new_id = f"p{len(PRODUCTS) + 1}_{int(__import__('time').time())}"
    PRODUCTS[new_id] = context.user_data['new_product']
    save_products(PRODUCTS)
    p = context.user_data['new_product']
    await update.message.reply_text(
        f"✅ *محصول جدید اضافه شد!*\n\n"
        f"{p['emoji']} {p['name']}\n"
        f"قیمت: {format_price(p['price'])}",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def admin_orders_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        return
    if not user_orders:
        await query.edit_message_text("📋 هنوز سفارشی ثبت نشده است.")
        return
    text = "📋 *لیست سفارشات:*\n\n"
    for order_id, order in list(user_orders.items())[-10:]:
        text += f"📦 `{order_id}`\n"
        text += f"👤 {order['name']} | 📞 {order['phone']}\n"
        text += f"💰 {format_price(order['total'])} | {order['status']}\n\n"
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def admin_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("📦 لیست محصولات", callback_data="admin_list")],
        [InlineKeyboardButton("➕ افزودن محصول جدید", callback_data="admin_add")],
        [InlineKeyboardButton("📋 لیست سفارشات", callback_data="admin_orders")],
    ]
    await query.edit_message_text(
        "⚙️ *پنل مدیریت*\n\nچه کاری می‌خواهید انجام دهید؟",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ==================== سایر هندلرها ====================

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    my = {k: v for k, v in user_orders.items() if v['user_id'] == user_id}
    if not my:
        await update.message.reply_text("شما هنوز سفارشی ثبت نکرده‌اید 📦")
        return
    text = "📦 *سفارش‌های شما:*\n\n"
    for order_id, order in my.items():
        text += f"📋 کد: `{order_id}`\n"
        text += f"💰 مبلغ: {format_price(order['total'])}\n"
        text += f"📌 وضعیت: {order['status']}\n\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 *پشتیبانی*\n\n"
        "برای ارتباط با پشتیبانی:\n"
        "📱 واتساپ: 09xxxxxxxxx\n"
        "💬 تلگرام: @your_support\n"
        "🕐 ساعات پاسخگویی: ۹ صبح تا ۹ شب",
        parse_mode="Markdown"
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *درباره ما*\n\n"
        "فروشگاه آرایشی نیکا با هدف ارائه محصولات باکیفیت\n"
        "و اصل به مشتریان عزیز فعالیت می‌کند.\n\n"
        "✅ محصولات ۱۰۰٪ اصل\n"
        "✅ ارسال به سراسر کشور\n"
        "✅ ضمانت بازگشت کالا",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🛍️ مشاهده محصولات":
        await show_products(update, context)
    elif text == "🛒 سبد خرید":
        await show_cart(update, context)
    elif text == "📦 سفارش‌های من":
        await my_orders(update, context)
    elif text == "📞 پشتیبانی":
        await support(update, context)
    elif text == "ℹ️ درباره ما":
        await about(update, context)
    elif text == "⚙️ پنل ادمین":
        await admin_panel(update, context)

# ==================== اجرای ربات ====================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # هندلر ثبت سفارش
    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(checkout, pattern="^checkout$")],
        states={
            WAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            WAITING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            WAITING_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
        },
        fallbacks=[CommandHandler("cancel", cancel_order)]
    )

    # هندلر ویرایش محصول
    edit_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_start_edit_name, pattern="^admin_edit_name_"),
            CallbackQueryHandler(admin_start_edit_price, pattern="^admin_edit_price_"),
            CallbackQueryHandler(admin_start_edit_desc, pattern="^admin_edit_desc_"),
        ],
        states={
            ADMIN_EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_save_edit_name)],
            ADMIN_EDIT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_save_edit_price)],
            ADMIN_EDIT_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_save_edit_desc)],
        },
        fallbacks=[CommandHandler("cancel", cancel_order)]
    )

    # هندلر افزودن محصول
    add_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(admin_start_add, pattern="^admin_add$")],
        states={
            ADMIN_ADD_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_get_name)],
            ADMIN_ADD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_get_price)],
            ADMIN_ADD_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_get_desc)],
            ADMIN_ADD_EMOJI: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_get_emoji)],
        },
        fallbacks=[CommandHandler("cancel", cancel_order)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(order_conv)
    app.add_handler(edit_conv)
    app.add_handler(add_conv)
    app.add_handler(CallbackQueryHandler(product_detail, pattern="^product_"))
    app.add_handler(CallbackQueryHandler(add_to_cart, pattern="^add_"))
    app.add_handler(CallbackQueryHandler(view_cart_button, pattern="^view_cart$"))
    app.add_handler(CallbackQueryHandler(clear_cart, pattern="^clear_cart$"))
    app.add_handler(CallbackQueryHandler(back_to_list, pattern="^back_to_list$"))
    app.add_handler(CallbackQueryHandler(admin_list_products, pattern="^admin_list$"))
    app.add_handler(CallbackQueryHandler(admin_edit_product, pattern="^admin_edit_p"))
    app.add_handler(CallbackQueryHandler(admin_delete_product, pattern="^admin_delete_"))
    app.add_handler(CallbackQueryHandler(admin_orders_list, pattern="^admin_orders$"))
    app.add_handler(CallbackQueryHandler(admin_back, pattern="^admin_back$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ ربات در حال اجراست...")
    app.run_polling()

if __name__ == "__main__":
    main()
