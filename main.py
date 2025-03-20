# main.py
from database import create_connection
import datetime

def add_transaction(conn):
    """ 手动添加一条记录 """
    print("\n--- 添加新记录 ---")
    date = input("日期 (YYYY-MM-DD，留空使用今天): ") or datetime.date.today().isoformat()
    trans_type = input("类型 (income/expense): ")
    amount = float(input("金额: "))
    category = input("分类 (可选): ")
    description = input("备注 (可选): ")

    sql = '''INSERT INTO transactions(date, type, amount, category, description)
             VALUES(?,?,?,?,?)'''
    cur = conn.cursor()
    cur.execute(sql, (date, trans_type, amount, category, description))
    conn.commit()
    print("记录添加成功！")

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