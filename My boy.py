import os
import re
import time
import base64
import json
import hashlib
import urllib.parse
import requests

BOT_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN"
)
V2RAY_ID = os.environ.get(
    "TELEGRAM_CHANNEL_V2RAY_ID"
)
PROXY_ID = os.environ.get(
    "TELEGRAM_CHANNEL_PROXY_ID"
)

# منابع خرد شده به خطوط کوچک برای جلوگیری از باگ موبایل
SRC = [
    "https://raw.githubusercontent.com/"
    "V2RAYCONFIGSPOOL/V2RAY_SUB/main/"
    "v2ray_configs_no1.txt",
    "https://raw.githubusercontent.com/"
    "V2RAYCONFIGSPOOL/V2RAY_SUB/main/"
    "v2ray_configs_no2.txt",
    "https://raw.githubusercontent.com/"
    "V2RAYCONFIGSPOOL/V2RAY_SUB/main/"
    "v2ray_configs_no3.txt",
    "https://raw.githubusercontent.com/"
    "V2RAYCONFIGSPOOL/V2RAY_SUB/main/"
    "v2ray_configs_no4.txt",
    "https://raw.githubusercontent.com/"
    "V2RAYCONFIGSPOOL/V2RAY_SUB/main/"
    "v2ray_configs_no5.txt",
    "https://raw.githubusercontent.com/"
    "V2RAYCONFIGSPOOL/V2RAY_SUB/main/"
    "v2ray_configs_no6.txt",
    "https://raw.githubusercontent.com/"
    "V2RAYCONFIGSPOOL/V2RAY_SUB/main/"
    "v2ray_configs_no7.txt",
    "https://raw.githubusercontent.com/"
    "V2RAYCONFIGSPOOL/V2RAY_SUB/main/"
    "v2ray_configs_no8.txt",
    "https://raw.githubusercontent.com/"
    "V2RAYCONFIGSPOOL/V2RAY_SUB/main/"
    "v2ray_configs_no9.txt",
    "https://raw.githubusercontent.com/"
    "V2RAYCONFIGSPOOL/V2RAY_SUB/main/"
    "v2ray_configs_no10.txt",
    "https://raw.githubusercontent.com/"
    "V2RAYCONFIGSPOOL/"
    "TELEGRAM_PROXY_SUB/main/"
    "telegram_proxy_no1.txt",
    "https://raw.githubusercontent.com/"
    "V2RAYCONFIGSPOOL/"
    "TELEGRAM_PROXY_SUB/main/"
    "telegram_proxy_no2.txt",
    "https://raw.githubusercontent.com/"
    "V2RAYCONFIGSPOOL/"
    "TELEGRAM_PROXY_SUB/main/"
    "telegram_proxy_no3.txt",
    "https://raw.githubusercontent.com/"
    "V2RAYCONFIGSPOOL/"
    "TELEGRAM_PROXY_SUB/main/"
    "telegram_proxy_no4.txt",
    "https://raw.githubusercontent.com/"
    "V2RAYCONFIGSPOOL/"
    "TELEGRAM_PROXY_SUB/main/"
    "telegram_proxy_no5.txt",
    "https://raw.githubusercontent.com/"
    "V2RAYCONFIGSPOOL/"
    "TELEGRAM_PROXY_SUB/main/"
    "telegram_proxy_no6.txt",
    "https://raw.githubusercontent.com/"
    "V2RAYCONFIGSPOOL/"
    "TELEGRAM_PROXY_SUB/main/"
    "telegram_proxy_no7.txt",
    "https://raw.githubusercontent.com/"
    "V2RAYCONFIGSPOOL/"
    "TELEGRAM_PROXY_SUB/main/"
    "telegram_proxy_no8.txt",
    "https://raw.githubusercontent.com/"
    "V2RAYCONFIGSPOOL/"
    "TELEGRAM_PROXY_SUB/main/"
    "telegram_proxy_no9.txt",
    "https://raw.githubusercontent.com/"
    "V2RAYCONFIGSPOOL/"
    "TELEGRAM_PROXY_SUB/main/"
    "telegram_proxy_no10.txt"
]

H_FILE = "sent_configs_history.json"

def load_history():
    if os.path.exists(H_FILE):
        try:
            with open(
                H_FILE, 'r',
                encoding='utf-8'
            ) as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_history(sent_hashes):
    try:
        with open(
            H_FILE, 'w',
            encoding='utf-8'
        ) as f:
            json.dump(
                list(sent_hashes),
                f, indent=4
            )
    except Exception:
        pass

