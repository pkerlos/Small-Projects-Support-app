import streamlit as st
import sqlite3
import hashlib
from datetime import date

# ====================== إعدادات الصفحة ======================
st.set_page_config(page_title="مكتب المشروعات الصغيرة", page_icon="💰", layout="wide")

# CSS لتحسين المظهر وجعل القائمة واضحة في نصف الصفحة
st.markdown("""
    <style>
        .stApp {direction: rtl; text-align: right;}
        .main-btn {
            background-color: #007bff;
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin: 10px;
            font-size: 20px;
            cursor: pointer;
        }
    </style>
    """, unsafe_allow_html=True)

# ====================== قاعدة البيانات ======================
def get_db_connection():
    return sqlite3.connect('charity_projects.db', check_same_thread=False)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS eparchies (id INTEGER PRIMARY KEY, name TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS churches (id INTEGER PRIMARY KEY, name TEXT, ep_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, user TEXT UNIQUE, pwd TEXT, name TEXT, role TEXT, ch_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS borrowers (id INTEGER PRIMARY KEY, name TEXT, ch_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS loans (id INTEGER PRIMARY KEY, b_id INTEGER, amount REAL, inst_count INTEGER, inst_val REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, loan_id INTEGER, p_date TEXT, amount REAL, rec_by INTEGER)''')
    
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
        st.title("🔐 دخول نظام المشروعات")
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة السر", type="password")
        if st.button("دخول"):
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE user=?", (u,))
            res = c.fetchone()
            if res and res[2] == hashlib.sha256(p.encode()).hexdigest():
                st.session_state.user = {'id':res[0], 'name':res[3], 'role':res[4], 'ch_id':res[5]}
                st.rerun()
            else: st.error("بيانات خطأ")
    else:
        user = st.session_state.user
        st.title(f"👋 مرحباً {user['name']}")
        
        # أزرار الخروج والتنقل في الأعلى
        col_out, col_home = st.columns([1, 5])
        if col_out.button("🚪 خروج"):
            del st.session_state.user
            st.rerun()

        # القائمة الرئيسية في نص الصفحة (Main UI)
        st.subheader("🛠️ قائمة التحكم الرئيسية")
        
        if user['role'] == 'admin':
            # تقسيم الشاشة لـ 3 أعمدة للأزرار
            c1, c2, c3 = st.columns(3)
            
            # الخيار اللي أنت بتدور عليه "إدارة المستخدمين"
            if c1.button("👥 إدارة المستخدمين", use_container_width=True): st.session_state.page = "users"
            if c2.button("⛪ إدارة الكنائس", use_container_width=True): st.session_state.page = "churches"
            if c3.button("🏛️ إدارة الأبرشيات", use_container_width=True): st.session_state.page = "eparchies"
            
            c4, c5, c6 = st.columns(3)
            if c4.button("👤 إدارة المقترضين", use_container_width=True): st.session_state.page = "borrowers"
            if c5.button("💰 إنشاء القروض", use_container_width=True): st.session_state.page = "loans"
            if c6.button("📝 تسجيل سداد", use_container_width=True): st.session_state.page = "payments"
        else:
            # لو موظف كنيسة يظهر له السداد فقط
            if st.button("📝 تسجيل سداد قسط", use_container_width=True): st.session_state.page = "payments"

        st.divider()

        # عرض المحتوى بناءً على الزر المضغوط
        page = st.session_state.get('page', 'home')
        
        if page == "users":
            st.header("👥 إضافة وتأمين المستخدمين")
            # هنا كود إضافة المستخدم (اكتب بياناتك الجديدة هنا)
            with st.form("new_user"):
                new_u = st.text_input("اسم الدخول الجديد")
                new_p = st.text_input("الباسورد الجديد", type="password")
                new_n = st.text_input("الاسم بالكامل")
                if st.form_submit_button("إضافة"):
                    conn = get_db_connection()
                    c = conn.cursor()
                    h = hashlib.sha256(new_p.encode()).hexdigest()
                    c.execute("INSERT INTO users (user, pwd, name, role) VALUES (?,?,?,?)", (new_u, h, new_n, 'admin'))
                    conn.commit()
                    st.success("تمت الإضافة بنجاح!")
        
        elif page == "churches":
            st.write("واجهة إدارة الكنائس قيد التفعيل...")
            # (هنا تكملة باقي الصفحات بنفس المنطق)

if __name__ == "__main__":
    main()
