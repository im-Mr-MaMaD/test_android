import unicodedata
import regex
import rubpy
import re
import logging
from rubpy import Client, filters
from typing import Dict, Any, Union, Optional, List
from rubpy.types import Update
import asyncio
import random
import json
import os
from datetime import datetime, timedelta
import time
import jdatetime
import aiohttp

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# متغیرهای جهانی
is_deleting = False  # قفل برای جلوگیری از اجرای همزمان
creator = None  # GUID سازنده ربات
owners = {}  # دیکشنری مالکان گروه‌ها: {group_guid: owner_guid}
special_users = {}  # دیکشنری کاربران ویژه: {group_guid: [user_guid1, user_guid2]}
voice_chats = {}  # دیکشنری برای ذخیره voice_chat_id
group_expiry = {}  # دیکشنری برای ذخیره زمان انقضای گروه‌ها
notified_groups = {}  # دیکشنری برای ردگیری گروه‌های اخطار داده‌شده
emoji_game_active = {}  # {group_id: bool} برای جلوگیری از تداخل
emoji_game_scores = {}  # {group_id: {user_id: score}}
emoji_game_current = {}  # {group_id: current_emoji}
emoji_game_round = {}  # {group_id: current_round}
pending_confirm = {}
emergency_active = {}
backup_exempt = {}
original_info = {}
welcome_config_file = "welcome_config.json"
welcome_config = {}
active_groups = []  # لیست گروه‌های فعال
learn_data = {}  # دیتابیس یادگیری {گپ: {کلید: {'type':'text'/'media','content':...}}}
warns = {}  # اخطار کاربران {گپ: {کاربر: تعداد}}
max_warn = {}  # بیشترین اخطار مجاز برای هر گروه
exempt_users = {}  # کاربران معاف از اخطار {گپ: [guid,...]}
ongoing_games = {}  # بازی‌های در حال اجرا {گپ: { 'number': int }}
user_stats = {}  # {گپ: {کاربر: {'messages':int}}}
lock_settings = {}  # {گپ: {نوع: حداکثر اخطار}}
user_messages = {}  # {گپ: {کاربر: [(timestamp, text), ...]}} برای ردیابی اسپم
creator_file = "creator_config.json"
learn_file = "learn_data.json"
active_calls = {}
listSpeam = []
current_dir = os.path.dirname(__file__)

# لود فایل چالش‌ها
try:
    with open("chalesh.txt", "r", encoding="utf-8") as f:
        chalesh_lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
except Exception as e:
    logger.error(f"Error loading chalesh.txt: {type(e).__name__}: {e}")
    chalesh_lines = []

# لیست ایموجی‌ها و نام‌های فارسی آنها
emoji_names = {
    "😀": "خنده", "😊": "لبخند", "😂": "خنده شدید", "😍": "عاشق", "😢": "گریه",
    "😡": "عصبانی", "😨": "ترسیده", "😴": "خواب‌آلود", "😎": "باحال", "😜": "شیطون",
    "😇": "فرشته", "😤": "ناراحت", "😪": "گریه خفیف", "😷": "ماسک", "🤗": "آغوش",
    "🤓": "عینکی", "🤩": "ستاره‌دار", "🥳": "جشن", "🥺": "التماس", "😣": "درد",
    "🐶": "سگ", "🐱": "گربه", "🐭": "موش", "🐰": "خرگوش", "🦁": "شیر",
    "🐯": "ببر", "🐻": "خرس", "🐷": "خوک", "🐮": "گاو", "🐵": "میمون",
    "🦒": "زرافه", "🦊": "روباه", "🦌": "گوزن", "🦓": "گورخر", "🐘": "فیل",
    "🐍": "مار", "🐢": "لاک‌پشت", "🐦": "پرنده", "🦋": "پروانه",
    "🍎": "سیب", "🍐": "گلابی", "🍊": "پرتقال", "🍋": "لیمو", "🍉": "هندوانه",
    "🍇": "انگور", "🍓": "توت‌فرنگی", "🍑": "هلو", "🍍": "آناناس", "🥥": "نارگیل",
    "🥐": "کروسان", "🍔": "همبرگر", "🍕": "پیتزا", "🍟": "سیب‌زمینی سرخ‌کرده", "🍗": "مرغ",
    "🍖": "گوشت", "🍝": "اسپاگتی", "🍜": "نودل", "🍣": "سوشی", "🍦": "بستنی",
    "💡": "لامپ", "📱": "موبایل", "💻": "لپ‌تاپ", "⌚": "ساعت", "📷": "دوربین",
    "🎥": "فیلم‌برداری", "🎤": "میکروفون", "🎧": "هدفون", "📚": "کتاب", "✏️": "مداد",
    "🔑": "کلید", "🔒": "قفل", "🔧": "آچار", "⚙️": "چرخ‌دنده", "🛠️": "ابزار",
    "💼": "کیف", "📦": "جعبه", "🎁": "هدیه", "🧳": "چمدان", "⏰": "ساعت زنگ‌دار",
    "⚽": "فوتبال", "🏀": "بسکتبال", "🏈": "فوتبال آمریکایی", "🎾": "تنیس", "🏐": "والیبال",
    "🏉": "راگبی", "🎱": "بیلیارد", "🏓": "پینگ‌پنگ", "🏸": "بدمینتون", "🏒": "هاکی",
    "⛳": "گلف", "🏹": "تیراندازی", "🎣": "ماهیگیری", "🥊": "بوکس", "🛹": "اسکیت‌برد",
    "🎿": "اسکی", "⛸️": "پاتیناژ", "🏋️‍♂️": "وزنه‌برداری", "🚴": "دوچرخه‌سواری", "🏄": "موج‌سواری",
    "🌞": "خورشید", "🌙": "ماه", "⭐": "ستاره", "🌈": "رنگین‌کمان", "☁️": "ابر",
    "⛈️": "طوفان", "❄️": "برف", "🌪️": "گردباد", "🌊": "موج", "🌴": "نخل",
    "🌵": "کاکتوس", "🌷": "لاله", "🌸": "شکوفه", "🌹": "گل رز", "🌺": "گل هیبیسکوس",
    "🌻": "آفتاب‌گردان", "🍂": "برگ پاییزی", "🍁": "برگ افرا", "🌾": "گندم", "🌲": "درخت کاج",
    "❤️": "قلب قرمز", "💙": "قلب آبی", "💚": "قلب سبز", "💛": "قلب زرد", "💜": "قلب بنفش",
    "🖤": "قلب سیاه", "💔": "قلب شکسته", "❣️": "قلب علامت", "💖": "قلب درخشان", "💞": "قلب چرخان",
    "✅": "تیک سبز", "❌": "ضربدر", "✔️": "تیک", "✖️": "ضربدر سیاه", "➡️": "پیکان راست",
    "⬅️": "پیکان چپ", "⬆️": "پیکان بالا", "⬇️": "پیکان پایین", "🔄": "چرخش", "🔥": "آتش",
    "🚀": "موشک", "✈️": "هواپیما", "🚗": "ماشین", "🚲": "دوچرخه", "🛵": "موتور",
    "🚤": "قایق", "🚁": "هلیکوپتر", "🚜": "تراکتور", "🏍️": "موتورسیکلت", "🚢": "کشتی",
    "🏠": "خانه", "🏰": "قلعه", "🗼": "برج", "🗽": "مجسمه آزادی", "⛪": "کلیسا",
    "🕌": "مسجد", "🕍": "کنیسه", "⛩️": "معبد", "🕋": "کعبه", "🎡": "چرخ‌فلک"
}
emoji_list = list(emoji_names.keys())

# تعریف ربات
bot = Client('rubika-bot')  # جایگزین کنید با توکن واقعی

