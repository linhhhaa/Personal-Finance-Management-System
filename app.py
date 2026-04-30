"""
app.py - Personal Finance Manager (Streamlit)
"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter
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


def select_user(label="Select user", key=None):
    users = get_users()
    if not users:
        st.warning("No users available. Please create a user first!")
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
st.sidebar.title("Personal finance management system")

menu = st.sidebar.radio(
     "Go to",
    ["Dashboard", "Users", "Bank Accounts",
     "Income", "Expenses", "Reports"]
)

st.sidebar.divider()
st.sidebar.caption("**NEU - Duong Ha linh**")
st.sidebar.caption("DS66A - 11247184")


# ============================================================
# PAGE 1: DASHBOARD
# ============================================================
if menu == "Dashboard":
    st.title("Financial overview")

    user_id = select_user()
    if user_id:
        today = date.today()
        col_m, col_y = st.columns(2)
        month = col_m.selectbox("Month", list(range(1, 13)), index=today.month - 1)
        year = col_y.number_input("Year", value=today.year, step=1)

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
                col1.metric("Total income", f"{fmt_money(income)} VND")
                col2.metric("Total expense", f"{fmt_money(expense)} VND")
                rate = (savings / income * 100) if income > 0 else 0
                
    #st.caption(f" Dữ liệu lấy qua **Stored Procedure** `GetMonthlyReport({user_id}, {month}, {year})`")
        except Exception as e:
            st.error(f"Error: {e}")

        # Số dư tài khoản
        st.subheader("Account balances")
        accounts = get_accounts(user_id)
        if accounts:
            total = sum(float(a['Balance']) for a in accounts)
            df = pd.DataFrame(accounts)
            df['Balance'] = df['Balance'].apply(lambda x: f"{fmt_money(x)} VND")
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.info(f"**Total balance**: {fmt_money(total)} VND")
        else:
            st.warning("This user does not have any bank accounts.")

        # Recent transactions
        st.subheader("10 most recent transactions")
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
            st.info("No transactions found.")


# ============================================================
# PAGE 2: USERS
# ============================================================
elif menu == "Users":
    st.title("User management")
    tab1, tab2 = st.tabs(["List", "Add/Update/Delete"])

    with tab1:
        users = get_users()
        if users:
            st.dataframe(pd.DataFrame(users), use_container_width=True, hide_index=True)
        else:
            st.info("No users found.")

    with tab2:
        action = st.radio("Action", ["Add new", "Update", "Delete"],
                          horizontal=True, key="user_act")

        if action == "Add new":
            with st.form("add_user", clear_on_submit=True):
                name = st.text_input("Name *")
                email = st.text_input("Email *")
                phone = st.text_input("Phone Number")
                if st.form_submit_button("➕ Add"):
                    if name and email:
                        try:
                            db.execute(
                                "INSERT INTO Users(UserName, Email, PhoneNumber) "
                                "VALUES(%s, %s, %s)",
                                (name, email, phone)
                            )
                            st.toast("User added successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                    else:
                        st.warning("Please enter name and email.")

        elif action == "Update":
            users = get_users()
            if users:
                opts = {f"{u['UserID']} - {u['UserName']}": u for u in users}
                sel = st.selectbox("Select user", list(opts.keys()))
                u = opts[sel]
                with st.form("upd_user"):
                    name = st.text_input("Name", value=u['UserName'])
                    email = st.text_input("Email", value=u['Email'])
                    phone = st.text_input("Phone Number", value=u['PhoneNumber'] or '')
                    if st.form_submit_button("Update"):
                        db.execute(
                            "UPDATE Users SET UserName=%s, Email=%s, PhoneNumber=%s "
                            "WHERE UserID=%s",
                            (name, email, phone, u['UserID'])
                        )
                        st.toast("User updated successfully!")
                        st.rerun()

        elif action == "Delete":
            users = get_users()
            if users:
                opts = {f"{u['UserID']} - {u['UserName']}": u['UserID'] for u in users}
                sel = st.selectbox("Select user to delete", list(opts.keys()))
                st.warning("⚠️ Deleting a user will delete all associated accounts and transactions!")
                if st.button("Confirm Delete", type="primary"):
                    try:
                        uid = opts[sel]
                        # Xóa theo thứ tự để tránh FK constraint
                        db.execute("DELETE FROM Expenses WHERE UserID=%s", (uid,))
                        db.execute("DELETE FROM Income WHERE UserID=%s", (uid,))
                        # BankAccounts có ON DELETE CASCADE
                        db.execute("DELETE FROM Users WHERE UserID=%s", (uid,))
                        st.toast("User deleted!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")


# ============================================================
# PAGE 3: BANK ACCOUNTS
# ============================================================
elif menu == "Bank Accounts":
    st.title("Bank account management")
    tab1, tab2 = st.tabs(["List", "Add/Update/Delete"])

    with tab1:
        accs = get_accounts()
        if accs:
            total = sum(float(a['Balance']) for a in accs)
            df = pd.DataFrame(accs)
            df['Balance'] = df['Balance'].apply(lambda x: f"{fmt_money(x)} VND")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No bank accounts found.")

    with tab2:
        action = st.radio("Action", ["Add New", "Update", "Delete"],
                          horizontal=True, key="acc_act")
        users = get_users()
        if not users:
            st.warning("Please create a user first!")
        else:
            user_dict = {u['UserName']: u['UserID'] for u in users}

            if action == "Add New":
                with st.form("add_acc", clear_on_submit=True):
                    user = st.selectbox("Account Holder", list(user_dict.keys()))
                    bank = st.text_input("Bank Name/Wallet *")
                    bal = st.number_input("Initial Balance (VND)", min_value=0.0, step=100000.0)
                    if st.form_submit_button("Add"):
                        if bank:
                            db.execute(
                                "INSERT INTO BankAccounts(UserID, BankName, Balance) "
                                "VALUES(%s, %s, %s)",
                                (user_dict[user], bank, bal)
                            )
                            st.toast("Bank account added successfully!")
                            st.rerun()

            elif action == "Update":
                accs = get_accounts()
                if accs:
                    opts = {f"{a['AccountID']} - {a['UserName']} - {a['BankName']}": a for a in accs}
                    sel = st.selectbox("Select account", list(opts.keys()))
                    a = opts[sel]
                    with st.form("upd_acc"):
                        bank = st.text_input("Bank Name", value=a['BankName'])
                        bal = st.number_input("Balance", value=float(a['Balance']))
                        if st.form_submit_button("Update"):
                            db.execute(
                                "UPDATE BankAccounts SET BankName=%s, Balance=%s "
                                "WHERE AccountID=%s",
                                (bank, bal, a['AccountID'])
                            )
                            st.toast("Bank account updated!")
                            st.rerun()

            elif action == "Delete":
                accs = get_accounts()
                if accs:
                    opts = {f"{a['AccountID']} - {a['UserName']} - {a['BankName']}": a['AccountID'] for a in accs}
                    sel = st.selectbox("Select account to delete", list(opts.keys()))
                    st.warning("⚠️ Deleting an account will delete all related transactions!")
                    if st.button("Confirm Delete", type="primary", key="del_acc"):
                        try:
                            aid = opts[sel]
                            db.execute("DELETE FROM Expenses WHERE AccountID=%s", (aid,))
                            db.execute("DELETE FROM Income WHERE AccountID=%s", (aid,))
                            db.execute("DELETE FROM BankAccounts WHERE AccountID=%s", (aid,))
                            st.toast("Bank account deleted!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")


# ============================================================
# PAGE 4: INCOME
# ============================================================
elif menu == "Income":
    st.title("Income management")
    tab1, tab2 = st.tabs(["List", "Add/Update/Delete"])

    with tab1:
        user_id = select_user("Filter by user", key="inc_filter")
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
                total = sum(float(i['Amount']) for i in data)
                df = pd.DataFrame(data)
                df['Amount'] = df['Amount'].apply(fmt_money)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.info(f"Total income: **{fmt_money(total)} VND**")
            else:
                st.info("No income records found.")

    with tab2:
        action = st.radio("Action", ["Add", "Update", "Delete"],
                          horizontal=True, key="inc_act")
        users = get_users()
        if not users:
            st.warning("Please create a user first!")
        else:
            user_dict = {u['UserName']: u['UserID'] for u in users}

            if action == "Add":
                user = st.selectbox("User", list(user_dict.keys()), key="inc_u")
                accs = get_accounts(user_dict[user])
                if not accs:
                    st.warning("This user has no bank accounts!")
                else:
                    acc_dict = {a['BankName']: a['AccountID'] for a in accs}
                    with st.form("add_inc", clear_on_submit=True):
                        acc = st.selectbox("Account to receive money", list(acc_dict.keys()))
                        amt = st.number_input("Amount (VND) *", min_value=0.0, step=10000.0)
                        d = st.date_input("Date", value=date.today())
                        desc = st.text_input("Description")
                       # st.caption(" **Trigger** `After_Income_Insert` will automatically add money to the balance.")
                        if st.form_submit_button("Add Income"):
                            if amt > 0:
                                db.execute(
                                    "INSERT INTO Income(UserID, AccountID, Amount, IncomeDate, Description) "
                                    "VALUES(%s, %s, %s, %s, %s)",
                                    (user_dict[user], acc_dict[acc], amt, d, desc)
                                )
                                st.toast("Income added! Balance has been updated.")
                                st.rerun()

            elif action == "Update":
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
                    sel = st.selectbox("Select", list(opts.keys()))
                    i = opts[sel]
                    with st.form("upd_inc"):
                        amt = st.number_input("Amount", value=float(i['Amount']), step=10000.0)
                        d = st.date_input("Date", value=i['IncomeDate'])
                        desc = st.text_input("Description", value=i['Description'] or '')
                        if st.form_submit_button("Update"):
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
                            st.toast("Income updated! Balance has been adjusted.")
                            st.rerun()

            elif action == "Delete":
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
                    sel = st.selectbox("Select to delete", list(opts.keys()))
                    if st.button("Confirm Delete", type="primary", key="del_inc"):
                        i = opts[sel]
                        db.execute(
                            "UPDATE BankAccounts SET Balance = Balance - %s WHERE AccountID=%s",
                            (float(i['Amount']), i['AccountID'])
                        )
                        db.execute("DELETE FROM Income WHERE IncomeID=%s", (i['IncomeID'],))
                        st.toast("Income deleted and balance has been restored!")
                        st.rerun()


# ============================================================
# PAGE 5: EXPENSES
# ============================================================
elif menu == "Expenses":
    st.title("Expense management")
    tab1, tab2 = st.tabs(["List", "Add/Edit/Delete"])

    with tab1:
        user_id = select_user("Filter by user", key="exp_filter")
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
                st.info(f"Total Expenses: **{fmt_money(total)} VND**")
            else:
                st.info("No expenses found.")

    with tab2:
        action = st.radio(
            "Action",
            ["Add New", "Update", "Delete"],
            #thêm mới qua stored procedure để demo trigger kiểm tra số dư
            horizontal=True, key="exp_act"
        )
        users = get_users()
        if not users:
            st.warning("No users found!")
        else:
            user_dict = {u['UserName']: u['UserID'] for u in users}

            if action == "Add New":
                user = st.selectbox("Name", list(user_dict.keys()), key="exp_u")
                accs = get_accounts(user_dict[user])
                if not accs:
                    st.warning("No accounts found!")
                else:
                    acc_dict = {
                        f"{a['BankName']} (Balance: {fmt_money(a['Balance'])} VND)": a['AccountID']
                        for a in accs
                    }
                    cats = get_categories()
                    cat_dict = {c['CategoryName']: c['CategoryID'] for c in cats}

                    with st.form("add_exp", clear_on_submit=True):
                        acc = st.selectbox("Account to deduct from", list(acc_dict.keys()))
                        cat = st.selectbox("Category", list(cat_dict.keys()))
                        amt = st.number_input("Amount (VND) *", min_value=0.0, step=10000.0)
                        d = st.date_input("Date", value=date.today())
                        desc = st.text_input("Description")
                      #  st.caption("Gọi **Stored Procedure** `AddExpense` (kiểm tra số dư + insert + trigger).")
                        if st.form_submit_button("Add Expense"):
                            if amt > 0:
                                try:
                                    db.call_proc('AddExpense', (
                                        user_dict[user], acc_dict[acc], cat_dict[cat],
                                        amt, d, desc
                                    ))
                                    st.toast("Expense added! Balance updated.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

            elif action == "Update":
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
                    sel = st.selectbox("Select", list(opts.keys()))
                    e = opts[sel]
                    cats = get_categories()
                    cat_dict = {c['CategoryName']: c['CategoryID'] for c in cats}
                    cat_idx = list(cat_dict.keys()).index(e['CategoryName'])

                    with st.form("upd_exp"):
                        cat = st.selectbox("Category", list(cat_dict.keys()), index=cat_idx)
                        amt = st.number_input("Amount", value=float(e['Amount']), step=10000.0)
                        d = st.date_input("Date", value=e['ExpenseDate'])
                        desc = st.text_input("Description", value=e['Description'] or '')
                        if st.form_submit_button("Update"):
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
                            st.toast("Expense updated and balance adjusted!")
                            st.rerun()

            elif action == "Delete":
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
                    sel = st.selectbox("Select to delete", list(opts.keys()))
                    if st.button("Confirm Delete", type="primary", key="del_exp"):
                        e = opts[sel]
                        db.execute(
                            "UPDATE BankAccounts SET Balance = Balance + %s WHERE AccountID=%s",
                            (float(e['Amount']), e['AccountID'])
                        )
                        db.execute("DELETE FROM Expenses WHERE ExpenseID=%s", (e['ExpenseID'],))
                        st.toast("Expense deleted and balance adjusted!")
                        st.rerun()


# ============================================================
# PAGE 6: REPORTS
# ============================================================
elif menu == "Reports":
    st.title("Financial reports and data summary")

    user_id = select_user("Select user to view reports")
    if user_id:
        report_type = st.selectbox(
            "Report type",
            ["Visualization", "Aggregation", "Data summary"]
        )
        st.markdown("---")

        # ============================================================
        # VISUALIZATION
        # ============================================================
        if report_type == "Visualization":
            chart_type = st.selectbox(
                "Select chart",
                ["Spending by category",
                 "Income vs Expense by month",
                 "Daily spending trend",
                 "Monthly income trend"]
            )
            st.markdown("---")

            # ----- Pie chart: Chi tiêu theo danh mục -----
            if chart_type == "Spending by category":
                st.subheader("Percentage of spending by category")
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
                        st.markdown("### Detailed breakdown")
                        df_d = df.copy()
                        df_d['TotalSpent'] = df_d['TotalSpent'].apply(fmt_money)
                        st.dataframe(df_d, hide_index=True)
                else:
                    st.info("No spending data available.")

            # ----- Bar chart: Thu vs Chi theo tháng -----
            elif chart_type == "Income vs Expense by month":
                st.subheader("Comparison of income and expenses by month")
                today = date.today()
                col1, col2, col3, col4 = st.columns(4)
                month_from = col1.selectbox("From month", list(range(1, 13)),
                                            index=0, key="bar_m_from")
                year_from = col2.number_input("From year", value=today.year,
                                              step=1, key="bar_yr_from")
                month_to = col3.selectbox("To month", list(range(1, 13)),
                                          index=today.month - 1, key="bar_m_to")
                year_to = col4.number_input("To year", value=today.year,
                                            step=1, key="bar_yr_to")
                data = db.fetch_all("""
                    SELECT * FROM MonthlyFinancialSummary
                    WHERE UserID=%s
                      AND (Year * 100 + Month) BETWEEN %s AND %s
                    ORDER BY Year, Month
                """, (user_id,
                      int(year_from) * 100 + int(month_from),
                      int(year_to) * 100 + int(month_to)))
                if data:
                    df = pd.DataFrame(data)
                    df['Period'] = df['Year'].astype(str) + '-' + df['Month'].astype(str).str.zfill(2)
                    df['TotalIncome'] = df['TotalIncome'].astype(float)
                    df['TotalExpense'] = df['TotalExpense'].astype(float)
                    df['NetSavings'] = df['NetSavings'].astype(float)
                    fig, ax = plt.subplots(figsize=(10, 5))
                    x = range(len(df))
                    w = 0.35
                    ax.bar([i - w/2 for i in x], df['TotalIncome'] / 1000, w,
                           label='Income', color='#2ecc71')
                    ax.bar([i + w/2 for i in x], df['TotalExpense'] / 1000, w,
                           label='Expense', color='#e74c3c')
                    ax.set_xlabel('Month')
                    ax.set_ylabel('Thousands VND')
                    ax.set_title('Income vs Expense by Month')
                    ax.set_xticks(list(x))
                    ax.set_xticklabels(df['Period'], rotation=45, ha='right')
                    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:,.0f}'))
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig)
                    df_d = df[['Period', 'TotalIncome', 'TotalExpense', 'NetSavings']].copy()
                    for col in ['TotalIncome', 'TotalExpense', 'NetSavings']:
                        df_d[col] = df_d[col].apply(fmt_money)
                    st.dataframe(df_d, use_container_width=True, hide_index=True)
                else:
                    st.info("No data available.")

            # ----- Line chart: Chi tiêu theo ngày -----
            elif chart_type == "Daily spending trend":
                import calendar
                st.subheader("Daily spending trend")
                today = date.today()
                col_m, col_y = st.columns(2)
                sel_month = col_m.selectbox("Month", list(range(1, 13)),
                                            index=today.month - 1, key="trend_month")
                sel_year = col_y.number_input("Year", value=today.year, step=1, key="trend_year")
                data = db.fetch_all("""
                    SELECT ExpenseDate AS d, SUM(Amount) AS total
                    FROM Expenses
                    WHERE UserID=%s
                      AND MONTH(ExpenseDate)=%s
                      AND YEAR(ExpenseDate)=%s
                    GROUP BY ExpenseDate
                    ORDER BY ExpenseDate
                """, (user_id, int(sel_month), int(sel_year)))
                if data:
                    df = pd.DataFrame(data)
                    df['total'] = df['total'].astype(float)
                    df['d'] = pd.to_datetime(df['d'])
                    m, y = int(sel_month), int(sel_year)
                    x_start = pd.Timestamp(year=y, month=m, day=1)
                    x_end = pd.Timestamp(year=y, month=m, day=calendar.monthrange(y, m)[1])
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.plot(df['d'], df['total'] / 1000, marker='o', linewidth=2, color='#3498db')
                    ax.fill_between(df['d'], df['total'] / 1000, alpha=0.3, color='#3498db')
                    ax.set_xlim(x_start, x_end)
                    ax.set_xlabel('Day')
                    ax.set_ylabel('Thousands VND')
                    ax.set_title(f'Daily Spending Trend — {m:02d}/{y}')
                    ax.grid(True, alpha=0.3)
                    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
                    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:,.0f}'))
                    fig.autofmt_xdate()
                    st.pyplot(fig)
                else:
                    st.info("No data available.")

            # ----- Line chart: Xu hướng thu nhập theo tháng (MỚI) -----
            elif chart_type == "Monthly income trend":
                st.subheader("Monthly income trend")
                today = date.today()
                col1, col2, col3, col4 = st.columns(4)
                month_from = col1.selectbox("From month", list(range(1, 13)),
                                            index=0, key="inc_trend_m_from")
                year_from = col2.number_input("From year", value=today.year,
                                              step=1, key="inc_trend_yr_from")
                month_to = col3.selectbox("To month", list(range(1, 13)),
                                          index=today.month - 1, key="inc_trend_m_to")
                year_to = col4.number_input("To year", value=today.year,
                                            step=1, key="inc_trend_yr_to")
                data = db.fetch_all("""
                    SELECT * FROM MonthlyFinancialSummary
                    WHERE UserID=%s
                      AND (Year * 100 + Month) BETWEEN %s AND %s
                    ORDER BY Year, Month
                """, (user_id,
                      int(year_from) * 100 + int(month_from),
                      int(year_to) * 100 + int(month_to)))
                if data:
                    df = pd.DataFrame(data)
                    df['Period'] = df['Year'].astype(str) + '-' + df['Month'].astype(str).str.zfill(2)
                    df['TotalIncome'] = df['TotalIncome'].astype(float)
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.plot(df['Period'], df['TotalIncome'] / 1000,
                            marker='o', linewidth=2, color='#2ecc71')
                    ax.fill_between(df['Period'], df['TotalIncome'] / 1000,
                                    alpha=0.25, color='#2ecc71')
                    ax.set_xlabel('Month')
                    ax.set_ylabel('Thousands VND')
                    ax.set_title('Monthly Income Trend')
                    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:,.0f}'))
                    ax.grid(True, alpha=0.3)
                    plt.xticks(rotation=45, ha='right')
                    st.pyplot(fig)
                    df_d = df[['Period', 'TotalIncome']].copy()
                    df_d['TotalIncome'] = df_d['TotalIncome'].apply(fmt_money)
                    df_d.columns = ['Period', 'Income (VND)']
                    st.dataframe(df_d, use_container_width=True, hide_index=True)
                else:
                    st.info("No income data available.")

        # ============================================================
        # AGGREGATION (Demo UDF)
        # ============================================================
        elif report_type == "Aggregation":
            st.subheader("Quick lookup of income/expense for any month")

            today = date.today()
            col1, col2 = st.columns(2)
            month = col1.selectbox("Month", list(range(1, 13)),
                                   index=today.month - 1, key="udf_m")
            year = col2.number_input("Year", value=today.year, step=1, key="udf_y")

            if st.button("Calculate"):
                inc = db.call_function('GetTotalMonthlyIncome', (user_id, month, year))
                exp = db.call_function('GetTotalMonthlyExpense', (user_id, month, year))
                savings = float(inc or 0) - float(exp or 0)
                exp_ratio = (float(exp or 0) / float(inc) * 100) if float(inc or 0) > 0 else 0.0
                if exp_ratio <= 70:
                    budget_status = "Excellent"
                elif exp_ratio <= 90:
                    budget_status = "Good"
                elif exp_ratio <= 100:
                    budget_status = "Warning"
                else:
                    budget_status = "Over budget"

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Income", f"{fmt_money(inc)} VND")
                col2.metric("Expense", f"{fmt_money(exp)} VND")
                col3.metric("Budget Status", budget_status,
                            delta=f"Expense {exp_ratio:.1f}% of income")
                col4.metric("Net Savings", f"{fmt_money(savings)} VND")

            #   st.markdown("**Câu SQL đã chạy ngầm:**")
            #st.code(f"SELECT GetTotalMonthlyIncome({user_id}, {month}, {year});\n" f"-- Kết quả: {inc}\n\n" f"SELECT GetTotalMonthlyExpense({user_id}, {month}, {year});\n" f"-- Kết quả: {exp}",
            #language='sql')

        # ----- 5. Xem các VIEW -----
        elif report_type == "Data summary":
            st.subheader("Summary data according to different views")
            # st.caption("VIEW = bảng ảo, tổng hợp dữ liệu từ nhiều bảng. "
            #"Đề bài yêu cầu tạo các view: monthly summary + category-wise spending.")

            view_choice = st.selectbox(
                "Select view option to display",
                ["Transaction history",
                 "Monthly financial summary"]
            )
            st.markdown("---")

            # ---- VIEW 2 ----
            if view_choice == "Transaction history":
                st.markdown("Transaction history")
            # st.caption("Toàn bộ lịch sử giao dịch (income + expense) gộp lại, sắp xếp theo ngày.")

                view_mode = st.radio(
                    "Display options",
                    ["10 latest transactions", "All transactions"],
                    horizontal=True
                )

                base_query = """
                    SELECT 'Income' AS Type, i.IncomeDate AS TransactionDate,
                           b.BankName AS Account, i.Amount, i.Description
                    FROM Income i JOIN BankAccounts b ON i.AccountID = b.AccountID
                    WHERE i.UserID = %s
                    UNION ALL
                    SELECT 'Expense', e.ExpenseDate, b.BankName, -e.Amount, e.Description
                    FROM Expenses e JOIN BankAccounts b ON e.AccountID = b.AccountID
                    WHERE e.UserID = %s
                    ORDER BY TransactionDate DESC
                """
                if view_mode == "10 latest transactions":
                    v2 = db.fetch_all(base_query + " LIMIT 10", (user_id, user_id))
                else:
                    v2 = db.fetch_all(base_query, (user_id, user_id))

                if v2:
                    df = pd.DataFrame(v2)
                    df['Amount'] = df['Amount'].apply(lambda x: f"{float(x):+,.0f}")
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    st.caption(f"Total number of transactions: **{len(v2)}**")
                else:
                    st.info("No transactions found.")

            # ---- VIEW 3 ----
            elif view_choice == "Monthly financial summary":
                st.markdown("Monthly financial summarys")
                #st.caption("Tổng hợp thu - chi - tiết kiệm theo từng tháng của user đã chọn. "
                #VIEW bắt buộc theo đề bài (monthly income/expense summaries).")
 
                v3 = db.fetch_all(
                    "SELECT * FROM MonthlyFinancialSummary WHERE UserID=%s ORDER BY Year, Month",
                    (user_id,)
                )
                if v3:
                    df = pd.DataFrame(v3)
                    for col in ['Total Income', 'Total Expense', 'Net Savings']:
                        df[col] = df[col].apply(fmt_money)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("This user has no financial data to summarize.")
 