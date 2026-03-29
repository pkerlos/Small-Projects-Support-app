import streamlit as st
import sqlite3
import hashlib
from datetime import date
import qrcode
from io import BytesIO
import os

# ====================== إعدادات الصفحة ======================
st.set_page_config(page_title="نظام القروض الحسنة", page_icon="💰", layout="centered")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700&display=swap');
        html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
        .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

# ====================== قاعدة البيانات ======================
DB_PATH = 'charity_projects.db'

def get_db_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS eparchies (id INTEGER PRIMARY KEY, name TEXT UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS churches (id INTEGER PRIMARY KEY, name TEXT, ep_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, user TEXT UNIQUE, pwd TEXT, name TEXT, role TEXT, ch_id INTEGER)''')
    
    # حساب الأدمن الأساسي لو مش موجود
    c.execute("SELECT * FROM users WHERE user='admin'")
    if not c.fetchone():
        h = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO users (user, pwd, name, role) VALUES (?,?,?,?)", ("admin", h, "المدير العام", "admin"))
    conn.commit()
    conn.close()

# ====================== التطبيق الرئيسي ======================
def main():
    init_db()
    
    if 'user' not in st.session_state:
        st.title("🔐 تسجيل الدخول")
        u_input = st.text_input("اسم المستخدم (ID)")
        p_input = st.text_input("كلمة السر", type="password")
        
        if st.button("دخول"):
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE user=?", (u_input.strip(),))
            res = c.fetchone()
            conn.close()
            
            if res:
                stored_pwd = res[2]
                entered_pwd = hashlib.sha256(p_input.encode()).hexdigest()
                if stored_pwd == entered_pwd:
                    st.session_state.user = {'id': res[0], 'username': res[1], 'name': res[3], 'role': res[4], 'ch_id': res[5]}
                    st.rerun()
                else:
                    st.error("❌ كلمة السر غير صحيحة")
            else:
                st.error("❌ اسم المستخدم غير موجود")
    else:
        user = st.session_state.user
        st.sidebar.title(f"👋 {user['name']}")
        st.sidebar.write(f"الصلاحية: {user['role']}")
        if st.sidebar.button("🚪 تسجيل خروج"):
            del st.session_state.user
            st.rerun()

        # القائمة الرئيسية للمدير
        if user['role'] == 'admin':
            st.title("🛠️ لوحة تحكم المدير")
            menu = st.columns(2)
            if menu[0].button("👥 إدارة المستخدمين"): st.session_state.page = "users"
            if menu[1].button("🏛️ الكنائس والأبرشيات"): st.session_state.page = "setup"
        else:
            st.title("⛪ واجهة خادم الكنيسة")
            st.info(f"كنيسة: {user['ch_id']}") # سنطور عرض الاسم لاحقاً

        st.divider()
        page = st.session_state.get('page', 'home')

        # --- صفحة إدارة المستخدمين ---
        if page == "users":
            st.header("👥 إضافة مستخدم جديد")
            with st.form("new_user_form"):
                new_id = st.text_input("اسم المستخدم للدخول (بالإنجليزي)")
                new_pwd = st.text_input("كلمة السر الجديدة", type="password")
                full_name = st.text_input("الاسم الثلاثي للخادم")
                role_type = st.selectbox("نوع الصلاحية", ["admin", "church_staff"], format_func=lambda x: "مدير مشروع" if x=="admin" else "خادم كنيسة")
                
                # جلب الكنائس لو كان خادم كنيسة
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("SELECT id, name FROM churches")
                church_list = c.fetchall()
                conn.close()
                
                selected_church = st.selectbox("اختر الكنيسة (للخدام فقط)", church_list, format_func=lambda x: x[1]) if role_type == "church_staff" else None
                
                if st.form_submit_button("حفظ البيانات"):
                    if new_id and new_pwd and full_name:
                        conn = get_db_connection()
                        c = conn.cursor()
                        h_pwd = hashlib.sha256(new_pwd.encode()).hexdigest()
                        ch_id = selected_church[0] if selected_church else None
                        try:
                            c.execute("INSERT INTO users (user, pwd, name, role, ch_id) VALUES (?,?,?,?,?)", 
                                      (new_id.strip(), h_pwd, full_name, role_type, ch_id))
                            conn.commit()
                            st.success(f"✅ تم إنشاء حساب {full_name} بنجاح!")
                        except:
                            st.error("اسم المستخدم مكرر!")
                        finally:
                            conn.close()
            
            if st.button("🔙 العودة"): 
                st.session_state.page = "home"
                st.rerun()

        # --- ظهور QR Code ---
        if page == 'home':
            st.divider()
            url = "https://small-projects-support-app.streamlit.app"
            img = qrcode.make(url)
            buf = BytesIO()
            img.save(buf)
            st.image(buf, caption="امسح الكود للدخول من الموبايل", width=150)

if __name__ == "__main__":
    main()
