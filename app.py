"""
app.py - Personal Finance Manager (Streamlit)
NEU - DATCOM Lab - Project 13
"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
import db

# ============================================================
# CẤU HÌNH TRANG
# ============================================================
st.set_page_config(
    page_title="Personal Finance Manager",
    page_icon="💰",
    layout="wide"
)

plt.rcParams['font.family'] = 'DejaVu Sans'

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def get_users():
    return db.fetch_all(
        "SELECT UserID, UserName, Email, PhoneNumber FROM Users ORDER BY UserName"
    )


def get_accounts(user_id=None):
    if user_id:
        return db.fetch_all(
            "SELECT AccountID, BankName, Balance FROM BankAccounts "
            "WHERE UserID=%s ORDER BY BankName",
            (user_id,)
        )
    return db.fetch_all("""
        SELECT a.AccountID, u.UserName, a.BankName, a.Balance
        FROM BankAccounts a JOIN Users u ON a.UserID=u.UserID
        ORDER BY u.UserName, a.BankName
    """)


def get_categories():
    return db.fetch_all(
        "SELECT CategoryID, CategoryName FROM ExpenseCategories ORDER BY CategoryName"
    )


def select_user(label="Chọn người dùng", key=None):
    users = get_users()
    if not users:
        st.warning("Chưa có user nào. Hãy tạo user trước!")
        return None
    user_dict = {u['UserName']: u['UserID'] for u in users}
    selected = st.selectbox(label, list(user_dict.keys()), key=key)
    return user_dict[selected]


def fmt_money(val):
    """Format số tiền: 1500000 -> 1,500,000"""
    return f"{float(val or 0):,.0f}"


# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.title("💰 Personal Finance")
st.sidebar.caption("Hệ thống quản lý tài chính cá nhân")

menu = st.sidebar.radio(
    "📋 Menu",
    ["🏠 Dashboard", "👤 Users", "🏦 Bank Accounts",
     "💰 Income", "💸 Expenses", "📊 Reports"]
)

st.sidebar.divider()
st.sidebar.caption("**NEU - DATCOM Lab**")
st.sidebar.caption("Project 13: Personal Finance")


# ============================================================
# PAGE 1: DASHBOARD
# ============================================================
if menu == "🏠 Dashboard":
    st.title("🏠 Tổng quan tài chính")

    user_id = select_user()
    if user_id:
        today = date.today()
        col_m, col_y = st.columns(2)
        month = col_m.selectbox("Tháng", list(range(1, 13)), index=today.month - 1)
        year = col_y.number_input("Năm", value=today.year, step=1)

        st.markdown("---")

        # Gọi STORED PROCEDURE GetMonthlyReport
        try:
            report = db.call_proc('GetMonthlyReport', (user_id, month, year))
            if report:
                r = report[0]
                income = float(r['TotalIncome'] or 0)
                expense = float(r['TotalExpense'] or 0)
                savings = float(r['NetSavings'] or 0)

                col1, col2, col3 = st.columns(3)
                col1.metric("💰 Tổng thu", f"{fmt_money(income)} VND")
                col2.metric("💸 Tổng chi", f"{fmt_money(expense)} VND")
                rate = (savings / income * 100) if income > 0 else 0
                col3.metric(
                    "💎 Tiết kiệm ròng",
                    f"{fmt_money(savings)} VND",
                    delta=f"{rate:.1f}% so với thu nhập"
                )
                st.caption(f"💡 Dữ liệu lấy qua **Stored Procedure** `GetMonthlyReport({user_id}, {month}, {year})`")
        except Exception as e:
            st.error(f"Lỗi: {e}")

        # Số dư tài khoản
        st.subheader("🏦 Số dư các tài khoản")
        accounts = get_accounts(user_id)
        if accounts:
            total = sum(float(a['Balance']) for a in accounts)
            df = pd.DataFrame(accounts)
            df['Balance'] = df['Balance'].apply(lambda x: f"{fmt_money(x)} VND")
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.info(f"💎 **Tổng số dư**: {fmt_money(total)} VND")
        else:
            st.warning("User này chưa có tài khoản ngân hàng nào.")

        # Giao dịch gần đây
        st.subheader("📜 10 giao dịch gần nhất")
        history = db.fetch_all("""
            SELECT 'Income' AS Type, i.IncomeDate AS Date,
                   b.BankName AS Account, i.Amount, i.Description
            FROM Income i JOIN BankAccounts b ON i.AccountID = b.AccountID
            WHERE i.UserID = %s
            UNION ALL
            SELECT 'Expense', e.ExpenseDate, b.BankName, -e.Amount, e.Description
            FROM Expenses e JOIN BankAccounts b ON e.AccountID = b.AccountID
            WHERE e.UserID = %s
            ORDER BY Date DESC
            LIMIT 10
        """, (user_id, user_id))
        if history:
            df = pd.DataFrame(history)
            df['Amount'] = df['Amount'].apply(lambda x: f"{float(x):+,.0f}")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có giao dịch nào.")


# ============================================================
# PAGE 2: USERS
# ============================================================
elif menu == "👤 Users":
    st.title("👤 Quản lý người dùng")
    tab1, tab2 = st.tabs(["📋 Danh sách", "➕ Thêm/Sửa/Xóa"])

    with tab1:
        users = get_users()
        if users:
            st.dataframe(pd.DataFrame(users), use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có người dùng nào.")

    with tab2:
        action = st.radio("Hành động", ["Thêm mới", "Cập nhật", "Xóa"],
                          horizontal=True, key="user_act")

        if action == "Thêm mới":
            with st.form("add_user", clear_on_submit=True):
                name = st.text_input("Tên người dùng *")
                email = st.text_input("Email *")
                phone = st.text_input("Số điện thoại")
                if st.form_submit_button("➕ Thêm"):
                    if name and email:
                        try:
                            db.execute(
                                "INSERT INTO Users(UserName, Email, PhoneNumber) "
                                "VALUES(%s, %s, %s)",
                                (name, email, phone)
                            )
                            st.success("✅ Đã thêm user!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi: {e}")
                    else:
                        st.warning("Vui lòng nhập tên và email.")

        elif action == "Cập nhật":
            users = get_users()
            if users:
                opts = {f"{u['UserID']} - {u['UserName']}": u for u in users}
                sel = st.selectbox("Chọn user", list(opts.keys()))
                u = opts[sel]
                with st.form("upd_user"):
                    name = st.text_input("Tên", value=u['UserName'])
                    email = st.text_input("Email", value=u['Email'])
                    phone = st.text_input("SĐT", value=u['PhoneNumber'] or '')
                    if st.form_submit_button("💾 Cập nhật"):
                        db.execute(
                            "UPDATE Users SET UserName=%s, Email=%s, PhoneNumber=%s "
                            "WHERE UserID=%s",
                            (name, email, phone, u['UserID'])
                        )
                        st.success("✅ Đã cập nhật!")
                        st.rerun()

        elif action == "Xóa":
            users = get_users()
            if users:
                opts = {f"{u['UserID']} - {u['UserName']}": u['UserID'] for u in users}
                sel = st.selectbox("Chọn user cần xóa", list(opts.keys()))
                st.warning("⚠️ Xóa user sẽ xóa toàn bộ tài khoản, thu/chi liên quan!")
                if st.button("🗑️ Xác nhận xóa", type="primary"):
                    try:
                        uid = opts[sel]
                        # Xóa theo thứ tự để tránh FK constraint
                        db.execute("DELETE FROM Expenses WHERE UserID=%s", (uid,))
                        db.execute("DELETE FROM Income WHERE UserID=%s", (uid,))
                        # BankAccounts có ON DELETE CASCADE
                        db.execute("DELETE FROM Users WHERE UserID=%s", (uid,))
                        st.success("✅ Đã xóa!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Lỗi: {e}")


# ============================================================
# PAGE 3: BANK ACCOUNTS
# ============================================================
elif menu == "🏦 Bank Accounts":
    st.title("🏦 Quản lý tài khoản ngân hàng")
    tab1, tab2 = st.tabs(["📋 Danh sách", "➕ Thêm/Sửa/Xóa"])

    with tab1:
        accs = get_accounts()
        if accs:
            total = sum(float(a['Balance']) for a in accs)
            df = pd.DataFrame(accs)
            df['Balance'] = df['Balance'].apply(lambda x: f"{fmt_money(x)} VND")
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.info(f"💰 Tổng số dư hệ thống: **{fmt_money(total)} VND**")
        else:
            st.info("Chưa có tài khoản nào.")

    with tab2:
        action = st.radio("Hành động", ["Thêm mới", "Cập nhật", "Xóa"],
                          horizontal=True, key="acc_act")
        users = get_users()
        if not users:
            st.warning("Cần tạo user trước!")
        else:
            user_dict = {u['UserName']: u['UserID'] for u in users}

            if action == "Thêm mới":
                with st.form("add_acc", clear_on_submit=True):
                    user = st.selectbox("Chủ tài khoản", list(user_dict.keys()))
                    bank = st.text_input("Tên ngân hàng/ví *")
                    bal = st.number_input("Số dư khởi tạo (VND)", min_value=0.0, step=100000.0)
                    if st.form_submit_button("➕ Thêm"):
                        if bank:
                            db.execute(
                                "INSERT INTO BankAccounts(UserID, BankName, Balance) "
                                "VALUES(%s, %s, %s)",
                                (user_dict[user], bank, bal)
                            )
                            st.success("✅ Đã thêm!")
                            st.rerun()

            elif action == "Cập nhật":
                accs = get_accounts()
                if accs:
                    opts = {f"{a['AccountID']} - {a['UserName']} - {a['BankName']}": a for a in accs}
                    sel = st.selectbox("Chọn tài khoản", list(opts.keys()))
                    a = opts[sel]
                    with st.form("upd_acc"):
                        bank = st.text_input("Tên ngân hàng", value=a['BankName'])
                        bal = st.number_input("Số dư", value=float(a['Balance']))
                        if st.form_submit_button("💾 Cập nhật"):
                            db.execute(
                                "UPDATE BankAccounts SET BankName=%s, Balance=%s "
                                "WHERE AccountID=%s",
                                (bank, bal, a['AccountID'])
                            )
                            st.success("✅ Đã cập nhật!")
                            st.rerun()

            elif action == "Xóa":
                accs = get_accounts()
                if accs:
                    opts = {f"{a['AccountID']} - {a['UserName']} - {a['BankName']}": a['AccountID'] for a in accs}
                    sel = st.selectbox("Chọn tài khoản cần xóa", list(opts.keys()))
                    st.warning("⚠️ Xóa tài khoản sẽ xóa các giao dịch liên quan!")
                    if st.button("🗑️ Xác nhận xóa", type="primary", key="del_acc"):
                        try:
                            aid = opts[sel]
                            db.execute("DELETE FROM Expenses WHERE AccountID=%s", (aid,))
                            db.execute("DELETE FROM Income WHERE AccountID=%s", (aid,))
                            db.execute("DELETE FROM BankAccounts WHERE AccountID=%s", (aid,))
                            st.success("✅ Đã xóa!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi: {e}")


# ============================================================
# PAGE 4: INCOME
# ============================================================
elif menu == "💰 Income":
    st.title("💰 Quản lý thu nhập")
    tab1, tab2 = st.tabs(["📋 Danh sách", "➕ Thêm/Sửa/Xóa"])

    with tab1:
        user_id = select_user("Lọc theo người dùng", key="inc_filter")
        if user_id:
            data = db.fetch_all("""
                SELECT i.IncomeID, u.UserName, b.BankName, i.Amount,
                       i.IncomeDate, i.Description
                FROM Income i
                JOIN Users u ON i.UserID=u.UserID
                JOIN BankAccounts b ON i.AccountID=b.AccountID
                WHERE i.UserID=%s
                ORDER BY i.IncomeDate DESC
            """, (user_id,))
            if data:
                df = pd.DataFrame(data)
                df['Amount'] = df['Amount'].apply(fmt_money)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("Chưa có khoản thu nhập nào.")

    with tab2:
        action = st.radio("Hành động", ["Thêm mới", "Cập nhật", "Xóa"],
                          horizontal=True, key="inc_act")
        users = get_users()
        if not users:
            st.warning("Cần tạo user trước!")
        else:
            user_dict = {u['UserName']: u['UserID'] for u in users}

            if action == "Thêm mới":
                user = st.selectbox("Người nhận", list(user_dict.keys()), key="inc_u")
                accs = get_accounts(user_dict[user])
                if not accs:
                    st.warning("User này chưa có tài khoản nào!")
                else:
                    acc_dict = {a['BankName']: a['AccountID'] for a in accs}
                    with st.form("add_inc", clear_on_submit=True):
                        acc = st.selectbox("Tài khoản nhận tiền", list(acc_dict.keys()))
                        amt = st.number_input("Số tiền (VND) *", min_value=0.0, step=10000.0)
                        d = st.date_input("Ngày", value=date.today())
                        desc = st.text_input("Mô tả")
                        st.caption("💡 **Trigger** `After_Income_Insert` sẽ tự động cộng tiền vào số dư.")
                        if st.form_submit_button("➕ Thêm thu nhập"):
                            if amt > 0:
                                db.execute(
                                    "INSERT INTO Income(UserID, AccountID, Amount, IncomeDate, Description) "
                                    "VALUES(%s, %s, %s, %s, %s)",
                                    (user_dict[user], acc_dict[acc], amt, d, desc)
                                )
                                st.success("✅ Đã thêm! Số dư đã được cập nhật qua trigger.")
                                st.rerun()

            elif action == "Cập nhật":
                data = db.fetch_all("""
                    SELECT i.*, u.UserName, b.BankName
                    FROM Income i JOIN Users u ON i.UserID=u.UserID
                    JOIN BankAccounts b ON i.AccountID=b.AccountID
                    ORDER BY i.IncomeDate DESC
                """)
                if data:
                    opts = {
                        f"{i['IncomeID']} - {i['UserName']} - {fmt_money(i['Amount'])} VND - {i['IncomeDate']}": i
                        for i in data
                    }
                    sel = st.selectbox("Chọn", list(opts.keys()))
                    i = opts[sel]
                    with st.form("upd_inc"):
                        amt = st.number_input("Số tiền", value=float(i['Amount']), step=10000.0)
                        d = st.date_input("Ngày", value=i['IncomeDate'])
                        desc = st.text_input("Mô tả", value=i['Description'] or '')
                        if st.form_submit_button("💾 Cập nhật"):
                            diff = amt - float(i['Amount'])
                            db.execute(
                                "UPDATE Income SET Amount=%s, IncomeDate=%s, Description=%s "
                                "WHERE IncomeID=%s",
                                (amt, d, desc, i['IncomeID'])
                            )
                            db.execute(
                                "UPDATE BankAccounts SET Balance = Balance + %s WHERE AccountID=%s",
                                (diff, i['AccountID'])
                            )
                            st.success("✅ Đã cập nhật và điều chỉnh số dư!")
                            st.rerun()

            elif action == "Xóa":
                data = db.fetch_all("""
                    SELECT i.*, u.UserName, b.BankName
                    FROM Income i JOIN Users u ON i.UserID=u.UserID
                    JOIN BankAccounts b ON i.AccountID=b.AccountID
                    ORDER BY i.IncomeDate DESC
                """)
                if data:
                    opts = {
                        f"{i['IncomeID']} - {i['UserName']} - {fmt_money(i['Amount'])} VND - {i['IncomeDate']}": i
                        for i in data
                    }
                    sel = st.selectbox("Chọn cần xóa", list(opts.keys()))
                    if st.button("🗑️ Xác nhận xóa", type="primary", key="del_inc"):
                        i = opts[sel]
                        db.execute(
                            "UPDATE BankAccounts SET Balance = Balance - %s WHERE AccountID=%s",
                            (float(i['Amount']), i['AccountID'])
                        )
                        db.execute("DELETE FROM Income WHERE IncomeID=%s", (i['IncomeID'],))
                        st.success("✅ Đã xóa và hoàn lại số dư!")
                        st.rerun()


# ============================================================
# PAGE 5: EXPENSES
# ============================================================
elif menu == "💸 Expenses":
    st.title("💸 Quản lý chi tiêu")
    tab1, tab2 = st.tabs(["📋 Danh sách", "➕ Thêm/Sửa/Xóa"])

    with tab1:
        user_id = select_user("Lọc theo người dùng", key="exp_filter")
        if user_id:
            data = db.fetch_all("""
                SELECT e.ExpenseID, u.UserName, b.BankName, c.CategoryName,
                       e.Amount, e.ExpenseDate, e.Description
                FROM Expenses e
                JOIN Users u ON e.UserID=u.UserID
                JOIN BankAccounts b ON e.AccountID=b.AccountID
                JOIN ExpenseCategories c ON e.CategoryID=c.CategoryID
                WHERE e.UserID=%s
                ORDER BY e.ExpenseDate DESC
            """, (user_id,))
            if data:
                total = sum(float(e['Amount']) for e in data)
                df = pd.DataFrame(data)
                df['Amount'] = df['Amount'].apply(fmt_money)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.info(f"💸 Tổng chi tiêu: **{fmt_money(total)} VND**")
            else:
                st.info("Chưa có chi tiêu nào.")

    with tab2:
        action = st.radio(
            "Hành động",
            ["Thêm mới (qua Stored Procedure)", "Cập nhật", "Xóa"],
            horizontal=True, key="exp_act"
        )
        users = get_users()
        if not users:
            st.warning("Cần tạo user trước!")
        else:
            user_dict = {u['UserName']: u['UserID'] for u in users}

            if action == "Thêm mới (qua Stored Procedure)":
                user = st.selectbox("Người chi", list(user_dict.keys()), key="exp_u")
                accs = get_accounts(user_dict[user])
                if not accs:
                    st.warning("User này chưa có tài khoản nào!")
                else:
                    acc_dict = {
                        f"{a['BankName']} (Số dư: {fmt_money(a['Balance'])} VND)": a['AccountID']
                        for a in accs
                    }
                    cats = get_categories()
                    cat_dict = {c['CategoryName']: c['CategoryID'] for c in cats}

                    with st.form("add_exp", clear_on_submit=True):
                        acc = st.selectbox("Tài khoản trừ tiền", list(acc_dict.keys()))
                        cat = st.selectbox("Danh mục", list(cat_dict.keys()))
                        amt = st.number_input("Số tiền (VND) *", min_value=0.0, step=10000.0)
                        d = st.date_input("Ngày", value=date.today())
                        desc = st.text_input("Mô tả")
                        st.caption("💡 Gọi **Stored Procedure** `AddExpense` (kiểm tra số dư + insert + trigger).")
                        if st.form_submit_button("➕ Thêm chi tiêu"):
                            if amt > 0:
                                try:
                                    db.call_proc('AddExpense', (
                                        user_dict[user], acc_dict[acc], cat_dict[cat],
                                        amt, d, desc
                                    ))
                                    st.success("✅ Đã thêm! Số dư cập nhật qua trigger.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ {e}")

            elif action == "Cập nhật":
                data = db.fetch_all("""
                    SELECT e.*, u.UserName, b.BankName, c.CategoryName
                    FROM Expenses e
                    JOIN Users u ON e.UserID=u.UserID
                    JOIN BankAccounts b ON e.AccountID=b.AccountID
                    JOIN ExpenseCategories c ON e.CategoryID=c.CategoryID
                    ORDER BY e.ExpenseDate DESC
                """)
                if data:
                    opts = {
                        f"{e['ExpenseID']} - {e['UserName']} - {e['CategoryName']} - {fmt_money(e['Amount'])}": e
                        for e in data
                    }
                    sel = st.selectbox("Chọn", list(opts.keys()))
                    e = opts[sel]
                    cats = get_categories()
                    cat_dict = {c['CategoryName']: c['CategoryID'] for c in cats}
                    cat_idx = list(cat_dict.keys()).index(e['CategoryName'])

                    with st.form("upd_exp"):
                        cat = st.selectbox("Danh mục", list(cat_dict.keys()), index=cat_idx)
                        amt = st.number_input("Số tiền", value=float(e['Amount']), step=10000.0)
                        d = st.date_input("Ngày", value=e['ExpenseDate'])
                        desc = st.text_input("Mô tả", value=e['Description'] or '')
                        if st.form_submit_button("💾 Cập nhật"):
                            diff = amt - float(e['Amount'])
                            db.execute(
                                "UPDATE Expenses SET CategoryID=%s, Amount=%s, "
                                "ExpenseDate=%s, Description=%s WHERE ExpenseID=%s",
                                (cat_dict[cat], amt, d, desc, e['ExpenseID'])
                            )
                            db.execute(
                                "UPDATE BankAccounts SET Balance = Balance - %s WHERE AccountID=%s",
                                (diff, e['AccountID'])
                            )
                            st.success("✅ Đã cập nhật và điều chỉnh số dư!")
                            st.rerun()

            elif action == "Xóa":
                data = db.fetch_all("""
                    SELECT e.*, u.UserName, b.BankName, c.CategoryName
                    FROM Expenses e
                    JOIN Users u ON e.UserID=u.UserID
                    JOIN BankAccounts b ON e.AccountID=b.AccountID
                    JOIN ExpenseCategories c ON e.CategoryID=c.CategoryID
                    ORDER BY e.ExpenseDate DESC
                """)
                if data:
                    opts = {
                        f"{e['ExpenseID']} - {e['UserName']} - {e['CategoryName']} - {fmt_money(e['Amount'])}": e
                        for e in data
                    }
                    sel = st.selectbox("Chọn cần xóa", list(opts.keys()))
                    if st.button("🗑️ Xác nhận xóa", type="primary", key="del_exp"):
                        e = opts[sel]
                        db.execute(
                            "UPDATE BankAccounts SET Balance = Balance + %s WHERE AccountID=%s",
                            (float(e['Amount']), e['AccountID'])
                        )
                        db.execute("DELETE FROM Expenses WHERE ExpenseID=%s", (e['ExpenseID'],))
                        st.success("✅ Đã xóa và hoàn lại số dư!")
                        st.rerun()


# ============================================================
# PAGE 6: REPORTS
# ============================================================
elif menu == "📊 Reports":
    st.title("📊 Báo cáo & Phân tích")

    user_id = select_user("Chọn người dùng để xem báo cáo")
    if user_id:
        report_type = st.selectbox(
            "Loại báo cáo",
            ["🥧 Chi tiêu theo danh mục",
             "📊 Thu vs Chi theo tháng (VIEW)",
             "📈 Xu hướng chi tiêu theo ngày",
             "🧮 Demo UDF (GetTotalMonthly...)",
             "🗃️ Xem dữ liệu các VIEW"]
        )
        st.markdown("---")

        # ----- 1. Pie chart: Chi tiêu theo danh mục -----
        if report_type == "🥧 Chi tiêu theo danh mục":
            st.subheader("Tỷ lệ chi tiêu theo danh mục")
            data = db.fetch_all("""
                SELECT c.CategoryName, SUM(e.Amount) AS TotalSpent,
                       COUNT(*) AS NumTrans
                FROM Expenses e
                JOIN ExpenseCategories c ON e.CategoryID=c.CategoryID
                WHERE e.UserID=%s
                GROUP BY c.CategoryName
                ORDER BY TotalSpent DESC
            """, (user_id,))
            if data:
                df = pd.DataFrame(data)
                df['TotalSpent'] = df['TotalSpent'].astype(float)

                col1, col2 = st.columns([2, 1])
                with col1:
                    fig, ax = plt.subplots(figsize=(8, 6))
                    colors = plt.cm.Set3(range(len(df)))
                    ax.pie(df['TotalSpent'], labels=df['CategoryName'],
                           autopct='%1.1f%%', startangle=90, colors=colors)
                    ax.set_title('Spending by Category', fontsize=14)
                    st.pyplot(fig)
                with col2:
                    st.markdown("### Chi tiết")
                    df_d = df.copy()
                    df_d['TotalSpent'] = df_d['TotalSpent'].apply(fmt_money)
                    st.dataframe(df_d, hide_index=True)
            else:
                st.info("Chưa có dữ liệu chi tiêu.")

        # ----- 2. Bar chart: Thu vs Chi theo tháng -----
        elif report_type == "📊 Thu vs Chi theo tháng (VIEW)":
            st.subheader("So sánh thu nhập vs chi tiêu theo tháng")
            st.caption("📌 Dữ liệu lấy từ **VIEW** `MonthlyFinancialSummary`")
            data = db.fetch_all("""
                SELECT * FROM MonthlyFinancialSummary
                WHERE UserID=%s
                ORDER BY Year, Month
            """, (user_id,))
            if data:
                df = pd.DataFrame(data)
                df['Period'] = df['Year'].astype(str) + '-' + df['Month'].astype(str).str.zfill(2)
                df['TotalIncome'] = df['TotalIncome'].astype(float)
                df['TotalExpense'] = df['TotalExpense'].astype(float)
                df['NetSavings'] = df['NetSavings'].astype(float)

                fig, ax = plt.subplots(figsize=(10, 5))
                x = range(len(df))
                w = 0.35
                ax.bar([i - w/2 for i in x], df['TotalIncome'], w,
                       label='Income', color='#2ecc71')
                ax.bar([i + w/2 for i in x], df['TotalExpense'], w,
                       label='Expense', color='#e74c3c')
                ax.set_xlabel('Month')
                ax.set_ylabel('VND')
                ax.set_title('Income vs Expense by Month')
                ax.set_xticks(list(x))
                ax.set_xticklabels(df['Period'])
                ax.legend()
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)

                df_d = df[['Period', 'TotalIncome', 'TotalExpense', 'NetSavings']].copy()
                for col in ['TotalIncome', 'TotalExpense', 'NetSavings']:
                    df_d[col] = df_d[col].apply(fmt_money)
                st.dataframe(df_d, use_container_width=True, hide_index=True)
            else:
                st.info("Chưa có dữ liệu.")

        # ----- 3. Line chart: Xu hướng chi tiêu -----
        elif report_type == "📈 Xu hướng chi tiêu theo ngày":
            st.subheader("Chi tiêu hàng ngày")
            data = db.fetch_all("""
                SELECT ExpenseDate AS d, SUM(Amount) AS total
                FROM Expenses
                WHERE UserID=%s
                GROUP BY ExpenseDate
                ORDER BY ExpenseDate
            """, (user_id,))
            if data:
                df = pd.DataFrame(data)
                df['total'] = df['total'].astype(float)

                fig, ax = plt.subplots(figsize=(10, 5))
                ax.plot(df['d'], df['total'], marker='o', linewidth=2, color='#3498db')
                ax.fill_between(df['d'], df['total'], alpha=0.3, color='#3498db')
                ax.set_xlabel('Date')
                ax.set_ylabel('VND')
                ax.set_title('Daily Spending Trend')
                ax.grid(True, alpha=0.3)
                fig.autofmt_xdate()
                st.pyplot(fig)
            else:
                st.info("Chưa có dữ liệu.")

        # ----- 4. Demo UDF -----
        elif report_type == "🧮 Demo UDF (GetTotalMonthly...)":
            st.subheader("Tính toán bằng User Defined Functions")
            today = date.today()
            col1, col2 = st.columns(2)
            month = col1.selectbox("Tháng", list(range(1, 13)),
                                   index=today.month - 1, key="udf_m")
            year = col2.number_input("Năm", value=today.year, step=1, key="udf_y")

            if st.button("🔍 Tính"):
                inc = db.call_function('GetTotalMonthlyIncome', (user_id, month, year))
                exp = db.call_function('GetTotalMonthlyExpense', (user_id, month, year))

                col1, col2, col3 = st.columns(3)
                col1.metric("💰 Thu nhập (UDF)", fmt_money(inc))
                col2.metric("💸 Chi tiêu (UDF)", fmt_money(exp))
                col3.metric("💎 Tiết kiệm", fmt_money(float(inc or 0) - float(exp or 0)))

                st.code(
                    f"-- SQL queries chạy ngầm:\n"
                    f"SELECT GetTotalMonthlyIncome({user_id}, {month}, {year});  -- {inc}\n"
                    f"SELECT GetTotalMonthlyExpense({user_id}, {month}, {year}); -- {exp}",
                    language='sql'
                )

        # ----- 5. Xem các VIEW -----
        elif report_type == "🗃️ Xem dữ liệu các VIEW":
            st.subheader("Dữ liệu trong các VIEW")

            st.markdown("#### 📌 VIEW `CategoryWiseSpending`")
            v1 = db.fetch_all("SELECT * FROM CategoryWiseSpending")
            if v1:
                df = pd.DataFrame(v1)
                df['TotalSpent'] = df['TotalSpent'].apply(fmt_money)
                st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown("#### 📌 VIEW `TransactionHistory` (10 giao dịch gần nhất)")
            v2 = db.fetch_all("SELECT * FROM TransactionHistory LIMIT 10")
            if v2:
                df = pd.DataFrame(v2)
                df['Amount'] = df['Amount'].apply(lambda x: f"{float(x):+,.0f}")
                st.dataframe(df, use_container_width=True, hide_index=True)

            st.markdown("#### 📌 VIEW `MonthlyFinancialSummary`")
            v3 = db.fetch_all("SELECT * FROM MonthlyFinancialSummary")
            if v3:
                df = pd.DataFrame(v3)
                for col in ['TotalIncome', 'TotalExpense', 'NetSavings']:
                    df[col] = df[col].apply(fmt_money)
                st.dataframe(df, use_container_width=True, hide_index=True)