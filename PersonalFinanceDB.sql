-- 1. TẠO DATABASE VÀ BẢNG
CREATE DATABASE IF NOT EXISTS PersonalFinanceDB;
USE PersonalFinanceDB;

-- Bảng Users
CREATE TABLE Users (
    UserID INT PRIMARY KEY AUTO_INCREMENT,
    UserName VARCHAR(100) NOT NULL,
    Email VARCHAR(100) UNIQUE NOT NULL,
    PhoneNumber VARCHAR(15)
);

-- Bảng BankAccounts
CREATE TABLE BankAccounts (
    AccountID INT PRIMARY KEY AUTO_INCREMENT,
    UserID INT,
    BankName VARCHAR(50) NOT NULL,
    Balance DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
);

-- Bảng ExpenseCategories
CREATE TABLE ExpenseCategories (
    CategoryID INT PRIMARY KEY AUTO_INCREMENT,
    CategoryName VARCHAR(100) NOT NULL
);

-- Bảng Income
CREATE TABLE Income (
    IncomeID INT PRIMARY KEY AUTO_INCREMENT,
    UserID INT,
    AccountID INT,
    Amount DECIMAL(15, 2) NOT NULL,
    IncomeDate DATE NOT NULL,
    Description VARCHAR(255),
    FOREIGN KEY (UserID) REFERENCES Users(UserID),
    FOREIGN KEY (AccountID) REFERENCES BankAccounts(AccountID)
);

-- Bảng Expenses
CREATE TABLE Expenses (
    ExpenseID INT PRIMARY KEY AUTO_INCREMENT,
    UserID INT,
    AccountID INT,
    CategoryID INT,
    Amount DECIMAL(15, 2) NOT NULL,
    ExpenseDate DATE NOT NULL,
    Description VARCHAR(255),
    FOREIGN KEY (UserID) REFERENCES Users(UserID),
    FOREIGN KEY (AccountID) REFERENCES BankAccounts(AccountID),
    FOREIGN KEY (CategoryID) REFERENCES ExpenseCategories(CategoryID)
);

-- 2. INDEXES

CREATE INDEX idx_expenses_user     ON Expenses(UserID);
CREATE INDEX idx_expenses_date     ON Expenses(ExpenseDate);
CREATE INDEX idx_expenses_category ON Expenses(CategoryID);
CREATE INDEX idx_income_user       ON Income(UserID);
CREATE INDEX idx_income_date       ON Income(IncomeDate);

-- 3. TRIGGERS 
-- Trigger cộng tiền khi có khoản Thu nhập mới
DELIMITER //
CREATE TRIGGER After_Income_Insert
AFTER INSERT ON Income
FOR EACH ROW
BEGIN
    UPDATE BankAccounts
    SET Balance = Balance + NEW.Amount
    WHERE AccountID = NEW.AccountID;
END //
DELIMITER ;

-- Trigger trừ tiền khi có khoản Chi tiêu mới
DELIMITER //
CREATE TRIGGER After_Expense_Insert
AFTER INSERT ON Expenses
FOR EACH ROW
BEGIN
    UPDATE BankAccounts
    SET Balance = Balance - NEW.Amount
    WHERE AccountID = NEW.AccountID;
END //
DELIMITER ;


-- 4. SAMPLE DATA
-- Users
INSERT INTO Users (UserName, Email, PhoneNumber) VALUES
('Duong Ha Linh',  'halinh@example.com',      '0912345678'),
('Nguyen Van A',   'vana@example.com',         '0987654321'),
('Tran Thi B',     'thib.tran@example.com',    '0901112223'),
('Le Hoang C',     'hoangc@example.com',       '0933444555'),
('Pham Dang D',    'dangd.pham@example.com',   '0944555666');

