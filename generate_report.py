import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from google import genai
from google.genai import types

# 1. Fetch Environment Secrets & Session Type
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

# SESSION_TYPE will be passed from GitHub Actions ("PREMARKET", "LONDON", "NEWYORK")
SESSION_TYPE = os.getenv("SESSION_TYPE", "PREMARKET")

client = genai.Client(api_key=GEMINI_API_KEY)

# Custom Subject and Header Based on Session
SESSION_MAP = {
    "PREMARKET": {
        "title": "🌅 8:00 AM IST Premarket Report & Indian Market Setup",
        "news_focus": "Focus heavily on Asian overnight markets, GIFT Nifty, domestic Indian news (Economic Times, Moneycontrol), and intraday Nifty/BankNifty option levels."
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
Act as a Lead Quantitative Strategist and Institutional Portfolio Manager. Generate a comprehensive Daily Multi-Asset Trading Blueprint & Level Execution Manual in PDF format.

CURRENT SESSION HIGHLIGHT: {current_session['title']}
SESSION NEWS FOCUS: {current_session['news_focus']}

### 📰 SECTION 0: DAILY MACRO & FINANCIAL NEWS DIGEST
Perform a live web search to aggregate and summarize major market-moving news headlines across global and domestic sources (e.g., Bloomberg, CNBC, BBC News, Economic Times India, Forex Factory, Reuters).

### 💰 CAPITAL BASE & ALLOCATION RULES ($3,000 TOTAL)
1. Crypto Futures: $400 (13.3%) | Rec. Leverage: 3x–5x Isolated | Risk Cap: 1–2% ($4–$8)
2. Indian Options (Intraday): $500 (16.7%) | Option Buying Only | Risk Cap: 10–15% Premium ($30–$45)
3. Commodities (Micro Gold & Oil): $400 (13.3%) | Rec. Leverage: 10x–15x Micro Lots | Risk Cap: 2% ($8)
4. US Stocks (Fractional): $400 (13.3%) | 1x Unleveraged Cash | Risk Cap: 3% ($12)
5. Indian Stocks (Delivery): $400 (13.3%) | 1x Unleveraged Cash | Risk Cap: 5% ($20)
6. Forex Short-Term Futures: $450 (15.0%) | Rec. Leverage: 10x–20x | Risk Cap: 1% ($4.50)
7. Forex Long-Term Carry Swing: $450 (15.0%) | Rec. Leverage: 2x–3x | Risk Cap: 2% ($9.00)

### 🎯 STRATEGY-BASED DAILY TICKER SELECTION & SECTOR RULES
Search live market data right now and dynamically select top-performing tickers:
1. US EQUITIES (Large-Cap: BI-DIRECTIONAL | Mid & Small-Cap: STRICTLY LONG-ONLY).
2. INDIAN EQUITIES (STRICTLY LONG-ONLY across Large, Mid, Small).
3. CRYPTO FUTURES (BI-DIRECTIONAL across Large, Mid, Small).
4. COMMODITIES (BI-DIRECTIONAL): Gold (XAU/USD) and WTI Crude Oil.
5. FOREX FUTURES (BI-DIRECTIONAL): Short-Term (EUR/USD, GBP/USD) & Macro Carry Swings (USD/JPY, AUD/USD).
6. INDIAN OPTIONS (BI-DIRECTIONAL): Nifty 50 / BankNifty 15-Minute Opening Range Breakouts.

### 📊 REPORT FORMAT & DESIGN REQUIREMENTS
Write a Python script using `weasyprint` and `HTML` to compile a PDF named 'daily_trading_blueprint.pdf'.
- Styling: Serif typography, warm off-white background (#FCFBF9), navy headers (#1A2B3C), color tags (LONG: Green, SHORT: Red).
- Dedicated "Strategy & Selection Reason" column for all stocks/crypto.
- Embedded 10-year backtest performance table and SVG equity curve chart ($3,000 to $36,512).

Output ONLY executable Python code inside ```python ``` code blocks.
"""

def generate_pdf():
    print(f"Generating PDF report for {SESSION_TYPE} session...")
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
        exec(py_code, globals())
        return True
    return False

def send_email():
    pdf_filename = "daily_trading_blueprint.pdf"
    if not os.path.exists(pdf_filename):
        return

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT_EMAIL
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
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully for {SESSION_TYPE} session!")
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == "__main__":
    if generate_pdf():
        send_email()
