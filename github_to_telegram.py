import os
import re
import time
import base64
import json
import hashlib
import socket
import urllib.parse
import requests

# --- تنظیمات تلگرام (از تنظیمات امنیتی گیت‌هاب خوانده می‌شود) ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")

# --- منابع دریافت کانفیگ از گیت‌هاب ---
# لینک‌های مستقیم (Raw) فایل‌های کانفیگ یا سابسکریپشن را اینجا وارد کنید.
# (نمونه‌های زیر پیش‌فرض هستند و می‌توانید آن‌ها را تغییر دهید)
GITHUB_SOURCES = [
    "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/yebekhe/TVVarzesh/main/subscription/v2ray/sub"
]

# نام فایل ذخیره تاریخچه برای جلوگیری از ارسال تکراری‌ها
HISTORY_FILE = "sent_configs_history.json"

def load_history():
    """بارگذاری آیدی‌های ارسال شده قبلی برای جلوگیری از تکرار"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_history(sent_hashes):
    """ذخیره تاریخچه جدید در ریپازیتوری شما"""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(sent_hashes), f, indent=4)
    except Exception as e:
        print(f"خطا در ذخیره فایل تاریخچه: {e}")

def get_config_identity(config_text):
    """
    استخراج هوشمند آدرس سرور و پورت کانفیگ به عنوان شناسه یکتا.
    این کار باعث می‌شود حتی اگر نام کانفیگ عوض شود، سرور تکراری ارسال نشود.
    """
    try:
        # برای کانفیگ‌های معمولی
        parsed = urllib.parse.urlparse(config_text)
        if parsed.netloc:
            # حذف نام کاربری در صورت وجود (مانند user@host:port)
            netloc = parsed.netloc.split('@')[-1]
            return hashlib.md5(netloc.encode('utf-8')).hexdigest()
    except Exception:
        pass
    # در صورت بروز خطا، از هش کل متن به عنوان بک‌آپ استفاده می‌شود
    return hashlib.md5(config_text.strip().encode('utf-8')).hexdigest()

def is_server_alive(host, port, timeout=3):
    """تست خراب یا سالم بودن سرور کانفیگ (تست پینگ و اتصال به پورت)"""
    try:
        # حل کردن نام دامنه به آی‌پی
        ip = socket.gethostbyname(host)
        # تلاش برای برقراری اتصال TCP کوتاه مدت
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except Exception:
        return False

def check_config_health(config_text):
    """بررسی سلامت کانفیگ قبل از ارسال به تلگرام"""
    try:
        parsed = urllib.parse.urlparse(config_text)
        netloc = parsed.netloc.split('@')[-1]
        
        # استخراج سرور و پورت
        if ':' in netloc:
            host, port_str = netloc.split(':', 1)
            # تمیزکاری پورت در صورت وجود پارامترها در آدرس
            port_str = port_str.split('?')[0].split('#')[0]
            port = int(port_str)
            
            print(f"در حال تست سلامت سرور: {host}:{port} ...")
            if is_server_alive(host, port):
                print("🟢 سرور سالم و فعال است.")
                return True
            else:
                print("🔴 سرور خاموش یا فیلتر است. (نادیده گرفته شد)")
                return False
    except Exception as e:
        print(f"خطا در بررسی سلامت کانفیگ: {e}")
    
    # اگر نتوانستیم بررسی کنیم، برای اطمینان فرض می‌کنیم سالم است
    return True

def decode_base64(data):
    """رمزگشایی لینک‌های سابسکریپشن رمزگذاری شده"""
    try:
        # اصلاح پدینگ استاندارد Base64
        missing_padding = len(data) % 4
        if missing_padding:
            data += '=' * (4 - missing_padding)
        return base64.b64decode(data).decode('utf-8')
    except Exception:
        return data

def fetch_configs():
    """دریافت کانفیگ‌ها از تمام منابع گیت‌هاب"""
    extracted_configs = []
    
    # الگوهای منظم برای استخراج دقیق انواع پروتکل‌ها
    v2ray_pattern = re.compile(
        r'(vless|vmess|trojan|ss|tuic|hysteria2?):\/\/[^\s#]+(?:#[^\s]*)?', 
        re.IGNORECASE
    )
    tg_proxy_pattern = re.compile(
        r'(?:tg:\/\/proxy\?|https:\/\/t\.me\/proxy\?)[^\s]+', 
        re.IGNORECASE
    )

    for url in GITHUB_SOURCES:
        try:
            print(f"در حال دریافت اطلاعات از منبع: {url}")
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                content = response.text
                
                # اگر محتوا سابسکریپشن و بیس۶۴ باشد، دکود می‌شود
                if not content.startswith(("vless://", "vmess://", "ss://", "trojan://", "tg://")):
                    decoded = decode_base64(content)
                    if decoded != content:
                        content = decoded
                
                # استخراج موارد پیدا شده
                for match in v2ray_pattern.finditer(content):
                    extracted_configs.append(('v2ray', match.group(0)))
                    
                for match in tg_proxy_pattern.finditer(content):
                    extracted_configs.append(('proxy', match.group(0)))
                    
        except Exception as e:
            print(f"خطا در دریافت اطلاعات از {url}: {e}")
            
    return extracted_configs

def clean_v2ray_remarks(config):
    """تغییر نام کانفیگ و شخصی‌سازی آن با آیدی کانال شما"""
    try:
        if '#' in config:
            base_part, remark = config.split('#', 1)
            decoded_remark = urllib.parse.unquote(remark)
            # حذف تبلیغات یا آیدی‌های تلگرامی قبلی که روی نام کانفیگ گذاشته شده بود
            clean_remark = re.sub(r'@[a-zA-Z0-9_]+', '', decoded_remark).strip()
            # قرار دادن آیدی کانال شما به جای ریمارک قبلی
            new_remark = f"{clean_remark} | {TELEGRAM_CHANNEL_ID}"
            encoded_remark = urllib.parse.quote(new_remark)
            return f"{base_part}#{encoded_remark}"
    except Exception:
        pass
    return config

def send_to_telegram(config_type, config_text):
    """ارسال کانفیگ تایید شده به کانال تلگرام"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        print("خطا: تنظیمات تلگرام (توکن یا آیدی کانال) کامل نیست!")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    if config_type == 'v2ray':
        formatted_config = clean_v2ray_remarks(config_text)
        protocol = formatted_config.split('://')[0].upper()
        message = (
            f"⚡️ **کانفیگ تست شده و فعال {protocol}**\n\n"
            f"`{formatted_config}`\n\n"
            f"👤 عضویت در کانال ما: {TELEGRAM_CHANNEL_ID}"
        )
    else:
        message = (
            f"⚡️ **پروکسی جدید تلگرام**\n\n"
            f"🔗 [برای اتصال سریع کلیک کنید]({config_text})\n\n"
            f"👤 عضویت در کانال ما: {TELEGRAM_CHANNEL_ID}"
        )

    payload = {
        "chat_id": TELEGRAM_CHANNEL_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        for attempt in range(5):
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                return True
            elif response.status_code == 429:
                retry_after = response.json().get("parameters", {}).get("retry_after", 5)
                print(f"محدودیت ارسال تلگرام! صبر به مدت {retry_after} ثانیه...")
                time.sleep(retry_after)
            else:
                print(f"خطای تلگرام: {response.status_code}")
                time.sleep(2 ** attempt)
    except Exception as e:
        print(f"خطا در ارسال پیام به تلگرام: {e}")
    return False

def main():
    print("شروع کار ربات هوشمند انتقال کانفیگ...")
    
    sent_hashes = load_history()
    configs = fetch_configs()
    print(f"در مجموع {len(configs)} کانفیگ و پروکسی در منابع یافت شد.")
    
    new_items_count = 0
    updated_hashes = set(sent_hashes)
    
    for config_type, config_text in configs:
        # ۱. فیلتر کردن کانفیگ‌های تکراری بر اساس آی‌پی و پورت سرور
        item_hash = get_config_identity(config_text)
        
        if item_hash not in sent_hashes:
            # ۲. فیلتر کردن کانفیگ‌های خراب با تست اتصال شبکه واقعی
            if config_type == 'v2ray' and not check_config_health(config_text):
                continue # نادیده گرفتن کانفیگ به دلیل عدم پاسخ‌دهی سرور
                
            print(f"کانفیگ جدید و سالم تایید شد. در حال ارسال به کانال...")
            success = send_to_telegram(config_type, config_text)
            if success:
                updated_hashes.add(item_hash)
                new_items_count += 1
                time.sleep(3) # مکث کوتاه برای جلوگیری از اسپم
        
    if new_items_count > 0:
        save_history(updated_hashes)
        print(f"موفقیت‌آمیز! تعداد {new_items_count} کانفیگ فعال و غیرتکراری به کانال ارسال شد.")
    else:
        print("هیچ کانفیگ جدید یا سالمی برای ارسال پیدا نشد.")

if __name__ == "__main__":
    main()
