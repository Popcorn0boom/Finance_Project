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

    # 新增薪资设置表
    sql_create_salary_table = """
        CREATE TABLE IF NOT EXISTS salary_settings (
            id INTEGER PRIMARY KEY,
            payday INTEGER NOT NULL CHECK(payday BETWEEN 1 AND 31),  -- 发薪日（1-31日）
            amount REAL NOT NULL,
            start_date TEXT NOT NULL,   -- 生效起始日期
            is_active BOOLEAN DEFAULT 1 -- 是否生效
        );
        """

    # 新增每日默认收支表
    sql_create_defaults_table = """
        CREATE TABLE IF NOT EXISTS daily_defaults (
            id INTEGER PRIMARY KEY,
            type TEXT CHECK(type IN ('income', 'expense')),
            amount REAL NOT NULL,
            category TEXT,
            description TEXT,
            is_active BOOLEAN DEFAULT 1
        );
        """

    # 新增预警设置表
    sql_create_alert_table = """
        CREATE TABLE IF NOT EXISTS budget_alert (
            id INTEGER PRIMARY KEY,
            monthly_budget REAL,
            last_alert_month TEXT  -- 上次提醒月份（防止重复提醒）
        );
        """

    # 执行所有建表语句
    tables = [sql_create_salary_table, sql_create_defaults_table, sql_create_alert_table]
    for table in tables:
        try:
            c = conn.cursor()
            c.execute(table)
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