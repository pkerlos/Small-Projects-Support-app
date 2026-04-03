# نسخة محسّنة نهائيًا: حل مشكلة إضافة المستخدم + QR لكل كنيسة
import streamlit as st
import sqlite3
import hashlib
from datetime import date
import qrcode
from io import BytesIO

DB_PATH = 'charity_projects.db'

# ================= DB =================
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with get_conn() as conn:
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS churches (
            id INTEGER PRIMARY KEY,
            name TEXT
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            user TEXT UNIQUE,
            pwd TEXT,
            name TEXT,
            role TEXT,
            ch_id INTEGER
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS borrowers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            phone TEXT,
            address TEXT,
            ch_id INTEGER
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY,
            borrower_id INTEGER,
            amount REAL,
            months INTEGER,
            start_date TEXT
        )''')

        c.execute('''CREATE TABLE IF NOT EXISTS installments (
            id INTEGER PRIMARY KEY,
            loan_id INTEGER,
            due_date TEXT,
            amount REAL,
            paid INTEGER DEFAULT 0
        )''')

        # admin
        c.execute("SELECT * FROM users WHERE user='admin'")
        if not c.fetchone():
            h = hashlib.sha256("admin123".encode()).hexdigest()
            c.execute("INSERT INTO users VALUES (NULL,?,?,?,?,?)",
                      ("admin", h, "المدير", "admin", None))

        conn.commit()

# ================= utils =================
def hash_pwd(p):
    return hashlib.sha256(p.encode()).hexdigest()

# ================= app =================
def main():
    init_db()

    # login
    if 'user' not in st.session_state:
        st.title("تسجيل الدخول")
        u = st.text_input("المستخدم")
        p = st.text_input("كلمة السر", type="password")

        if st.button("دخول"):
            with get_conn() as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE user=?", (u,))
                r = c.fetchone()

            if r and hash_pwd(p) == r[2]:
                st.session_state.user = r
                st.rerun()
            else:
                st.error("خطأ")

    else:
        user = st.session_state.user

        st.sidebar.write(user[3])

        page = st.sidebar.selectbox("القائمة", [
            "المستخدمين",
            "إضافة مستخدم",
            "الكنائس + QR",
            "المقترضين",
            "القروض",
            "الأقساط"
        ])

        # ================= ADD USER (تم إصلاح المشكلة) =================
        if page == "إضافة مستخدم":
            st.header("إضافة مستخدم جديد")

            with get_conn() as conn:
                c = conn.cursor()
                c.execute("SELECT id,name FROM churches")
                churches = c.fetchall()

            with st.form("add_user"):
                username = st.text_input("اسم المستخدم")
                password = st.text_input("كلمة السر", type="password")
                name = st.text_input("الاسم")
                role = st.selectbox("الدور", ["admin","church_staff"])

                ch_id = None
                if role == "church_staff":
                    if churches:
                        ch = st.selectbox("الكنيسة", churches, format_func=lambda x: x[1])
                        ch_id = ch[0]
                    else:
                        st.warning("لا توجد كنائس، أضف كنيسة أولاً")

                if st.form_submit_button("حفظ"):
                    if not username or not password or not name:
                        st.warning("كل الحقول مطلوبة")
                    else:
                        try:
                            with get_conn() as conn:
                                c = conn.cursor()
                                c.execute("INSERT INTO users VALUES (NULL,?,?,?,?,?)",
                                          (username, hash_pwd(password), name, role, ch_id))
                                conn.commit()
                            st.success("تم إضافة المستخدم ✅")
                        except sqlite3.IntegrityError:
                            st.error("اسم المستخدم موجود بالفعل")

        # ================= USERS VIEW =================
        if page == "المستخدمين":
            st.header("إدارة المستخدمين")

            with get_conn() as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM users")
                users = c.fetchall()

            for u in users:
                with st.expander(f"{u[3]} ({u[1]})"):
                    new_name = st.text_input("الاسم", u[3], key=f"n{u[0]}")
                    new_role = st.selectbox("الدور", ["admin","church_staff"], index=0 if u[4]=='admin' else 1, key=f"r{u[0]}")

                    if st.button("تعديل", key=f"edit{u[0]}"):
                        with get_conn() as conn:
                            c = conn.cursor()
                            c.execute("UPDATE users SET name=?, role=? WHERE id=?",
                                      (new_name, new_role, u[0]))
                            conn.commit()
                        st.success("تم التعديل")
                        st.rerun()

        # ================= CHURCHES + QR =================
        if page == "الكنائس + QR":
            st.header("إدارة الكنائس و QR")

            with st.form("add_ch"):
                cname = st.text_input("اسم الكنيسة")
                if st.form_submit_button("إضافة"):
                    with get_conn() as conn:
                        c = conn.cursor()
                        c.execute("INSERT INTO churches VALUES (NULL,?)", (cname,))
                        conn.commit()
                    st.success("تمت الإضافة")

            with get_conn() as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM churches")
                data = c.fetchall()

            base_url = "https://small-projects-support-app.streamlit.app"

            for ch in data:
                st.subheader(f"🏛️ {ch[1]}")

                url = f"{base_url}?ch={ch[0]}"

                qr = qrcode.make(url)
                buf = BytesIO()
                qr.save(buf)

                st.image(buf, width=150)
                st.code(url)

        # ================= BORROWERS =================
        if page == "المقترضين":
            st.header("المقترضين")

            with st.form("add_borrower"):
                name = st.text_input("الاسم")
                phone = st.text_input("الموبايل")
                address = st.text_input("العنوان")

                if st.form_submit_button("إضافة"):
                    with get_conn() as conn:
                        c = conn.cursor()
                        c.execute("INSERT INTO borrowers VALUES (NULL,?,?,?,?)",
                                  (name, phone, address, None))
                        conn.commit()
                    st.success("تمت الإضافة")

            with get_conn() as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM borrowers")
                data = c.fetchall()

            for b in data:
                st.write(f"{b[1]} - {b[2]}")

        # ================= LOANS =================
        if page == "القروض":
            st.header("إضافة قرض")

            with get_conn() as conn:
                c = conn.cursor()
                c.execute("SELECT id,name FROM borrowers")
                borrowers = c.fetchall()

            with st.form("loan"):
                b = st.selectbox("المقترض", borrowers, format_func=lambda x: x[1])
                amount = st.number_input("المبلغ")
                months = st.number_input("عدد الشهور", step=1)

                if st.form_submit_button("حفظ"):
                    with get_conn() as conn:
                        c = conn.cursor()
                        c.execute("INSERT INTO loans VALUES (NULL,?,?,?,?)",
                                  (b[0], amount, months, str(date.today())))
                        loan_id = c.lastrowid

                        monthly = amount / months
                        for i in range(months):
                            c.execute("INSERT INTO installments VALUES (NULL,?,?,?,0)",
                                      (loan_id, str(date.today()), monthly))

                        conn.commit()
                    st.success("تم إنشاء القرض")

        # ================= INSTALLMENTS =================
        if page == "الأقساط":
            st.header("الأقساط")

            with get_conn() as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM installments")
                data = c.fetchall()

            for ins in data:
                st.write(f"قسط {ins[0]} - {ins[3]} جنيه")
                if not ins[4]:
                    if st.button("تحصيل", key=ins[0]):
                        with get_conn() as conn:
                            c = conn.cursor()
                            c.execute("UPDATE installments SET paid=1 WHERE id=?", (ins[0],))
                            conn.commit()
                        st.success("تم السداد")
                        st.rerun()


if __name__ == '__main__':
    main()
