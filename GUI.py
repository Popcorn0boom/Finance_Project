# gui.py
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3
import datetime
from database import create_connection
from main import (add_transaction, get_budget_alert_status,
                  show_summary, set_budget_alert, set_salary)
import threading

class FinanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("个人记账系统 v1.0")
        self.conn = create_connection()
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # 初始化预警检查
        self.check_budget_alert()

        # 构建主界面
        self.create_widgets()
        self.load_recent_transactions()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        self.conn.close()
        self.root.destroy()

    def create_widgets(self):
        """ 创建主界面组件 """
        # 顶部工具栏
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="+ 添加记录", command=self.show_add_dialog).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="📅 本月统计", command=self.show_monthly_summary).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="💰 薪资管理", command=self.show_salary_management).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="⚙️ 设置预警", command=self.show_budget_dialog).pack(side=tk.LEFT, padx=5)

        # 最近交易列表
        self.tree = ttk.Treeview(self.root, columns=("Date", "Type", "Amount", "Category"), show="headings")
        self.tree.heading("Date", text="日期")
        self.tree.heading("Type", text="类型")
        self.tree.heading("Amount", text="金额")
        self.tree.heading("Category", text="分类")
        self.tree.column("Date", width=100)
        self.tree.column("Type", width=80)
        self.tree.column("Amount", width=100)
        self.tree.column("Category", width=120)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 状态栏
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var,
                               relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 右键菜单
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="删除记录", command=self.delete_selected_record)

        self.tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        """ 显示右键菜单 """
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def delete_selected_record(self):
        """ 删除选中记录 """
        selected = self.tree.selection()
        if not selected:
            return

        record_id = self.tree.item(selected[0], "values")[0]
        if messagebox.askyesno("确认删除", "确定要删除这条记录吗？"):
            try:
                cur = self.conn.cursor()
                cur.execute("DELETE FROM transactions WHERE id=?", (record_id,))
                self.conn.commit()
                self.load_recent_transactions()
                self.status_var.set("记录删除成功")
            except sqlite3.Error as e:
                messagebox.showerror("错误", f"删除失败: {str(e)}")

    def check_budget_alert(self):
        """ 检查并显示预算预警 """
        alert_status = get_budget_alert_status(self.conn)
        if alert_status["is_over"]:
            self.status_var.set(f"⚠️ 警告：{alert_status['month']}月支出已超预算！")
            messagebox.showwarning(
                "超支警告",
                f"当前支出：¥{alert_status['current']:.2f}\n"
                f"预算金额：¥{alert_status['budget']:.2f}"
            )

    def load_recent_transactions(self, limit=20):
        """ 加载最近交易记录 """
        for row in self.tree.get_children():
            self.tree.delete(row)

        cur = self.conn.cursor()
        cur.execute('''SELECT id, date, type, amount, category 
                     FROM transactions ORDER BY date DESC LIMIT ?''', (limit,))

        for row in cur.fetchall():
            self.tree.insert("", tk.END, values=row)

    def show_add_dialog(self):
        """ 显示添加记录对话框 """
        dialog = tk.Toplevel(self.root)
        dialog.title("添加新记录")

        # 表单字段
        ttk.Label(dialog, text="日期:").grid(row=0, column=0, padx=5, pady=5)
        date_entry = DateEntry(dialog, date_pattern="y-mm-dd")
        date_entry.grid(row=0, column=1, padx=5)

        ttk.Label(dialog, text="类型:").grid(row=1, column=0)
        type_var = tk.StringVar()
        ttk.Combobox(dialog, textvariable=type_var,
                     values=["income", "expense"]).grid(row=1, column=1)

        ttk.Label(dialog, text="金额:").grid(row=2, column=0)
        amount_entry = ttk.Entry(dialog)
        amount_entry.grid(row=2, column=1)

        ttk.Label(dialog, text="分类:").grid(row=3, column=0)
        category_entry = ttk.Entry(dialog)
        category_entry.grid(row=3, column=1)

        ttk.Label(dialog, text="备注:").grid(row=4, column=0)
        desc_entry = ttk.Entry(dialog)
        desc_entry.grid(row=4, column=1)

        # 提交按钮
        # def submit():
        #     data = {
        #         "date": date_entry.get(),
        #         "type": type_var.get().lower(),
        #         "amount": amount_entry.get(),
        #         "category": category_entry.get(),
        #         "description": desc_entry.get()
        #     }
        #     if add_transaction(self.conn, auto=False, auto_data=data):
        #         self.load_recent_transactions()
        #         self.status_var.set("记录添加成功！")
        #         dialog.destroy()
        #         self.check_budget_alert()

        def submit():
            # 获取输入数据
            data = {
                "date": date_entry.get(),
                "type": type_var.get().lower(),
                "amount": amount_entry.get(),
                "category": category_entry.get(),
                "description": desc_entry.get()
            }

            # 禁用提交按钮避免重复点击
            submit_btn.config(state=tk.DISABLED)
            self.status_var.set("正在保存...")

            def db_operation():
                """ 在后台线程执行的数据库操作 """
                try:
                    # 在子线程中创建独立连接（重要！）
                    thread_conn = create_connection()
                    if add_transaction(thread_conn, auto=False, auto_data=data):
                        # 操作成功后更新UI（必须通过主线程）
                        self.root.after(0, lambda: self.on_add_success(thread_conn))
                    else:
                        self.root.after(0, lambda: self.on_add_failure("添加失败"))
                except Exception as e:
                    self.root.after(0, lambda: self.on_add_failure(str(e)))
                finally:
                    if thread_conn:
                        thread_conn.close()

            # 启动后台线程
            threading.Thread(target=db_operation, daemon=True).start()

        # 在 dialog 中添加提交按钮时保留引用
        submit_btn = ttk.Button(dialog, text="提交", command=submit)
        submit_btn.grid(row=5, columnspan=2, pady=10)

        ttk.Button(dialog, text="提交", command=submit).grid(row=5, columnspan=2, pady=10)

    def show_monthly_summary(self):
        """ 显示本月统计摘要 """
        summary = show_summary(self.conn, gui_mode=True)
        dialog = tk.Toplevel(self.root)
        dialog.title("本月统计")

        ttk.Label(dialog, text=f"统计月份: {summary['month']}").grid(row=0, columnspan=2, pady=5)
        ttk.Label(dialog, text="总收入:").grid(row=1, column=0, sticky="e")
        ttk.Label(dialog, text=f"¥{summary['income']:.2f}").grid(row=1, column=1)
        ttk.Label(dialog, text="总支出:").grid(row=2, column=0, sticky="e")
        ttk.Label(dialog, text=f"¥{summary['expense']:.2f}").grid(row=2, column=1)
        ttk.Label(dialog, text="当前结余:").grid(row=3, column=0, sticky="e")
        ttk.Label(dialog, text=f"¥{summary['balance']:.2f}",
                  foreground="green" if summary['balance'] >= 0 else "red").grid(row=3, column=1)

    def show_salary_management(self):
        """ 薪资管理界面 """
        salary_window = tk.Toplevel(self.root)
        salary_window.title("薪资管理")

        # 当前设置显示
        cur = self.conn.cursor()
        cur.execute("SELECT payday, amount FROM salary_settings WHERE is_active=1")
        current = cur.fetchone()

        ttk.Label(salary_window, text="当前生效设置:").grid(row=0, columnspan=2, pady=5)
        if current:
            ttk.Label(salary_window, text=f"发薪日: 每月{current[0]}号").grid(row=1, column=0)
            ttk.Label(salary_window, text=f"金额: ¥{current[1]:.2f}").grid(row=1, column=1)
        else:
            ttk.Label(salary_window, text="未设置薪资信息").grid(row=1, columnspan=2)

        # 设置新薪资
        ttk.Button(salary_window, text="设置新薪资",
                   command=lambda: self.set_new_salary(salary_window)).grid(row=2, columnspan=2, pady=10)

    def set_new_salary(self, parent):
        """ 设置新薪资对话框 """
        dialog = tk.Toplevel(parent)
        dialog.title("设置薪资")

        ttk.Label(dialog, text="发薪日 (1-31):").grid(row=0, column=0)
        payday_entry = ttk.Entry(dialog)
        payday_entry.grid(row=0, column=1)

        ttk.Label(dialog, text="月薪金额:").grid(row=1, column=0)
        amount_entry = ttk.Entry(dialog)
        amount_entry.grid(row=1, column=1)

        def submit():
            try:
                payday = int(payday_entry.get())
                amount = float(amount_entry.get())
                if set_salary(self.conn, payday, amount):  # 调用新函数
                    parent.destroy()
                    dialog.destroy()
                    self.status_var.set("薪资设置更新成功！")
            except ValueError:
                messagebox.showerror("错误", "输入无效！")

        ttk.Button(dialog, text="保存", command=submit).grid(row=2, columnspan=2)

    def show_budget_dialog(self):
        """ 设置预算对话框 """
        dialog = tk.Toplevel(self.root)
        dialog.title("设置预算")

        cur = self.conn.cursor()
        cur.execute("SELECT monthly_budget FROM budget_alert")
        current = cur.fetchone()

        ttk.Label(dialog, text="当前月度预算:").grid(row=0, column=0)
        budget_entry = ttk.Entry(dialog)
        budget_entry.grid(row=0, column=1)
        if current and current[0]:
            budget_entry.insert(0, str(current[0]))

        def save_budget():
            try:
                amount = float(budget_entry.get())
                set_budget_alert(self.conn, amount)
                self.status_var.set(f"月度预算已设置为 ¥{amount:.2f}")
                dialog.destroy()
                self.check_budget_alert()
            except ValueError:
                messagebox.showerror("错误", "请输入有效数字")

        ttk.Button(dialog, text="保存", command=save_budget).grid(row=1, columnspan=2)

    def on_add_success(self, thread_conn):
        """ 添加成功后的UI更新 """
        # 刷新主连接的数据（确保数据一致性）
        self.conn.commit()  # 如果使用连接池可能需要其他处理
        self.load_recent_transactions()
        self.status_var.set("记录添加成功！")
        # 重新启用按钮
        self.show_add_dialog.dialog.submit_btn.config(state=tk.NORMAL)
        self.check_budget_alert()

    def on_add_failure(self, error_msg):
        """ 添加失败处理 """
        messagebox.showerror("错误", f"保存失败: {error_msg}")
        self.status_var.set("保存失败")
        self.show_add_dialog.dialog.submit_btn.config(state=tk.NORMAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = FinanceApp(root)
    root.geometry("800x600")
    root.mainloop()