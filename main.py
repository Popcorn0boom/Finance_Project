# main.py
from database import create_connection
import datetime

def add_transaction(conn):
    """ 手动添加一条记录（包含完整数据校验） """
    print("\n--- 添加新记录 ---")

    # 1. 获取日期输入并验证
    date_input = input("日期 (YYYY-MM-DD，留空使用今天): ").strip()

    # 处理空输入（默认今天）
    date = date_input if date_input else datetime.date.today().isoformat()

    try:
        # 强制验证日期格式（即使使用默认值也重新格式化）
        validated_date = datetime.datetime.strptime(date, "%Y-%m-%d").date().isoformat()
    except ValueError:
        print("错误：日期格式必须为 YYYY-MM-DD（例如 2023-08-20）")
        return  # 验证失败直接退出函数

    # 2. 获取交易类型并验证
    trans_type = input("类型 (income/expense): ").strip().lower()  # 统一转为小写
    if trans_type not in ('income', 'expense'):
        print("错误：类型必须为 income 或 expense")
        return

    # 3. 获取金额并验证
    amount_input = input("金额: ").strip()
    try:
        amount = float(amount_input)
        if amount <= 0:
            print("错误：金额必须大于0")
            return
    except ValueError:
        print("错误：请输入有效的数字（例如 15.5）")
        return

    # 4. 可选字段（无需严格校验）
    category = input("分类 (可选): ").strip() or "未分类"  # 空输入默认值
    description = input("备注 (可选): ").strip()

    # 5. 所有校验通过后写入数据库
    sql = '''INSERT INTO transactions(date, type, amount, category, description)
             VALUES(?,?,?,?,?)'''
    try:
        cur = conn.cursor()
        cur.execute(sql, (validated_date, trans_type, amount, category, description))
        conn.commit()
        print(f"记录添加成功！ID: {cur.lastrowid}")
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        conn.rollback()  # 回滚事务保证数据一致性

def show_summary(conn):
    """ 显示本月汇总 """
    cur = conn.cursor()
    # 本月总收入
    cur.execute("SELECT SUM(amount) FROM transactions WHERE type='income' AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')")
    total_income = cur.fetchone()[0] or 0.0
    # 本月总支出
    cur.execute("SELECT SUM(amount) FROM transactions WHERE type='expense' AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')")
    total_expense = cur.fetchone()[0] or 0.0

    print(f"\n--- 本月汇总 ({datetime.date.today().strftime('%Y-%m')}) ---")
    print(f"总收入: {total_income:.2f} 元")
    print(f"总支出: {total_expense:.2f} 元")
    print(f"当前结余: {total_income - total_expense:.2f} 元")

def main():
    conn = create_connection()
    if not conn:
        return

    while True:
        print("\n===== 简易记账系统 =====")
        print("1. 添加记录")
        print("2. 查看本月汇总")
        print("3. 退出")
        choice = input("请选择操作: ")

        if choice == '1':
            add_transaction(conn)
        elif choice == '2':
            show_summary(conn)
        elif choice == '3':
            break
        else:
            print("无效输入！")

    conn.close()
    print("已退出系统")

if __name__ == "__main__":
    main()