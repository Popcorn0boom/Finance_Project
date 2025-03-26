# main.py
import sqlite3
from database import create_connection
import datetime


def add_transaction(conn=None, auto=False, auto_data=None):
    """
    完整版添加记录函数（支持线程安全）
    参数:
        conn: 可选，数据库连接对象（未提供时自动创建）
        auto: 是否为自动模式
        auto_data: 自动模式数据字典
    返回: bool (是否成功)
    """
    local_conn = None
    try:
        # 处理数据库连接
        if not conn:
            local_conn = create_connection()
            conn = local_conn

        # === 数据验证 ===
        if not auto:
            # 手动模式验证
            date_input = input("日期 (YYYY-MM-DD，留空使用今天): ").strip()
            date = date_input if date_input else datetime.date.today().isoformat()

            try:
                datetime.datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                print("错误：日期格式必须为 YYYY-MM-DD")
                return False

            trans_type = input("类型 (income/expense): ").strip().lower()
            if trans_type not in ('income', 'expense'):
                print("错误：类型必须为 income 或 expense")
                return False

            amount_input = input("金额: ").strip()
            try:
                amount = float(amount_input)
                if amount <= 0:
                    print("错误：金额必须大于0")
                    return False
            except ValueError:
                print("错误：请输入有效的数字")
                return False

            category = input("分类 (可选): ").strip() or "未分类"
            description = input("备注 (可选): ").strip()
        else:
            # 自动模式验证
            required_keys = ['date', 'type', 'amount']
            if not all(k in auto_data for k in required_keys):
                raise ValueError("自动模式数据缺失必要字段")

            date = auto_data['date']
            trans_type = auto_data['type']
            amount = auto_data['amount']
            category = auto_data.get('category', '未分类')
            description = auto_data.get('description', '')

            # 验证自动数据
            try:
                datetime.datetime.strptime(date, "%Y-%m-%d")
                if trans_type not in ('income', 'expense'):
                    raise ValueError
                if float(amount) <= 0:
                    raise ValueError
            except:
                raise ValueError("自动数据验证失败")

        # === 数据库操作 ===
        sql = '''INSERT INTO transactions(date, type, amount, category, description)
                 VALUES(?,?,?,?,?)'''
        cur = conn.cursor()
        cur.execute(sql, (date, trans_type, amount, category, description))

        # 提交事务（如果是独立连接）
        if local_conn:
            conn.commit()

        return True

    except sqlite3.Error as e:
        if local_conn:
            conn.rollback()
        raise Exception(f"数据库错误: {str(e)}")
    except Exception as e:
        if local_conn:
            conn.rollback()
        raise e
    finally:
        if local_conn:
            local_conn.close()

# def show_summary(conn):
#     """ 显示本月汇总 """
#     cur = conn.cursor()
#     # 本月总收入
#     cur.execute("SELECT SUM(amount) FROM transactions WHERE type='income' AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')")
#     total_income = cur.fetchone()[0] or 0.0
#     # 本月总支出
#     cur.execute("SELECT SUM(amount) FROM transactions WHERE type='expense' AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')")
#     total_expense = cur.fetchone()[0] or 0.0
#
#     print(f"\n--- 本月汇总 ({datetime.date.today().strftime('%Y-%m')}) ---")
#     print(f"总收入: {total_income:.2f} 元")
#     print(f"总支出: {total_expense:.2f} 元")
#     print(f"当前结余: {total_income - total_expense:.2f} 元")

def show_summary(conn, gui_mode=False):
    """ 返回字典格式的数据以便GUI显示 """
    summary = {
        "month": datetime.date.today().strftime("%Y-%m"),
        "income": 0.0,
        "expense": 0.0,
        "balance": 0.0
    }

    cur = conn.cursor()
    # 本月总收入
    cur.execute("SELECT SUM(amount) FROM transactions WHERE type='income' AND strftime('%Y-%m', date) = ?",
                (summary["month"],))
    summary["income"] = cur.fetchone()[0] or 0.0

    # 本月总支出
    cur.execute("SELECT SUM(amount) FROM transactions WHERE type='expense' AND strftime('%Y-%m', date) = ?",
                (summary["month"],))
    summary["expense"] = cur.fetchone()[0] or 0.0

    summary["balance"] = summary["income"] - summary["expense"]

    return summary if gui_mode else print_summary(summary)  # 命令行模式保持原样

