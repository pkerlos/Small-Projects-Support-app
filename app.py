import streamlit as st
import sqlite3
import hashlib
from datetime import date
import socket
import qrcode
from io import BytesIO
import os

# ====================== إعدادات الصفحة ======================
st.set_page_config(page_title="نظام المشروعات الصغيرة", page_icon="💰", layout="centered")

# الحصول على رابط الشبكة للموبايل
def get_network_url():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return f"http://{ip}:8501"
    except:
        return "برجاء استخدام رابط المتصفح"

# تنسيق الواجهة (CSS)
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
        html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
        .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-size: 18px !important; background-color: #007bff; color: white; margin-bottom: 10px; }
        .stTextInput>div>div>input { font-size: 18px !important; }
    </style>
    """, unsafe_allow_html=True)

# ====================== قاعدة البيانات (المسار الثابت) ======================
DB_PATH = os.path.join(os.getcwd(), 'charity_projects.db')

def get_db_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, user TEXT UNIQUE, pwd TEXT, name TEXT, role TEXT, ch_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS eparchies (id INTEGER PRIMARY KEY, name TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS churches (id INTEGER PRIMARY KEY, name TEXT, ep_id INTEGER)''')
    # تأكد من وجود الأدمن الافتراضي
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        hashed = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO users (user, pwd, name, role) VALUES (?, ?, ?, ?)", ("admin", hashed, "مدير المكتب", "admin"))
    conn.commit()
    conn.close()

# ====================== التطبيق الرئيسي ======================
def main():
    init_db()
    
    if 'user' not in st.session_state:
        st.title("🔐 تسجيل الدخول")
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة السر", type="password")
        if st.button("دخول"):
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE user=?", (u,))
            res = c.fetchone()
            conn.close()
            if res and res[2] == hashlib.sha256(p.encode()).hexdigest():
                st.session_state.user = {'id':res[0], 'name':res[3], 'role':res[4]}
                st.rerun()
            else:
                st.error("بيانات الدخول غير صحيحة")
    else:
        user = st.session_state.user
        st.subheader(f"👋 أهلاً بك: {user['name']}")
        
        if st.button("🚪 تسجيل خروج"):
            del st.session_state.user
            st.rerun()

        st.divider()
        
        # القائمة الرئيسية
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👥 إدارة المستخدمين"): st.session_state.page = "users"
        with col2:
            if st.button("🏛️ الأبرشيات والكنائس"): st.session_state.page = "setup"

        # --- صفحة المستخدمين ---
        page = st.session_state.get('page', 'home')
        if page == "users":
            st.markdown("### ➕ إضافة مستخدم جديد")
            with st.form("new_user_form", clear_on_submit=True):
                new_u = st.text_input("اسم الدخول (بالإنجليزي)")
                new_p = st.text_input("كلمة السر", type="password")
                new_n = st.text_input("الاسم الثلاثي")
                submit = st.form_submit_button("حفظ الحساب")
                if submit:
                    if new_u and new_p and new_n:
                        conn = get_db_connection()
                        c = conn.cursor()
                        h = hashlib.sha256(new_p.encode()).hexdigest()
                        try:
                            c.execute("INSERT INTO users (user, pwd, name, role) VALUES (?,?,?,?)", (new_u, h, new_n, 'admin'))
                            conn.commit()
                            st.success(f"✅ تم حفظ {new_u} بنجاح! جرب تسجيل الخروج والدخول به.")
                        except sqlite3.IntegrityError:
                            st.error("اسم المستخدم موجود بالفعل!")
                        finally:
                            conn.close()
                    else:
                        st.warning("برجاء ملء كافة الخانات")

        if page != 'home':
            if st.button("🔙 العودة للرئيسية"):
                st.session_state.page = 'home'
                st.rerun()

        # --- ظهور QR Code في أسفل الصفحة الرئيسية ---
        if page == 'home':
            st.divider()
            st.write("📲 **للدخول من الموبايل:**")
            url = get_network_url()
            # في Streamlit Cloud الرابط هو لينك المتصفح نفسه
            current_url = "https://small-projects-support-app.streamlit.app" 
            img = qrcode.make(current_url)
            buf = BytesIO()
            img.save(buf)
            st.image(buf, caption="امسح الكود لفتح البرنامج على موبايلك", width=200)

if __name__ == "__main__":
    main()
