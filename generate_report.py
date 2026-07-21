import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from google import genai
from google.genai import types

# 1. Fetch Environment Secrets
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")  # Accepts single email OR comma-separated emails

# Session Type passed from GitHub Actions or defaults to PREMARKET
SESSION_TYPE = os.getenv("SESSION_TYPE", "PREMARKET")

client = genai.Client(api_key=GEMINI_API_KEY)

# 2. Dynamic Session Configuration
SESSION_MAP = {
    "PREMARKET": {
        "title": "🌅 8:00 AM IST Premarket Report & Indian Market Setup",
        "news_focus": "Focus heavily on Asian overnight markets, GIFT Nifty, domestic Indian news (Economic Times India, Moneycontrol), institutional flows (FII/DII), and intraday Nifty/BankNifty option levels."
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

# 3. Master Prompt with Strict CSS Layout & Strategy Rules
PROMPT = f"""
Act as a Lead Quantitative Strategist and Institutional Portfolio Manager. Generate a comprehensive 2-page Daily Multi-Asset Trading Blueprint & Level Execution Manual in PDF format based on today's live market conditions and top financial news headlines.

CURRENT SESSION HIGHLIGHT: {current_session['title']}
SESSION NEWS FOCUS: {current_session['news_focus']}

### 📰 SECTION 0: DAILY MACRO & FINANCIAL NEWS DIGEST
Perform a live web search to aggregate and summarize today's major market-moving news headlines across global and domestic sources (e.g., Bloomberg, CNBC, BBC News, Economic Times India, Forex Factory, Reuters). Organize into:
1. Global Macro & Central Banks: Key interest rate developments, inflation metrics, FOMC/ECB/RBI updates, and currency drivers.
2. US & European Markets: Wall Street futures, mega-cap tech earnings, semiconductor developments, and index momentum.
3. Indian Markets & Dalal Street: Sensex/Nifty updates, Q1/Q2 corporate earnings, FII/DII institutional flows, and sectoral momentum.
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
   - Mid-Cap & Small-Cap (STRICTLY LONG-ONLY): Screen using Stage-2 VCP (Volatility Contraction Pattern) or High Relative Volume (RVOL > 2.0) breakouts.
3. CRYPTO FUTURES (BI-DIRECTIONAL across Large, Mid, Small): Screen using 4H 21-EMA trend following and high-volume volatility breakouts.
4. COMMODITIES (BI-DIRECTIONAL): Gold (XAU/USD) and WTI Crude Oil using Pivot & Fibonacci extension levels.
5. FOREX FUTURES (BI-DIRECTIONAL): Short-Term (EUR/USD, GBP/USD) & Macro Carry Swings (USD/JPY, AUD/USD).
6. INDIAN OPTIONS (BI-DIRECTIONAL): Nifty 50 / BankNifty 15-Minute Opening Range Breakouts (Call for Long, Put for Short).

### 📊 MANDATORY HTML/CSS LAYOUT RULES FOR WEASYPRINT (STRICT COMPLIANCE REQUIRED)
Write a Python script using `weasyprint` and `HTML` to compile a PDF named 'daily_trading_blueprint.pdf'.
To ensure perfect table alignment and prevent text wrapping bugs, you MUST enforce the following CSS:
1. Set page size to A4 portrait with 10mm margins, and a serif font family ("Georgia", "Times New Roman", serif).
2. Set `table-layout: fixed; width: 100%; border-collapse: collapse; margin-bottom: 6px;` on ALL `<table>` elements.
3. Define explicit percentage widths on every `<th>` element (e.g., `<th style="width: 15%;">`).
4. Apply `word-wrap: break-word; overflow-wrap: break-word; vertical-align: top;` to ALL `<td>` elements to prevent horizontal overflow.
5. Set `page-break-inside: avoid;` on all tables, section boxes, and SVG graph containers.
6. Limit font size to 7pt–8pt for table contents and 6.8pt for table headers to maintain clean visual balance.
7. Include the 10-year backtest performance comparison table (Target CAGR 28.4%, Sharpe 1.45, Max DD -18.2%) vs S&P 500 TRI (~13.0%) and Nifty 50 TRI (~12.5%), along with an embedded vector/SVG equity curve chart ($3,000 to $36,512).
8. Every stock/crypto table must have a dedicated "Strategy & Selection Reason" column.

Output ONLY executable Python code inside ```python ``` code blocks.
"""

def generate_pdf():
    print(f"Fetching live market data and generating blueprint for [{SESSION_TYPE}] session...")
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=PROMPT,
            config=types.GenerateContentConfig(
                tools=[{"google_search": {}}] # Live Search Grounding Enabled
            )
        )

        match = re.search(r'```python\s*(.*?)\s*```', response.text, re.DOTALL)
        if match:
            py_code = match.group(1)
            print("Executing WeasyPrint script to render daily_trading_blueprint.pdf...")
            exec(py_code, globals())
            print("PDF generation complete!")
            return True
        else:
            print("Error: Could not extract Python code block from response.")
            return False
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return False

def send_email():
    pdf_filename = "daily_trading_blueprint.pdf"
    if not os.path.exists(pdf_filename):
        print("PDF file not found. Skipping email delivery.")
        return

    # Parse single or multiple comma-separated emails
    recipients = [e.strip() for e in RECIPIENT_EMAIL.split(",") if e.strip()]

    if not recipients:
        print("No valid recipient emails found.")
        return

    print(f"Sending automated briefing to {len(recipients)} recipient(s): {', '.join(recipients)}")
    
    # Setup MIME Message
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = current_session['title']

    body = f"Hello,\n\nAttached is your automated trading briefing for the {SESSION_TYPE} session.\n\nIncluded:\n- Section 0: Live Financial News Wire Digest\n- Strategy-Filtered Stock, Crypto & Forex Setups\n- Granular Long/Short Entry, Target & Stop Loss Levels\n- 10-Year Backtest Analytics\n\nBest regards,\nYour Automated Trading Desk"
    msg.attach(MIMEText(body, 'plain'))

    # Attach PDF Document
    with open(pdf_filename, "rb") as f:
        attach = MIMEApplication(f.read(), _subtype="pdf")
        attach.add_header('Content-Disposition', 'attachment', filename=pdf_filename)
        msg.attach(attach)

    # Send via Gmail SMTP Server
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipients, msg.as_string())
        server.quit()
        print(f"Email successfully delivered to all {len(recipients)} recipient(s)!")
    except Exception as e:
        print(f"Error sending email via SMTP: {e}")

if __name__ == "__main__":
    if generate_pdf():
        send_email()