def set_salary(conn, payday, amount):
    """ 供GUI调用的设置薪资函数 """
    try:
        cur = conn.cursor()
        # 停用旧设置
        cur.execute("UPDATE salary_settings SET is_active = 0 WHERE is_active = 1")
        # 插入新记录
        cur.execute('''INSERT INTO salary_settings(payday, amount, start_date, is_active)
                     VALUES(?,?,?,1)''',
                   (payday, amount, datetime.date.today().isoformat()))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"设置薪资失败: {e}")
        return False

def show_history(conn):
    """ 查看历史记录 """
    print("\n--- 历史记录 ---")
    cur = conn.cursor()
    cur.execute("SELECT date, type, amount, category FROM transactions ORDER BY date DESC LIMIT 10")
    records = cur.fetchall()

    if not records:
        print("暂无记录")
        return

    for idx, (date, trans_type, amount, category) in enumerate(records, 1):
        print(f"{idx}. [{date}] {trans_type.upper()} - ¥{amount:.2f} ({category})")

# def manage_salary(conn):
#     """ 薪资管理主菜单 """
#     while True:
#         print("\n=== 薪资管理 ===")
#         print("1. 设置/修改发薪日")
#         print("2. 调整本月薪资")
#         print("3. 查看历史薪资设置")
#         print("4. 返回主菜单")
#         choice = input("请选择操作: ")
#
#         if choice == '1':
#             set_payday(conn)
#         elif choice == '2':
#             adjust_current_salary(conn)
#         elif choice == '3':
#             show_salary_history(conn)
#         elif choice == '4':
#             break
#         else:
#             print("无效输入！")

def set_payday(conn):
    """ 设置发薪日逻辑 """
    print("\n--- 设置发薪日 ---")

    # 获取当前设置
    cur = conn.cursor()
    cur.execute("SELECT payday, amount FROM salary_settings WHERE is_active = 1")
    current_setting = cur.fetchone()

    if current_setting:
        print(f"当前生效设置: 每月 {current_setting[0]} 号发薪，金额 {current_setting[1]} 元")

    # 获取新输入
    try:
        new_payday = int(input("请输入新的发薪日（1-31）: "))
        new_amount = float(input("请输入新的月薪金额: "))
        if not 1 <= new_payday <= 31:
            raise ValueError
    except ValueError:
        print("输入无效！必须满足：\n- 发薪日为 1-31 的整数\n- 金额为有效数字")
        return

    # 停用旧设置
    cur.execute("UPDATE salary_settings SET is_active = 0 WHERE is_active = 1")

    # 插入新记录
    sql = '''INSERT INTO salary_settings(payday, amount, start_date, is_active)
             VALUES(?,?,?,1)'''
    start_date = datetime.date.today().isoformat()
    cur.execute(sql, (new_payday, new_amount, start_date))
    conn.commit()

    print(f"已更新！新的发薪日设置为每月 {new_payday} 号，月薪 {new_amount} 元")

def adjust_current_salary(conn):
    """ 调整当前生效薪资 """
    print("\n--- 调整本月薪资 ---")

    # 获取当前设置
    cur = conn.cursor()
    cur.execute('''SELECT id, payday, amount 
                   FROM salary_settings 
                   WHERE is_active = 1 
                   ORDER BY start_date DESC LIMIT 1''')
    current = cur.fetchone()

    if not current:
        print("错误：请先设置发薪日！")
        return

    salary_id, payday, old_amount = current
    print(f"当前生效薪资：每月 {payday} 号发薪 {old_amount} 元")

    try:
        new_amount = float(input("请输入新的本月薪资金额: "))
        if new_amount <= 0:
            raise ValueError
    except ValueError:
        print("错误：请输入有效的正数金额")
        return

    # 创建调整记录（保留历史版本）
    sql = '''INSERT INTO salary_settings(payday, amount, start_date, is_active)
             VALUES(?,?,?,0)'''  # is_active=0 表示调整记录
    adjustment_date = datetime.date.today().isoformat()
    cur.execute(sql, (payday, new_amount, adjustment_date))

    # 更新当前生效记录
    cur.execute("UPDATE salary_settings SET amount = ? WHERE id = ?",
                (new_amount, salary_id))
    conn.commit()

    print(f"本月薪资已调整为 {new_amount} 元（原金额 {old_amount} 元）")

