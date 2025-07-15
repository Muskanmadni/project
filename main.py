import streamlit as st
import pandas as pd
import sqlite3
import hashlib
import matplotlib.pyplot as plt

# --- Custom CSS Styling ---
# This block applies custom styles to Streamlit elements for nicer UI appearance
st.markdown("""
    <style>
        #MainMenu, footer {visibility: hidden;}
        body {
            font-family: 'Poppins', 'Segoe UI', sans-serif;
            background: linear-gradient(145deg, #f3f4f7, #ffffff);
        }
        h1, h2, h3 { color: #1f2937; font-weight: 600; }
        .stTextInput>div>div>input,
        .stNumberInput>div>div>input,
        .stDateInput>div>div>input {
            border-radius: 12px;
            padding: 10px 14px;
            border: 1px solid #d1d5db;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
            transition: all 0.2s ease-in-out;
        }
        input:focus {
            border-color: #4F46E5;
            box-shadow: 0 0 0 3px rgba(79,70,229,0.2);
        }
        .stButton>button {
            border-radius: 12px;
            padding: 10px 24px;
            background: linear-gradient(135deg, #4F46E5, #6366F1);
            color: white;
            font-weight: 600;
            border: none;
            box-shadow: 0 4px 14px rgba(99,102,241,0.3);
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            background: linear-gradient(135deg, #4338CA, #6366F1);
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(99,102,241,0.5);
        }
        .stMetric {
            background: #000000;
            border-radius: 20px;
            padding: 20px;
            color: #ffffff !important;
            box-shadow: 0 6px 12px rgba(0,0,0,0.3);
            transition: 0.3s ease;
        }
        .stMetric:hover {
            box-shadow: 0 0 15px rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
        }
        .css-1d391kg {
            background: rgba(0, 0, 0, 0.7) !important;
            backdrop-filter: blur(8px);
        }
        .css-1d391kg .css-10trblm {
            color: #ffffff;
        }
        .css-1d391kg .stRadio, .css-1d391kg .stSelectbox {
            background: transparent !important;
            color: white !important;
        }
        label[data-baseweb="radio"] > div {
            color: white !important;
        }
        .css-1d391kg .stButton>button {
            background-color: #EF4444;
            color: white;
        }
        .stDataFrame, .stTable {
            border-radius: 14px;
            background-color: rgba(255, 255, 255, 0.9);
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            padding: 10px;
        }
        .stPlotlyChart, .stImage {
            background-color: #1f2937;
            border-radius: 16px;
            padding: 16px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        }
        .element-container {
            margin-top: 10px;
            margin-bottom: 15px;
        }
    </style>
""", unsafe_allow_html=True)

# --- Utility Functions ---

def hash_password(password):
    """
    Returns the SHA-256 hash of the input password string.
    Used to securely store user passwords.
    """
    return hashlib.sha256(password.encode()).hexdigest()

