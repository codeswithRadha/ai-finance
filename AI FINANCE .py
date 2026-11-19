import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import csv
from datetime import date, datetime
from collections import defaultdict

db = sqlite3.connect("finance_data.db")
db.execute("""
CREATE TABLE IF NOT EXISTS transactions(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 type TEXT, category TEXT, description TEXT,
 amount REAL, date TEXT
)
""")
db.commit()

root = tk.Tk()
root.title("AI Finance & Expense Manager")
root.geometry("1100x700")
root.configure(bg="#f1f5f9")

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", rowheight=28)
style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

header = tk.Frame(root, bg="#172554")
header.pack(fill="x")

tk.Label(header, text="AI FINANCE MANAGER",
         bg="#172554", fg="white",
         font=("Arial", 22, "bold")).pack(pady=15)

tabs = ttk.Notebook(root)
tabs.pack(fill="both", expand=True, padx=10, pady=10)

home = tk.Frame(tabs, bg="#f1f5f9")
records = tk.Frame(tabs, bg="#f1f5f9")
analysis = tk.Frame(tabs, bg="#f1f5f9")

tabs.add(home, text="Dashboard")
tabs.add(records, text="Transactions")
tabs.add(analysis, text="Analysis & Forecast")

# Dashboard
tk.Label(home, text="Financial Overview",
         bg="#f1f5f9", font=("Arial", 17, "bold")).pack(pady=10)

cards = tk.Frame(home, bg="#f1f5f9")
cards.pack(fill="x")

def make_card(title, color):
    box = tk.Frame(cards, bg=color, padx=20, pady=12)
    box.pack(side="left", fill="x", expand=True, padx=7)
    tk.Label(box, text=title, bg=color,
             font=("Arial", 10, "bold")).pack()
    label = tk.Label(box, text="Rs. 0.00", bg=color,
                     font=("Arial", 18, "bold"))
    label.pack(pady=5)
    return label

income_label = make_card("TOTAL INCOME", "#dcfce7")
expense_label = make_card("TOTAL EXPENSE", "#fee2e2")
balance_label = make_card("BALANCE", "#dbeafe")

form = tk.LabelFrame(home, text="Add Transaction",
                     bg="white", padx=10, pady=12)
form.pack(fill="x", padx=15, pady=15)

kind = tk.StringVar(value="Expense")
category = tk.StringVar(value="Food")
amount = tk.StringVar()
description = tk.StringVar()
txn_date = tk.StringVar(value=date.today().isoformat())

fields = [
    ("Type", kind, ["Expense", "Income"]),
    ("Category", category, [
        "Food", "Travel", "Shopping", "Bills",
        "Education", "Health", "Salary", "Business", "Other"
    ])
]

for i, (name, var, options) in enumerate(fields):
    tk.Label(form, text=name, bg="white").grid(row=0, column=i)
    ttk.Combobox(form, textvariable=var, values=options,
                 state="readonly", width=15).grid(row=1, column=i, padx=5)

for i, (name, var) in enumerate([
    ("Amount", amount),
    ("Date YYYY-MM-DD", txn_date),
    ("Description", description)
], 2):
    tk.Label(form, text=name, bg="white").grid(row=0, column=i)
    ttk.Entry(form, textvariable=var, width=18).grid(row=1, column=i, padx=5)

columns = ("ID", "Type", "Category", "Description", "Amount", "Date")

def create_table(parent, height=15):
    tree = ttk.Treeview(parent, columns=columns,
                        show="headings", height=height)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=140, anchor="center")
    return tree

recent = create_table(home, 7)
recent.pack(fill="both", expand=True, padx=15, pady=5)

# Transactions page
tk.Label(records, text="Transaction Records",
         bg="#f1f5f9", font=("Arial", 17, "bold")).pack(pady=10)

tools = tk.Frame(records, bg="#f1f5f9")
tools.pack(fill="x", padx=10)

search = tk.StringVar()
filter_type = tk.StringVar(value="All")

ttk.Entry(tools, textvariable=search, width=20).pack(side="left", padx=4)
all_table = create_table(records, 18)

# Analysis page
tk.Label(analysis, text="Financial Analysis",
         bg="#f1f5f9", font=("Arial", 17, "bold")).pack(pady=10)

summary = tk.Label(analysis, text="", bg="#f1f5f9",
                   font=("Arial", 11))
summary.pack(pady=5)

charts = tk.Frame(analysis, bg="#f1f5f9")
charts.pack(fill="both", expand=True)

category_canvas = tk.Canvas(charts, bg="white", height=300)
category_canvas.pack(side="left", fill="both", expand=True, padx=5)

month_canvas = tk.Canvas(charts, bg="white", height=300)
month_canvas.pack(side="left", fill="both", expand=True, padx=5)

forecast = tk.Label(analysis, text="Forecast will appear here",
                    bg="#dbeafe", fg="#1e40af",
                    font=("Arial", 12, "bold"), pady=12)
forecast.pack(fill="x", padx=15, pady=10)


def get_data():
    return db.execute(
        "SELECT * FROM transactions ORDER BY date DESC, id DESC"
    ).fetchall()


def fill_table(tree, rows):
    tree.delete(*tree.get_children())
    for r in rows:
        tree.insert("", "end", values=(
            r[0], r[1], r[2], r[3] or "",
            f"Rs. {r[4]:,.2f}", r[5]
        ))


