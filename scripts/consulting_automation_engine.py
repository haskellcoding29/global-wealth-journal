import os
import json
import datetime
import urllib.request
import urllib.parse
from pathlib import Path

# Load .env variables from LLM_wiki or local environment
def load_env():
    env_vars = {}
    env_paths = [
        r"c:\Users\user\Documents\LLM_wiki\.env",
        r"c:\Users\user\Documents\global-wealth-journal\.env"
    ]
    for p in env_paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env_vars[k.strip()] = v.strip().strip('"').strip("'")
    return env_vars

ENV = load_env()
TELEGRAM_BOT_TOKEN = ENV.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_ADMIN_CHAT_ID = ENV.get("TELEGRAM_ADMIN_CHAT_ID") or ENV.get("TELEGRAM_CHAT_ID")

BASE_DIR = Path(r"c:\Users\user\Documents\global-wealth-journal")
TEMPLATES_DIR = BASE_DIR / "templates"
RECORDS_DIR = BASE_DIR / "data" / "consulting_records"
RECORDS_DIR.mkdir(parents=True, exist_ok=True)

def send_telegram_alert(text):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_ADMIN_CHAT_ID:
        print("[Telegram Alert Skipped] Bot token or Chat ID not found.")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_ADMIN_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"[Telegram Alert Error] {e}")
        return False

