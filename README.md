# Personal-Finance-Management-System

A system that enables users to effectively manage personal income and expenses, track financial activities, analyze spending habits, and optimize savings through data-driven reports and alerts.

**Stack**: MySQL + Python + Streamlit + matplotlib + pandas

---

## Hướng dẫn cài đặt

### 1. Cài thư viện Python
```bash
pip install -r requirements.txt
```

### 2. Chuẩn bị database
- Mở MySQL Workbench
- Chạy file `PersonalFinanceDB.sql` để tạo database `PersonalFinanceDB` cùng toàn bộ bảng, sample data, indexes, triggers, views, UDFs và stored procedures.

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

## Các chức năng

| Trang | Mô tả |
|---|---|
| **Dashboard** | Tổng quan tài chính tháng (income / expense / net savings), số dư tài khoản, 10 giao dịch gần nhất |
| **Users** | CRUD người dùng |
| **Bank Accounts** | CRUD tài khoản ngân hàng / ví điện tử |
| **Income** | Thêm / sửa / xóa thu nhập (auto cập nhật số dư qua trigger) |
| **Expenses** | Thêm / sửa / xóa chi tiêu (qua Stored Procedure có kiểm tra số dư) |
| **Reports** | Visualization (4 biểu đồ) / Aggregation / Data summary |

---

## Các SQL object đã triển khai

| Loại | Tên | Sử dụng tại |
|---|---|---|
| **Index** | `idx_expenses_user`, `idx_expenses_date`, `idx_expenses_category`, `idx_income_user`, `idx_income_date` | Tăng tốc filter theo user/date/category |
| **Trigger** | `After_Income_Insert` | Tự động cộng số dư khi thêm thu nhập |
| **Trigger** | `After_Expense_Insert` | Tự động trừ số dư khi thêm chi tiêu |
| **View** | `CategoryWiseSpending` | Tổng hợp chi tiêu theo danh mục |
| **View** | `TransactionHistory` | Reports → Data summary → Transaction history |
| **View** | `MonthlyFinancialSummary` | Reports → Bar chart, Monthly income trend, Monthly financial summary |
| **UDF** | `GetTotalMonthlyIncome` | Reports → Aggregation; Dashboard (gián tiếp) |
| **UDF** | `GetTotalMonthlyExpense` | Reports → Aggregation; Dashboard (gián tiếp) |
| **Stored Procedure** | `AddExpense` | Expenses → Add (kiểm tra số dư + insert) |
| **Stored Procedure** | `GetMonthlyReport` | Dashboard → Tổng quan tháng |

---

## Cấu trúc file

```
Personal-Finace-Management-System/
├── app.py                  # Streamlit main app (6 trang)
├── db.py                   # Helper kết nối MySQL
├── PersonalFinanceDB.sql   # Schema + sample data + tất cả SQL objects
├── requirements.txt        # Thư viện Python cần cài
└── README.md               # File này
```

---

## Lưu ý

- Khi **sửa/xóa** Income hoặc Expense, app tự động điều chỉnh số dư trong code Python (vì trigger chỉ chạy khi INSERT).
- Stored Procedure `AddExpense` sẽ **báo lỗi** nếu số dư không đủ — đây là cơ chế kiểm tra spending limit ngay tại tầng database.
- Toàn bộ truy vấn trong Reports đều filter theo `UserID` để đảm bảo dữ liệu tách biệt giữa các user.
