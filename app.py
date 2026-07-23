import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# إعدادات واجهة التطبيق
st.set_page_config(page_title="الرادار اللحظي المتقدم للأسهم", layout="centered")

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
    div[data-testid="stMetricValue"] { font-size: 22px !important; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; color: #58a6ff;'>⚡ رادار المضاربة اللحظية والتدفق الفوري للأسهم</h2>", unsafe_allow_html=True)

# شريط التحكم والأدوات المدمجة بالتحديث اللحظي
col_ctrl1, col_ctrl2 = st.columns(2)
with col_ctrl1:
    ticker_input = st.text_input("✍️ أدخل رمز أو اسم السهم (مثال: AAPL, NVDA, 1120):", "AAPL")
with col_ctrl2:
    interval = st.selectbox("⏱️ الفريم اللحظي:", ["1m", "5m", "15m", "1h", "1d"], index=1)

# معالجة تلقائية للرموز والأسماء الشائعة
ticker_str = ticker_input.strip().upper()
if ticker_str.isdigit() and len(ticker_str) == 4:
    ticker_str = f"{ticker_str}.SR"
    
arabic_map = {
    "الراجحي": "1120.SR", "أرامكو": "2222.SR", "سابك": "2010.SR", 
    "الأهلي": "1180.SR", "اس تي سي": "7010.SR", "STC": "7010.SR",
    "أبل": "AAPL", "ابل": "AAPL", "تسلا": "TSLA", "انفيديا": "NVDA", "جوجل": "GOOGL"
}
if ticker_str in arabic_map:
    ticker_str = arabic_map[ticker_str]

period = "5d" if interval in ["1m", "5m", "15m"] else "1mo"
currency = "ريال" if ".SR" in ticker_str else "$"
tradingview_url = f"https://tradingview.com{ticker_str.replace('.SR', '')}/" if ".SR" not in ticker_str else f"https://tradingview.com{ticker_str.replace('.SR', '')}/"

try:
    # جلب حزم البيانات الفورية والمالية التفصيلية
    stock = yf.Ticker(ticker_str)
    df = stock.history(interval=interval, period=period, prepost=True)
    df_yearly = stock.history(period="1y")
    
    # حماية سحب معلومات الشركة لتجنب توقف السكربت في حال عدم توفرها
    try:
        info = stock.info
    except:
        info = {}
    
    if df.empty or df_yearly.empty:
        st.error("❌ تعذر العثور على بيانات للسهم المكتوب. يرجى التحقق من الرمز أو انتظار مواعيد عمل السوق.")
    else:
        # 1. استخراج السعر المباشر النشط في هذه اللحظة بدقة متناهية والتوقيت الممتد
        live_price = df['Close'].iloc[-1]
        pre_market_price = info.get('preMarketPrice', None)
        post_market_price = info.get('postMarketPrice', None)
        market_state = str(info.get('marketState', 'REGULAR')).upper()
        
        current_active_price = live_price
        price_status_label = "الجلسة الرسمية 🟢"
        
        if "PRE" in market_state and pre_market_price:
            current_active_price = pre_market_price
            price_status_label = "ما قبل السوق (Pre-Market) 🟡"
        elif "POST" in market_state and post_market_price:
            current_active_price = post_market_price
            price_status_label = "ما بعد الإغلاق (After-Hours) 🔵"
        elif "REGULAR" not in market_state:
            price_status_label = "السوق مغلق حالياً 🔴"

        # 2. حساب المؤشرات الفنية المضاربية
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

        yearly_high = df_yearly['High'].max()
        yearly_low = df_yearly['Low'].min()

        # 3. استخراج اتجاه السهم، السيولة والأسهم الحرة للتداول
        trend_text = "اتجاه صاعد 📈" if live_price >= live_ema9 else "اتجاه هابط 📉"
        live_volume = df['Volume'].iloc[-1]
        
        # جلب حجم الأسهم الحرة المتاحة للتداول (Float Shares)
        float_shares = info.get('floatShares', None)
        if float_shares:
            if float_shares >= 1e9: float_shares_text = f"{float_shares / 1e9:.2f} مليار سهم"
            elif float_shares >= 1e6: float_shares_text = f"{float_shares / 1e6:.2f} مليون سهم"
            else: float_shares_text = f"{float_shares:,} سهم"
        else:
            float_shares_text = "متوفر للأسهم الكبرى"

        # 4. فلترة وتوليد النصيحة الاستراتيجية الفورية للسهم بناءً على حركة المؤشرات
        if live_price <= buy_zone_max and live_rsi <= 42:
            st.success("🟩 **[ تنبيه شراء ذهبي ]** السهم في منطقة طلب قوية وتجميع قاع الشارت!")
            advice_text = "💡 **نصيحة الرادار:** السهم يتداول حالياً عند مستويات دعم تجميعية قوية مع تشبع بيعي واضح، تعتبر فرصة ممتازة لبناء مراكز شرائية أولية وتفعيل أمر وقف الخسارة الصارم."
        elif live_price > live_ema9 and live_rsi < 65:
            st.info("🔵 **[ تنبيه دخول سريع ]** اختراق إيجابي وزخم سيولة متصاعد لركوب الموجة!")
            advice_text = "💡 **نصيحة الرادار:** السهم يُظهر اختراقاً إيجابياً لمتوسط الحركة السريعة EMA9 مع اندفاع في السيولة اللحظية، ينصح بالدخول السريع لاقتناص موجة الزخم ومتابعة الأهداف."
        elif live_rsi >= 72:
            st.error("🔴 **[ تنبيه جني أرباح ]** تشبع شرائي حاد، السهم يقترب من قمم بيعية!")
            advice_text = "💡 **نصيحة الرادار:** المؤشرات الفنية اللحظية دخلت في مناطق الإفراط والتشبع الشرائي الحاد (RSI > 72). يفضل البدء في جني الأرباح التدريجي لتأمين مكاسبك."
        else:
            st.warning("🟡 **[ حالة مراقبة ]** السهم مستقر داخل النطاق، انتظر تأكيد الاختراق.")
            advice_text = "💡 **نصيحة الرادار:** السهم يتحرك حالياً في مسار عرضي متذبذب دون اتجاه واضح، يفضل البقاء في الانتظار والمراقبة حتى تأكيد اختراق المقاومة الأولى أو ملامسة الدعم الأول."

        # عرض الكروت الرقمية المحدثة
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label=f"💰 السعر المباشر الآن ({price_status_label})", value=f"{current_active_price:.2f} {currency}")
            st.metric(label="📊 اتجاه السهم الفني الحالي", value=trend_text)
            st.metric(label="🌊 حجم السيولة المتداولة (Volume)", value=f"{live_volume:,}")
        with col2:
            st.metric(label="🟩 منطقة أفضل سعر شراء (آمن)", value=f"{buy_zone_min:.2f} - {buy_zone_max:.2f}")
            st.metric(label="⚡ منطقة الدخول السريع (زخم)", value=f"{fast_entry_min:.2f} - {fast_entry_max:.2f}")
            st.metric(label="💎 الأسهم المتاحة للتداول (Float)", value=float_shares_text)

        # حقن النصيحة الاستراتيجية للسهم في الواجهة
        st.markdown(f"<div style='background-color:#161b22; padding:15px; border-radius:10px; border:1px solid #30363d; margin-top:10px; margin-bottom:15px; line-height:1.6;'>{advice_text}</div>", unsafe_allow_html=True)

        # عرض المستهدفات ووقف الخسارة
        st.markdown("### 🎯 المستهدفات الفنية المضاربية:")
        st.write(f"🥇 **الهدف الأول (جني سريع):** `{target1:.2f} {currency}`")
        st.write(f"🥈 **الهدف الثاني (متوسط اليوم):** `{target2:.2f} {currency}`")
        st.write(f"🥉 **الهدف الثالث (القمة القريبة):** `{target3:.2f} {currency}`")
        st.markdown(f"🚨 **وقف الخسارة الصارم النهائي (SL):** <span style='color:#ff7b72; font-weight:bold;'>{stop_loss:.2f} {currency}</span>", unsafe_allow_html=True)

        # 5. سحب شريط الأخبار العاجلة المحدث مع الحماية من تغير حقول البورصة
        st.markdown("---")
        st.markdown("### 📰 آخر أخبار السهم والتحليل الذكي للخبر:")
        
        try:
            news_list = stock.news
            if news_list and len(news_list) > 0:
                count = 0
                for article in news_list:
                    if count >= 3: break # الاكتفاء بآخر 3 أخبار منعاً للازدحام
                    
                    # سحب البيانات بأمان مع وضع نصوص بديلة منعاً لأخطاء الحقول المعطوبة
                    title = article.get('title', article.get('headline', ''))
                    link = article.get('link', article.get('url', '#'))
                    publisher = article.get('publisher', article.get('source', 'موقع إخباري'))
                    
                    if not title: continue
                    
                    title_lower = title.lower()
                    positive_keywords = ['up', 'growth', 'gain', 'profit', 'buy', 'positive', 'surpass', 'bullish', 'invest', 'ارتفاع', 'نمو', 'أرباح', 'شراء']
                    negative_keywords = ['down', 'fall', 'loss', 'drop', 'negative', 'sell', 'bearish', 'risk', 'deficit', 'انخفاض', 'خسارة', 'تراجع', 'بيع']
                    
                    if any(k in title_lower for k in positive_keywords):
                        sentiment_label = "🟢 خبر إيجابي يدعم صعود السهم والزخم"
                    elif any(k in title_lower for k in negative_keywords):
