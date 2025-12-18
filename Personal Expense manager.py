
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import os
from datetime import datetime
from collections import defaultdict
import pandas as pd
import matplotlib.pyplot as plt

CSV_FILE = "expenses.csv"
DATE_FMT = "%d/%m/%Y"

# Ensure matplotlib uses a font that displays £ symbol nicely
plt.rcParams['font.family'] = 'DejaVu Sans'

CATEGORIES_DEFAULT = [
    "Groceries", "Transport", "Eating Out", "Bills", "Rent",
    "Entertainment", "Health", "Education", "Subscriptions",
    "Gifts", "Savings", "Other"
]

def ensure_csv_exists():
    """Create the CSV with headers if it doesn't exist."""
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "type", "category", "amount", "note"])

def parse_date(date_str):
    """Validate and parse date string (DD/MM/YYYY)."""
    try:
        dt = datetime.strptime(date_str.strip(), DATE_FMT)
        return dt
    except ValueError:
        raise ValueError("Invalid date format. Use DD/MM/YYYY (e.g., 05/11/2025).")

def parse_amount(amount_str):
    """Validate amount to positive float."""
    try:
        val = float(amount_str)
        if val <= 0:
            raise ValueError
        return round(val, 2)
    except Exception:
        raise ValueError("Amount must be a positive number (e.g., 12.50).")

def add_record(record_type):
    """Add income or expense record."""
    record_type = record_type.lower().strip()
    if record_type not in ("income", "expense"):
        print("Type must be 'income' or 'expense'.")
        return

    print("\n➡️  Adding a new {} record".format(record_type))
    date_str = input("Date (DD/MM/YYYY): ").strip()
    try:
        dt = parse_date(date_str)
    except ValueError as e:
        print("Error:", e)
        return

    # Suggest categories for expenses; allow custom
    if record_type == "expense":
        print("Categories:", ", ".join(CATEGORIES_DEFAULT))
    category = input("Category: ").strip()
    if not category:
        category = "Other"

    amount_str = input("Amount (£): ").strip()
    try:
        amount = parse_amount(amount_str)
    except ValueError as e:
        print("Error:", e)
        return

    note = input("Note (optional): ").strip()

    # Append to CSV
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([dt.strftime(DATE_FMT), record_type, category, amount, note])

    print(f"✅ Saved: {dt.strftime(DATE_FMT)} | {record_type} | {category} | £{amount:.2f} | {note}")

def load_data():
    """Load CSV into a pandas DataFrame with parsed date."""
    ensure_csv_exists()
    df = pd.read_csv(CSV_FILE, encoding="utf-8")
    if df.empty:
        return df
    # Parse dates
    df["date"] = pd.to_datetime(df["date"], format=DATE_FMT, errors="coerce")
    # Coerce amount to float
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    # Clean types/categories
    df["type"] = df["type"].str.lower().str.strip()
    df["category"] = df["category"].fillna("Other").astype(str)
    # Drop invalid rows
    df = df.dropna(subset=["date", "amount", "type"])
    return df

def summary_overview(df):
    """Print overall totals."""
    income = df.loc[df["type"] == "income", "amount"].sum()
    expense = df.loc[df["type"] == "expense", "amount"].sum()
    net = income - expense
    print("\n📊 Overview")
    print(f"Total income:   £{income:.2f}")
    print(f"Total expenses: £{expense:.2f}")
    print(f"Net balance:    £{net:.2f} {'(surplus)' if net >= 0 else '(deficit)'}")

def summary_by_month(df):
    """Group by month-year and show income/expense/net."""
    if df.empty:
        print("\n(no data)")
        return
    df["month"] = df["date"].dt.to_period("M")
    inc = df[df["type"] == "income"].groupby("month")["amount"].sum()
    exp = df[df["type"] == "expense"].groupby("month")["amount"].sum()
    months = sorted(set(df["month"]))
    print("\n🗓️  Monthly Summary")
    print(f"{'Month':<10} {'Income':>10} {'Expense':>10} {'Net':>10}")
    for m in months:
        i = inc.get(m, 0.0)
        e = exp.get(m, 0.0)
        n = i - e
        print(f"{str(m):<10} £{i:>9.2f} £{e:>9.2f} £{n:>9.2f}")

