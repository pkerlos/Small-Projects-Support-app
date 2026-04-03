import streamlit as st
import sqlite3
import hashlib
from datetime import date
import qrcode
from io import BytesIO

# ====================== إعدادات الصفحة ======================
st.set_page_config(page_title="نظام القروض الحسنة", page_icon="💰", layout="centered")

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
    border-radius: 12px;
    height: 3.5em;
    background-color: #007bff;
    color: white;
}
</style>
""", unsafe_allow_html=True)

DB_PATH = 'charity_projects.db'

# ====================== قاعدة البيانات ======================
def get_db_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS eparchies (
        id INTEGER PRIMARY KEY, name TEXT UNIQUE)''')

    c.execute('''CREATE TABLE IF NOT EXISTS churches (
        id INTEGER PRIMARY KEY, name TEXT, ep_id INTEGER)''')

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY, user TEXT UNIQUE, pwd TEXT,
        name TEXT, role TEXT, ch_id INTEGER)''')

    # إنشاء الأدمن
    c.execute("SELECT * FROM users WHERE user='admin'")
    if not c.fetchone():
        h = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO users (user, pwd, name, role) VALUES (?,?,?,?)",
                  ("admin", h, "المدير العام", "admin"))

    conn.commit()
    conn.close()

# ====================== دوال مساعدة ======================
def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def get_church_name(ch_id):
    if not ch_id:
        return "غير محدد"
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT name FROM churches WHERE id=?", (ch_id,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else "غير معروف"

# ====================== التطبيق ======================
def main():
    init_db()

    # ---------- تسجيل الدخول ----------
    if 'user' not in st.session_state:
        st.title("🔐 تسجيل الدخول")
        u = st.text_input("اسم المستخدم")
        p = st.text_input("كلمة السر", type="password")

        if st.button("دخول"):
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE user=?", (u.strip(),))
            res = c.fetchone()
            conn.close()

            if res and hash_password(p) == res[2]:
                st.session_state.user = {
                    'id': res[0],
                    'username': res[1],
                    'name': res[3],
                    'role': res[4],
                    'ch_id': res[5]
                }
                st.rerun()
            else:
                st.error("❌ بيانات غير صحيحة")

    # ---------- بعد تسجيل الدخول ----------
    else:
        user = st.session_state.user

        st.sidebar.title(f"👋 {user['name']}")
        st.sidebar.write(f"الصلاحية: {user['role']}")

        if st.sidebar.button("🚪 تسجيل خروج"):
            del st.session_state.user
            st.rerun()

        # ---------- لوحة المدير ----------
        if user['role'] == 'admin':
            st.title("🛠️ لوحة التحكم")

            col1, col2 = st.columns(2)
            if col1.button("👥 المستخدمين"):
                st.session_state.page = "users"
            if col2.button("🏛️ الكنائس"):
                st.session_state.page = "setup"

        else:
            st.title("⛪ واجهة الكنيسة")
            st.success(f"كنيسة: {get_church_name(user['ch_id'])}")

        page = st.session_state.get("page", "home")

        # ================= المستخدمين =================
        if page == "users":
            st.header("إضافة مستخدم")

            with st.form("add_user"):
                u = st.text_input("اسم المستخدم")
                p = st.text_input("كلمة السر", type="password")
                name = st.text_input("الاسم")
                role = st.selectbox("الصلاحية", ["admin", "church_staff"])

                conn = get_db_connection()
                c = conn.cursor()
                c.execute("SELECT id, name FROM churches")
                churches = c.fetchall()
                conn.close()

                ch = st.selectbox("الكنيسة", churches,
                                  format_func=lambda x: x[1]) if role == "church_staff" else None

                if st.form_submit_button("حفظ"):
                    if len(p) < 4:
                        st.warning("كلمة السر ضعيفة")
                    else:
                        try:
                            conn = get_db_connection()
                            c = conn.cursor()
                            c.execute("INSERT INTO users VALUES (NULL,?,?,?,?,?)",
                                      (u, hash_password(p), name, role, ch[0] if ch else None))
                            conn.commit()
                            st.success("تم الحفظ")
                        except:
                            st.error("اسم المستخدم مكرر")
                        finally:
                            conn.close()

            if st.button("رجوع"):
                st.session_state.page = "home"
                st.rerun()

        # ================= الكنائس =================
        if page == "setup":
            st.header("إدارة الكنائس")

            with st.form("add_church"):
                name = st.text_input("اسم الكنيسة")
                if st.form_submit_button("إضافة"):
                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute("INSERT INTO churches VALUES (NULL,?,NULL)", (name,))
                    conn.commit()
                    conn.close()
                    st.success("تمت الإضافة")

            # عرض الكنائس
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM churches")
            data = c.fetchall()
            conn.close()

            for d in data:
                st.write(f"🏛️ {d[1]}")

            if st.button("رجوع"):
                st.session_state.page = "home"
                st.rerun()

        # ================= الصفحة الرئيسية =================
        if page == "home":
            st.divider()

            # QR ديناميكي
            base_url = "https://small-projects-support-app.streamlit.app"
            user_url = f"{base_url}?ch={user['ch_id']}"

            img = qrcode.make(user_url)
            buf = BytesIO()
            img.save(buf)

            st.image(buf, caption="QR خاص بك", width=150)
            st.code(user_url)

# تشغيل
if __name__ == "__main__":
    main()
