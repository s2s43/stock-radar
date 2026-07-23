import time
import requests

# إعدادات السهم والتنبيه
ticker = "AAPL"  # رمز السهم كمثال
threshold_percent = 1.0  # نسبة التغير المطلوبة لإطلاق التنبيه
previous_price = None

def get_stock_price(symbol):
    # هنا يتم الاتصال بالـ API لجلب السعر الحالي
    # كمثال افتراضي لـ API يعيد السعر:
    url = f"https://example.com{symbol}&apikey=YOUR_API_KEY"
    response = requests.get(url).json()
    return float(response['current_price'])

def send_telegram_alert(message):
    # كود إرسال الرسالة إلى هاتف المستخدم عبر تليجرام
    print(f"🚨 تنبيه عاجل: {message}")

# حلقة الرصد التلقائي اللانهائية
while True:
    try:
        current_price = get_stock_price(ticker)
        
        if previous_price is not None:
            # حساب نسبة التغير بين القراءة الحالية والسابقة
            change = ((current_price - previous_price) / previous_price) * 100
            
            if abs(change) >= threshold_percent:
                direction = "📈 صعود" if change > 0 else "📉 هبوط"
                send_telegram_alert(f"سهم {ticker} شهد {direction} بنسبة {change:.2f}%! السعر الحالي: {current_price}")
        
        # تحديث السعر السابق للقراءة القادمة
        previous_price = current_price
        
    except Exception as e:
        print(f"خطأ في جلب البيانات: {e}")
    
    # الانتظار لمدة 20 ثانية قبل التحديث القادم دون أي تدخل منك
    time.sleep(20)