def draw_chart(canvas, data):
    canvas.delete("all")
    canvas.update_idletasks()
    width = max(canvas.winfo_width(), 350)

    if not data:
        canvas.create_text(170, 120, text="No data available")
        return

    items = sorted(data.items(), key=lambda x: x[1],
                   reverse=True)[:8]
    maximum = max(data.values()) or 1

    for i, (name, value) in enumerate(items):
        y = 25 + i * 32
        bar = 200 * value / maximum
        canvas.create_text(85, y+10, text=str(name)[:12], anchor="e")
        canvas.create_rectangle(95, y, 95+bar, y+20,
                                fill="#2563eb", outline="")
        canvas.create_text(min(100+bar, width-30), y+10,
                           text=f"{value:.0f}", anchor="w")


def update_forecast(months):
    if not months:
        forecast.config(text="Add expenses to calculate forecast.")
        return

    keys = sorted(months)
    values = [months[k] for k in keys]

    if len(values) == 1:
        prediction = values[0]
    else:
        n = len(values)
        mean_x = (n+1)/2
        mean_y = sum(values)/n
        slope = sum(
            (i+1-mean_x)*(v-mean_y)
            for i, v in enumerate(values)
        ) / sum((i+1-mean_x)**2 for i in range(n))
        prediction = max(0, mean_y+slope*(n+1-mean_x))

    last = datetime.strptime(keys[-1], "%Y-%m")
    next_month = last.replace(
        year=last.year+(last.month == 12),
        month=1 if last.month == 12 else last.month+1
    )

    forecast.config(
        text=f"Predicted Expense for {next_month.strftime('%B %Y')}: "
             f"Rs. {prediction:,.2f} (Statistical estimate)"
    )


def refresh():
    rows = get_data()
    income = sum(r[4] for r in rows if r[1] == "Income")
    expense = sum(r[4] for r in rows if r[1] == "Expense")

    income_label.config(text=f"Rs. {income:,.2f}")
    expense_label.config(text=f"Rs. {expense:,.2f}")
    balance_label.config(text=f"Rs. {income-expense:,.2f}")

    fill_table(recent, rows[:7])

    selected = filter_type.get()
    keyword = search.get().lower().strip()

    filtered = [
        r for r in rows
        if (selected == "All" or r[1] == selected)
        and (not keyword or keyword in " ".join(map(str, r)).lower())
    ]
    fill_table(all_table, filtered)

    categories = defaultdict(float)
    months = defaultdict(float)

    for r in rows:
        if r[1] == "Expense":
            categories[r[2]] += r[4]
            months[r[5][:7]] += r[4]

    summary.config(
        text=f"Income: Rs. {income:,.2f} | "
             f"Expense: Rs. {expense:,.2f} | "
             f"Balance: Rs. {income-expense:,.2f}"
    )

    draw_chart(category_canvas, categories)
    draw_chart(month_canvas, months)
    update_forecast(months)


def add_transaction():
    try:
        value = float(amount.get())
        if value <= 0:
            raise ValueError
        datetime.strptime(txn_date.get(), "%Y-%m-%d")

        db.execute("""
            INSERT INTO transactions
            (type, category, description, amount, date)
            VALUES (?, ?, ?, ?, ?)
        """, (kind.get(), category.get(), description.get(),
              value, txn_date.get()))
        db.commit()

        amount.set("")
        description.set("")
        refresh()
        messagebox.showinfo("Success", "Transaction saved!")

    except ValueError:
        messagebox.showerror(
            "Error", "Enter a positive amount and valid date."
        )


def selected_record():
    selected = all_table.selection()
    if not selected:
        messagebox.showwarning("Warning", "Select a transaction.")
        return None
    txn_id = all_table.item(selected[0], "values")[0]
    return db.execute(
        "SELECT * FROM transactions WHERE id=?", (txn_id,)
    ).fetchone()


def delete_transaction():
    row = selected_record()
    if row and messagebox.askyesno("Confirm", "Delete this record?"):
        db.execute("DELETE FROM transactions WHERE id=?", (row[0],))
        db.commit()
        refresh()


def receipt():
    row = selected_record()
    if not row:
        return

    path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        initialfile=f"receipt_{row[0]}.txt"
    )
    if path:
        content = f"""
================================
       FINANCE MANAGER
       TRANSACTION RECEIPT
================================
Receipt ID : {row[0]}
Type       : {row[1]}
Category   : {row[2]}
Description: {row[3]}
Amount     : Rs. {row[4]:,.2f}
Date       : {row[5]}
================================
Computer generated receipt
"""
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)
        messagebox.showinfo("Success", "Receipt generated!")


def export_csv():
    rows = get_data()
    if not rows:
        messagebox.showinfo("Empty", "No transactions available.")
        return

    path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv")]
    )
    if path:
        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(columns)
            writer.writerows(rows)
        messagebox.showinfo("Success", "CSV exported!")


ttk.Button(form, text="Save Transaction",
           command=add_transaction).grid(row=1, column=5, padx=8)

ttk.Button(tools, text="Search / Filter",
           command=refresh).pack(side="left", padx=4)

ttk.Combobox(tools, textvariable=filter_type,
             values=["All", "Income", "Expense"],
             state="readonly", width=12).pack(side="left", padx=4)

ttk.Button(tools, text="Delete",
           command=delete_transaction).pack(side="right", padx=4)

ttk.Button(tools, text="Receipt",
           command=receipt).pack(side="right", padx=4)

ttk.Button(tools, text="Export CSV",
           command=export_csv).pack(side="right", padx=4)

refresh()

def close():
    db.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", close)
root.mainloop()