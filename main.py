import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from dateutil import parser
from fuzzywuzzy import process

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

MENU, TRIP, FROM_CITY, TO_CITY, DEPART, RETURN, HOTEL_CITY, CHECKIN, CHECKOUT = range(9)

CITIES = ["Johannesburg", "Cape Town", "Durban", "Dubai", "London", "Nairobi", "Cairo"]
TRIP_TYPES = ["One-way", "Round-trip", "Multi-city"]

MAIN_MENU = [["Flights", "Buses"], ["Hotels"], ["Travel Insurance", "Other Essentials"]]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✈️ *Budget Travel Deals*\nChoose a service:",
        reply_markup=ReplyKeyboardMarkup(MAIN_MENU, resize_keyboard=True),
        parse_mode=ParseMode.MARKDOWN
    )
    return MENU

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.lower()
    context.user_data.clear()

    if txt in ["flights", "buses"]:
        context.user_data["service"] = txt
        await update.message.reply_text("Choose trip type:", reply_markup=ReplyKeyboardMarkup([[x] for x in TRIP_TYPES], resize_keyboard=True))
        return TRIP

    if txt == "hotels":
        await update.message.reply_text("Enter hotel city:")
        return HOTEL_CITY

    await update.message.reply_text("Select Flights, Buses or Hotels.")
    return MENU

def match_city(text):
    match = process.extractOne(text, CITIES)
    return match[0] if match and match[1] > 70 else None

async def trip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["trip"] = update.message.text
    await update.message.reply_text("Departure city:")
    return FROM_CITY

async def from_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = match_city(update.message.text)
    if not city:
        await update.message.reply_text(f"City not found. Try: {', '.join(CITIES)}")
        return FROM_CITY
    context.user_data["from"] = city
    await update.message.reply_text("Arrival city:")
    return TO_CITY

async def to_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = match_city(update.message.text)
    if not city:
        await update.message.reply_text(f"City not found. Try: {', '.join(CITIES)}")
        return TO_CITY
    context.user_data["to"] = city
    await update.message.reply_text("Departure date:")
    return DEPART

async def depart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["depart"] = parser.parse(update.message.text).strftime("%Y-%m-%d")
    except:
        await update.message.reply_text("Invalid date.")
        return DEPART

    if context.user_data["trip"] == "Round-trip":
        await update.message.reply_text("Return date:")
        return RETURN

    return await show_results(update, context)

async def return_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["return"] = parser.parse(update.message.text).strftime("%Y-%m-%d")
    except:
        await update.message.reply_text("Invalid date.")
        return RETURN

    return await show_results(update, context)

async def hotel_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["hotel"] = update.message.text
    await update.message.reply_text("Check-in date:")
    return CHECKIN

async def checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["checkin"] = update.message.text
    await update.message.reply_text("Check-out date:")
    return CHECKOUT

async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"🏨 *Hotels in {context.user_data['hotel']}*\n\n**R1800** – [Book](https://example.com)\n**R2400** – [Book](https://example.com)"
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END

async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data
    msg = f"✈️ *{data['from']} → {data['to']}*\n\n**R5200** – [Book](https://example.com)\n**R6100** – [Book](https://example.com)\n**R7400** – [Book](https://example.com)"
    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [MessageHandler(filters.TEXT, menu)],
            TRIP: [MessageHandler(filters.TEXT, trip)],
            FROM_CITY: [MessageHandler(filters.TEXT, from_city)],
            TO_CITY: [MessageHandler(filters.TEXT, to_city)],
            DEPART: [MessageHandler(filters.TEXT, depart)],
            RETURN: [MessageHandler(filters.TEXT, return_date)],
            HOTEL_CITY: [MessageHandler(filters.TEXT, hotel_city)],
            CHECKIN: [MessageHandler(filters.TEXT, checkin)],
            CHECKOUT: [MessageHandler(filters.TEXT, checkout)],
        },
        fallbacks=[]
    )

    app.add_handler(conv)
    app.run_polling()

main()
