# Personal-Finace-Management-System

A system that enables users to effectively manage personal income and expenses, track financial activities, analyze spending habits, and optimize savings through data-driven reports and alerts.

**Stack**: MySQL + Python + Streamlit + matplotlib

---

## 🚀 Hướng dẫn cài đặt

### 1. Cài thư viện Python
```bash
pip install -r requirements.txt
```

### 2. Chuẩn bị database
- Mở MySQL Workbench
- Chạy file `PersonalFinanceDB` để tạo database `PersonalFinanceDB` cùng toàn bộ bảng, trigger, view, UDF, stored procedure.

### 3. Cấu hình kết nối
Mở file `db.py`, sửa `password` cho khớp với MySQL của bạn:
```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'YOUR_PASSWORD',   # ← Sửa ở đây
    'database': 'PersonalFinanceDB',
    'charset': 'utf8mb4'
}
```

### 4. Chạy ứng dụng
```bash
streamlit run app.py
```
App sẽ tự động mở trên trình duyệt tại `http://localhost:8501`.

---

## 📋 Các chức năng

| Trang | Mô tả |
|---|---|
| 🏠 **Dashboard** | Tổng quan tài chính tháng, số dư tài khoản, giao dịch gần đây |
| 👤 **Users** | CRUD người dùng |
| 🏦 **Bank Accounts** | CRUD tài khoản ngân hàng |
| 💰 **Income** | Thêm / sửa / xóa thu nhập |
| 💸 **Expenses** | Thêm / sửa / xóa chi tiêu (qua Stored Procedure) |
| 📊 **Reports** | Pie / Bar / Line chart, Demo UDF, View |

---

## 🔧 Các SQL object được sử dụng

| Loại | Tên | Sử dụng tại |
|---|---|---|
| **Trigger** | `After_Income_Insert` | Tự động khi thêm thu nhập |
| **Trigger** | `After_Expense_Insert` | Tự động khi thêm chi tiêu |
| **View** | `CategoryWiseSpending` | Reports → Xem VIEW |
| **View** | `TransactionHistory` | Reports → Xem VIEW |
| **View** | `MonthlyFinancialSummary` | Reports → Bar chart |
| **UDF** | `GetTotalMonthlyIncome` | Reports → Demo UDF |
| **UDF** | `GetTotalMonthlyExpense` | Reports → Demo UDF |
| **Stored Procedure** | `AddExpense` | Expenses → Thêm mới |
| **Stored Procedure** | `GetMonthlyReport` | Dashboard → Tổng quan tháng |

---

## 📁 Cấu trúc file

```
finance_app/
├── app.py              # Streamlit main app (6 trang)
├── db.py               # Helper kết nối MySQL
├── requirements.txt    # Thư viện Python
└── README.md           # File này
```

---

## ⚠️ Lưu ý

- Khi **sửa/xóa** Income hoặc Expense, app tự động điều chỉnh số dư trong code Python (vì trigger chỉ chạy khi INSERT).
- Stored Procedure `AddExpense` sẽ **báo lỗi** nếu số dư không đủ — đây là tính năng kiểm tra thông minh.
