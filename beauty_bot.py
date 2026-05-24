#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ربات فروش محصولات آرایشی تلگرام
Telegram Cosmetics Sales Bot
"""

import logging
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ==================== تنظیمات ====================
import os
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID"))
# ==================== محصولات ====================
# محصولات خود را اینجا تعریف کنید
PRODUCTS = {
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

# ==================== سبد خرید کاربران ====================
user_carts = {}  # ذخیره سبد خرید هر کاربر
user_orders = {}  # ذخیره سفارشات

# ==================== مراحل گفتگو ====================
WAITING_ADDRESS, WAITING_PHONE, WAITING_NAME = range(3)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ==================== توابع کمکی ====================

def format_price(price: int) -> str:
    """فرمت قیمت با جداکننده هزارگان"""
    return f"{price:,} تومان"

def get_cart(user_id: int) -> dict:
    """دریافت سبد خرید کاربر"""
    if user_id not in user_carts:
        user_carts[user_id] = {}
    return user_carts[user_id]

def cart_total(user_id: int) -> int:
    """محاسبه جمع کل سبد خرید"""
    cart = get_cart(user_id)
    total = 0
    for product_id, qty in cart.items():
        if product_id in PRODUCTS:
            total += PRODUCTS[product_id]["price"] * qty
    return total

def cart_summary(user_id: int) -> str:
    """خلاصه سبد خرید"""
    cart = get_cart(user_id)
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

# ==================== هندلرهای اصلی ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع ربات"""
    user = update.effective_user
    keyboard = [
        [KeyboardButton("🛍️ مشاهده محصولات")],
        [KeyboardButton("🛒 سبد خرید"), KeyboardButton("📦 سفارش‌های من")],
        [KeyboardButton("📞 پشتیبانی"), KeyboardButton("ℹ️ درباره ما")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        f"سلام {user.first_name} عزیز! 👋\n\n"
        f"به فروشگاه آرایشی ما خوش آمدید! 💄✨\n\n"
        f"از منوی زیر انتخاب کنید:",
        reply_markup=reply_markup
    )

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست محصولات"""
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
    """نمایش جزئیات محصول"""
    query = update.callback_query
    await query.answer()
    
    product_id = query.data.replace("product_", "")
    if product_id not in PRODUCTS:
        await query.edit_message_text("محصول یافت نشد!")
        return
    
    product = PRODUCTS[product_id]
    keyboard = [
        [
            InlineKeyboardButton("➕ افزودن به سبد", callback_data=f"add_{product_id}"),
        ],
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
    """افزودن به سبد خرید"""
    query = update.callback_query
    await query.answer("✅ به سبد خرید اضافه شد!")
    
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
    """نمایش سبد خرید از دکمه"""
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
    """نمایش سبد خرید از منو"""
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
    """خالی کردن سبد"""
    query = update.callback_query
    await query.answer("سبد خرید خالی شد!")
    user_carts[query.from_user.id] = {}
    await query.edit_message_text("🗑️ سبد خرید خالی شد.")

async def back_to_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بازگشت به لیست محصولات"""
    query = update.callback_query
    await query.answer()
    
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
    """شروع فرآیند ثبت سفارش"""
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
    """دریافت نام کاربر"""
    context.user_data['order_name'] = update.message.text
    await update.message.reply_text(
        "📞 لطفاً شماره موبایل خود را وارد کنید:\n(مثال: 09123456789)"
    )
    return WAITING_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت شماره تلفن"""
    phone = update.message.text
    if not phone.startswith("09") or len(phone) != 11:
        await update.message.reply_text("⚠️ شماره موبایل اشتباه است. لطفاً دوباره وارد کنید (مثال: 09123456789):")
        return WAITING_PHONE
    
    context.user_data['order_phone'] = phone
    await update.message.reply_text(
        "🏠 لطفاً آدرس کامل خود را وارد کنید:\n(استان، شهر، خیابان، پلاک)"
    )
    return WAITING_ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت آدرس و نهایی‌سازی سفارش"""
    user_id = update.effective_user.id
    context.user_data['order_address'] = update.message.text
    
    cart = get_cart(user_id)
    total = cart_total(user_id)
    
    # ذخیره سفارش
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
    
    # پیام تایید برای کاربر
    order_text = f"✅ *سفارش شما با موفقیت ثبت شد!*\n\n"
    order_text += f"📋 کد سفارش: `{order_id}`\n\n"
    order_text += cart_summary(user_id) + "\n\n"
    order_text += f"👤 نام: {context.user_data.get('order_name')}\n"
    order_text += f"📞 تلفن: {context.user_data.get('order_phone')}\n"
    order_text += f"🏠 آدرس: {context.user_data.get('order_address')}\n\n"
    order_text += f"💰 *جمع کل: {format_price(total)}*\n\n"
    order_text += "🔔 پس از بررسی سفارش، با شما تماس خواهیم گرفت."
    
    await update.message.reply_text(order_text, parse_mode="Markdown")
    
    # ارسال اطلاع به ادمین
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
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.error(f"خطا در ارسال به ادمین: {e}")
    
    # خالی کردن سبد
    user_carts[user_id] = {}
    
    return ConversationHandler.END

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو فرآیند سفارش"""
    await update.message.reply_text("❌ فرآیند سفارش لغو شد.")
    return ConversationHandler.END

# ==================== سایر هندلرها ====================

async def my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش سفارش‌های کاربر"""
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
    """پشتیبانی"""
    await update.message.reply_text(
        "📞 *پشتیبانی*\n\n"
        "برای ارتباط با پشتیبانی:\n"
        "📱 واتساپ: 09xxxxxxxxx\n"
        "💬 تلگرام: @your_support\n"
        "🕐 ساعات پاسخگویی: ۹ صبح تا ۹ شب",
        parse_mode="Markdown"
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """درباره ما"""
    await update.message.reply_text(
        "ℹ️ *درباره ما*\n\n"
        "فروشگاه آرایشی ما با هدف ارائه محصولات باکیفیت\n"
        "و اصل به مشتریان عزیز فعالیت می‌کند.\n\n"
        "✅ محصولات ۱۰۰٪ اصل\n"
        "✅ ارسال به سراسر کشور\n"
        "✅ ضمانت بازگشت کالا",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندل پیام‌های متنی منو"""
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

# ==================== اجرای ربات ====================

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # هندلر مکالمه برای ثبت سفارش
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(checkout, pattern="^checkout$")],
        states={
            WAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            WAITING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            WAITING_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
        },
        fallbacks=[CommandHandler("cancel", cancel_order)]
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(product_detail, pattern="^product_"))
    app.add_handler(CallbackQueryHandler(add_to_cart, pattern="^add_"))
    app.add_handler(CallbackQueryHandler(view_cart_button, pattern="^view_cart$"))
    app.add_handler(CallbackQueryHandler(clear_cart, pattern="^clear_cart$"))
    app.add_handler(CallbackQueryHandler(back_to_list, pattern="^back_to_list$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ ربات در حال اجراست...")
    app.run_polling()

if __name__ == "__main__":
    main()
