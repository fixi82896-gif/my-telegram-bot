import os
import re
import time
import base64
import json
import hashlib
import urllib.parse
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_V2RAY_ID = os.environ.get("TELEGRAM_CHANNEL_V2RAY_ID")
TELEGRAM_CHANNEL_PROXY_ID = os.environ.get("TELEGRAM_CHANNEL_PROXY_ID")

# --- لیست یکپارچه ۲۰ منبع اختصاصی شما ---
GITHUB_SOURCES = [
    # --- ۱۰ منبع کانفیگ V2Ray ---
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/main/v2ray_configs_no1.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/main/v2ray_configs_no2.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/main/v2ray_configs_no3.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/main/v2ray_configs_no4.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/main/v2ray_configs_no5.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/main/v2ray_configs_no6.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/main/v2ray_configs_no7.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/main/v2ray_configs_no8.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/main/v2ray_configs_no9.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/V2RAY_SUB/main/v2ray_configs_no10.txt",

    # --- ۱۰ منبع پروکسی تلگرام ---
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/main/telegram_proxy_no1.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/main/telegram_proxy_no2.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/main/telegram_proxy_no3.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/main/telegram_proxy_no4.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/main/telegram_proxy_no5.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/main/telegram_proxy_no6.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/main/telegram_proxy_no7.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/main/telegram_proxy_no8.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/main/telegram_proxy_no9.txt",
    "https://raw.githubusercontent.com/V2RAYCONFIGSPOOL/TELEGRAM_PROXY_SUB/main/telegram_proxy_no10.txt"
]

HISTORY_FILE = "sent_configs_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_history(sent_hashes):
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(sent_hashes), f, indent=4)
    except Exception:
        pass

def get_config_identity(config_type, config_text):
    try:
        if config_type == 'v2ray':
            parsed = urllib.parse.urlparse(config_text)
            if parsed.netloc:
                netloc = parsed.netloc.split('@')[-1]
                return hashlib.md5(netloc.encode('utf-8')).hexdigest()
    except Exception:
        pass
    return hashlib.md5(config_text.strip().encode('utf-8')).hexdigest()

def decode_base64(data):
    try:
        missing_padding = len(data) % 4
        if missing_padding:
            data += '=' * (4 - missing_padding)
        return base64.b64decode(data).decode('utf-8')
    except Exception:
        return data

def fetch_configs():
    extracted_configs = []
    v2ray_pattern = re.compile(r'(vless|vmess|trojan|ss|tuic|hysteria2?):\/\/[^\s#]+(?:#[^\s]*)?', re.IGNORECASE)
    tg_proxy_pattern = re.compile(r'(?:tg:\/\/proxy\?|https:\/\/t\.me\/proxy\?|tg:\/\/socks\?|https:\/\/t\.me\/socks\?)[^\s]+', re.IGNORECASE)

    for url in GITHUB_SOURCES:
        try:
            print(f"🔗 در حال بررسی منبع: {url}")
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                content = response.text
                
                if "://" not in content.strip()[:100]:
                    decoded = decode_base64(content)
                    if decoded != content:
                        content = decoded
                
                v2ray_count = 0
                proxy_count = 0
                
                for match in v2ray_pattern.finditer(content):
                    extracted_configs.append(('v2ray', match.group(0)))
                    v2ray_count += 1
                for match in tg_proxy_pattern.finditer(content):
                    extracted_configs.append(('proxy', match.group(0)))
                    proxy_count += 1
                    
                print(f"📊 یافته‌ها -> کانفیگ: {v2ray_count} | پروکسی: {proxy_count}")
        except Exception as e:
            print(f"❌ خطا در دریافت از منبع: {e}")
            
    return extracted_configs

def clean_v2ray_remarks(config):
    try:
        if '#' in config:
            base_part, remark = config.split('#', 1)
            decoded_remark = urllib.parse.unquote(remark)
            clean_remark = re.sub(r'@[a-zA-Z0-9_]+', '', decoded_remark).strip()
            new_remark = f"⚡ {clean_remark}"
            encoded_remark = urllib.parse.quote(new_remark)
            return f"{base_part}#{encoded_remark}"
    except Exception:
        pass
    return config

def send_to_telegram(config_type, config_text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    if config_type == 'v2ray':
        if not TELEGRAM_CHANNEL_V2RAY_ID:
            print("⚠️ خطا: آیدی کانال V2Ray تنظیم نشده است.")
            return False
        target_chat = TELEGRAM_CHANNEL_V2RAY_ID
        formatted_config = clean_v2ray_remarks(config_text)
        protocol = formatted_config.split('://')[0].upper()
        
        # تعبیر نو و دیزاین شیک کانفیگ بدون متن تبلیغاتی فرعی
        message = (
            f"🚀 <b>بروزرسانی سرور [{protocol}]</b>\n"
            f"📶 اتصال پایدار • ظرفیت پرسرعت\n\n"
            f"<code>{formatted_config}</code>"
        )
    else:
        if not TELEGRAM_CHANNEL_PROXY_ID:
            print("⚠️ خطا: آیدی کانال پروکسی تنظیم نشده است.")
            return False
        target_chat = TELEGRAM_CHANNEL_PROXY_ID
        
        # دیزاین شیک و تمیز پروکسی بدون متن تبلیغاتی فرعی
        message = (
            f"⚡️ <b>پروکسی اختصاصی و جدید تلگرام</b>\n"
            f"🟢 وضعیت: فعال و پرسرعت\n\n"
            f'🔗 <a href="{config_text}"><b>[ برای اتصال فوری کلیک کنید ]</b></a>'
        )

    payload = {
        "chat_id": target_chat,
        "text": message,
        "parse_mode": "HTML"
    }

    try:
        for attempt in range(5):
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                return True
            elif response.status_code == 429:
                retry_after = response.json().get("parameters", {}).get("retry_after", 5)
                time.sleep(retry_after)
            else:
                print(f"❌ خطای ارسال تلگرام: {response.status_code}")
                time.sleep(2 ** attempt)
    except Exception as e:
        print(f"❌ خطای ارتباطی تلگرام: {e}")
    return False

def main():
    print("🚀 شروع کار ربات تفکیک‌کننده هوشمند...")
    if not TELEGRAM_BOT_TOKEN:
        print("❌ خطا: TELEGRAM_BOT_TOKEN یافت نشد.")
        return

    sent_hashes = load_history()
    configs = fetch_configs()
    print(f"📦 مجموع کل کلیدهای یافت‌شده در این پارت: {len(configs)}")
    
    new_items_count = 0
    updated_hashes = set(sent_hashes)
    
    for config_type, config_text in configs:
        item_hash = get_config_identity(config_type, config_text)
        
        if item_hash not in sent_hashes:
            print(f" Forwarding new {config_type}...")
            success = send_to_telegram(config_type, config_text)
            if success:
                updated_hashes.add(item_hash)
                new_items_count += 1
                time.sleep(3)
        
    if new_items_count > 0:
        save_history(updated_hashes)
        print(f"✅ با موفقیت {new_items_count} مورد جدید ارسال شد.")
    else:
        print("ℹ️ مورد جدیدی برای ارسال پیدا نشد.")

if __name__ == "__main__":
    main()
            
