import streamlit as st
import yfinance as yf
from textblob import TextBlob
import datetime

# 1. دالة جلب الأخبار وتحليل مشاعرها
def get_stock_news_with_sentiment(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        news_list = stock.news
        
        analyzed_news = []
        for item in news_list[:5]: # جلب آخر 5 أخبار فقط للسرعة
            title = item.get('title', '')
            link = item.get('link', '')
            publisher = item.get('publisher', '')
            
            # تحويل الطابع الزمني المقروء (إذا توفر)
            pub_time = item.get('providerPublishTime', '')
            if pub_time:
                pub_date = datetime.datetime.fromtimestamp(pub_time).strftime('%Y-%m-%d %H:%M')
            else:
                pub_date = "غير محدد"
            
            # تحليل المشاعر باستخدام TextBlob (يعتمد على النص الإنجليزي للخبر)
            analysis = TextBlob(title)
            polarity = analysis.sentiment.polarity # قيمة بين -1 و 1
            
            if polarity > 0.05:
                sentiment = "إيجابي 🟢"
                color = "green"
            elif polarity < -0.05:
                sentiment = "سلبي 🔴"
                color = "red"
            else:
                sentiment = "محايد 🟡"
                color = "gray"
                
            analyzed_news.append({
                'title': title,
                'link': link,
                'publisher': publisher,
                'date': pub_date,
                'sentiment': sentiment,
                'color': color,
                'polarity': polarity
            })
        return analyzed_news
    except Exception as e:
        return []

# 2. كود العرض والتنبيهات الذكية داخل واجهة Streamlit
def render_news_radar(ticker):
    st.subheader(f"📡 رادار الأخبار والتنبيهات الذكية للرمز: {ticker}")
    
    with st.spinner("جلب وتحليل الأخبار الحالية..."):
        news_data = get_stock_news_with_sentiment(ticker)
        
    if not news_data:
        st.info("لا توجد أخبار حديثة متوفرة لهذا السهم حالياً.")
        return

    # حساب النبض العام للمشاعر (Overall Sentiment Pulse)
    avg_polarity = sum([item['polarity'] for item in news_data]) / len(news_data)
    
    # عرض التنبيه الذكي للرادار (Alert Box) بناءً على متوسط المشاعر
    if avg_polarity > 0.1:
        st.success(f"🚨 **تنبيه الرادار الذكي:** الزخم العام للأخبار **إيجابي** نحو الشركة! قد يشير هذا إلى تفاؤل في السوق.")
    elif avg_polarity < -0.1:
        st.error(f"🚨 **تنبيه الرادار الذكي:** رصد أخبار ذات طابع **سلبي**. يرجى توخي الحذر ومتابعة التطورات.")
    else:
        st.warning(f"🚨 **تنبيه الرادار الذكي:** المشاعر العامة للأخبار **محايدة / مستقرة** حالياً.")

    # عرض تفاصيل الأخبار داخل بطاقات منظمة
    st.markdown("### 📰 آخر المستجدات وتحليلها:")
    for news in news_data:
        with st.container():
            st.markdown(
                f"""
                <div style="padding:15px; border-radius:10px; border-right: 5px solid {news['color']}; background-color: #f9f9f9; margin-bottom:10px">
                    <h4 style="margin:0; color:#333;"><a href="{news['link']}" target="_blank" style="text-decoration:none; color:#1f77b4;">{news['title']}</a></h4>
                    <p style="margin:5px 0; color:#666; font-size:12px;">المصدر: {news['publisher']} | التاريخ: {news['date']}</p>
                    <span style="background-color:{news['color']}; color:white; padding:3px 8px; border-radius:5px; font-size:12px;">{news['sentiment']}</span>
                </div>
                """, 
                unsafe_allow_html=True
            )

# مثال لطريقة التشغيل داخل واجهتك الحالية:
# ستحتاج فقط لتمرير اسم متغير السهم المختار (مثل 'AAPL' أو '2222.SR' للأسهم السعودية) إلى الدالة
# render_news_radar(selected_ticker)
