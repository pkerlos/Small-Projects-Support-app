import streamlit as st
import sqlite3
from datetime import date
import hashlib
import socket
import qrcode
from io import BytesIO

# ====================== إعدادات الصفحة وتحسين الموبايل ======================
st.set_page_config(page_title="مكتب المشروعات الصغيرة", page_icon="💰", layout="wide")

# CSS لتحسين المظهر على الموبايل واللغة العربية
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
        html, body, [class*="css"] {
            font-family: 'Cairo', sans-serif;
            direction: rtl;
            text-align: right;
        }
        .stButton>button {
            width: 100%;
            border-radius: 10px;
            height: 3em;
            background-color: #007bff;
            color: white;
        }
        /* تحسين شكل المدخلات على الموبايل */
        .stTextInput>div>div>input {
            font-size: 18px !important;
        }
    </style>
    """, unsafe_allow_html=True)

# دالة للحصول على آي بي الجهاز لتوليد QR Code
def get_status_info():
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return f"http://{local_ip}:8501"
    except:
        return None

# ====================== الجزء الخاص بقاعدة البيانات (نفس الكود السابق مع التأكد من وجوده) ======================
def get_db_connection():
    return sqlite3.connect('charity_projects.db', check_same_thread=False)

def init_database():
    conn = get_db_connection()
    c = conn.cursor()
    # (نفس الجداول السابقة: eparchies, churches, users, borrowers, loans, payments)
    # ملاحظة: تأكد من إضافة الجداول هنا كما في الكود السابق
    c.execute('''CREATE TABLE IF NOT EXISTS eparchies (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS churches (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, eparchy_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT, full_name TEXT, role TEXT, church_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS borrowers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, church_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS loans (id INTEGER PRIMARY KEY AUTOINCREMENT, borrower_id INTEGER, amount REAL, approval_date TEXT, num_installments INTEGER, installment_amount REAL, status TEXT DEFAULT 'active')''')
    c.execute('''CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY AUTOINCREMENT, loan_id INTEGER, payment_date TEXT, amount REAL, recorded_by INTEGER)''')
    
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        hashed = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
                  ("admin", hashed, "مدير المكتب", "admin"))
    conn.commit()
    conn.close()

# (بقية الدوال: hash_password, verify_password, show_login, dashboard, إلخ...)
# سأضع لك فقط الجزء الخاص بظهور الـ QR Code في الجانب (Sidebar)

def main():
    init_database()
    
    if 'user' not in st.session_state or st.session_state.user is None:
        # شاشة الدخول
        st.title("🔐 تسجيل دخول الموظفين")
        user_input = st.text_input("اسم المستخدم")
        pass_input = st.text_input("كلمة السر", type="password")
        if st.button("دخول"):
            # منطق التحقق (كما في الكود السابق)
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE username = ?", (user_input,))
            res = c.fetchone()
            if res and res[2] == hashlib.sha256(pass_input.encode()).hexdigest():
                st.session_state.user = {'id':res[0], 'name':res[3], 'role':res[4], 'church_id':res[5]}
                st.rerun()
            else: st.error("خطأ في البيانات")
            
    else:
        # عرض QR Code في القائمة الجانبية للمساعدة في ربط الموبايلات
        network_url = get_status_info()
        if network_url:
            with st.sidebar.expander("📲 ربط الموبايل (Scan QR)"):
                img = qrcode.make(network_url)
                buf = BytesIO()
                img.save(buf)
                st.image(buf, caption="امسح الكود بالموبايل للدخول")
                st.code(network_url)

        st.sidebar.success(f"مرحباً: {st.session_state.user['name']}")
        # (بقية منطق الصفحات والتقارير...)
        st.info("البرنامج جاهز للعمل من الموبايل أو الكمبيوتر")

if __name__ == "__main__":
    main()