def show_salary_history(conn):
    """ 显示历史薪资设置 """
    cur = conn.cursor()
    cur.execute('''SELECT payday, amount, start_date, 
                   CASE WHEN is_active THEN '生效中' ELSE '历史记录' END AS status
                 FROM salary_settings
                 ORDER BY start_date DESC''')

    print("\n=== 历史薪资设置 ===")
    print("发薪日 | 金额    | 生效日期   | 状态")
    print("-" * 40)
    for payday, amount, start_date, status in cur.fetchall():
        print(f"{payday:6} | {amount:7.2f} | {start_date} | {status}")

def auto_add_salary(conn):
    """ 每天启动时检查是否发薪日（应添加到main函数初始化处）"""
    today = datetime.date.today()
    cur = conn.cursor()

    # 检查今天是否是激活的发薪日
    cur.execute('''SELECT payday, amount FROM salary_settings 
                 WHERE is_active = 1 AND payday = ?''', (today.day,))
    result = cur.fetchone()

    if result:
        payday, amount = result
        # 检查本月是否已添加
        cur.execute('''SELECT id FROM transactions 
                     WHERE type='income' AND category='薪资'
                     AND strftime('%Y-%m', date) = ?''',
                    (today.strftime('%Y-%m'),))
        if not cur.fetchone():
            add_transaction(conn, auto=True, auto_data={
                'date': today.isoformat(),
                'type': 'income',
                'amount': amount,
                'category': '薪资',
                'description': '月度工资'
            })

def add_daily_defaults(conn):
    """ 添加每日默认收支项 """
    print("\n--- 设置每日默认收支 ---")
    trans_type = input("类型 (income/expense): ").lower()
    amount = float(input("金额: "))
    category = input("分类: ")
    desc = input("描述（如'早餐'）: ")

    sql = '''INSERT INTO daily_defaults(type, amount, category, description)
             VALUES(?,?,?,?)'''
    cur = conn.cursor()
    cur.execute(sql, (trans_type, amount, category, desc))
    conn.commit()
    print("已添加每日默认项！")

def apply_daily_defaults(conn):
    """ 应用今日默认项（在程序启动时调用）"""
    today = datetime.date.today().isoformat()
    cur = conn.cursor()

    # 获取所有激活的默认项
    cur.execute("SELECT * FROM daily_defaults WHERE is_active = 1")
    defaults = cur.fetchall()

    for item in defaults:
        _, trans_type, amount, category, desc, _ = item
        # 检查今日是否已有该类型记录
        cur.execute('''SELECT id FROM transactions 
                     WHERE date=? AND type=? AND category=?''',
                    (today, trans_type, category))
        if not cur.fetchone():
            add_transaction(conn, auto=True, auto_data={
                'date': today,
                'type': trans_type,
                'amount': amount,
                'category': category,
                'description': desc
            })

# def set_budget_alert(conn):
#     """ 设置月度预算 """
#     budget = input("请输入月度支出预警金额（留空不设置）: ")
#     if not budget:
#         return
#
#     try:
#         budget = float(budget)
#     except:
#         print("无效金额！")
#         return
#
#     # 更新或插入记录
#     cur = conn.cursor()
#     cur.execute("SELECT id FROM budget_alert")
#     if cur.fetchone():
#         sql = "UPDATE budget_alert SET monthly_budget = ?"
#     else:
#         sql = "INSERT INTO budget_alert(monthly_budget) VALUES(?)"
#     cur.execute(sql, (budget,))
#     conn.commit()


