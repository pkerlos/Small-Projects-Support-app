import streamlit as st
import sqlite3
import hashlib
from datetime import date

# ====================== إعدادات الصفحة وتحسين الموبايل ======================
st.set_page_config(page_title="مكتب المشروعات", page_icon="💰", layout="wide")

# CSS احترافي للموبايل واللغة العربية
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
        html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
        
        /* تحسين شكل الأزرار للموبايل */
        .stButton>button {
            width: 100% !important;
            height: 3.5em;
            border-radius: 12px;
            font-size: 18px !important;
            margin-bottom: 10px;
            background-color: #007bff;
            color: white;
        }
        
        /* جعل الحقول مريحة للعين */
        .stTextInput>div>div>input { font-size: 18px !important; padding: 10px !important; }
        
        /* إخفاء القائمة الجانبية في الموبايل لتقليل التشتت */
        @media (max-width: 768px) {
            [data-testid="stSidebar"] { display: none; }
        }
    </style>
    """, unsafe_allow_html=True)

# ====================== قاعدة البيانات ======================
def get_db_connection():
    # استخدام ملف قاعدة بيانات ثابت
    return sqlite3.connect('charity_projects.db', check_same_thread=False)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # تأكد من وجود الجداول
    c.execute('''CREATE TABLE IF NOT EXISTS eparchies (id INTEGER PRIMARY KEY, name TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS churches (id INTEGER PRIMARY KEY, name TEXT, ep_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, user TEXT UNIQUE, pwd TEXT, name TEXT, role TEXT, ch_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS borrowers (id INTEGER PRIMARY KEY, name TEXT, phone TEXT, ch_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS loans (id INTEGER PRIMARY KEY, b_id INTEGER, amount REAL, inst_count INTEGER, inst_val REAL, status TEXT DEFAULT 'نشط')''')
    c.execute('''CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, loan_id INTEGER, p_date TEXT, amount REAL, rec_by TEXT)''')
    
    # حساب الأدمن الافتراضي
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        hashed = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO users (user, pwd, name, role) VALUES (?, ?, ?, ?)",
                  ("admin", hashed, "مدير المكتب", "admin"))
    conn.commit()
    conn.close()

# ====================== التطبيق الرئيسي ======================
def main():
    init_db()
    
    if 'user' not in st.session_state:
        st.title("🔐 دخول النظام")
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة السر", type="password")
        if st.button("دخول"):
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE user=?", (u,))
            res = c.fetchone()
            conn.close()
            if res and res[2] == hashlib.sha256(p.encode()).hexdigest():
                st.session_state.user = {'id':res[0], 'name':res[3], 'role':res[4], 'ch_id':res[5]}
                st.rerun()
            else:
                st.error("❌ اسم المستخدم أو الباسورد غلط")
    else:
        user = st.session_state.user
        st.header(f"👋 أهلاً {user['name']}")
        
        # زر الخروج في الأعلى (واضح للموبايل)
        if st.button("🚪 تسجيل خروج"):
            del st.session_state.user
            st.rerun()

        st.divider()

        # أزرار لوحة التحكم (متجاوبة تماماً)
        if user['role'] == 'admin':
            st.subheader("🛠️ الإدارة المركزية")
            c1, c2 = st.columns(2)
            if c1.button("👥 المستخدمين"): st.session_state.page = "users"
            if c2.button("⛪ الكنائس والأبرشيات"): st.session_state.page = "church_man"
            
            c3, c4 = st.columns(2)
            if c3.button("👤 المقترضين"): st.session_state.page = "borrowers"
            if c4.button("💰 إنشاء القروض"): st.session_state.page = "loans"
            
            if st.button("📝 تسجيل سداد قسط"): st.session_state.page = "payments"
        else:
            if st.button("📝 تسجيل سداد"): st.session_state.page = "payments"

        st.divider()
        page = st.session_state.get('page', 'home')
        
        # --- هنا تبدأ الصفحات (سأختصر لك صفحة المستخدمين للتجربة) ---
        if page == "users":
            st.subheader("إضافة مستخدم جديد")
            with st.form("add_u"):
                new_u = st.text_input("اسم الدخول")
                new_p = st.text_input("الباسورد", type="password")
                new_n = st.text_input("الاسم الثلاثي")
                if st.form_submit_button("حفظ المستخدم"):
                    conn = get_db_connection()
                    c = conn.cursor()
                    h = hashlib.sha256(new_p.encode()).hexdigest()
                    try:
                        c.execute("INSERT INTO users (user, pwd, name, role) VALUES (?,?,?,?)", (new_u, h, new_n, 'admin'))
                        conn.commit()
                        st.success("✅ تم الحفظ! جرب تخرج وتدخل بيه دلوقتي.")
                    except: st.error("اسم المستخدم ده موجود قبل كدة!")
                    conn.close()
        
        # يمكنك العودة للرئيسية
        if page != 'home':
            if st.button("🔙 العودة للرئيسية"):
                st.session_state.page = 'home'
                st.rerun()

if __name__ == "__main__":
    main()