def create_tables():
    """
    Creates the SQLite tables if they don't exist:
    - users: stores username and hashed password
    - income: stores user's income entries
    - expenses: stores user's expense entries
    """
    conn = sqlite3.connect("finance.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS income (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        date TEXT,
        source TEXT,
        amount REAL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        date TEXT,
        category TEXT,
        amount REAL
    )''')
    conn.commit()
    conn.close()

def add_user(username, password):
    """
    Adds a new user with hashed password to the database.
    Raises IntegrityError if username already exists.
    """
    conn = sqlite3.connect("finance.db")
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
    conn.commit()
    conn.close()

def check_user(username, password):
    """
    Checks if the username exists and password matches (hashed).
    Returns True if valid, False otherwise.
    """
    conn = sqlite3.connect("finance.db")
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE username=?", (username,))
    data = c.fetchone()
    conn.close()
    return data and data[0] == hash_password(password)

def load_data(username):
    """
    Loads income and expense data for a given username as pandas DataFrames.
    Includes the unique 'id' column for each entry.
    """
    conn = sqlite3.connect("finance.db")
    income = pd.read_sql("SELECT id, date, source, amount FROM income WHERE username=?", conn, params=(username,))
    expense = pd.read_sql("SELECT id, date, category, amount FROM expenses WHERE username=?", conn, params=(username,))
    conn.close()
    return income, expense

def save_income(username, date, source, amount):
    """
    Saves a new income entry for the user into the database.
    """
    conn = sqlite3.connect("finance.db")
    c = conn.cursor()
    c.execute("INSERT INTO income (username, date, source, amount) VALUES (?, ?, ?, ?)",
              (username, str(date), source, amount))
    conn.commit()
    conn.close()

def save_expense(username, date, category, amount):
    """
    Saves a new expense entry for the user into the database.
    """
    conn = sqlite3.connect("finance.db")
    c = conn.cursor()
    c.execute("INSERT INTO expenses (username, date, category, amount) VALUES (?, ?, ?, ?)",
              (username, str(date), category, amount))
    conn.commit()
    conn.close()

def delete_income_entry(entry_id):
    """
    Deletes an income entry by its unique ID.
    """
    conn = sqlite3.connect("finance.db")
    c = conn.cursor()
    c.execute("DELETE FROM income WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()

def delete_expense_entry(entry_id):
    """
    Deletes an expense entry by its unique ID.
    """
    conn = sqlite3.connect("finance.db")
    c = conn.cursor()
    c.execute("DELETE FROM expenses WHERE id=?", (entry_id,))
    conn.commit()
    conn.close()

# --- Session State Setup ---
# Initialize session state variables to keep track of login and signup status
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "signup" not in st.session_state:
    st.session_state.signup = False

# --- Alert Card ---
def bootstrap_alert(message, alert_type="info"):
    """
    Displays a styled alert message in Streamlit.
    alert_type: one of 'success', 'warning', 'error', 'info'
    """
    colors = {
        "success": ("#d4edda", "#155724", "#28a745", "✅"),
        "warning": ("#fff3cd", "#856404", "#ffeeba", "⚠️"),
        "error": ("#f8d7da", "#721c24", "#f5c6cb", "❌"),
        "info": ("#d1ecf1", "#0c5460", "#bee5eb", "ℹ️"),
    }
    bg, fg, border, emoji = colors.get(alert_type, colors["info"])
    st.markdown(f"""
    <div style='background-color: {bg}; color: {fg}; padding: 16px;
                border-radius: 12px; border-left: 6px solid {border};
                margin-bottom: 1rem; box-shadow: 0 4px 12px rgba(0,0,0,0.05);'>
        {emoji} {message}
    </div>
    """, unsafe_allow_html=True)

# --- Authentication Pages ---

def login():
    """
    Login page UI and logic.
    Checks user credentials and updates session state on success.
    """
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if check_user(username, password):
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"✨ Welcome {username}!")
            st.rerun()  # Refresh the app state after login
        else:
            st.error("Invalid credentials")
    st.info("Don't have an account?")
    if st.button("Go to Signup"):
        st.session_state.signup = True
        st.rerun()

def signup():
    """
    Signup page UI and logic.
    Allows new users to create accounts.
    """
    st.title("📝 Create Account")
    username = st.text_input("Create Username")
    password = st.text_input("Create Password", type="password")
    if st.button("Sign Up"):
        try:
            add_user(username, password)
            st.success("Account created! Please log in.")
            st.session_state.signup = False
            st.rerun()
        except sqlite3.IntegrityError:
            st.error("Username already exists!")
    if st.button("Back to Login"):
        st.session_state.signup = False
        st.rerun()

def logout():
    """
    Logs out the current user by resetting session state.
    """
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.rerun()

# --- Main Application ---

def main_app():
    """
    Main app UI after login.
    Allows navigation between Dashboard, Add Income, and Add Expense pages.
    """
    st.markdown("<h1 style='color:#4CAF50;'>💰 Personal Finance Tracker</h1>", unsafe_allow_html=True)

    with st.sidebar:
        # Show username and navigation menu
        st.markdown(f"## Welcome, {st.session_state.username}")
        page = st.radio("📌 Navigation", ["Dashboard", "Add Income", "Add Expense"])
        st.markdown("---")
        if st.button("🚪 Logout"):
            logout()

    # Load user's income and expense data
    income_df, expense_df = load_data(st.session_state.username)

    if page == "Add Income":
        # Page for adding new income
        st.header("🧾 Add Income")
        with st.form("income_form"):
            date = st.date_input("Date")
            source = st.text_input("Source")
            amount = st.number_input("Amount", min_value=0.0, format="%.2f")
            submit = st.form_submit_button("Add Income")
            if submit:
                save_income(st.session_state.username, date, source, amount)
                bootstrap_alert("Income added successfully!", "success")

    elif page == "Add Expense":
        # Page for adding new expense
        st.header("🧾 Add Expense")
        with st.form("expense_form"):
            date = st.date_input("Date")
            category = st.selectbox("Category", ["Rent", "Food", "Transport", "Utilities", "Other"])
            amount = st.number_input("Amount", min_value=0.0, format="%.2f")
            submit = st.form_submit_button("Add Expense")
            if submit:
                save_expense(st.session_state.username, date, category, amount)
                bootstrap_alert("Expense added successfully!", "success")

    elif page == "Dashboard":
        # Dashboard overview page

        st.header("📊 Dashboard")

        # Convert date columns to datetime for processing
        if not income_df.empty:
            income_df["Date"] = pd.to_datetime(income_df["date"])
        if not expense_df.empty:
            expense_df["Date"] = pd.to_datetime(expense_df["date"])

        # Calculate totals
        total_income = income_df["amount"].sum() if not income_df.empty else 0
        total_expenses = expense_df["amount"].sum() if not expense_df.empty else 0
        savings = total_income - total_expenses

        # Show metrics in columns
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Total Income", f"{total_income:.2f}")
        col2.metric("💸 Total Expenses", f"{total_expenses:.2f}")
        col3.metric("💹 Net Savings", f"{savings:.2f}")

        # --- Search Transactions ---
        st.subheader("🔎 Search Transactions")
        search_query = st.text_input("Search by source (income) or category (expense):").strip().lower()

        # Filter income and expenses based on search query if provided
        filtered_income = income_df[income_df['source'].str.lower().str.contains(search_query)] if search_query else income_df
        filtered_expense = expense_df[expense_df['category'].str.lower().str.contains(search_query)] if search_query else expense_df

        # --- Download Buttons ---
        # Download all income and expense data as CSV files
        st.download_button("📥 Download All Income", income_df.to_csv(index=False), "income.csv", "text/csv")
        st.download_button("📥 Download All Expenses", expense_df.to_csv(index=False), "expenses.csv", "text/csv")

        # If filtered, allow download of filtered data as well
        if search_query:
            st.download_button("🔍 Download Filtered Income", filtered_income.to_csv(index=False), "filtered_income.csv", "text/csv")
            st.download_button("🔍 Download Filtered Expenses", filtered_expense.to_csv(index=False), "filtered_expenses.csv", "text/csv")

        # --- Charts ---
        # Pie chart for expense category breakdown
        if not expense_df.empty:
            st.subheader("💸 Expenses Breakdown by Category")
            expense_summary = expense_df.groupby("category")["amount"].sum()
            fig1, ax1 = plt.subplots()
            ax1.pie(expense_summary, labels=expense_summary.index, autopct="%1.1f%%", startangle=90)
            ax1.axis("equal")  # Equal aspect ratio for pie chart
            st.pyplot(fig1)

        # Line chart for monthly income and expenses trends
        if not income_df.empty and not expense_df.empty:
            st.subheader("📈 Monthly Trends")
            income_df["Month"] = income_df["Date"].dt.to_period("M")
            expense_df["Month"] = expense_df["Date"].dt.to_period("M")
            monthly_income = income_df.groupby("Month")["amount"].sum()
            monthly_expense = expense_df.groupby("Month")["amount"].sum()
            trend_df = pd.DataFrame({"Income": monthly_income, "Expenses": monthly_expense}).fillna(0)
            st.line_chart(trend_df)

        # --- Saving Suggestions ---
        st.subheader("💡 Smart Saving Suggestions")
        if total_income == 0:
            bootstrap_alert("Add income to get savings advice.", "info")
        else:
            ratio = total_expenses / total_income
            if ratio > 1:
                bootstrap_alert("You're spending more than you earn! Consider reducing bills.", "error")
            elif ratio > 0.8:
                bootstrap_alert("You're spending over 80% of your income. Try cutting down non-essentials.", "warning")
            elif ratio > 0.5:
                bootstrap_alert("You're saving some money, but review your biggest expenses.", "info")
            else:
                bootstrap_alert("Excellent! You're saving a healthy portion of your income.", "success")

            # Suggest cutting the biggest expense category by 15%
            if not expense_df.empty:
                top_category = expense_df.groupby("category")["amount"].sum().idxmax()
                top_amount = expense_df.groupby("category")["amount"].sum().max()
                suggested_cut = top_amount * 0.15
                st.markdown(f"""
                🧠 You're spending the most on **{top_category}** ({top_amount:.2f}).

                👉 Try reducing it by 15% to save **{suggested_cut:.2f}** this month.
                """)

        # --- Recent Transactions with Delete Buttons ---
        st.subheader("📋 Recent Transactions")

        # Show latest 5 income entries, with delete buttons
        st.write("### Latest Income")
        latest_income = filtered_income.sort_values(by="date", ascending=False).head(5)
        for _, row in latest_income.iterrows():
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            col1.write(row["date"])
            col2.write(row["source"])
            col3.write(f"{row['amount']:.2f}")
            # Delete button per entry; triggers deletion and app refresh
            if col4.button("🗑️", key=f"del_income_{row['id']}"):
                delete_income_entry(row["id"])
                st.success("Income entry deleted.")
                st.rerun()

        # Show latest 5 expense entries, with delete buttons
        st.write("### Latest Expenses")
        latest_expense = filtered_expense.sort_values(by="date", ascending=False).head(5)
        for _, row in latest_expense.iterrows():
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            col1.write(row["date"])
            col2.write(row["category"])
            col3.write(f"{row['amount']:.2f}")
            if col4.button("🗑️", key=f"del_expense_{row['id']}"):
                delete_expense_entry(row["id"])
                st.success("Expense entry deleted.")
                st.rerun()

# --- Run the App ---

# Create necessary tables if not present
create_tables()

# Decide which page to show based on login/signup state
if st.session_state.logged_in:
    main_app()
elif st.session_state.signup:
    signup()
else:
    login()
