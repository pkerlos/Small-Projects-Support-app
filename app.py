import streamlit as st
import sqlite3
import hashlib
from datetime import date

# ====================== إعدادات الصفحة ======================
st.set_page_config(page_title="مكتب المشروعات الصغيرة", page_icon="💰", layout="wide")

st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo&display=swap');
        html, body, [class*="css"] { font-family: 'Cairo', sans-serif; direction: rtl; text-align: right; }
        .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
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
    c.execute('''CREATE TABLE IF NOT EXISTS borrowers (id INTEGER PRIMARY KEY, name TEXT, phone TEXT, ch_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS loans (id INTEGER PRIMARY KEY, b_id INTEGER, amount REAL, inst_count INTEGER, inst_val REAL, status TEXT DEFAULT 'نشط')''')
    c.execute('''CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, loan_id INTEGER, p_date TEXT, amount REAL, rec_by TEXT)''')
    
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
        st.sidebar.title(f"👋 {user['name']}")
        if st.sidebar.button("🚪 خروج"):
            del st.session_state.user
            st.rerun()
        
        # القائمة الرئيسية كأزرار في الصفحة
        st.title("🛠️ لوحة التحكم")
        
        if user['role'] == 'admin':
            cols = st.columns(3)
            if cols[0].button("👥 إدارة المستخدمين"): st.session_state.page = "users"
            if cols[1].button("⛪ إدارة الكنائس"): st.session_state.page = "churches"
            if cols[2].button("🏛️ إدارة الأبرشيات"): st.session_state.page = "eparchies"
            
            cols2 = st.columns(3)
            if cols2[0].button("👤 إضافة مقترضين"): st.session_state.page = "borrowers"
            if cols2[1].button("💰 إنشاء قروض"): st.session_state.page = "loans"
            if cols2[2].button("📝 تسجيل سداد"): st.session_state.page = "payments"
        else:
            if st.button("📝 تسجيل سداد"): st.session_state.page = "payments"

        st.divider()
        page = st.session_state.get('page', 'home')

        conn = get_db_connection()
        c = conn.cursor()

        if page == "users":
            st.header("👥 إدارة المستخدمين")
            with st.form("u_f"):
                u_user = st.text_input("اسم المستخدم")
                u_pwd = st.text_input("الباسورد", type="password")
                u_name = st.text_input("الاسم بالكامل")
                u_role = st.selectbox("الدور", ["admin", "church_staff"])
                # لو موظف كنيسة نخليه يختار كنيسته
                c.execute("SELECT id, name FROM churches")
                chs = c.fetchall()
                u_ch = st.selectbox("الكنيسة (للموظفين فقط)", [f"{x[0]}-{x[1]}" for x in chs]) if u_role == "church_staff" else None
                if st.form_submit_button("إضافة"):
                    h = hashlib.sha256(u_pwd.encode()).hexdigest()
                    ch_id = int(u_ch.split('-')[0]) if u_ch else None
                    c.execute("INSERT INTO users (user, pwd, name, role, ch_id) VALUES (?,?,?,?,?)", (u_user, h, u_name, u_role, ch_id))
                    conn.commit()
                    st.success("تم الإضافة!")

        elif page == "eparchies":
            st.header("🏛️ الأبرشيات")
            ep_name = st.text_input("اسم الأبرشية")
            if st.button("إضافة"):
                c.execute("INSERT INTO eparchies (name) VALUES (?)", (ep_name,))
                conn.commit()
                st.success("تم!")
            c.execute("SELECT name FROM eparchies")
            for r in c.fetchall(): st.write(f"- {r[0]}")

        elif page == "churches":
            st.header("⛪ الكنائس")
            c.execute("SELECT id, name FROM eparchies")
            eps = c.fetchall()
            sel_ep = st.selectbox("اختر الأبرشية", [f"{x[0]}-{x[1]}" for x in eps])
            ch_name = st.text_input("اسم الكنيسة")
            if st.button("إضافة كنيسة"):
                c.execute("INSERT INTO churches (name, ep_id) VALUES (?,?)", (ch_name, int(sel_ep.split('-')[0])))
                conn.commit()
                st.success("تم!")

        elif page == "borrowers":
            st.header("👤 المقترضين")
            c.execute("SELECT id, name FROM churches")
            chs = c.fetchall()
            sel_ch = st.selectbox("الكنيسة", [f"{x[0]}-{x[1]}" for x in chs])
            b_name = st.text_input("اسم الشخص")
            if st.button("إضافة"):
                c.execute("INSERT INTO borrowers (name, ch_id) VALUES (?,?)", (b_name, int(sel_ch.split('-')[0])))
                conn.commit()
                st.success("تم!")

        elif page == "loans":
            st.header("💰 إنشاء قرض")
            c.execute("SELECT id, name FROM borrowers")
            bs = c.fetchall()
            sel_b = st.selectbox("المقترض", [f"{x[0]}-{x[1]}" for x in bs])
            amt = st.number_input("المبلغ", min_value=100)
            inst = st.number_input("عدد الأقساط", min_value=1)
            if st.button("تفعيل القرض"):
                c.execute("INSERT INTO loans (b_id, amount, inst_count, inst_val) VALUES (?,?,?,?)", 
                          (int(sel_b.split('-')[0]), amt, inst, amt/inst))
                conn.commit()
                st.success(f"تم! قيمة القسط: {amt/inst}")

        elif page == "payments":
            st.header("📝 تسجيل سداد")
            # لو موظف كنيسة يظهر له ناس كنيسته بس
            if user['role'] == 'church_staff':
                c.execute("SELECT id, name FROM borrowers WHERE ch_id=?", (user['ch_id'],))
            else:
                c.execute("SELECT id, name FROM borrowers")
            bs = c.fetchall()
            sel_b = st.selectbox("المقترض", [f"{x[0]}-{x[1]}" for x in bs])
            b_id = int(sel_b.split('-')[0])
            c.execute("SELECT id, amount, inst_val FROM loans WHERE b_id=? AND status='نشط'", (b_id,))
            loan = c.fetchone()
            if loan:
                st.info(f"قرض بمبلغ {loan[1]} - القسط: {loan[2]}")
                p_amt = st.number_input("المبلغ المدفوع", value=loan[2])
                if st.button("تأكيد السداد"):
                    c.execute("INSERT INTO payments (loan_id, p_date, amount, rec_by) VALUES (?,?,?,?)",
                              (loan[0], date.today().isoformat(), p_amt, user['name']))
                    conn.commit()
                    st.success("تم تسجيل السداد!")
            else: st.warning("لا يوجد قرض نشط")

        conn.close()

if __name__ == "__main__":
    main()