-- BankAccounts
INSERT INTO BankAccounts (UserID, BankName, Balance) VALUES
(1, 'Vietcombank',  5000000.00),
(1, 'Momo Wallet',  1500000.00),
(1, 'Cash',          500000.00),
(2, 'ShopeePay',     200000.00),
(2, 'Techcombank', 10000000.00),
(3, 'TPBank',       8500000.00),
(4, 'Agribank',    12000000.00),
(5, 'ZaloPay',      3000000.00);

-- ExpenseCategories
INSERT INTO ExpenseCategories (CategoryName) VALUES
('Food and dining'),
('Transportation'),
('Education'),
('Entertainment'),
('Shopping'),
('Health and fitness'),
('Utilities'),
('Housing');

-- Income (trigger sẽ tự động cộng vào Balance)
INSERT INTO Income (UserID, AccountID, Amount, IncomeDate, Description) VALUES
(1, 1, 3000000.00, '2026-04-01', 'Allowance from parents'),
(1, 2,  500000.00, '2026-04-10', 'Part-time job'),
(1, 1, 2000000.00, '2026-04-15', 'University scholarship'),
(2, 5,15000000.00, '2026-04-05', 'Monthly salary'),
(3, 6,12000000.00, '2026-04-05', 'Monthly salary'),
(1, 4,  150000.00, '2026-04-18', 'Shopee affiliate cashback'),
(4, 7, 8000000.00, '2026-04-20', 'Part-time job'),
(5, 8, 5000000.00, '2026-04-22', 'Freelance project');

-- Expenses (trigger sẽ tự động trừ khỏi Balance)
INSERT INTO Expenses (UserID, AccountID, CategoryID, Amount, ExpenseDate, Description) VALUES
(1, 2, 1,   55000.00, '2026-04-12', 'Lunch at NEU cafeteria'),
(1, 1, 3,  250000.00, '2026-04-15', 'Buy books'),
(1, 3, 2,   20000.00, '2026-04-16', 'Bus ticket'),
(1, 1, 4,  120000.00, '2026-04-18', 'Movie ticket'),
(1, 2, 1,   65000.00, '2026-04-20', 'Highlands coffee'),
(2, 5, 5, 1500000.00, '2026-04-10', 'New running shoes'),
(3, 6, 7,  500000.00, '2026-04-25', 'Electricity and water bill'),
(4, 7, 6,  400000.00, '2026-04-02', 'Gym membership'),
(5, 8, 8, 4500000.00, '2026-04-05', 'Apartment rent'),
(1, 1, 6,  150000.00, '2026-04-26', 'Medicine');

-- 5. VIEWS
-- View 1: Chi tiêu theo từng danh mục
CREATE OR REPLACE VIEW CategoryWiseSpending AS
SELECT
    ec.CategoryName,
    SUM(e.Amount)       AS TotalSpent,
    COUNT(e.ExpenseID)  AS NumberOfTransactions
FROM Expenses e
JOIN ExpenseCategories ec ON e.CategoryID = ec.CategoryID
GROUP BY ec.CategoryName;

-- View 2: Lịch sử giao dịch chi tiết kèm tên tài khoản
CREATE OR REPLACE VIEW TransactionHistory AS
SELECT
    'Income'            AS TransactionType,
    i.IncomeDate        AS TransactionDate,
    b.BankName          AS Account,
    i.Amount,
    i.Description
FROM Income i
JOIN BankAccounts b ON i.AccountID = b.AccountID
UNION ALL
SELECT
    'Expense'           AS TransactionType,
    e.ExpenseDate       AS TransactionDate,
    b.BankName          AS Account,
    -e.Amount           AS Amount,   -- Số âm cho chi tiêu
    e.Description
FROM Expenses e
JOIN BankAccounts b ON e.AccountID = b.AccountID
ORDER BY TransactionDate DESC;

