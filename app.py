import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# إعدادات واجهة التطبيق
st.set_page_config(page_title="رادار المضاربة اللحظية الشامل", layout="centered")

# تنسيق المظهر الداكن وتعديل الخطوط للغة العربية
st.markdown("""
    <style>
    @import url('https://googleapis.com');
    html, body, [class*="css"]  {
        font-family: 'Cairo', sans-serif;
        text-align: right;
        direction: rtl;
    }
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; color: #58a6ff;'>⚡ رادار المضاربة اللحظية والأهداف الفورية</h2>", unsafe_allow_html=True)

# حقول الإدخال بشكل عصري
ticker_input = st.text_input("✍️ أدخل رمز أو اسم السهم (مثال: AAPL, NVDA, 1120):", "AAPL")
interval = st.selectbox("⏱️ حدد الفريم اللحظي للمضاربة:", ["1m", "5m", "15m", "1h", "1d"], index=1)

ticker_str = ticker_input.strip().upper()
if ticker_str.isdigit() and len(ticker_str) == 4:
    ticker_str = f"{ticker_str}.SR"
    
arabic_map = {
    "الراجحي": "1120.SR", "أرامكو": "2222.SR", "سابك": "2010.SR", 
    "الأهلي": "1180.SR", "اس تي سي": "7010.SR", "STC": "7010.SR",
    "أبل": "AAPL", "ابل": "AAPL", "تسلا": "TSLA", "انفيديا": "NVDA"
}
if ticker_str in arabic_map:
    ticker_str = arabic_map[ticker_str]

period = "5d" if interval in ["1m", "5m", "15m"] else "1mo"
currency = "ريال" if ".SR" in ticker_str else "$"
tradingview_url = f"https://tradingview.com{ticker_str.replace('.SR', '')}/" if ".SR" not in ticker_str else f"https://tradingview.com{ticker_str.replace('.SR', '')}/"

try:
    stock = yf.Ticker(ticker_str)
    df = stock.history(interval=interval, period=period, prepost=True)
    df_yearly = stock.history(period="1y")
    
    if df.empty or df_yearly.empty:
        st.error("❌ تعذر العثور على بيانات للسهم المكتوب. يرجى التحقق من الرمز.")
    else:
        live_price = df['Close'].iloc[-1]
        yearly_high = df_yearly['High'].max()
        yearly_low = df_yearly['Low'].min()
        
        # المؤشرات الفنية
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 0.00001)
        df['RSI'] = 100 - (100 / (1 + rs))
        live_rsi = df['RSI'].iloc[-1] if not np.isnan(df['RSI'].iloc[-1]) else 50.0
        
        df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
        live_ema9 = df['EMA9'].iloc[-1]
        
        high_low = df['High'] - df['Low']
        high_cp = np.abs(df['High'] - df['Close'].shift())
        low_cp = np.abs(df['Low'] - df['Close'].shift())
        df['TR'] = pd.concat([high_low, high_cp, low_cp], axis=1).max(axis=1)
        df['ATR'] = df['TR'].rolling(window=14).mean()
        live_atr = df['ATR'].iloc[-1] if not np.isnan(df['ATR'].iloc[-1]) else (live_price * 0.01)

        recent_high = df['High'].tail(15).max()
        recent_low = df['Low'].tail(15).min()
        
        pivot = (recent_high + recent_low + live_price) / 3
        res1 = (2 * pivot) - recent_low
        sup1 = (2 * pivot) - recent_high
        res2 = pivot + (recent_high - recent_low)
        sup2 = pivot - (recent_high - recent_low)

        buy_zone_min, buy_zone_max = sup1 * 0.998, sup1 * 1.01
        fast_entry_min, fast_entry_max = live_price, live_price * 1.012
        
        target1 = live_price + (live_atr * 1.5)
        target2 = live_price + (live_atr * 2.5)
        target3 = recent_high
        stop_loss = sup2 * 0.995

        # تحديد التنبيه اللحظي
        if live_price <= buy_zone_max and live_rsi <= 42:
            st.success("🟩 **[ تنبيه شراء ذهبي ]** السهم في منطقة طلب قوية وتجميع قاع الشارت!")
        elif live_price > live_ema9 and live_rsi < 65:
            st.info("🔵 **[ تنبيه دخول سريع ]** اختراق إيجابي وزخم سيولة متصاعد لركوب الموجة!")
        elif live_rsi >= 72:
            st.error("🔴 **[ تنبيه جني أرباح ]** تشبع شرائي حاد، السهم يقترب من قمم بيعية!")
        else:
            st.warning("🟡 **[ حالة مراقبة ]** السهم مستقر داخل النطاق، انتظر تأكيد الاختراق.")

        # عرض الكروت الرقمية المنسقة
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="السعر المباشر الآن", value=f"{live_price:.2f} {currency}")
            st.metric(label="مؤشر القوة RSI", value=f"{live_rsi:.2f}")
        with col2:
            st.metric(label="منطقة الدخول المناسبة (آمن)", value=f"{buy_zone_min:.2f} - {buy_zone_max:.2f}")
            st.metric(label="منطقة الدخول السريع (زخم)", value=f"{fast_entry_min:.2f} - {fast_entry_max:.2f}")

        # عرض المستهدفات
        st.markdown("### 🎯 المستهدفات الفنية المضاربية:")
        st.write(f"🥇 **الهدف الأول:** `{target1:.2f} {currency}`")
        st.write(f"🥈 **الهدف الثاني:** `{target2:.2f} {currency}`")
        st.write(f"🥉 **الهدف الثالث:** `{target3:.2f} {currency}`")
        st.markdown(f"🚨 **وقف الخسارة الصارم النهائي (SL):** <span style='color:#ff7b72; font-weight:bold;'>{stop_loss:.2f} {currency}</span>", unsafe_allow_html=True)

        # مستويات الدعم والمقاومة الكلاسيكية
        with st.expander("🧱 مستويات الدعم والمقاومة والقنوات السنوية"):
            st.write(f"🟢 **الدعم 1:** `{sup1:.2f}` | 🟢 **الدعم 2:** `{sup2:.2f}`")
            st.write(f"🔴 **المقاومة 1:** `{res1:.2f}` | 🔴 **المقاومة 2:** `{res2:.2f}`")
            st.write(f"🔝 **القمة السنوية:** `{yearly_high:.2f}` | 🛑 **القاع السنوي:** `{yearly_low:.2f}`")

except Exception:
    st.warning("⚠️ حقول تدفق البيانات معطلة مؤقتاً خارج أوقات العمل الرسمية.")
    st.markdown(f"👉 [تصفح شارت {ticker_str} الفوري على منصة TradingView]({tradingview_url})")