def get_config_identity(ctype, ctext):
    try:
        if ctype == 'v2ray':
            parsed = urllib.parse.urlparse(
                ctext
            )
            if parsed.netloc:
                netloc = parsed.netloc.split(
                    '@'
                )[-1]
                return hashlib.md5(
                    netloc.encode('utf-8')
                ).hexdigest()
    except Exception:
        pass
    return hashlib.md5(
        ctext.strip().encode('utf-8')
    ).hexdigest()

def decode_base64(data):
    try:
        missing = len(data) % 4
        if missing:
            data += '=' * (4 - missing)
        return base64.b64decode(
            data
        ).decode('utf-8')
    except Exception:
        return data

def fetch_configs():
    extracted = []
    v2ray_p = re.compile(
        r'(vless|vmess|trojan|ss|'
        r'tuic|hysteria2?):\/\/'
        r'[^\s#]+(?:#[^\s]*)?',
        re.IGNORECASE
    )
    proxy_p = re.compile(
        r'(?:tg:\/\/proxy\?|'
        r'https:\/\/t\.me\/proxy\?)'
        r'[^\s]+',
        re.IGNORECASE
    )

    for url in SRC:
        try:
            res = requests.get(
                url, timeout=15
            )
            if res.status_code == 200:
                content = res.text
                pfx = (
                    "vless://", "vmess://",
                    "ss://", "trojan://",
                    "tg://"
                )
                if not content.startswith(
                    pfx
                ):
                    dec = decode_base64(
                        content
                    )
                    if dec != content:
                        content = dec
                
                for m in v2ray_p.finditer(
                    content
                ):
                    extracted.append(
                        ('v2ray', m.group(0))
                    )
                for m in proxy_p.finditer(
                    content
                ):
                    extracted.append(
                        ('proxy', m.group(0))
                    )
        except Exception:
            pass
            
    return extracted

def clean_v2ray_remarks(config):
    try:
        if '#' in config:
            base, rem = config.split(
                '#', 1
            )
            dec_rem = urllib.parse.unquote(
                rem
            )
            clean = re.sub(
                r'@[a-zA-Z0-9_]+',
                '', dec_rem
            ).strip()
            new_rem = (
                f"{clean} | {V2RAY_ID}"
            )
            enc_rem = urllib.parse.quote(
                new_rem
            )
            return f"{base}#{enc_rem}"
    except Exception:
        pass
    return config

def send_to_telegram(ctype, ctext):
    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendMessage"
    )
    
    if ctype == 'v2ray':
        if not V2RAY_ID:
            return False
        chat = V2RAY_ID
        fmt = clean_v2ray_remarks(ctext)
        proto = fmt.split('://')[0].upper()
        msg = (
            f"⚡️ **کانفیگ جدید {proto}**\n\n"
            f"`{fmt}`\n\n"
            f"👤 عضویت ما: {V2RAY_ID}"
        )
    else:
        if not PROXY_ID:
            return False
        chat = PROXY_ID
        msg = (
            f"⚡️ **پروکسی جدید تلگرام**\n\n"
            f"🔗 [اتصال سریع]({ctext})\n\n"
            f"👤 عضویت ما: {PROXY_ID}"
        )

    payload = {
        "chat_id": chat,
        "text": msg,
        "parse_mode": "Markdown"
    }

    try:
        for att in range(5):
            res = requests.post(
                url, json=payload,
                timeout=10
            )
            if res.status_code == 200:
                return True
            elif res.status_code == 429:
                ret = res.json().get(
                    "parameters", {}
                ).get("retry_after", 5)
                time.sleep(ret)
            else:
                time.sleep(2 ** att)
    except Exception:
        pass
    return False

def main():
    if not BOT_TOKEN:
        return

    sent_hashes = load_history()
    configs = fetch_configs()
    
    updated_hashes = set(sent_hashes)
    
    for ctype, ctext in configs:
        ihash = get_config_identity(
            ctype, ctext
        )
        
        if ihash not in sent_hashes:
            success = send_to_telegram(
                ctype, ctext
            )
            if success:
                updated_hashes.add(ihash)
                time.sleep(3)
        
    if len(updated_hashes) > len(sent_hashes):
        save_history(updated_hashes)

if __name__ == "__main__":
    main()