# لود تنظیمات
def load_creator():
    global creator
    if os.path.exists(creator_file):
        try:
            with open(creator_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                creator = data.get("creator_guid")
        except Exception as e:
            logger.error(f"Error loading creator: {type(e).__name__}: {e}")
    return creator

def save_creator(guid):
    global creator
    creator = guid
    try:
        with open(creator_file, "w", encoding="utf-8") as f:
            json.dump({"creator_guid": guid}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving creator: {type(e).__name__}: {e}")

def load_welcome_config():
    global welcome_config
    if os.path.exists(welcome_config_file):
        try:
            with open(welcome_config_file, "r", encoding="utf-8") as f:
                welcome_config = json.load(f)
        except Exception as e:
            logger.error(f"Error loading welcome_config: {type(e).__name__}: {e}")

def save_welcome_config():
    try:
        with open(welcome_config_file, "w", encoding="utf-8") as f:
            json.dump(welcome_config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving welcome_config: {type(e).__name__}: {e}")

def load_learn_data():
    global learn_data
    if os.path.exists(learn_file):
        try:
            with open(learn_file, "r", encoding="utf-8") as f:
                learn_data = json.load(f)
        except Exception as e:
            logger.error(f"Error loading learn_data: {type(e).__name__}: {e}")
    
def load_group_active():
    global active_groups
    if os.path.exists("group_active.json"):
        path = os.path.abspath("group_active.json")
        print(path)
        try:
            with open("group_active.json", "r", encoding="utf-8") as f:
                active_groups = json.load(f)
        except Exception as e:
            logger.error(f"Error loading active_groups: {type(e).__name__}: {e}")

def save_group_active():
    try:
        with open("group_active.json", "w", encoding="utf-8") as f:
            json.dump(active_groups, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving active_groups: {type(e).__name__}: {e}")
    
def save_learn_data():
    try:
        with open(learn_file, "w", encoding="utf-8") as f:
            json.dump(learn_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving learn_data: {type(e).__name__}: {e}")

# تابع کمکی برای دریافت نام کاربر
async def get_name_user(bot: Client, guid: str) -> str:
    try:
        info = await bot.get_user_info(guid)
        return info['user'].get('first_name', 'کاربر')
    except Exception:
        return "کاربر"

# تابع اتصال مجدد
async def reconnect_bot(bot, retries=3, delay=5):
    for attempt in range(retries):
        try:
            await bot.disconnect()
            await bot.connect()
            logger.info(f"Reconnected successfully on attempt {attempt + 1}")
            return True
        except Exception as e:
            logger.error(f"Reconnect attempt {attempt + 1} failed: {type(e).__name__}: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(delay)
    logger.error("All reconnect attempts failed")
    return False

# شناسایی سازنده و جوین به گروه
@bot.on_message_updates(filters.is_private)
async def identify_creator(m: Update):
    global creator
    text = m.text or ""
    uid = m.author_guid

    # لود creator از فایل
    load_creator()

    # اگر creator قبلاً تنظیم شده باشد
    if creator:
        if text.strip().startswith("تنظیم سازنده"):
            try:
                await m.reply("❌ سازنده قبلاً تنظیم شده است!")
                logger.info(f"Attempt to set new creator blocked: {uid}")
            except Exception as e:
                logger.error(f"Error sending creator block message: {type(e).__name__}: {e}")
            return
    else:
        # تنظیم اولین کاربر به عنوان سازنده
        creator = uid
        save_creator(creator)
        try:
            await m.reply(f"✅ شما به عنوان سازنده ربات ثبت شدید (GUID: {creator})")
            logger.info(f"Creator set automatically: {creator}")
        except Exception as e:
            logger.error(f"Error sending creator confirmation message: {type(e).__name__}: {e}")

    # مدیریت جوین به گروه
    if uid == creator and text.startswith("https://rubika.ir/joing/"):
        try:
            link = text.split("https://rubika.ir/joing/")[1]
            result = await bot.join_group(link)
            gid = result['group']['group_guid']
            title = result['group']['group_title']
            await m.reply(f"در گروه {title} جوین شدم ✅")
            await bot.send_message(gid, "سلام! برای فعال‌سازی بنویسید فعال")
        except Exception as e:
            await m.reply(f"خطا در جوین گروه: {type(e).__name__}: {e}")
            logger.error(f"Error joining group: {type(e).__name__}: {e}")

# فعال‌سازی ربات در گروه
@bot.on_message_updates(filters.is_group)
async def activate_bot(m: Update):
    text = m.text or ""
    gid = m.object_guid
    if m.author_guid == creator and text.strip() == "فعال":
        if gid not in active_groups:
            active_groups.append(gid)
            save_group_active()
            learn_data.setdefault(gid, {})
            warns.setdefault(gid, {})
            max_warn[gid] = 3
            exempt_users.setdefault(gid, [])
            user_messages.setdefault(gid, {})
            await m.reply("✅ ربات فعال شد")
        else:
            await m.reply("✅ ربات قبلاً در این گروه فعال است")

# تنظیم مالک گروه
@bot.on_message_updates(filters.is_group)
async def set_owner(m: Update):
    gid = m.object_guid
    text = m.text or ""
    uid = m.author_guid
    if gid in active_groups and text.startswith("مالک"):
        is_creator = uid == creator
        is_owner = uid == owners.get(gid)
        if not (is_creator or is_owner):
            return
        
        if "@" in text:
            uname = text.split("مالک")[1].strip().replace("@", "")
            try:
                info = await bot.get_object_by_username(uname)
                owners[gid] = info['user']['user_guid']
                await m.reply(f"@{uname} به‌عنوان مالک ثبت شد ✅")
            except Exception as e:
                await m.reply(f"کاربر یافت نشد ❌: {type(e).__name__}: {e}")
                logger.error(f"Error setting owner: {type(e).__name__}: {e}")
        elif m.reply_to_message_id and is_creator:  # جدید: تنظیم مالک توسط سازنده با ریپلای
            msgs = await bot.get_messages(gid, center_message_id=m.reply_to_message_id, limit=1)
            target = msgs['messages'][0]['author_object_guid']
            owners[gid] = target
            name = await get_name_user(bot, target)
            await m.reply(f"{name} به عنوان مالک جدید تنظیم شد ✅")

# خوش‌آمدگویی و مدیریت ورود/خروج
@bot.on_chat_updates()
async def handle_join_leave(m: Update):
    gid = m.object_guid
    txt = m.raw_text or ""
    if gid not in active_groups:
        return
    if "یک عضو از طریق لینک" in txt or "اضافه شد به گروه" in txt:
        uid = m.message.author_object_guid if m.message else None
        if not uid:
            return
        try:
            info = await bot.get_user_info(uid)
            name = info['user'].get('first_name', 'کاربر')
        except Exception as e:
            name = "کاربر"
            logger.error(f"Error getting user info: {type(e).__name__}: {e}")
        now = jdatetime.datetime.now().strftime("%Y/%m/%d")
        clock = datetime.now().strftime("%H:%M")
        group_name = m.group_metadata.get("group_title", "گروه")
        gif_id = welcome_config.get(str(gid), {}).get("welcome")
        gif_obj = next((g["content"] for g in welcome_config.get("gifs", []) if g["id"] == gif_id), None)
        if gif_obj:
            await bot.send_file(gid, gif_obj)
        msg = f"👋 خوش آمدی {name} به گروه {group_name}!\n📅 تاریخ: {now}\n⏰ ساعت: {clock}"
        await bot.send_message(gid, msg, parse_mode="markdown")
        return
    if "گروه را ترک کرد" in txt or "حذف شد از گروه" in txt:
        gif_id = welcome_config.get(str(gid), {}).get("goodbye")
        gif_obj = next((g["content"] for g in welcome_config.get("gifs", []) if g["id"] == gif_id), None)
        if gif_obj:
            await bot.send_file(gid, gif_obj)
        else:
            await bot.send_message(gid, "👋 یکی از اعضا از گروه خارج شد.", parse_mode="markdown")

# تنظیم گیف ورود و خروج
@bot.on_message_updates(filters.is_group)
async def auto_welcome(m: Update):
    gid = m.object_guid
    uid = m.author_guid
    text = m.text or ""
    roles = [creator, owners.get(gid)] + special_users.get(gid, [])
    is_admin = uid in roles

    if is_admin and m.reply_to_message_id and text.startswith("سیو ورود"):
        msgs = await bot.get_messages(gid, center_message_id=m.reply_to_message_id, limit=1)
        msg = msgs['messages'][0]
        if "file_inline" in msg:
            count = len(welcome_config.get("gifs", [])) + 1
            gif_id = f"gif{count}"
            welcome_config.setdefault("gifs", []).append({
                "id": gif_id,
                "content": msg['file_inline']
            })
            save_welcome_config()
            await m.reply(f"🎞 گیف ورود با نام {gif_id} ذخیره شد")
        return

    if is_admin and m.reply_to_message_id and text.startswith("سیو خروج"):
        msgs = await bot.get_messages(gid, center_message_id=m.reply_to_message_id, limit=1)
        msg = msgs['messages'][0]
        if "file_inline" in msg:
            count = len(welcome_config.get("gifs", []) + 1)
            gif_id = f"gif{count}"
            welcome_config.setdefault("gifs", []).append({
                "id": gif_id,
                "content": msg['file_inline']
            })
            save_welcome_config()
            await m.reply(f"🎞 گیف خروج با نام {gif_id} ذخیره شد")
        return

    if is_admin and text.startswith("تنظیم ورود"):
        gifname = text.replace("تنظیم ورود", "").strip()
        welcome_config.setdefault(str(gid), {})["welcome"] = gifname
        save_welcome_config()
        await m.reply(f"✅ گیف «{gifname}» برای ورود تنظیم شد")
        return

    if is_admin and text.startswith("تنظیم خروج"):
        gifname = text.replace("تنظیم خروج", "").strip()
        welcome_config.setdefault(str(gid), {})["goodbye"] = gifname
        save_welcome_config()
        await m.reply(f"✅ گیف «{gifname}» برای خروج تنظیم شد")
        return

# مدیریت قفل‌ها
@bot.on_message_updates(filters.is_group)
async def manage_locks(m: Update):
    gid = m.object_guid
    if gid not in active_groups:
        return
    uid = m.author_guid
    roles = [creator, owners.get(gid)] + special_users.get(gid, [])
    is_admin = uid in roles
    text = m.text or ""
    if not is_admin:
        return

    valid_locks = ["لینک", "آیدی", "عکس", "فیلم", "متن نامناسب", "اسپم", "گیف", "آهنگ", "ویس", "استوری"]
    
    if text.strip().startswith("قفل "):
        lock_type = text.strip().split("قفل ")[1].strip()
        if lock_type == "همه":
            lock_settings[gid] = {lock: 3 for lock in valid_locks}
            await m.reply("✅ تمام قفل‌ها فعال شدند")
        elif lock_type in valid_locks:
            lock_settings.setdefault(gid, {})
            lock_settings[gid][lock_type] = 3
            await m.reply(f"✅ قفل {lock_type} فعال شد")
        else:
            await m.reply(f"❌ نوع قفل نامعتبر است. قفل‌های معتبر: {', '.join(valid_locks)}")
        return

    if text.strip().startswith("باز کردن قفل "):
        lock_type = text.strip().split("باز کردن قفل ")[1].strip()
        if lock_type == "همه":
            lock_settings.pop(gid, None)
            await m.reply("✅ تمام قفل‌ها غیرفعال شدند")
        elif lock_type in valid_locks and gid in lock_settings and lock_type in lock_settings[gid]:
            lock_settings[gid].pop(lock_type, None)
            if not lock_settings[gid]:
                lock_settings.pop(gid, None)
            await m.reply(f"✅ قفل {lock_type} غیرفعال شد")
        else:
            await m.reply("❌ قفل موردنظر فعال نیست یا نامعتبر است")
        return

    if text.strip().startswith("تنظیم اخطار ") and len(text.strip().split()) >= 3:
        try:
            parts = text.strip().split()
            lock_type = parts[2]
            warn_count = int(parts[3])
            if lock_type not in valid_locks:
                await m.reply(f"❌ نوع قفل نامعتبر است. قفل‌های معتبر: {', '.join(valid_locks)}")
                return
            if warn_count < 1:
                await m.reply("❌ تعداد اخطار باید بیشتر از 0 باشد")
                return
            lock_settings.setdefault(gid, {})
            lock_settings[gid][lock_type] = warn_count
            await m.reply(f"✅ تعداد اخطار برای قفل {lock_type} به {warn_count} تنظیم شد")
        except ValueError:
            await m.reply("❌ تعداد اخطار باید عدد باشد")
        return

# برسی وجود پیام در لیست قل
@bot.on_message_updates(filters.is_group)
async def check_locks(m: Update):
    guid = m.author_guid
    group = m.object_guid
    id = m.message_id
    text = m.text
    list = dict(m.to_dict.get("message", {}))
    
    if group not in active_groups:
        return
    
    roles = [creator, owners.get(group)] + special_users.get(group, [])
    is_admin = guid in roles
    
    try:
            
        list_f = loadData("lock").get(group, {})
        
        if list_f:
            text = list.get("text", "1")
            if text:
                if (not is_admin and 
                    ("@" in text or "http" in text or ".ir" in text or ".com" in text or 
                    list.get("forwarded_from", {}).get("type_from") == "Channel" or 
                    list.get("metadata", {}).get("meta_data_parts", [{}])[0].get("type") == "Link")):
                    
                    await m.delete()
                    is_das = int(list_f.get("لینک", 3))
                    if is_das < 1:
                        return True
                    
                    if is_das > 1:
                        await ekhtar(guid, group, "ارسال لینک", "لینک", is_das)
                    else:
                        await m.ban_member(group, guid)
                    
                    return True

            
            for keye, value in list_f.items():
                
                if keye == "لینک":
                    continue
                
                value = int(value)
                
                if keye == "کد هنگی":
                    if code_hangi_bug(text):
                        is_das = value
                        await m.delete()
                        if is_das < 1:
                            return True
                    
                        if is_das > 1:
                            await ekhtar(guid, group, f"ارسال {keye}", keye, is_das)
                        else:
                            await m.ban_member(group, guid)
                        return True
                    continue
                
                if keye == "انگلیسی" and not is_admin:
                    if is_english(text):
                        is_das = value
                        await bot.delete(id, group)
                        if is_das < 1:
                            return True
                        
                        if is_das > 1:
                            await ekhtar(guid, group, f"ارسال {keye}", keye, is_das)
                        else:
                            await m.ban_member(group, guid)
                        return True
                    continue
                        
                
                if keye == "فحش" and not is_admin:
                    if check_bad_words(text):
                        is_das = value
                    
                        await m.delete()
                        if is_das == 0:
                            return True
                        
                        if is_das > 1:
                            await ekhtar(guid, group, f"ارسال {keye}", keye, is_das)
                        else:
                            await m.ban_member(group, guid)
                            
                        return True
                    continue
                
                if keye == "اسپم" and not is_admin:
                    t_get = int(list.get("time", 0))
                    t_bef = listSpeam.get(guid, [])
                        
                    listSpeam[guid] = [t for t in listSpeam.get(guid, []) if t_get - t <= 2]
                    listSpeam[guid].append(t_get)
                    if len(listSpeam.get(guid, [])) > 2:
                        is_das = value
                        if is_das > 1:
                            await ekhtar(guid, group, f"ارسال {keye}", keye, is_das)
                        else:
                            await m.ban_member(group, guid)
                            
                        return True
                    continue
                
                if not is_admin and (
                    list.get("type") == typeRubika(keye) or 
                    list.get("file_inline", {}).get("type") == typeRubika(keye)
                ):
                    is_das = value
                    
                    await m.delete()
                    if is_das == 0:
                        return True
                    
                    if is_das > 1:
                        await ekhtar(guid, group, f"ارسال {keye}", keye, is_das)
                    else:
                        await m.ban_member(group, guid)
                        
                    return True
                    
    except Exception as e:
        print("error lock group")

def is_english(text):
    return bool(re.fullmatch(r"[a-zA-Z0-9\s!?.,:;\"'()\-]*", text)) and bool(re.search(r"[a-zA-Z]", text))

def typeRubika(text: str) -> str:
    # تعریف دیکشنری از معادل‌های ممکن
    replacements = {
        "گیف": "Gif",
        "عکس": "Image",
        "فیلم": "Video",
        "اهنگ": "Music",
        "آهنگ": "Music",
        "ویس": "Voice",
        "فایل": "File",
        "استوری": "RubinoStory",
        "پست": "RubinoPost",
        "اونت": "Event",
        "ایونت": "Event",
        "اعلان": "Event",
        "شیشه": "Event"
    }

    # جایگزینی کلمات بر اساس دیکشنری
    for key, value in replacements.items():
        # استفاده از regex برای شناسایی دقیق کلمات
        text = re.sub(rf'\b{key}\b', value, text, flags=re.IGNORECASE)

    return text

def check_bad_words(text: str, max_errors: int = 0) -> bool:
    """
    بررسی می‌کند که آیا متن ورودی شامل کلمات نامناسب موجود در لیست (حتی در صورت تغییرات جزئی یا استفاده از نویسه‌های نامرئی) هست یا خیر.
    
    پارامترها:
    - text: متن ورودی به عنوان رشته.
    - max_errors: تعداد خطاهای مجاز (حذف، جایگزینی یا درج کاراکتر) برای تطبیق fuzzy. مقدار پیش‌فرض ۱ است.
    
    خروجی:
    - True در صورتی که حداقل یکی از کلمات موجود در لیست در متن پیدا شود.
    - False در غیر اینصورت.
    """

    bad_words = [
        "کیر", "جنده", "کصده", "کص", "گایید", "بیناموس", "بی ناموس", "مادرتو",
        "گاییدم", "کونی", "کون", "یتیم", "اوب", "اوبی", "جینده", "جیندا",
        "کیونی", "کاندوم", "کاندومی", "حرومزاده", "حرامزاده", "حروم زاده",
        "کسکش", "کسخل", "کصخل", "کصشعر", "کسشعر", "کس شعر", "خوارتو", "خواهرتو",
        "خارتو", "ممه", "حروم زاده", "پدر سگ", "پدسگ", "مادر سگ", "کوسکش", "کوصکش", "کص ننت", "کس ننت", "ننتو"
    ]
    
    def normalize_texte(text: str) -> str:
        """
        نرمال‌سازی متن:
        - تبدیل به فرم Unicode استاندارد (NFKC)
        - حذف دیاکریتیک‌ها (علامت‌های تلفظ)
        - حذف نویسه‌های نامرئی مانند ZERO WIDTH NON-JOINER و ZERO WIDTH JOINER
        """
        normalized = unicodedata.normalize('NFKC', text)
        normalized = regex.sub(r'\p{Mn}', '', normalized)
        normalized = normalized.replace('\u200c', '').replace('\u200d', '')
        return normalized

    def create_fuzzy_pattern(word: str, max_errors: int) -> str:
        """
        ایجاد الگوی fuzzy برای یک کلمه با مجاز دانستن تا max_errors خطا (حذف، جایگزینی یا درج کاراکتر).
        """
        escaped_word = regex.escape(word)
        pattern = f"({escaped_word}){{e<={max_errors}}}"
        return pattern


    normalized_text = normalize_texte(text)
    
    
    for word in bad_words:
        norm_word = normalize_texte(word)
        pattern = create_fuzzy_pattern(norm_word, max_errors)
        # جستجوی الگوی fuzzy در متن (بدون حساسیت به حروف)
        if regex.search(pattern, normalized_text, flags=regex.IGNORECASE):
            return True
    
    return False

# مدیریت گروه (بستن، باز کردن, بن, اخطار, معاف)
@bot.on_message_updates(filters.is_group)
async def manage_and_warn(m: Update):
    gid = m.object_guid
    if gid not in active_groups:
        return
    uid = m.author_guid
    roles = [creator, owners.get(gid)] + special_users.get(gid, [])
    is_admin = uid in roles
    text = m.text or ""

    # ردیابی پیام‌ها برای تشخیص اسپم
    user_messages.setdefault(gid, {}).setdefault(uid, [])
    current_time = time.time()
    user_messages[gid][uid].append((current_time, text))
    user_messages[gid][uid] = [(t, msg) for t, msg in user_messages[gid][uid] if current_time - t <= 60]
    
    if text.strip() == "بستن گروه" and is_admin:
        
        try:
            await bot.set_group_default_access(gid, [])
            await m.reply("🔒 گروه بسته شد و هیچ کاربری نمی‌تواند پیام یا رسانه ارسال کند ✅")
        except Exception as e:
            await m.reply(f"❌ خطا در بستن گروه: {type(e).__name__}: {e}")
            logger.error(f"Error closing group: {type(e).__name__}: {e}")
        return

    if text.strip() == "باز کردن گروه" and is_admin:
        try:
            access_list = [
                "SendMessages", "AddMember"
            ]
            await bot.set_group_default_access(gid, access_list)
            logger.info(f"Group {gid} opened with access: {access_list}")
            await m.reply("🔓 گروه باز شد و کاربران می‌توانند پیام و رسانه ارسال کنند ✅")
        except Exception as e:
            await m.reply(f"❌ خطا در باز کردن گروه: {type(e).__name__}: {e}")
            logger.error(f"Error opening group: {type(e).__name__}: {e}")
            if isinstance(e, rubpy.exceptions.InvalidAuth):
                if await reconnect_bot(bot):
                    await m.reply("✅ اتصال مجدد موفق! دوباره امتحان کنید.")
                else:
                    await m.reply("❌ اتصال مجدد ناموفق! لطفاً ربات را ری‌استارت کنید.")
        return

    if text.strip().startswith("بن") and m.reply_message_id and is_admin:
        msgs = await bot.get_messages_by_id(gid, m.reply_message_id)
        target = msgs['messages'][0]['author_object_guid']
        try:
            await bot.ban_member(gid, target)
            await m.reply("🚫 کاربر بن شد ❌")
        except Exception as e:
            await m.reply(f"❌ خطا در بن کاربر: {type(e).__name__}: {e}")
            logger.error(f"Error banning user: {type(e).__name__}: {e}")
        return

    if text.strip().startswith("ان بن") and m.reply_message_id and is_admin:
        msgs = await bot.get_messages_by_id(gid, m.reply_message_id)
        target = msgs['messages'][0]['author_object_guid']
        try:
            await bot.add_group_members(gid, target)
            await m.reply("✅ کاربر آزاد شد")
        except Exception as e:
            await m.reply(f"❌ خطا در آزاد کردن کاربر: {type(e).__name__}: {e}")
            logger.error(f"Error unbanning user: {type(e).__name__}: {e}")
        return

    if text.strip() == "لیست اخطار" and is_admin:
        lines = [f"📋 اخطار‌ها (حداکثر {max_warn.get(gid, 3)})"]
        warns.setdefault(gid, {})
        for u, c in warns[gid].items():
            name = await get_name_user(bot, u)
            lines.append(f"{name} ({u}) : {c}")
        await m.reply("\n".join(lines))
        return

    if text.strip() == "حذف معاف" and m.reply_to_message_id and is_admin:
        msgs = await bot.get_messages(gid, center_message_id=m.reply_to_message_id, limit=1)
        target = msgs['messages'][0]['author_object_guid']
        exempt_users.setdefault(gid, [])
        if target in exempt_users[gid]:
            exempt_users[gid].remove(target)
            await m.reply("✅ معافیت کاربر حذف شد")
        return

    if text.strip() == "ریست اخطار" and m.reply_to_message_id and is_admin:
        msgs = await bot.get_messages(gid, center_message_id=m.reply_to_message_id, limit=1)
        target = msgs['messages'][0]['author_object_guid']
        warns.setdefault(gid, {})
        warns[gid].pop(target, None)
        await m.reply("✅ اخطار کاربر پاک شد")
        return

    if text.strip() == "معاف" and m.reply_to_message_id and is_admin:
        msgs = await bot.get_messages(gid, center_message_id=m.reply_to_message_id, limit=1)
        target = msgs['messages'][0]['author_object_guid']
        exempt_users.setdefault(gid, []).append(target)
        await m.reply("✅ کاربر از دریافت اخطار معاف شد")
        return

    # جدید: حذف تعداد پیام
    if text.strip().startswith("حذف ") and is_admin:
        try:
            parts = text.strip().split()
            if len(parts) == 2 and parts[0] == "حذف":
                num = int(parts[1])
                if num > 0:
                    current_id = int(m.message_id)
                    await delete_messages(gid, current_id, num)
                else:
                    await m.reply("❌ تعداد باید بیشتر از 0 باشد")
        except ValueError:
            await m.reply("❌ لطفاً یک عدد معتبر وارد کنید. مثال: حذف 5")
        except Exception as e:
            await m.reply(f"⚠️ خطا در حذف پیام‌ها: {type(e).__name__}: {e}")
            logger.error(f"Error deleting messages: {type(e).__name__}: {e}")
        return

    # جدید: تنظیم کاربر ویژه
    if text.strip() == "ویژه" and m.reply_to_message_id and is_admin:
        msgs = await bot.get_messages(gid, center_message_id=m.reply_to_message_id, limit=1)
        target = msgs['messages'][0]['author_object_guid']
        special_users.setdefault(gid, []).append(target)
        name = await get_name_user(bot, target)
        await m.reply(f"✅ {name} به عنوان کاربر ویژه اضافه شد")
        return

    # بررسی قفل‌ها و حذف پیام هنگام اخطار
    if gid in lock_settings:
        exempt_users.setdefault(gid, [])
        raw_json = m.raw_json or {}
        for lock_type, max_warns in lock_settings[gid].items():
            triggered = False
            if lock_type == "لینک" and any(x in text for x in ["http://", "https://", "www.", ".ir", ".com"]):
                triggered = True
            elif lock_type == "آیدی" and "@" in text:
                triggered = True
            elif lock_type == "عکس" and not text and raw_json.get('type') == "Image":
                triggered = True
            elif lock_type == "فیلم" and raw_json.get('type') == "Video":
                triggered = True
            elif lock_type == "گیف" and raw_json.get('type') == "Gif":
                triggered = True
            elif lock_type == "آهنگ" and raw_json.get('type') == "Music":
                triggered = True
            elif lock_type == "ویس" and raw_json.get('type') == "Voice":
                triggered = True
            elif lock_type == "استوری" and raw_json.get('type') == "Story":
                triggered = True
            elif lock_type == "متن نامناسب" and any(x in text.lower() for x in ["فحش", "بد", "لعنت"]):
                triggered = True
            elif lock_type == "اسپم":
                messages = user_messages[gid][uid]
                if len(messages) > 3:
                    message_texts = [msg for _, msg in messages]
                    if len(set(message_texts)) < len(message_texts):
                        triggered = True
            if triggered and m.author_guid not in exempt_users[gid]:
                warns.setdefault(gid, {}).setdefault(m.author_guid, 0)
                warns[gid][m.author_guid] += 1
                try:
                    await bot.delete_messages(gid, [m.message_id])
                    await m.reply(f"⚠️ اخطار برای {lock_type}: {warns[gid][m.author_guid]}/{max_warns} - پیام حذف شد")
                except Exception as e:
                    await m.reply(f"⚠️ اخطار برای {lock_type}: {warns[gid][m.author_guid]}/{max_warns} - خطا در حذف پیام: {type(e).__name__}: {e}")
                    logger.error(f"Error deleting message: {type(e).__name__}: {e}")
                if warns[gid][m.author_guid] >= max_warns:
                    try:
                        await bot.ban_member(gid, m.author_guid)
                        warns[gid].pop(m.author_guid, None)
                        user_messages[gid].pop(m.author_guid, None)
                        await m.reply(f"🚫 کاربر به دلیل اخطار بیش از حد ({lock_type}) حذف شد")
                    except Exception as e:
                        await m.reply(f"❌ خطا در بن کاربر: {type(e).__name__}: {e}")
                        logger.error(f"Error banning user: {type(e).__name__}: {e}")
                return

# مدیریت ویس‌کال و سایر دستورات
@bot.on_message_updates()
async def handle_messages(m: Update):
    gid = m.object_guid
    uid = m.author_guid
    text = m.text or ""
    is_group = m.chat_type == "Group"
    roles = [creator, owners.get(gid)] + special_users.get(gid, [])

    if (is_group or (not is_group and uid == creator)) and text.strip() == "لیست گروه‌ها":
        try:
            chats = await bot.get_chats()
            active_groups_list = [chat for chat in chats.get("chats", []) if chat.get("chat_type") == "Group"]
            if not active_groups_list:
                await m.reply("❌ هیچ گروه فعالی یافت نشد!")
                return
            response = "**لیست گروه‌های فعال:**\n\n"
            for group in active_groups_list:
                gid = group.get("object_guid")
                title = group.get("title", "بدون نام")
                created_at = group.get("created_at") or group.get("time")
                created_at_str = datetime.fromtimestamp(created_at).strftime("%Y-%m-%d %H:%M:%S") if created_at else "نامشخص"
                try:
                    link = (await bot.get_group_link(gid)).get("join_link", "لینک موجود نیست")
                except Exception:
                    link = "لینک موجود نیست"
                response += f"📌 **گروه**: {title}\n🔢 **GUID**: {gid}\n🔗 **لینک**: {link}\n⏰ **زمان اضافه شدن**: {created_at_str}\n\n"
            await m.reply(response)
        except rubpy.exceptions.InvalidAuth:
            await m.reply("❌ خطای احراز هویت! در حال تلاش برای اتصال مجدد...")
            if await reconnect_bot(bot):
                await m.reply("✅ اتصال مجدد موفق! دوباره امتحان کنید.")
            else:
                await m.reply("❌ اتصال مجدد ناموفق! لطفاً ربات را ری‌استارت کنید.")
        except Exception as e:
            await m.reply(f"❌ خطا در دریافت لیست گروه‌ها: {type(e).__name__}: {e}")
        return

    if is_group and uid == creator and text.strip().startswith("ترک گروه "):
        try:
            days = int(text.strip().split()[-1])
            if days <= 0:
                await m.reply("❌ تعداد روزها باید بیشتر از 0 باشد!")
                return
            expiry_time = datetime.now() + timedelta(days=days)
            group_expiry[gid] = expiry_time
            notified_groups.pop(gid, None)
            await m.reply(f"✅ گروه بعد از {days} روز ترک خواهد شد. زمان انقضا: {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}")
        except ValueError:
            await m.reply("❌ لطفاً یک عدد معتبر برای روزها وارد کنید! مثال: ترک گروه 20")
        except Exception as e:
            await m.reply(f"❌ خطا در تنظیم ترک گروه: {type(e).__name__}: {e}")
        return

    if (is_group or (not is_group and uid == creator)) and text.strip() == "شارژ":
        try:
            expiry_time = datetime.now() + timedelta(days=20)
            group_expiry[gid] = expiry_time
            notified_groups.pop(gid, None)
            await m.reply(f"✅ شارژ گروه تمدید شد! زمان انقضای جدید: {expiry_time.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            await m.reply(f"❌ خطا در شارژ گروه: {type(e).__name__}: {e}")
        return

# مدیریت ادمین‌ها
@bot.on_message_updates(filters.is_group)
async def manage_admins(m: Update):
    gid = m.object_guid
    uid = m.author_guid
    text = m.text or ""
    roles = [creator, owners.get(gid)] + special_users.get(gid, [])
    is_admin = uid in roles

    if not is_admin or not m.reply_message_id:
        return

    mw = await bot.get_messages_by_id(gid, m.reply_message_id)
    msgs = mw.original_update
    target = msgs['messages'][0]['author_object_guid']
    target_name = await get_name_user(bot, target)

    if text.strip() == "ارتقا":
        try:
            await bot.set_group_admin(gid, target, access_list=["DeleteGlobalAllMessages", "BanMember"])
            await m.reply(f"✅ {target_name} به ادمین گروه ارتقا یافت.")
        except Exception as e:
            await m.reply(f"❌ خطا در ارتقای ادمین: {type(e).__name__}: {e}")
        return

    if text.strip() == "ارتقای کامل":
        try:
            await bot.set_group_admin(gid, target, access_list=[
                "SetJoinLink", "BanMember", "SetAdmin", "ChangeInfo",
                "PinMessages", "SetMemberAccess", "DeleteGlobalAllMessages"
            ])
            await m.reply(f"✅ {target_name} به ادمین کامل گروه ارتقا یافت.")
        except Exception as e:
            await m.reply(f"❌ خطا در ارتقای کامل ادمین: {type(e).__name__}: {e}")
        return

    if text.strip() == "برکناری":
        try:
            await bot.set_group_admin(gid, target, action="UnsetAdmin")
            await m.reply(f"✅ {target_name} از ادمینی گروه برکنار شد.")
        except Exception as e:
            await m.reply(f"❌ خطا در برکناری ادمین: {type(e).__name__}: {e}")
        return

# نمایش لیست قفل‌ها
@bot.on_message_updates(filters.is_group)
async def list_locks(m: Update):
    group = m.object_guid
    uid = m.author_guid
    text = m.text or ""
    id = m.message_id
    
    LOCKABLE_TYPES = {
        "گیف": "Gif",
        "عکس": "Image",
        "فیلم": "Video",
        "آهنگ": "Music",
        "ویس": "Voice",
        "فایل": "File",
        "استوری": "RubinoStory",
        "پست": "RubinoPost",
        "کد هنگی": "Text",
        "لینک": "Text",
        "ایونت": "Event",
        "فحش": "Text",
        "اسپم": "Text",
        "انگلیسی": "Text",
        "جوین تکراری": "Text"
        }


    if text.startswith("قفل "):
        tex = text.replace("قفل ", "", 1).replace("،،", "،")
        liste_l = tex.split("،")

        if len(liste_l) > 0:
            data = loadData("lock").get(group, {})  # خواندن اطلاعات قفل‌ها
            az = False
            for value in liste_l:
                converted_value = value.replace("اهنگ", "آهنگ").strip()
                if converted_value in LOCKABLE_TYPES and converted_value not in data:
                    az = True
                    if converted_value == "ایونت":
                        inp = {converted_value : 0}
                    else:
                        inp = {converted_value : 3}
            if az:
                saveData(inp, "lock", sub_key=group)  # ذخیره‌سازی لیست قفل‌ها
                await m.reply("با موفقیت به لیست قفل‌ها اضافه شد")
        else:
            await m.reply("دستوری یافت نشد یا کلمه معتبر نبود")
        return True

    
    if text.startswith("حذف قفل "):
        tex = text.replace("حذف قفل ", "", 1).replace("،،", "،")
        liste_l = tex.split("،")

        if len(liste_l) > 0:
            data = loadData("lock").get(group, {})
            for value in liste_l:
                converted_value = value.strip()
                if converted_value in data:
                    removeKey(converted_value, "lock", group)
            
            await m.reply("با موفقیت از لیست قفل‌ها حذف شد")
        else:
            await m.reply("دستوری یافت نشد یا کلمه معتبر نبود")
        return True

    
    if text == "لیست قفل":
        
        data = loadData("lock").get(group, {})
            
        liste = "لیست قفل‌ها:\n"
        for key, value in LOCKABLE_TYPES.items():
            if key in data:
                val = int(data[key])
                if key == "ایونت":
                    liste += "\n" + f"- {key} : [✅][حذف]"
                else:
                    liste += "\n" + f"- {key} : [✅][{val}]"
                    
            else:
                liste += "\n" + f"- {key} : [❌]"
        
        liste += "\n\n[ایونت] همان پیام هایه شیشه‌ای هستند"
        liste += "\nدریافت راهنمایی کامل لیست قفل : ^راهنما قفل^"
        
        await m.reply(liste)
        return True
        
    
    if text.startswith("تنظیم اخطار ") or text.startswith("تنظیم ") and re.search(r"\d+$", text):
        try:
            tex = text.replace("تنظیم اخطار", "", 1).strip()
            tex = text.replace("تنظیم", "", 1).strip()
            
            match = re.search(r"(\d+)$", tex)
            number_str = match.group(1)
            number = int(number_str)
            tex = tex[: -len(str(number))].strip()
            if number > 10 or number < 0:
                await m.reply("تعداد اخطار باید بین 0 تا 10 تنظیم بشه")
                return True
            
            data = loadData("lock").get(group, {})
            if tex == "ایونت":
                await m.reply("ایونت ها قابل تنظیم نیستند و فقط حذف میشوند")
                return True
            
            if tex in data:
                inp = {tex: number}
                saveData(inp, "lock", sub_key=group)
                await m.reply(f"تعداده اخطاره {tex} به {number} تا تنظیم شد")
            else:
                await m.reply(f"مقدار {tex} قفل نشده است\nبرایه قفل شدن ^قفل {tex}^")
        except Exception as e:
            pass
        return True
    
    
    if text == "راهنما قفل":
        tex = """
    🔒 راهنمای استفاده از قفل گروه:

    💡 1. دریافت لیست پیام‌های قفل‌شده
    
    برای مشاهده لیست پیام‌های قفل‌شده و مجاز به قفل، فقط کلمه *لیست قفل* را ارسال کنید. این لیست به شما کمک می‌کند که متوجه شوید چه مواردی قبلاً قفل شده‌اند.

    💬 2. قفل کردن یک پیام
    بعد از مشاهده لیست، برای قفل کردن یک پیام خاص، فقط کافیست کلمه `قفل` را همراه با نام پیام ارسال کنید.
    مثال: 
    {قفل کد هنگی}

    ⚠️ 3. پیام‌های قفل شده و پیش‌فرض‌ها
    
    هر پیام که قفل می‌شود، به صورت خودکار برای ارسال‌کننده یک اخطار ارسال خواهد شد. مثلاً اگر کسی **کد هنگی** ارسال کند، به طور خودکار اخطار دریافت خواهد کرد.

    🔧 4. تنظیمات اخطار خاص برای قفل
    
    برای تنظیم تعداد اخطار برایه یه قفل کافیه اول بنویسید `تنظیم اخطار ... 3` جایه ... نام قفل
    - {تنظیم اخطار کد هنگی 3} → تعداد اخطار هایه مربوط به هر قفل تنظیم میشود
    
    اگر میخواهید اخطاری ارسال نشود و فقط پیام حذف شود برایه اخطار 0 بگذارید
    - {تنظیم اخطار کد هنگی 0} → در این صورت فقط حذف میشود و بدون اخطار است

    🗑 5. حذف قفل
    
    اگر خواستید یک قفل را حذف کنید، ابتدا کلمه `حذف قفل` را بنویسید و سپس نام پیام قفل‌شده را وارد کنید.
    مثال:
    {حذف قفل کد هنگی}

    ✅ با استفاده از این راهنما می‌توانید به راحتی پیام‌های ناخواسته را کنترل کنید و از گروه خود محافظت کنید!
        """.strip()

        await m.reply(tex)
        return True


# لیست کاربران معاف
@bot.on_message_updates(filters.is_group)
async def exempt_list(m: Update):
    gid = m.object_guid
    uid = m.author_guid
    text = m.text or ""
    roles = [creator, owners.get(gid)] + special_users.get(gid, [])
    if text.strip() != "لیست معاف" or uid not in roles:
        return
    ids = exempt_users.get(gid, [])
    if not ids:
        await m.reply("❌ هیچ کاربری معاف نیست")
        return
    names = []
    for u in ids:
        try:
            info = await bot.get_user_info(u)
            name = info['user'].get('first_name', '-') + " " + info['user'].get('last_name', '')
            names.append(f"• {name.strip()} ({u})")
        except:
            names.append(f"• (نامشخص) ({u})")
    await m.reply("📋 کاربران معاف:\n" + "\n".join(names))

# یادگیری هوشمند
@bot.on_message_updates(filters.is_group)
async def smart_learning_system(m: Update):
    gid = m.object_guid
    uid = m.author_guid
    text = m.text or ""
    roles = [creator, owners.get(gid)] + special_users.get(gid, [])
    is_admin = uid in roles

    if is_admin and m.reply_to_message_id and text.strip() == "سیو":
        msgs = await bot.get_messages(gid, center_message_id=m.reply_to_message_id, limit=1)
        msg = msgs['messages'][0]
        learn_data.setdefault(str(gid), {})
        count = len(learn_data[str(gid)]) + 1
        key = f"gif{count}"
        if 'file_inline' in msg:
            learn_data[str(gid)][key] = {'type': 'media', 'content': msg['file_inline']}
        elif 'text' in msg:
            learn_data[str(gid)][key] = {'type': 'text', 'content': [msg['text']]}
        else:
            await m.reply("❌ این پیام قابل ذخیره نیست.")
            return
        save_learn_data()
        await m.reply(f"✅ ذخیره شد با کلید: {key}")
        return

    if is_admin and "!" in text and not m.reply_to_message_id:
        try:
            key, values = text.split("!", 1)
            options = [v.strip() for v in values.split(",,")]
            learn_data.setdefault(str(gid), {})
            learn_data[str(gid)][key.strip()] = {'type': 'text', 'content': options}
            save_learn_data()
            await m.reply(f"✅ پاسخ «{key.strip()}» ذخیره شد")
        except:
            await m.reply("❌ فرمت اشتباه است. مثال:\nسلام!سلام ,, درود")
        return

    if text.strip() in learn_data.get(str(gid), {}):
        data = learn_data[str(gid)][text.strip()]
        if data["type"] == "text":
            content = data["content"]
            if isinstance(content, list):
                await m.reply(random.choice(content))
            else:
                await m.reply(content)
        elif data["type"] == "media":
            await bot.send_file(gid, data["content"])
        return

# مدیریت کلیدهای یادگیری
@bot.on_message_updates(filters.is_group)
async def manage_learned_keys(m: Update):
    gid = m.object_guid
    uid = m.author_guid
    text = m.text or ""
    roles = [creator, owners.get(gid)] + special_users.get(gid, [])
    is_admin = uid in roles

    if is_admin and text.startswith("حذف "):
        key = text.replace("حذف", "").strip()
        if key in learn_data.get(str(gid), {}):
            learn_data[str(gid)].pop(key)
            save_learn_data()
            await m.reply(f"❌ کلید «{key}» حذف شد")
        else:
            await m.reply("❌ چنین کلیدی ذخیره نشده")
        return

    if is_admin and text.strip() == "لیست کلیدها":
        keys = list(learn_data.get(str(gid), {}).keys())
        if not keys:
            await m.reply("❌ هیچ کلیدی ذخیره نشده")
            return
        msg = "📌 کلیدهای ذخیره‌شده:\n" + "\n".join(f"• {k}" for k in keys)
        await m.reply(msg)
        return

    if is_admin and "ویرایش" in text and "!" in text:
        try:
            part = text.replace("ویرایش", "").strip()
            key, values = part.split("!", 1)
            options = [v.strip() for v in values.split(",,")]
            if key.strip() in learn_data.get(str(gid), {}):
                learn_data[str(gid)][key.strip()] = {'type': 'text', 'content': options}
                save_learn_data()
                await m.reply(f"✅ کلید «{key.strip()}» ویرایش شد")
            else:
                await m.reply("❌ چنین کلیدی وجود ندارد")
        except:
            await m.reply("❌ فرمت نادرست. مثال:\nویرایش سلام!سلام ,, درود")
        return

# چالش تصادفی
@bot.on_message_updates(filters.is_group)
async def send_random_chalesh(m: Update):
    text = m.text or ""
    if text.strip() == "چالش":
        if chalesh_lines:
            choice = random.choice(chalesh_lines)
            await m.reply(choice)
        else:
            await m.reply("❌ فایل چالش‌ها خالی است یا خطایی رخ داده است!")
        return

# حالت اضطراری
@bot.on_message_updates(filters.is_group)
async def emergency_mode(m: Update):
    gid = m.object_guid
    uid = m.author_guid
    text = m.text or ""
    roles = [creator, owners.get(gid)]
    is_admin = uid in roles
    if not is_admin:
        return

    if text.strip() == "حالت اضطراری":
        pending_confirm[gid] = 'emergency'
        await m.reply(
            "🚨 حالت اضطراری فعال خواهد شد:\n"
            "🔁 لینک گروه تغییر می‌کند\n"
            "🔒 گروه بسته می‌شود\n"
            "🧹 لیست معاف پاک می‌شود\n"
            "🗑 حذف حداکثر ۲۰ پیام اخیر\n"
            "🖼 نام و عکس گروه قفل می‌شود\n\n"
            "آیا تأیید می‌کنی؟ (بله/خیر)"
        )
        return

    if pending_confirm.get(gid) == 'emergency':
        if text.strip() != "بله":
            pending_confirm.pop(gid, None)
            await m.reply("❌ لغو شد.")
            return
        exempt_users.setdefault(gid, [])
        backup_exempt[gid] = exempt_users[gid].copy()
        exempt_users[gid] = []
        await m.reply("🧹 لیست معاف پاک شد")
        try:
            raw = await bot.get_group_info(gid)
            info = raw if isinstance(raw, dict) else {}
            grp = info.get("group", {}) if isinstance(info.get("group"), dict) else info
            original_info[gid] = {
                "title": grp.get("group_title"),
                "photo": grp.get("group_photo")
            }
            await m.reply("🖼 اطلاعات گروه ذخیره شد")
        except Exception as e:
            await m.reply(f"⚠️ خطا در دریافت اطلاعات گروه: {type(e).__name__}: {e}")
            logger.error(f"Error saving group info: {type(e).__name__}: {e}")
        try:
            await bot.set_group_link(gid)
            await m.reply("✅ لینک گروه عوض شد")
        except Exception as e:
            await m.reply(f"❌ خطا در تغییر لینک گروه: {type(e).__name__}: {e}")
            logger.error(f"Error changing group link: {type(e).__name__}: {e}")
        try:
            await bot.set_group_default_access(gid, [])
            await m.reply("🔒 گروه بسته شد")
        except Exception as e:
            await m.reply(f"❌ خطا در بستن گروه: {type(e).__name__}: {e}")
            logger.error(f"Error closing group: {type(e).__name__}: {e}")
        try:
            current_id = int(m.message_id)
            await delete_messages(gid, current_id, 20)
        except Exception as e:
            await m.reply(f"⚠️ خطا در حذف پیام‌ها: {type(e).__name__}: {e}")
            logger.error(f"Error deleting messages: {type(e).__name__}: {e}")
        emergency_active[gid] = True
        pending_confirm.pop(gid, None)
        await m.reply("✅ حالت اضطراری فعال شد.")
        return

    if text.strip() == "حالت عادی":
        pending_confirm[gid] = 'normal'
        await m.reply("♻️ بازگشت به حالت عادی؟ (بله/خیر)")
        return

    if pending_confirm.get(gid) == 'normal':
        if text.strip() != "بله":
            pending_confirm.pop(gid, None)
            await m.reply("❌ لغو شد.")
            return
        exempt_users[gid] = backup_exempt.get(gid, []).copy()
        try:
            access_list = [
                "SendMessages", "AddMember"
            ]
            await bot.set_group_default_access(gid, access_list)
            logger.info(f"Group {gid} opened with access: {access_list}")
            await m.reply("🔓 گروه باز شد")
        except Exception as e:
            await m.reply(f"❌ خطا در باز کردن گروه: {type(e).__name__}: {e}")
            logger.error(f"Error opening group: {type(e).__name__}: {e}")
            if isinstance(e, rubpy.exceptions.InvalidAuth):
                if await reconnect_bot(bot):
                    await m.reply("✅ اتصال مجدد موفق! دوباره امتحان کنید.")
                else:
                    await m.reply("❌ اتصال مجدد ناموفق! لطفاً ربات را ری‌استارت کنید.")
        emergency_active[gid] = False
        pending_confirm.pop(gid, None)
        await m.reply("✅ گروه به حالت عادی بازگشت.")
        return

    if emergency_active.get(gid):
        try:
            raw = await bot.get_group_info(gid)
            info = raw if isinstance(raw, dict) else {}
            grp = info.get("group", {}) if isinstance(info.get("group"), dict) else info
            old = original_info.get(gid, {})
            if old.get("title") and grp.get("group_title") != old["title"]:
                await bot.update_group_title(gid, old["title"])
                await m.reply("🖼 عنوان گروه به حالت اولیه بازگشت")
            if old.get("photo") and grp.get("group_photo") != old["photo"]:
                await bot.update_group_photo(gid, old["photo"])
                await m.reply("🖼 عکس گروه به حالت اولیه بازگشت")
        except Exception as e:
            await m.reply(f"⚠️ خطا در پایداری حالت اضطراری: {type(e).__name__}: {e}")
            logger.error(f"Error maintaining emergency mode: {type(e).__name__}: {e}")

# بازی حدس ایموجی
@bot.on_message_updates(filters.is_group)
async def emoji_game(m: Update):
    gid = m.object_guid
    uid = m.author_guid
    text = m.text or ""
    roles = [creator, owners.get(gid)] + special_users.get(gid, [])
    is_admin = uid in roles

    if text.strip() == "بازی ایموجی" and is_admin:
        if emoji_game_active.get(gid, False):
            await m.reply("⚠️ بازی در حال اجرا است!")
            return
        emoji_game_active[gid] = True
        emoji_game_scores.setdefault(gid, {})
        emoji_game_round[gid] = 0
        for round_num in range(10):
            if not emoji_game_active.get(gid, False):
                break
            emoji_game_round[gid] = round_num + 1
            current_emoji = random.choice(emoji_list)
            emoji_game_current[gid] = current_emoji
            await m.reply(f"🎮 **دور {emoji_game_round[gid]}/10**\nایموجی: {current_emoji}\nنام ایموجی را حدس بزن! 10 ثانیه وقت داری! ⏳")
            await asyncio.sleep(10)
            emoji_game_current[gid] = None
        if emoji_game_active.get(gid, False):
            emoji_game_active[gid] = False
            scores = emoji_game_scores.get(gid, {})
            if not scores:
                await m.reply("🏆 **نتایج بازی حدس ایموجی**\nهیچ امتیازی ثبت نشد! 😔")
                return
            leaderboard = ["🏆 **نتایج بازی حدس ایموجی**"]
            for user_id, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
                try:
                    name = await get_name_user(bot, user_id)
                    leaderboard.append(f"**{name}**: {score} امتیاز")
                except:
                    leaderboard.append(f"کاربر {user_id[:8]}...: {score} امتیاز")
            await m.reply("\n".join(leaderboard))
            for user_id, score in scores.items():
                try:
                    name = await get_name_user(bot, user_id)
                    await bot.send_message(user_id, f"🏆 **نتایج بازی حدس ایموجی در گروه**\nامتیاز شما: {score}\nنام: {name}\nممنون که بازی کردی! 😊")
                except Exception as e:
                    await m.reply(f"❌ خطا در ارسال پیام به کاربر {user_id[:8]}...: {type(e).__name__}: {e}")
            emoji_game_scores.pop(gid, None)
            emoji_game_round.pop(gid, None)
        return

    if emoji_game_active.get(gid, False) and emoji_game_current.get(gid):
        current_emoji = emoji_game_current[gid]
        correct_name = emoji_names[current_emoji]
        if text.strip() == correct_name:
            emoji_game_scores[gid].setdefault(uid, 0)
            emoji_game_scores[gid][uid] += 1
            try:
                name = await get_name_user(bot, uid)
                await m.reply(f"✅ درست حدس زدی، **{name}**! +1 امتیاز")
            except:
                await m.reply(f"✅ درست حدس زدی! +1 امتیاز")
        elif text.strip() and text.strip() in emoji_names.values():
            await m.reply(f"❌ غلط بود! نام درست: **{correct_name}**")
        return

# نمایش راهنما
@bot.on_message_updates(filters.is_group)
async def show_help(m: Update):
    text = m.text or ""
    if text.strip() == "راهنما":
        await m.reply("""
📘 *راهنمای ربات مدیریتی روبیکا*

🛡 **دستورات مدیریت گروه:**
• فعال — فعال‌سازی ربات در گروه
• مالک @username — تعیین مالک گروه
• بستن گروه / باز کردن گروه
• بن / آن‌بن — با ریپلای
• ارتقا — ارتقای کاربر به ادمین (با ریپلای)
• ارتقای کامل — ارتقای کاربر به ادمین کامل (با ریپلای)
• برکناری — حذف کاربر از ادمینی (با ریپلای)
• تغییر لینک — ایجاد لینک دعوت جدید برای گروه
• حالت اضطراری — تغییر لینک، بستن گروه، حذف پیام‌ها و معاف‌ها
• حالت عادی — بازگشت به حالت عادی
• قفل [نوع] — فعال‌سازی قفل (مثال: قفل لینک، قفل اسپم، قفل آیدی)
• باز کردن قفل [نوع] — غیرفعال کردن قفل
• قفل همه — فعال‌سازی تمام قفل‌ها
• باز کردن قفل همه — غیرفعال کردن تمام قفل‌ها
• تنظیم اخطار [نوع] [تعداد] — تنظیم تعداد اخطار
• لیست قفل — نمایش وضعیت قفل‌های گروه
• معاف / حذف معاف — با ریپلای
• لیست اخطار / ریست اخطار — مدیریت اخطارها
• لیست معاف — افراد معاف از اخطار

🔒 **قفل‌ها:**
• لینک — http, .com, .ir و ...
• آیدی — هر نوع @
• عکس / فیلم / گیف / ویس / آهنگ / استوری
• متن نامناسب — فحش، کلمات زشت
• اسپم — پیام‌های طولانی یا پشت سر هم

📚 **یادگیری پاسخ:**
• پیام: `کلید!پاسخ`
• رسانه: ریپلای + `کلید!`
• ارسال با تایپ `کلید`

👥 **نقش‌ها:**
• سازنده: کنترل کامل
• مالک: مدیر گروه
• ویژه: قدرت‌هایی مثل بن، تنظیم قفل، آمار، ویس‌کال، ارتقای ادمین
• کاربر: عضو عادی

🎯 **دیگر امکانات:**
• خوش‌آمد خودکار — هنگام ورود عضو جدید
• بازی کوروش — حدس عدد 1 تا 10
• بازی ایموجی — حدس نام ایموجی در 10 دور
• آمارم — نمایش اطلاعات شما
• چالش — ارسال یک چالش تصادفی
• کال — ایجاد تماس صوتی گروهی
• قطع کال — متوقف کردن تماس صوتی گروهی

📎 *دستورات را بدون فاصله اضافی و در حالت فارسی ارسال کنید*
""")

# --- شروع کد CortexAii کامل + ویسکال ---


# دیتابیس
class BotDatabase:
    def __init__(self, db_file="bot_data.json"):
        self.db_file = db_file
        self.data = self._load_data()

    def _load_data(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return self._default_data()
        return self._default_data()

    def _default_data(self):
        return {
            "users": {},
            "settings": {
                "strict_mode": False,
                "filters": {
                    "gif": False,
                    "story": False,
                    "photo": False,
                    "voice": False,
                    "video": False,
                    "other_files": False
                },
                "voice_call_active": True
            }
        }

    def _save_data(self):
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4, ensure_ascii=False)
        except:
            pass

    def get_user_data(self, guid):
        return self.data["users"].get(guid, {})

    def update_user_data(self, guid, key, value):
        if guid not in self.data["users"]:
            self.data["users"][guid] = {}
        self.data["users"][guid][key] = value
        self._save_data()

    def increment_message_count(self, guid):
        if guid not in self.data["users"]:
            self.data["users"][guid] = {"messages_count": 0}
        self.data["users"][guid]["messages_count"] = self.data["users"][guid].get("messages_count", 0) + 1
        self._save_data()

    def set_strict_mode(self, status):
        self.data["settings"]["strict_mode"] = status
        self._save_data()

    def get_strict_mode(self):
        return self.data["settings"]["strict_mode"]

    def set_filter(self, ftype, status):
        if ftype in self.data["settings"]["filters"]:
            self.data["settings"]["filters"][ftype] = status
            self._save_data()

    def get_filter_status(self, ftype):
        return self.data["settings"]["filters"].get(ftype, False)

    def set_voice_call_status(self, status):
        self.data["settings"]["voice_call_active"] = status
        self._save_data()

    def get_voice_call_status(self):
        return self.data["settings"]["voice_call_active"]


db = BotDatabase()
SILENT_USERS = {}
HANG_PATTERNS = [
    r"(22\.){15,}",
    r"(\d{1,3}\.){8,}",
    r"([^\w\s]{4,}){8,}",
    r"(\w{1,3}\s*){30,}",
]

def is_hang_message(text):
    if isinstance(text, str):
        for p in HANG_PATTERNS:
            if re.search(p, text):
                return True
    return False


@bot.on_chat_updates()
async def cortexai_welcome(m: Update):
    if m.update_type == "NewMessage" and m.message and m.message.type == "Event":
        event_type = m.message.event_data.get("type")
        gid = m.object_guid

        if event_type == "AddGroupMembers":
            for uid in m.message.event_data.get("peer_guids", []):
                try:
                    info = await bot.get_user_info(uid)
                    name = info["user"].get("first_name", "کاربر")
                    if info["user"].get("last_name"):
                        name += " " + info["user"]["last_name"]

                    join_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    db.update_user_data(uid, "name", name)
                    db.update_user_data(uid, "join_date", join_date)
                    db.update_user_data(uid, "messages_count", 0)
                    db.update_user_data(uid, "warnings", 0)
                    db.update_user_data(uid, "title", "")
                    db.update_user_data(uid, "is_original", False)

                    await bot.send_message(gid, f"سلام {name} عزیز! خوش آمدی 🌹\n⏰ {join_date}")
                except:
                    pass

        elif event_type == "RemoveGroupMembers":
            for uid in m.message.event_data.get("peer_guids", []):
                try:
                    name = db.get_user_data(uid).get("name", "کاربر")
                    await bot.send_message(gid, f"کاربر {name} گروه را ترک کرد.")
                except:
                    pass


@bot.on_message_updates()
async def cortexai_manager(m: Update):
    gid = m.object_guid
    uid = m.author_guid
    mid = m.message_id
    mtype = m.type
    text = m.text or ""

    if uid == bot.guid:
        return

    # حذف هنگ
    if mtype == "Text" and is_hang_message(text):
        await bot.delete_messages(gid, [mid])
        return

    # سکوت
    if uid in SILENT_USERS:
        if datetime.now() < SILENT_USERS[uid]:
            await bot.delete_messages(gid, [mid])
            return
        else:
            del SILENT_USERS[uid]

    if mtype == "Text":
        db.increment_message_count(uid)

    # آمار
    if text == "آمارم":
        d = db.get_user_data(uid)
        await bot.send_message(gid,
            f"📊 آمار {d.get('name','شما')}:\n"
            f"👑 لقب: {d.get('title','ندارد')}\n"
            f"💬 پیام‌ها: {d.get('messages_count',0)}\n"
            f"⚠️ اخطارها: {d.get('warnings',0)}\n"
            f"📝 اصل: {'ثبت شده' if d.get('is_original',False) else 'ثبت نشده'}\n"
            f"🕰️ ورود: {d.get('join_date','نامشخص')}",
            reply_to_message_id=mid
        )

    # اصل
    elif text.startswith("اصل "):
        content = text[4:].strip()
        if content:
            db.update_user_data(uid, "is_original", content)
            await bot.send_message(gid, f"✅ اصل شما ثبت شد: '{content}'", reply_to_message_id=mid)
        else:
            await bot.send_message(gid, "بعد از 'اصل' متن را وارد کنید.", reply_to_message_id=mid)

    elif text == "اصل":
        d = db.get_user_data(uid)
        await bot.send_message(gid, f"اصل شما: '{d.get('is_original','ثبت نشده')}'", reply_to_message_id=mid)



# --- شروع بخش مدیریت مالک، حذف پیام و پینگ ---



BOT_CREATOR_GUID = bot.guid
BOT_CREATOR_LINK = None
GROUP_OWNER_GUID = None
GROUP_OWNER_LINK = None

async def get_user_link(user_guid):
    """برگشت لینک مستقیم پروفایل حتی بدون username"""
    try:
        info = await bot.get_user_info(user_guid)
        username = info["user"].get("username")
        if username:
            return f"https://rubika.ir/{username}"
        else:
            return f"https://rubika.ir/user/{user_guid}"  # لینک مستقیم بدون یوزرنیم
    except:
        return None

async def get_group_owner(gid):
    """گرفتن اطلاعات مالک گروه"""
    try:
        group_info = await bot.get_group_info(gid)
        return group_info["group"].get("creator_guid")
    except:
        return None

@bot.on_message_updates()
async def owner_delete_ping(m):
    global GROUP_OWNER_GUID, GROUP_OWNER_LINK, BOT_CREATOR_LINK

    gid = m.object_guid
    uid = m.author_guid
    text = (m.text or "").strip()

    # گرفتن لینک سازنده یکبار
    if BOT_CREATOR_LINK is None:
        BOT_CREATOR_LINK = await get_user_link(BOT_CREATOR_GUID)

    # گرفتن مالک گروه یکبار
    if GROUP_OWNER_GUID is None:
        GROUP_OWNER_GUID = await get_group_owner(gid)
        if GROUP_OWNER_GUID:
            GROUP_OWNER_LINK = await get_user_link(GROUP_OWNER_GUID)

    # بررسی نقش مجاز
    role_ok = (
        uid == BOT_CREATOR_GUID or
        uid == GROUP_OWNER_GUID or
        db.get_user_data(uid).get("role") == "ویژه"
    )

    # ارسال لینک سازنده
    if text == "سازنده" and BOT_CREATOR_LINK:
        await bot.send_message(gid, f"[سازنده]({BOT_CREATOR_LINK})", link_preview=True)

    # ارسال لینک مالک
    if text == "مالک" and GROUP_OWNER_LINK:
        await bot.send_message(gid, f"[مالک]({GROUP_OWNER_LINK})", link_preview=True)

# ---------------- VoiceCallBuilder (شروع / قطع ویسکال) ----------------
from typing import Union, Optional

class VoiceCallBuilder:
    """
    یک بیلدر ساده برای مدیریت ویس‌کال گروه:
    usage:
        v = VoiceCallBuilder(bot).for_group(gid)
        await v.start()   # شروع ویسکال
        await v.stop()    # قطع ویسکال (اگر voice_chat_id شناخته شده باشد)
    این بیلدر چند امضا/حالت مختلف را امتحان می‌کند تا با انواع پیاده‌سازی‌های rubpy سازگار باشد.
    """
    def __init__(self, client):
        self.client = client
        self.gid = None
        self.voice_chat_id = None
        self.logger = logger  # فرض بر این است logger قبلاً تعریف شده است

    def for_group(self, gid: str):
        self.gid = gid
        return self

    def with_voice_id(self, voice_chat_id: Union[str, int, None]):
        self.voice_chat_id = voice_chat_id
        return self

    async def start(self) -> Optional[dict]:
        if not self.gid:
            raise ValueError("group id (gid) باید تنظیم شود: use .for_group(gid)")

        trials = [
            (("group_guid",), {"group_guid": self.gid}),
            ((self.gid,), {}),
            ((), {}),
        ]

        if hasattr(self.client, "create_group_voice_chat"):
            func = self.client.create_group_voice_chat
            for args_names, kwargs in trials:
                args = []
                if args_names and args_names[0] == "group_guid":
                    args = []
                    kwargs = {"group_guid": self.gid}
                elif args_names and args_names[0] == self.gid:
                    args = (self.gid,)
                try:
                    resp = await func(*args, **kwargs)
                    try:
                        if isinstance(resp, dict):
                            vid = resp.get("voice_chat_id") or resp.get("voiceChatId") or resp.get("voice_id")
                            if not vid:
                                g = resp.get("group") or {}
                                vid = g.get("voice_chat_id") or g.get("voiceChatId")
                        else:
                            vid = None
                    except Exception:
                        vid = None

                    if vid:
                        self.voice_chat_id = vid
                    return resp if isinstance(resp, dict) else {"result": resp}
                except Exception as e:
                    self.logger.warning(f"create_group_voice_chat trial failed: {type(e).__name__}: {e}")
                    continue

        self.logger.error("All trials for create_group_voice_chat failed.")
        return None

    async def stop(self) -> Optional[dict]:
        if not self.gid or not self.voice_chat_id:
            self.logger.error("gid or voice_chat_id is missing.")
            return None


async def discard_group_voice_chat(group_guid: str, voice_chat_id: str):
    return await bot.builder(
        name="discardGroupVoiceChat",
        input={
            "group_guid": group_guid,
            "voice_chat_id": voice_chat_id
        },
        dict=True
    )


# ---------------- هندلرهای قدرتمند مدیریت ویس (اصلاح شده) ----------------

# این تابع دستی چک میکنه ببینه تو گروه ویس هست یا نه و آیدیشو میکشه بیرون
async def get_live_voice_id(gid):
    try:
        # دریافت اطلاعات تازه از گروه
        info = await bot.get_group_info(gid)
        vid = info.chat.group_voice_chat_id
        return vid
    except Exception as e:
        print(f"Error fetching voice ID: {e}")
        return None

is_deleting = False  # قفل برای جلوگیری از اجرای همزمان

async def delete_messages(gid, start_id, limit=100):
    global is_deleting

    # اگر قبلاً در حال حذف پیام بوده
    if is_deleting:
        await bot.send_message(gid, "⚠️ عملیات حذف پیام در حال انجام است. لطفاً صبر کنید.")
        return

    # فعال کردن قفل
    is_deleting = True

    collected_ids = []
    next_id = start_id

    try:
        while len(collected_ids) < limit:
            result = await bot.get_messages_interval(gid, next_id)
            result = result.original_update
            messages = result.get("messages", [])

            if not messages:
                break

            for msg in messages:
                if len(collected_ids) < limit:
                    collected_ids.append(msg["message_id"])
                else:
                    break

            if result.get("old_has_continue"):
                next_id = result.get("old_max_id")
            else:
                break

        # حذف پیام‌ها 40تایی
        for i in range(0, len(collected_ids), 40):
            chunk = collected_ids[i:i+40]
            await bot.delete_messages(gid, chunk)

        await bot.send_message(gid, f"✔️ {len(collected_ids)} پیام حذف شد.")

    except Exception as e:
        await bot.send_message(gid, f"❌ خطا: {e}")

    finally:
        # آزاد کردن قفل حتی اگر خطا رخ دهد
        is_deleting = False


def code_hangi_bug(self, text):
    try:
        digit_count = sum(char.isdigit() for char in text)
        dot_count = text.count('.')
        return dot_count > 20
    except Exception as e:
        return False
        
        

def saveData(data, file_path, update: bool = True, sub_key: str = ""):
    """
    در sub_key  میتوانید زیرمجموعه را وارد کنید تا داده ها انجا ذخیره شوند
    """
    if not file_path.endswith(".json"):
        file_path += ".json"

    file_path = os.path.join(current_dir, file_path)

    # بارگذاری داده‌های موجود (در صورت وجود فایل)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding="utf-8") as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = {}
    else:
        existing_data = {}

    if not update:
        existing_data = data
    elif sub_key:
        # بررسی وجود زیرمجموعه و آپدیت کردن آن
        if sub_key not in existing_data or not isinstance(existing_data[sub_key], dict):
            existing_data[sub_key] = {}
        existing_data[sub_key].update(data)
    else:
        existing_data.update(data)

    with open(file_path, 'w', encoding="utf-8") as file:
        json.dump(existing_data, file, ensure_ascii=False)


def removeKey(data_key, file_path, sub_key=None):
    """
    حذف یک یا چند کلید از دیکشنری یا زیرمجموعه‌ای خاص داخل فایل JSON و ذخیره تغییرات.

    پارامترها:
        sub_key (str): کلید اصلی که ممکن است دیکشنری اصلی یا زیرمجموعه را مشخص کند.
        data_key (str | list | None): کلید یا لیستی از کلیدهایی که باید حذف شوند (در صورت وجود زیرمجموعه).
        file_path (str): مسیر فایل JSON.
    """

    if not file_path.endswith(".json"):
        file_path += ".json"
        
    file_path = os.path.join(current_dir, file_path)

    # بارگذاری داده‌های موجود
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding="utf-8") as file:
            try:
                existing_data = json.load(file)
            except json.JSONDecodeError:
                existing_data = {}
    else:
        existing_data = {}

    
    if isinstance(data_key, str):
        data_key = [data_key]
    elif data_key is None:
        data_key = []

    
    if not sub_key:
        for key in data_key:
            if key in existing_data:
                existing_data.pop(key, None)
            
        with open(file_path, 'w', encoding="utf-8") as file:
                    json.dump(existing_data, file, ensure_ascii=False)
        
        return f"کلید '{data_key}' با موفقیت حذف شد."

    
    if sub_key in existing_data and isinstance(existing_data[sub_key], dict):
        for key in data_key:
            if key in existing_data[sub_key]:
                existing_data[sub_key].pop(key, None)
        # ذخیره تغییرات
        with open(file_path, 'w', encoding="utf-8") as file:
            json.dump(existing_data, file, ensure_ascii=False)
        return f"کلید(های) {data_key} از زیرمجموعه '{sub_key}' با موفقیت حذف شد."
    else:
        return f"کلید '{sub_key}' یا زیرمجموعه مربوطه وجود ندارد."


def loadData(file_path: str, liste: bool = False) -> Union[dict, list]:
    """
    اگه اخر فایل هم .json نباشه مشکلی نیست
    
    :param liste: اگر درست باشد و هیچ فایلی وجود نداشته باشد خروجی لیست خالی است
    """
    if not file_path.endswith(".json"):
        file_path += ".json"
        
    full_path = os.path.join(current_dir, file_path)

    if os.path.exists(full_path):
        with open(full_path, 'r', encoding="utf-8") as file:
            try:
                content = json.load(file)
            except Exception as e:
                if liste:
                    content = []
                else:
                    content = {}
    else:
        if liste:
            content = []
        else:
            content = {}
    
    return content   
    
    
    
@bot.on_message_updates()
async def handler_start_voice_builder(m: Update):
    text = (m.text or "").strip()
    if text != "کال":
        return

    gid = m.object_guid
    await m.reply("⏳ در حال بررسی وضعیت و ایجاد ویس‌کال...")

    # 1. اول چک کن شاید اصلا ویس باز باشه
    current_vid = await get_live_voice_id(gid)
    if current_vid:
        voice_chats[gid] = current_vid
        await m.reply(f"⚠️ ویس‌کال از قبل فعال است!\nشناسه: {current_vid}\n(در حافظه ذخیره شد)")
        return

    # 2. اگه باز نبود، استارت بزن
    v = VoiceCallBuilder(bot).for_group(gid)
    resp = await v.start()
    result = resp.get('result') if isinstance(resp, dict) else resp

    # تلاش برای گرفتن آیدی از پاسخ استارت
    vid = None
    if hasattr(result, "group_voice_chat_update"):
        group_voice_chat_update = getattr(result, "group_voice_chat_update")
        vid = getattr(group_voice_chat_update, "voice_chat_id", None)
    
    # اگر باز هم آیدی نبود، دوباره از سرور چک کن (محکم کاری)
    if not vid:
        vid = await get_live_voice_id(gid)

    if vid:
        voice_chats[gid] = vid
        await m.reply(f"✅ ویس‌کال با موفقیت ایجاد شد.\nID: {vid}")
    else:
        await m.reply("❌ درخواست ارسال شد اما آیدی ویس دریافت نشد.")

@bot.on_message_updates()
async def handler_stop_voice_builder(m: Update):
    text = (m.text or "").strip()
    if text != "قطع کال":
        return

    gid = m.object_guid
    await m.reply("⏳ در حال جستجوی ویس‌کال فعال برای قطع کردن...")

    # 1. دریافت آیدی واقعی از سرور (حتی اگه کاربر باز کرده باشه)
    real_vid = await get_live_voice_id(gid)

    # اگر سرور آیدی نداد، یه نگاه به حافظه خودمون هم میندازیم
    if not real_vid:
        real_vid = voice_chats.get(gid)

    if not real_vid:
        await m.reply("❌ هیچ ویس‌کال فعالی در این گروه پیدا نشد (نه توسط من، نه توسط کاربر).")
        return

    # 2. تلاش برای قطع کردن با آیدی پیدا شده
    try:
        # اینجا هم آیدی رو از حافظه پاک میکنیم هم درخواست قطع میدیم
        voice_chats.pop(gid, None) 
        resp = await discard_group_voice_chat(gid, real_vid)
        
        # بررسی نتیجه (گاهی اوقات خالی برمیگرده ولی کار انجام شده)
        if resp: 
            await m.reply("✅ ویس‌کال با موفقیت قطع شد.")
        else:
            # چک نهایی: دوباره میپرسیم ببینیم قطع شده یا نه
            check_again = await get_live_voice_id(gid)
            if not check_again:
                await m.reply("✅ ویس‌کال قطع شد (تایید نهایی).")
            else:
                await m.reply("❌ تلاش کردم اما ویس قطع نشد. شاید دسترسی ادمین ندارم.")
                
    except Exception as e:
        await m.reply(f"❌ خطا در عملیات قطع: {e}")

# قابلیت خفن جدید: ارسال جوک تصادفی
jokes = [
    "چرا کامپیوترها هیچوقت خسته نمی‌شن؟ چون همیشه ریست می‌شن!",
    "چرا مرغ جاده رو رد کرد؟ چون اون طرف مرغداری بود!",
    "دو تا programer با هم ازدواج کردن، بچه‌شون bug داره!",
    # اضافه کنید جوک‌های بیشتر
]

#متود اخطار
async def ekhtar(self, guid: str, group: str, subject: str = "دستور ادمین", key: str = "دستور ادمین", value: int = 3):
    
    roles = [creator, owners.get(group)] + special_users.get(group, [])
    is_admin = guid in roles
    
    if is_admin:
        # پیام برای ادمین‌ها
        await bot.send_message(group, "ادمین اخطار دریافت نمیکند")
        return
    
    # بارگذاری داده‌های اخطار
    ekh = loadData("ekhtar").get(group, {})
    
    # بررسی و مقداردهی اولیه اخطار
    user_warnings = ekh.get(guid, {})
    val = user_warnings.get(key, 0) + 1
    user_warnings[key] = val
    ekh[guid] = user_warnings

    # بررسی وضعیت اخطار و اقدام مناسب
    if val >= value:
        # مسدود کردن کاربر
        await bot.ban_member(group, guid)
        
        # ارسال پیام حذف کاربر
    
        await bot.send_message(
            group,
            
                f"❌ اخطار {val} از {value}\n"
                f"👤 کاربر به دلیل {subject} از گروه حذف شد"
        )
        
        # حذف اخطارهای کاربر پس از مسدود شدن
        del ekh[guid]
    else:
        # ارسال پیام اخطار
        remaining = value - val
        
        await bot.send_message(
            group,
            f"⚠️ اخطار {val} از {value}\n"
            f"👤 کاربر به دلیل {subject}\n"
            f"⏳ تعداد اخطارهای باقی‌مانده: {remaining}"
        )
    
    # ذخیره داده‌ها
    saveData(ekh, "ekhtar.json", sub_key=group)
        

@bot.on_message_updates(filters.is_group)
async def send_random_joke(m: Update):
    text = m.text or ""
    if text.strip() == "جوک":
        choice = random.choice(jokes)
        await m.reply(choice)
        return

# لود اولیه
load_creator()
load_welcome_config()
load_learn_data()
load_group_active()

bot.run()