def summary_by_category(df):
    """Group expenses by category."""
    exp = df[df["type"] == "expense"]
    if exp.empty:
        print("\n(no expenses yet)")
        return
    cat = exp.groupby("category")["amount"].sum().sort_values(ascending=False)
    print("\n🏷️  Expenses by Category")
    print(f"{'Category':<20} {'Total':>10}")
    for k, v in cat.items():
        print(f"{k:<20} £{v:>9.2f}")

def generate_charts(df):
    """Create charts: category pie, monthly line trend."""
    if df.empty:
        print("\nNo data to chart.")
        return

    # 1) Category pie (expenses)
    exp = df[df["type"] == "expense"]
    if not exp.empty:
        cat = exp.groupby("category")["amount"].sum().sort_values(ascending=False)
        plt.figure(figsize=(8, 6))
        plt.title("Expenses by Category (£)")
        plt.pie(
            cat.values,
            labels=cat.index,
            autopct=lambda p: f"{p:.1f}% (£{(p/100.0)*cat.sum():.2f})",
            startangle=90
        )
        plt.tight_layout()
        plt.savefig("chart_expenses_by_category.png", dpi=140)
        plt.close()
        print("🖼️  Saved: chart_expenses_by_category.png")

    # 2) Monthly trend: income vs expense
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    inc = df[df["type"] == "income"].groupby("month")["amount"].sum()
    expm = df[df["type"] == "expense"].groupby("month")["amount"].sum()
    months = sorted(set(df["month"]))
    income_series = [inc.get(m, 0.0) for m in months]
    expense_series = [expm.get(m, 0.0) for m in months]
    net_series = [i - e for i, e in zip(income_series, expense_series)]

    plt.figure(figsize=(10, 6))
    plt.plot(months, income_series, marker='o', label="Income")
    plt.plot(months, expense_series, marker='o', label="Expenses")
    plt.plot(months, net_series, marker='o', label="Net")
    plt.title("Monthly Income vs Expenses (£)")
    plt.xlabel("Month")
    plt.ylabel("Amount (£)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig("chart_monthly_trend.png", dpi=140)
    plt.close()
    print("🖼️  Saved: chart_monthly_trend.png")

def export_filtered(df):
    """Filter by date range or category and export to CSV."""
    if df.empty:
        print("\nNo data to export.")
        return
    print("\n📤 Export filtered data")
    start = input("Start date (DD/MM/YYYY) or leave blank: ").strip()
    end = input("End date   (DD/MM/YYYY) or leave blank: ").strip()
    category = input("Category (optional): ").strip()

    filtered = df.copy()
    try:
        if start:
            filtered = filtered[filtered["date"] >= parse_date(start)]
        if end:
            filtered = filtered[filtered["date"] <= parse_date(end)]
    except ValueError as e:
        print("Error:", e)
        return

    if category:
        filtered = filtered[filtered["category"].str.lower() == category.lower()]

    if filtered.empty:
        print("No matching records.")
        return

    out_file = "export.csv"
    filtered_sorted = filtered.sort_values(by="date")
    filtered_sorted.to_csv(out_file, index=False)
    print(f"✅ Exported {len(filtered_sorted)} rows to {out_file}")

def show_menu():
    print("\n========== Expense Tracker ==========")
    print("1) Add expense")
    print("2) Add income")
    print("3) View summaries")
    print("4) Generate charts")
    print("5) Export filtered data")
    print("6) Quit")

def view_summaries(df):
    if df.empty:
        print("\nNo data yet. Add some records first!")
        return
    summary_overview(df)
    summary_by_month(df)
    summary_by_category(df)

def main():
    ensure_csv_exists()
    while True:
        show_menu()
        choice = input("Choose an option (1-6): ").strip()
        if choice == "1":
            add_record("expense")
        elif choice == "2":
            add_record("income")
        elif choice == "3":
            df = load_data()
            view_summaries(df)
        elif choice == "4":
            df = load_data()
            generate_charts(df)
        elif choice == "5":
            df = load_data()
            export_filtered(df)
        elif choice == "6":
            print("👋 Goodbye! Keep tracking wisely.")
            break
        else:
            print("Invalid choice. Please select 1-6.")

if __name__ == "__main__":
    main()
