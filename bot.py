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

GITHUB_SOURCES = [
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
    tg_proxy_pattern = re.compile(r'(?:tg:\/\/proxy\?|https:\/\/t\.me\/proxy\?)[^\s]+', re.IGNORECASE)

    for url in GITHUB_SOURCES:
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                content = response.text
                if not content.startswith(("vless://", "vmess://", "ss://", "trojan://", "tg://")):
                    decoded = decode_base64(content)
                    if decoded != content:
                        content = decoded
                
                for match in v2ray_pattern.finditer(content):
                    extracted_configs.append(('v2ray', match.group(0)))
                for match in tg_proxy_pattern.finditer(content):
                    extracted_configs.append(('proxy', match.group(0)))
        except Exception:
            pass
            
    return extracted_configs

def clean_v2ray_remarks(config):
    try:
        if '#' in config:
            base_part, remark = config.split('#', 1)
            decoded_remark = urllib.parse.unquote(remark)
            clean_remark = re.sub(r'@[a-zA-Z0-9_]+', '', decoded_remark).strip()
            new_remark = f"{clean_remark} | {TELEGRAM_CHANNEL_V2RAY_ID}"
            encoded_remark = urllib.parse.quote(new_remark)
            return f"{base_part}#{encoded_remark}"
    except Exception:
        pass
    return config

def send_to_telegram(config_type, config_text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    if config_type == 'v2ray':
        if not TELEGRAM_CHANNEL_V2RAY_ID:
            return False
        target_chat = TELEGRAM_CHANNEL_V2RAY_ID
        formatted_config = clean_v2ray_remarks(config_text)
        protocol = formatted_config.split('://')[0].upper()
        message = (
            f"⚡️ **کانفیگ جدید {protocol}**\n\n"
            f"`{formatted_config}`\n\n"
            f"👤 عضویت در کانال ما: {TELEGRAM_CHANNEL_V2RAY_ID}"
        )
    else:
        if not TELEGRAM_CHANNEL_PROXY_ID:
            return False
        target_chat = TELEGRAM_CHANNEL_PROXY_ID
        message = (
            f"⚡️ **پروکسی جدید تلگرام**\n\n"
            f"🔗 [برای اتصال سریع کلیک کنید]({config_text})\n\n"
            f"👤 عضویت در کانال پروکسی ما: {TELEGRAM_CHANNEL_PROXY_ID}"
        )

    payload = {
        "chat_id": target_chat,
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
                time.sleep(retry_after)
            else:
                time.sleep(2 ** attempt)
    except Exception:
        pass
    return False

def main():
    if not TELEGRAM_BOT_TOKEN:
        return

    sent_hashes = load_history()
    configs = fetch_configs()
    
    new_items_count = 0
    updated_hashes = set(sent_hashes)
    
    for config_type, config_text in configs:
        item_hash = get_config_identity(config_type, config_text)
        
        if item_hash not in sent_hashes:
            success = send_to_telegram(config_type, config_text)
            if success:
                updated_hashes.add(item_hash)
                new_items_count += 1
                time.sleep(3)
        
    if new_items_count > 0:
        save_history(updated_hashes)

if __name__ == "__main__":
    main()
