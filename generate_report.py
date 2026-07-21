import os
import re
import sys
import smtplib
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from google import genai
from google.genai import types

print("=== STARTING REPORT GENERATION SCRIPT ===")

# 1. Environment Verification
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

SESSION_TYPE = os.getenv("SESSION_TYPE", "PREMARKET")

if not GEMINI_API_KEY:
    print("❌ CRITICAL ERROR: GEMINI_API_KEY environment variable is missing!")
    sys.exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)

SESSION_MAP = {
    "PREMARKET": {
        "title": "🌅 8:00 AM IST Premarket Report & Indian Market Setup",
        "news_focus": "Focus heavily on Asian overnight markets, GIFT Nifty, domestic Indian news (Economic Times India, Moneycontrol), FII/DII institutional flows, and intraday Nifty/BankNifty option levels."
    },
    "LONDON": {
        "title": "🇬🇧 London Session Pre-Open Briefing (1 Hr Before Open)",
        "news_focus": "Focus heavily on European macroeconomic releases, ECB/BOE news, Forex short-term futures (EUR/USD, GBP/USD), and Gold (XAU/USD) supply/demand zones."
    },
    "NEWYORK": {
        "title": "🇺🇸 New York Session Pre-Open Briefing (1 Hr Before Open)",
        "news_focus": "Focus heavily on Wall Street pre-market movers, US Federal Reserve news, mega-cap US stocks (NVDA, MSFT, TSLA), and WTI Crude Oil catalysts."
    }
}

current_session = SESSION_MAP.get(SESSION_TYPE, SESSION_MAP["PREMARKET"])

PROMPT = f"""
Act as a Lead Quantitative Strategist and Institutional Portfolio Manager. Generate a comprehensive 2-page Daily Multi-Asset Trading Blueprint & Level Execution Manual in PDF format based on today's live market conditions and top financial news headlines.

CURRENT SESSION HIGHLIGHT: {current_session['title']}
SESSION NEWS FOCUS: {current_session['news_focus']}

### 📰 SECTION 0: DAILY MACRO & FINANCIAL NEWS DIGEST
Perform a live web search to aggregate and summarize today's major market-moving news headlines across global and domestic sources (e.g., Bloomberg, CNBC, BBC News, Economic Times India, Forex Factory, Reuters). Organize into:
1. Global Macro & Central Banks: Key interest rate developments, inflation metrics, FOMC/ECB/RBI updates, and currency drivers.
2. US & European Markets: Wall Street futures, mega-cap tech earnings, semiconductor developments, and index momentum.
3. Indian Markets & Dalal Street: Sensex/Nifty updates, corporate earnings, FII/DII institutional flows, and sectoral momentum.
4. Commodities & Crypto Wire: Crude oil geopolitics, OPEC+ updates, Gold supply/demand drivers, and major crypto regulatory/adoption headlines.

### 💰 CAPITAL BASE & ALLOCATION RULES ($3,000 TOTAL)
1. Crypto Futures: $400 (13.3%) | Rec. Leverage: 3x–5x Isolated | Risk Cap: 1–2% ($4–$8)
2. Indian Options (Intraday): $500 (16.7%) | Option Buying Only | Risk Cap: 10–15% Premium ($30–$45)
3. Commodities (Micro Gold & Oil): $400 (13.3%) | Rec. Leverage: 10x–15x Micro Lots | Risk Cap: 2% ($8)
4. US Stocks (Fractional): $400 (13.3%) | 1x Unleveraged Cash | Risk Cap: 3% ($12)
5. Indian Stocks (Delivery): $400 (13.3%) | 1x Unleveraged Cash | Risk Cap: 5% ($20)
6. Forex Short-Term Futures: $450 (15.0%) | Rec. Leverage: 10x–20x | Risk Cap: 1% ($4.50)
7. Forex Long-Term Carry Swing: $450 (15.0%) | Rec. Leverage: 2x–3x | Risk Cap: 2% ($9.00)

### 🎯 STRATEGY-BASED DAILY TICKER SELECTION & SECTOR CONSTRAINTS
Search live market data today and dynamically select top-performing tickers based on the well-known trading strategies below:
1. INDIAN EQUITIES (STRICTLY LONG-ONLY across Large, Mid, Small): Screen Nifty leaders using 50-SMA support bounces or 20/50 EMA golden crosses.
2. US EQUITIES:
   - Large-Cap (BI-DIRECTIONAL): Screen using 21-day EMA pullbacks or 50-day SMA rejection strategy on mega-cap growth leaders.
   - Mid-Cap & Small-Cap (STRICTLY LONG-ONLY): Screen using Stage-2 VCP or High Relative Volume (RVOL > 2.0) breakouts.
3. CRYPTO FUTURES (BI-DIRECTIONAL across Large, Mid, Small): Screen using 4H 21-EMA trend following and high-volume volatility breakouts.
4. COMMODITIES (BI-DIRECTIONAL): Gold (XAU/USD) and WTI Crude Oil using Pivot & Fibonacci extension levels.
5. FOREX FUTURES (BI-DIRECTIONAL): Short-Term (EUR/USD, GBP/USD) & Macro Carry Swings (USD/JPY, AUD/USD).
6. INDIAN OPTIONS (BI-DIRECTIONAL): Nifty 50 / BankNifty 15-Minute Opening Range Breakouts (Call for Long, Put for Short).

### 📊 MANDATORY HTML/CSS LAYOUT RULES FOR WEASYPRINT (STRICT COMPLIANCE REQUIRED)
Write a Python script using `weasyprint` and `HTML` to compile a PDF named 'daily_trading_blueprint.pdf'.
To ensure perfect table alignment and prevent text wrapping bugs, enforce strict CSS:
1. `@page {{ size: A4 portrait; margin: 10mm 12mm 12mm 12mm; background-color: #fcfbf9; }}`. Typography: `"Georgia", serif`. Font size: `7.2pt` to `8pt`.
2. Set `table-layout: fixed; width: 100%; border-collapse: collapse; margin-bottom: 6px;` on ALL `<table>` elements.
3. Define explicit percentage widths on every `<th>` element (e.g., `<th style="width: 15%;">`).
4. Apply `word-wrap: break-word; overflow-wrap: break-word; vertical-align: top; padding: 3px 4px;` to ALL `<td>` elements.
5. Set `page-break-inside: avoid;` on all tables, section boxes, and SVG graph containers.
6. Include 10-year backtest metrics table (Target CAGR 28.4%, Sharpe 1.45, Max DD -18.2%) vs S&P 500 TRI (~13.0%) and Nifty 50 TRI (~12.5%), along with an embedded vector/SVG equity curve chart ($3,000 to $36,512).
7. Every stock/crypto table must have a dedicated "Strategy & Selection Reason" column.

Output ONLY executable Python code inside ```python ``` code blocks.
"""