-- View 3: Tổng hợp thu/chi/tiết kiệm theo tháng 
CREATE OR REPLACE VIEW MonthlyFinancialSummary AS
SELECT
    u.UserID,
    u.UserName,
    YEAR(trans.TransDate)   AS Year,
    MONTH(trans.TransDate)  AS Month,
    SUM(CASE WHEN trans.Type = 'Income'  THEN trans.Amount ELSE 0 END) AS TotalIncome,
    SUM(CASE WHEN trans.Type = 'Expense' THEN trans.Amount ELSE 0 END) AS TotalExpense,
    SUM(CASE WHEN trans.Type = 'Income'  THEN trans.Amount ELSE 0 END) -
    SUM(CASE WHEN trans.Type = 'Expense' THEN trans.Amount ELSE 0 END) AS NetSavings
FROM Users u
JOIN (
    SELECT UserID, Amount, IncomeDate  AS TransDate, 'Income'  AS Type FROM Income
    UNION ALL
    SELECT UserID, Amount, ExpenseDate AS TransDate, 'Expense' AS Type FROM Expenses
) AS trans ON u.UserID = trans.UserID
GROUP BY u.UserID, u.UserName, Year, Month
ORDER BY u.UserID, Year, Month;

-- 6. USER DEFINED FUNCTIONS (UDF)
-- UDF 1: Tổng chi tiêu của 1 user trong tháng cụ thể
DELIMITER //
CREATE FUNCTION GetTotalMonthlyExpense(p_UserID INT, p_Month INT, p_Year INT)
RETURNS DECIMAL(15,2)
READS SQL DATA
BEGIN
    DECLARE total DECIMAL(15,2);
    SELECT COALESCE(SUM(Amount), 0) INTO total
    FROM Expenses
    WHERE UserID = p_UserID
      AND MONTH(ExpenseDate) = p_Month
      AND YEAR(ExpenseDate)  = p_Year;
    RETURN total;
END //
DELIMITER ;

-- UDF 2: Tổng thu nhập của 1 user trong tháng cụ thể
DELIMITER //
CREATE FUNCTION GetTotalMonthlyIncome(p_UserID INT, p_Month INT, p_Year INT)
RETURNS DECIMAL(15,2)
READS SQL DATA
BEGIN
    DECLARE total DECIMAL(15,2);
    SELECT COALESCE(SUM(Amount), 0) INTO total
    FROM Income
    WHERE UserID = p_UserID
      AND MONTH(IncomeDate) = p_Month
      AND YEAR(IncomeDate)  = p_Year;
    RETURN total;
END //
DELIMITER ;

-- 7. STORED PROCEDURES
-- SP 1: Thêm khoản chi tiêu mới (có kiểm tra số dư)
DELIMITER //
CREATE PROCEDURE AddExpense(
    IN p_UserID      INT,
    IN p_AccountID   INT,
    IN p_CategoryID  INT,
    IN p_Amount      DECIMAL(15,2),
    IN p_Date        DATE,
    IN p_Description VARCHAR(255)
)
BEGIN
    DECLARE current_balance DECIMAL(15,2);

    SELECT Balance INTO current_balance
    FROM BankAccounts
    WHERE AccountID = p_AccountID;

    IF current_balance < p_Amount THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Insufficient balance in account';
    ELSE
        INSERT INTO Expenses(UserID, AccountID, CategoryID, Amount, ExpenseDate, Description)
        VALUES (p_UserID, p_AccountID, p_CategoryID, p_Amount, p_Date, p_Description);
    END IF;
END //
DELIMITER ;

-- SP 2: Báo cáo tài chính tháng cho 1 user
DELIMITER //
CREATE PROCEDURE GetMonthlyReport(IN p_UserID INT, IN p_Month INT, IN p_Year INT)
BEGIN
    SELECT
        GetTotalMonthlyIncome (p_UserID, p_Month, p_Year) AS TotalIncome,
        GetTotalMonthlyExpense(p_UserID, p_Month, p_Year) AS TotalExpense,
        GetTotalMonthlyIncome (p_UserID, p_Month, p_Year) -
        GetTotalMonthlyExpense(p_UserID, p_Month, p_Year) AS NetSavings;
END //
DELIMITER ;