def generate_advisory_agreement(client_data):
    template_path = TEMPLATES_DIR / "US_LLC_ADVISORY_AGREEMENT_TEMPLATE.md"
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    rendered = template.replace("{{CLIENT_NAME}}", client_data.get("name", "Valued Client"))
    rendered = rendered.replace("{{CLIENT_RESIDENCE}}", client_data.get("residence", "South Korea"))
    rendered = rendered.replace("{{AGREEMENT_DATE}}", today_str)
    rendered = rendered.replace("{{PAYMENT_METHOD}}", client_data.get("payment_method", "USDT / Stripe"))
    rendered = rendered.replace("{{TX_REF}}", client_data.get("tx_ref", f"TX-{int(datetime.datetime.now().timestamp())}"))
    
    client_id = client_data.get("client_id", f"VIP_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
    out_path = RECORDS_DIR / f"{client_id}_Advisory_Agreement.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(rendered)
        
    return str(out_path)

def generate_ai_client_dossier(client_data):
    template_path = TEMPLATES_DIR / "CLIENT_DOSSIER_PROMPT.md"
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
        
    residence = client_data.get("residence", "대한민국 (South Korea)")
    net_worth = client_data.get("net_worth", "30억~100억 원 상당 ($2.5M~$7.5M)")
    crypto_ratio = client_data.get("crypto_ratio", 60)
    equity_ratio = client_data.get("equity_ratio", 30)
    domestic_ratio = client_data.get("domestic_ratio", 10)
    pain_points = client_data.get("pain_points", "2026 가상자산 과세, 최고 50% 상속세 방어, 파나마 0% 영토세 거주권 취득")
    
    if "한국" in residence or "Korea" in residence:
        risk_summary = "한국 국세청 최고 50%(할증 60%) 상속·증여세, 2026-2027 가상자산 소득세(22%) 및 해외금융계좌(CRS) 자진신고 과태료 리스크"
        exposure_amt = "예상 상속/양도 과세 시 총 자산의 40~50% 이상 잠식 위험"
    elif "일본" in residence or "Japan" in residence:
        risk_summary = "일본 최고 55% 소득세율, 엔화 약세, 국외전출세(유가증권 미실현 이익 15.315% 강제 징수) 및 비거주자 판정 엄격화"
        exposure_amt = "출국 시점 미실현 이익 강제 과세 및 최고세율 자산 유출"
    else:
        risk_summary = "글로벌 CRS 자동정보교환 및 본국 고율 자산 소득세 노출"
        exposure_amt = "연간 소득의 30~45% 누진 과세"

    rendered = template.replace("{{CLIENT_NAME}}", client_data.get("name", "Unknown"))
    rendered = rendered.replace("{{CLIENT_RESIDENCE}}", residence)
    rendered = rendered.replace("{{ESTIMATED_WEALTH}}", net_worth)
    rendered = rendered.replace("{{CRYPTO_RATIO}}", str(crypto_ratio))
    rendered = rendered.replace("{{EQUITY_RATIO}}", str(equity_ratio))
    rendered = rendered.replace("{{DOMESTIC_RATIO}}", str(domestic_ratio))
    rendered = rendered.replace("{{PAIN_POINTS}}", pain_points)
    rendered = rendered.replace("{{HOME_COUNTRY_RISK_SUMMARY}}", risk_summary)
    rendered = rendered.replace("{{EXPOSURE_AMOUNT}}", exposure_amt)
    
    client_id = client_data.get("client_id", f"VIP_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}")
    out_path = RECORDS_DIR / f"{client_id}_AI_Executive_Dossier.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(rendered)
        
    return str(out_path)

def process_vip_intake(client_data):
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    client_id = f"VIP_{timestamp}_{client_data.get('name', 'client').replace(' ', '_')}"
    client_data["client_id"] = client_id
    client_data["processed_at"] = datetime.datetime.now().isoformat()
    
    agreement_file = generate_advisory_agreement(client_data)
    dossier_file = generate_ai_client_dossier(client_data)
    
    record_json_path = RECORDS_DIR / f"{client_id}_Record.json"
    with open(record_json_path, "w", encoding="utf-8") as f:
        json.dump(client_data, f, ensure_ascii=False, indent=2)
        
    tg_message = f"""👑 <b>[긴급 VIP 컨설팅 예약 접수 ($1,500)]</b>

🏛️ <b>주체 법인</b>: Global Sovereign Wealth Advisory LLC (Wyoming, USA)
👤 <b>고객 성함</b>: <code>{client_data.get('name')}</code>
📍 <b>거주 국가</b>: {client_data.get('residence')}
💰 <b>추정 자산</b>: {client_data.get('net_worth')}
💳 <b>결제 수단</b>: {client_data.get('payment_method')} ($1,500 USD)
📲 <b>연락처</b>: {client_data.get('contact')}
✉️ <b>이메일</b>: {client_data.get('email')}

🎯 <b>주요 과제</b>:
{client_data.get('pain_points')}

📁 <b>생성된 문서</b>:
• 미국 법인 자문계약서: <code>{os.path.basename(agreement_file)}</code>
• AI 사전 인텔리전스 보고서: <code>{os.path.basename(dossier_file)}</code>

<i>*90분 VIP 세션 캘린더 일정을 확인하시기 바랍니다.*</i>"""

    sent = send_telegram_alert(tg_message)
    
    return {
        "status": "success",
        "client_id": client_id,
        "agreement_file": agreement_file,
        "dossier_file": dossier_file,
        "record_file": str(record_json_path),
        "telegram_notified": sent
    }

if __name__ == "__main__":
    sample_client = {
        "name": "홍길동 (Paul Kim)",
        "email": "paul.kim.invest@example.com",
        "contact": "+82 10-9876-5432 / @paul_kim_crypto",
        "residence": "대한민국 (South Korea)",
        "net_worth": "약 75억 원 ($5.5M)",
        "crypto_ratio": 70,
        "equity_ratio": 20,
        "domestic_ratio": 10,
        "pain_points": "2026-2027 가상자산 22% 과세 회피, 최고 50% 상속세 철통 방어, 파나마 사익재단 0% 영토세 설립 및 타워뱅크 비트코인 오프램프 계좌 개설",
        "payment_method": "USDT (TRC-20)",
        "tx_ref": "0x7a8f9c1b3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0"
    }
    
    print("Running Panama Consulting Automation Pipeline Test...")
    res = process_vip_intake(sample_client)
    print("Pipeline Output:\n", json.dumps(res, ensure_ascii=False, indent=2))
