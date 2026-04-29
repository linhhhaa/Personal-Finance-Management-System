import mysql.connector
from mysql.connector import Error

# CẤU HÌNH KẾT NỐI 
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Mysql@1234',   
    'database': 'PersonalFinanceDB',
    'charset': 'utf8mb4'
}

#tạo kết nối với database
def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def fetch_all(query, params=None):
    """Chạy SELECT, trả về list các dict"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def fetch_one(query, params=None):
    """Chạy SELECT, trả về 1 dict (hoặc None)"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        return cursor.fetchone()
    finally:
        cursor.close()
        conn.close()


def execute(query, params=None):
    """Chạy INSERT/UPDATE/DELETE, trả về (rowcount, lastrowid)"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        conn.commit()
        return cursor.rowcount, cursor.lastrowid
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def call_proc(name, args):
    """Gọi Stored Procedure"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.callproc(name, args)
        results = []
        for result in cursor.stored_results():
            results.extend(result.fetchall())
        conn.commit()
        return results
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def call_function(func_name, args):
    """Gọi User Defined Function (UDF), trả về 1 giá trị"""
    placeholders = ','.join(['%s'] * len(args))
    query = f"SELECT {func_name}({placeholders}) AS result"
    row = fetch_one(query, args)
    return row['result'] if row else None