import requests
from random import randint
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

URL = "https://leakosintapi.com/"
BOT_TOKEN = "8252573449:AAG6jEYERw3DDk1bSiXs9flAN_koRoX7AbU"
API_TOKEN = "8176628365:sXgGAZTZ"
LANG = "en"
LIMIT = 300

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
cash_reports = {}

def check_access(user_id):
    return True

def generate_report(query, query_id, user_id):
    global cash_reports
    data = {"token": API_TOKEN, "request": query.split("\n")[0], "limit": LIMIT, "lang": LANG}
    
    try:
        response = requests.post(URL, json=data).json()
    except:
        return ["❌ <b>SYSTEM ALERT:</b> API is currently unreachable. Please try again later."]

    if "Error code" in response:
        return [f"⚠️ <b>API ERROR:</b> {response['Error code']}"]

    cash_reports[str(query_id)] = {'user': user_id, 'pages': []}
    
    if "List" not in response or not response["List"] or "No results found" in response["List"]:
        return ["📭 <b>NO DATA FOUND:</b> The target is secure or not in our current databases."]

    for database_name, db_data in response["List"].items():
        text = [f"🗄 <b>DATABASE: {database_name}</b>", ""]
        
        info_leak = db_data.get("InfoLeak", "")
        if info_leak:
            text.append(f"ℹ️ <i>{info_leak}</i>\n")
            
        if database_name != "No results found":
            for report_data in db_data.get("Data", []):
                text.append("━━━━━━━━━━━━━━━━━━")
                for column_name, value in report_data.items():
                    display_key = column_name
                    col_lower = column_name.lower()
                    
                    if col_lower == "name":
                        display_key = "Father Name"
                    elif col_lower in ["father name", "fathername", "father_name"]:
                        display_key = "Name"
                    
                    text.append(f"🔹 <b>{display_key}:</b> <code>{value}</code>")
                text.append("") 
                
        text.append("━━━━━━━━━━━━━━━━━━")
        text.append("👨‍💻 <b>Developer:</b> <i>toxic</i>")
        
        joined_text = "\n".join(text)
        if len(joined_text) > 3500:
            joined_text = joined_text[:3500] + "\n\n⚠️ <i>Data truncated for security and limits.</i>"
            
        cash_reports[str(query_id)]['pages'].append(joined_text)
        
    return cash_reports[str(query_id)]['pages']

def create_inline_keyboard(query_id, page_id, count_page):
    markup = InlineKeyboardMarkup()
    if count_page <= 1:
        return markup
        
    if page_id < 0:
        page_id = count_page - 1
    elif page_id > count_page - 1:
        page_id = page_id % count_page
        
    markup.row_width = 3
    markup.add(
        InlineKeyboardButton(text="⬅️ Back", callback_data=f"page_{query_id}_{page_id-1}"),
        InlineKeyboardButton(text=f"📄 {page_id+1}/{count_page}", callback_data="ignore"),
        InlineKeyboardButton(text="Next ➡️", callback_data=f"page_{query_id}_{page_id+1}")
    )
    return markup

@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🚀 Channel", url="https://t.me/your_channel_link"),
        InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/your_username")
    )
    bot.reply_to(message, "🔥 <b>Advanced OSINT System</b>\n\nUse <code>/search &lt;target&gt;</code> in groups or send text here directly.\n\n<i>⚡ Secure. Fast. Private.</i>\n\n👨‍💻 <b>Developer:</b> toxic", reply_markup=markup)

@bot.message_handler(commands=["search"])
def handle_search_command(message):
    process_search(message, is_command=True)

@bot.message_handler(func=lambda message: message.chat.type == "private")
def handle_private_text(message):
    process_search(message, is_command=False)

def process_search(message, is_command):
    user_id = message.from_user.id
    if not check_access(user_id):
        bot.send_message(message.chat.id, "🚫 <b>ACCESS DENIED.</b>")
        return

    query = message.text
    if is_command:
        if len(message.text.split(maxsplit=1)) < 2:
            bot.reply_to(message, "⚠️ <b>FORMAT ERROR:</b> Use <code>/search target</code>")
            return
        query = message.text.split(maxsplit=1)[1]

    wait_msg = bot.reply_to(message, "⏳ <i>Encrypting connection & scanning databases...</i>")
    
    query_id = randint(100000, 999999)
    report_pages = generate_report(query, query_id, user_id)
    
    try:
        bot.delete_message(message.chat.id, wait_msg.message_id)
        if is_command:
            bot.delete_message(message.chat.id, message.message_id) 
    except:
        pass

    if not report_pages:
        bot.send_message(message.chat.id, "❌ <b>SYSTEM FAULT:</b> Generation failed.")
        return
        
    markup = create_inline_keyboard(query_id, 0, len(report_pages))
    
    try:
        bot.send_message(message.chat.id, report_pages[0], reply_markup=markup)
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ <b>DISPLAY ERROR:</b> Output contains invalid characters.")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call: CallbackQuery):
    if call.data == "ignore":
        bot.answer_callback_query(call.id, "Page Indicator")
        return
        
    if call.data.startswith("page_"):
        parts = call.data.split("_")
        query_id = parts[1]
        page_id = int(parts[2])
        
        if query_id not in cash_reports:
            bot.answer_callback_query(call.id, "❌ Session expired for security.", show_alert=True)
            return
            
        if cash_reports[query_id]['user'] != call.from_user.id:
            bot.answer_callback_query(call.id, "🚫 PRIVACY LOCK: Only the requester can navigate this report.", show_alert=True)
            return

        report_pages = cash_reports[query_id]['pages']
        markup = create_inline_keyboard(query_id, page_id, len(report_pages))
        
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id, 
                text=report_pages[page_id], 
                reply_markup=markup
            )
        except:
            pass

if __name__ == "__main__":
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

