import os
import re
import sys
import smtplib
import traceback
import requests
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from google import genai
from google.genai import types
from weasyprint import HTML

print("=== STARTING MULTI-ASSET REPORT GENERATOR ===")

# 1. Fetch Environment Variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

SESSION_TYPE = os.getenv("SESSION_TYPE", "PREMARKET")
PDF_FILENAME = "daily_trading_blueprint.pdf"

if not GEMINI_API_KEY:
    print("❌ FATAL ERROR: 'GEMINI_API_KEY' environment variable is not set!")
    print("Please verify your GitHub Secrets settings.")
    sys.exit(1)

# Initialize Gemini Client
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"❌ FATAL ERROR: Failed to initialize Gemini Client: {e}")
    sys.exit(1)

# 2. Session Context Configuration
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

# ---------------------------------------------------------------------------
# Reliability note: previously Gemini was asked to WRITE a Python/WeasyPrint
# script which we exec()'d. Any single syntax slip in that generated code (e.g.
# an unterminated f-string) crashed the whole run. We now ask Gemini for the
# report *content as HTML only*; the strict page/table CSS and the WeasyPrint
# render are owned by this stable script, so a bad-code class of failure is gone.
# ---------------------------------------------------------------------------

REPORT_CSS = """
@page { size: A4 portrait; margin: 10mm 12mm 12mm 12mm; background-color: #fcfbf9; }
* { box-sizing: border-box; }
body { font-family: "Georgia", serif; font-size: 7.6pt; color: #1a1a1a; line-height: 1.35; }
h1 { font-size: 13pt; margin: 0 0 2px 0; }
h2 { font-size: 10pt; margin: 10px 0 4px 0; border-bottom: 1.5px solid #b8860b; padding-bottom: 2px; color: #4a3510; }
h3 { font-size: 8.4pt; margin: 6px 0 3px 0; color: #333; }
p { margin: 3px 0; }
ul { margin: 3px 0 3px 14px; padding: 0; }
li { margin: 1px 0; }
.box { border: 1px solid #d8d2c4; background: #ffffff; padding: 6px 8px; margin-bottom: 6px; page-break-inside: avoid; }
.meta { font-size: 7pt; color: #777; margin-bottom: 6px; }
table { table-layout: fixed; width: 100%; border-collapse: collapse; margin-bottom: 6px; page-break-inside: avoid; }
th { background: #4a3510; color: #fff; font-size: 7pt; padding: 3px 4px; text-align: left; }
td { border: 1px solid #ddd; word-wrap: break-word; overflow-wrap: break-word; vertical-align: top; padding: 3px 4px; }
tr:nth-child(even) td { background: #faf8f3; }
svg { max-width: 100%; }
"""

PROMPT = f"""
Act as a Lead Quantitative Strategist and Institutional Portfolio Manager. Generate a comprehensive 2-page Daily Multi-Asset Trading Blueprint & Level Execution Manual based on today's live market conditions and top financial news headlines.

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

Also include a 10-year backtest metrics table (Target CAGR 28.4%, Sharpe 1.45, Max DD -18.2%) vs S&P 500 TRI (~13.0%) and Nifty 50 TRI (~12.5%), and an inline SVG equity-curve chart ($3,000 → $36,512). Every stock/crypto table must have a dedicated "Strategy & Selection Reason" column.

### OUTPUT FORMAT — READ CAREFULLY
Return ONLY the report body as clean, self-contained HTML fragment inside a single ```html ``` code block. Rules:
- Output the inner content that belongs INSIDE <body> — do NOT include <!DOCTYPE>, <html>, <head>, <style>, or <body> tags (styling is applied by the host). No JavaScript.
- Use <h1>, <h2>, <h3>, <p>, <ul>/<li>, and <table><thead><th style="width:NN%"><tbody><td> for every table (give every <th> an explicit percentage width).
- Wrap each major section in <div class="box"> ... </div>.
- You MAY include an inline <svg>...</svg> for the equity curve. Do not use external images.
- Do not output any explanation, prose, or Python — HTML only, inside the one code block.
"""


def _extract_html(text: str) -> str:
    """Pull the HTML body fragment from Gemini's response, tolerating missing fences."""
    m = re.search(r'```html\s*(.*?)\s*```', text, re.DOTALL | re.IGNORECASE)
    if m:
        body = m.group(1)
    else:
        # Fallback: strip any code fences and use whatever came back.
        body = re.sub(r'```[a-zA-Z]*', '', text).replace('```', '').strip()
    # Defensive: if the model wrapped a full document, keep only the body inner.
    bm = re.search(r'<body[^>]*>(.*?)</body>', body, re.DOTALL | re.IGNORECASE)
    if bm:
        body = bm.group(1)
    return body.strip()


def generate_pdf():
    print(f"📡 Requesting market search & report content from Gemini [{SESSION_TYPE}]...")
    try:
        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=PROMPT,
            config=config,
        )

        body = _extract_html(response.text or "")
        if not body:
            print("❌ ERROR: Gemini returned no usable HTML content!")
            print("Gemini Output Snippet:", (response.text or "")[:300])
            return False

        ist_now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
        stamp = ist_now.strftime("%d %b %Y, %H:%M IST")
        full_html = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'>"
            f"<style>{REPORT_CSS}</style></head><body>"
            f"<h1>{current_session['title']}</h1>"
            f"<div class='meta'>Automated {SESSION_TYPE} blueprint · generated {stamp} · for education, not investment advice.</div>"
            f"{body}"
            "</body></html>"
        )

        print("⚙️ Rendering PDF via WeasyPrint (host-controlled, no exec)...")
        HTML(string=full_html).write_pdf(PDF_FILENAME)
        print(f"✅ PDF generated successfully: {PDF_FILENAME}")
        return True
    except Exception as e:
        print(f"❌ Error during Gemini PDF Generation: {e}")
        traceback.print_exc()
        return False


def send_telegram():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials missing. Skipping Telegram upload.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    caption_text = f"📈 *{current_session['title']}*\n\nAttached is your automated trading briefing for the *{SESSION_TYPE}* session."

    print("📱 Sending document to Telegram...")
    try:
        with open(PDF_FILENAME, "rb") as pdf_file:
            files = {"document": (PDF_FILENAME, pdf_file, "application/pdf")}
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

    try:
        with open(PDF_FILENAME, "rb") as f:
            attach = MIMEApplication(f.read(), _subtype="pdf")
            attach.add_header('Content-Disposition', 'attachment', filename=PDF_FILENAME)
            msg.attach(attach)

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