# def check_budget_alert(conn):
#     """ 检查是否超支（在查看汇总时自动调用）"""
#     cur = conn.cursor()
#
#     # 1. 获取预警设置
#     cur.execute("SELECT monthly_budget, last_alert_month FROM budget_alert")
#     result = cur.fetchone()
#
#     # 无预警设置时直接返回
#     if not result or result[0] is None:
#         return
#
#     budget, last_alert_month = result
#     current_month = datetime.date.today().strftime("%Y-%m")
#
#     # 2. 检查是否需要提醒（允许 last_alert_month 为 NULL）
#     if last_alert_month == current_month:
#         return  # 本月已提醒过
#
#     # 3. 计算本月总支出
#     cur.execute('''SELECT SUM(amount) FROM transactions
#                  WHERE type='expense' AND strftime('%Y-%m', date) = ?''',
#                 (current_month,))
#     total_expense = cur.fetchone()[0] or 0.0
#
#     # 4. 触发预警
#     if total_expense > budget:
#         print(f"\n⚠️ 警告：本月支出已超预算！（预算: {budget} 元，实际: {total_expense:.2f} 元）")
#
#         # 5. 更新提醒月份（处理 NULL 值）
#         if last_alert_month is None:
#             # 如果表中字段初始为 NULL，需特殊处理
#             cur.execute("UPDATE budget_alert SET last_alert_month = ? WHERE id = 1",
#                         (current_month,))
#         else:
#             cur.execute("UPDATE budget_alert SET last_alert_month = ?",
#                         (current_month,))
#         conn.commit()

def set_budget_alert(conn, amount):
    """ 设置预警金额 """
    cur = conn.cursor()
    # 检查是否存在记录
    cur.execute("SELECT id FROM budget_alert")
    if cur.fetchone():
        sql = "UPDATE budget_alert SET monthly_budget = ?"
    else:
        sql = "INSERT INTO budget_alert(monthly_budget) VALUES(?)"

    try:
        cur.execute(sql, (amount,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"设置预警失败: {e}")
        return False

def get_budget_alert_status(conn):
    """
    获取当前预算预警状态
    返回格式:
        {
            "is_over": bool,      # 是否超支
            "budget": float,      # 预算金额
            "current": float,     # 当前支出
            "month": str          # 当前月份 (YYYY-MM)
        }
    """
    cur = conn.cursor()
    cur.execute("SELECT monthly_budget, last_alert_month FROM budget_alert")
    result = cur.fetchone()

    status = {
        "is_over": False,
        "budget": 0.0,
        "current": 0.0,
        "month": datetime.date.today().strftime("%Y-%m")
    }

    if not result or result[0] is None:
        return status

    budget, last_alert_month = result
    status["budget"] = budget

    # 计算本月支出
    cur.execute('''SELECT SUM(amount) FROM transactions 
                 WHERE type='expense' AND strftime('%Y-%m', date) = ?''',
                (status["month"],))
    total_expense = cur.fetchone()[0] or 0.0
    status["current"] = total_expense

    # 判断是否需要提示（允许首次提示或新月）
    if (last_alert_month != status["month"]) and (total_expense > budget):
        status["is_over"] = True
        # 更新提醒状态（避免重复提示）
        cur.execute("UPDATE budget_alert SET last_alert_month = ?", (status["month"],))
        conn.commit()

    return status

def main():
    conn = create_connection()
    if not conn:
        return

    # 启动时自动处理
    auto_add_salary(conn)  # 自动加薪
    apply_daily_defaults(conn)  # 应用默认项

    while True:
        print("\n===== 个人记账系统 =====")
        print("1. 添加记录")
        print("2. 查看本月汇总")
        print("3. 查看历史记录")
        print("4. 薪资管理")
        print("5. 设置每日默认收支")
        print("6. 设置支出预警")
        print("7. 退出")

        choice = input("请选择操作: ")

        if choice == '1':
            add_transaction(conn)
        elif choice == '2':
            show_summary(conn)
        elif choice == '3':
            show_history(conn)
        elif choice == '4':
            manage_salary(conn)
        elif choice == '5':
            add_daily_defaults(conn)
        elif choice == '6':
            set_budget_alert(conn)
        elif choice == '7':
            break

    conn.close()
    print("已退出系统")

if __name__ == "__main__":
    main()