def generate_pdf():
    print(f"📡 Requesting market search & PDF blueprint from Gemini [{SESSION_TYPE}]...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=PROMPT,
            config=types.GenerateContentConfig(
                tools=[{"google_search": {}}]
            )
        )

        match = re.search(r'```python\s*(.*?)\s*```', response.text, re.DOTALL)
        if match:
            py_code = match.group(1)
            print("⚙️ Executing rendered Python code via WeasyPrint...")
            exec(py_code, globals())
            print("✅ PDF generated successfully: daily_trading_blueprint.pdf")
            return True
        else:
            print("❌ ERROR: Could not parse Python code block from Gemini output!")
            print("Raw Gemini output snippet:", response.text[:300])
            return False
    except Exception as e:
        print(f"❌ Gemini API Call Failed: {e}")
        return False

def send_telegram():
    pdf_filename = "daily_trading_blueprint.pdf"
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials missing. Skipping Telegram upload.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    caption_text = f"📈 *{current_session['title']}*\n\nAttached is your automated trading briefing for the *{SESSION_TYPE}* session."

    print("📱 Sending document to Telegram...")
    try:
        with open(pdf_filename, "rb") as pdf_file:
            files = {"document": (pdf_filename, pdf_file, "application/pdf")}
            data = {
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption_text,
                "parse_mode": "Markdown"
            }
            res = requests.post(url, data=data, files=files)
        
        if res.status_code == 200:
            print("✅ Telegram delivery successful!")
        else:
            print(f"❌ Telegram API returned error [{res.status_code}]: {res.text}")
    except Exception as e:
        print(f"❌ Exception during Telegram send: {e}")

def send_email():
    pdf_filename = "daily_trading_blueprint.pdf"
    if not SENDER_EMAIL or not SENDER_PASSWORD or not RECIPIENT_EMAIL:
        print("⚠️ Email credentials missing. Skipping email delivery.")
        return

    recipients = [e.strip() for e in RECIPIENT_EMAIL.split(",") if e.strip()]
    if not recipients:
        print("⚠️ No valid recipient emails found.")
        return

    print(f"📧 Sending email to {len(recipients)} address(es): {', '.join(recipients)}")
    
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = current_session['title']

    body = f"Attached is your automated trading briefing for the {SESSION_TYPE} session."
    msg.attach(MIMEText(body, 'plain'))

    with open(pdf_filename, "rb") as f:
        attach = MIMEApplication(f.read(), _subtype="pdf")
        attach.add_header('Content-Disposition', 'attachment', filename=pdf_filename)
        msg.attach(attach)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipients, msg.as_string())
        server.quit()
        print("✅ Email delivery successful!")
    except Exception as e:
        print(f"❌ SMTP Error sending email: {e}")

if __name__ == "__main__":
    if generate_pdf():
        send_telegram()
        send_email()
    else:
        print("❌ Workflow failed during PDF generation step.")
        sys.exit(1)
