# database.py
import sqlite3
from sqlite3 import Error

def create_connection():
    """ 创建数据库连接 """
    conn = None
    try:
        conn = sqlite3.connect('data/finance.db')  # 数据库文件保存在data目录
        print("数据库连接成功！SQLite版本:", sqlite3.version)
    except Error as e:
        print(f"连接数据库失败: {e}")
    return conn

def create_tables(conn):
    """ 创建核心数据表 """
    sql_create_transactions_table = """
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,         -- 日期 (格式: YYYY-MM-DD)
        type TEXT NOT NULL,         -- 类型 (income/expense)
        amount REAL NOT NULL,       -- 金额
        category TEXT,             -- 分类 (如餐饮、交通)
        description TEXT           -- 备注
    );
    """
    try:
        c = conn.cursor()
        c.execute(sql_create_transactions_table)
        conn.commit()
        print("数据表创建成功！")
    except Error as e:
        print(f"创建表失败: {e}")

# 测试数据库初始化
if __name__ == "__main__":
    conn = create_connection()
    if conn:
        create_tables(conn)
        conn.close()