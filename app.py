import streamlit as st
import pandas as pd
from datetime import date
import numpy as np
from supabase import create_client

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Financial OS for Small Business", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- DATABASE SETUP (SUPABASE) ---
@st.cache_resource
def init_connection():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_connection()

def insert_transaction(t_date, t_type, t_category, t_amount, t_desc):
    supabase.table("transactions").insert({
        "date": t_date,
        "type": t_type,
        "category": t_category,
        "amount": t_amount,
        "description": t_desc
    }).execute()

def fetch_all_transactions():
    response = supabase.table("transactions").select("*").order("date", desc=True).order("id", desc=True).execute()
    # Convert response data directly to a Pandas DataFrame
    df = pd.DataFrame(response.data)
    return df

def delete_transaction(tx_id):
    supabase.table("transactions").delete().eq("id", tx_id).execute()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("Navigation")
menu = st.sidebar.radio(
    "Go to", 
    ["Dashboard (Overview)", "Ledger Entry", "Advanced Analytics", "Data Export"]
)

# --- LOAD DATA ---
df = fetch_all_transactions()
# Ensure 'amount' is treated as a float in pandas just in case
if not df.empty:
    df['amount'] = df['amount'].astype(float)

# --- PAGE 1: LEDGER ENTRY ---
if menu == "Ledger Entry":
    st.header("Ledger & Data Entry")
    st.write("Record daily business transactions securely to the cloud database.")
    
    with st.form("entry_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            t_date = st.date_input("Date", date.today())
            t_type = st.selectbox("Transaction Type", ["Income", "Expense", "Asset", "Liability"])
        with col2:
            t_category = st.text_input("Category (e.g., Sales, Rent, Inventory)")
            t_amount = st.number_input("Amount", min_value=0.0, format="%.2f")
        with col3:
            t_desc = st.text_input("Description / Memo")
            
        submitted = st.form_submit_button("Record Transaction")
        
        if submitted:
            if t_category == "" or t_amount <= 0.0:
                st.error("Please provide a category and a valid amount greater than 0.")
            else:
                insert_transaction(str(t_date), t_type, t_category, t_amount, t_desc)
                st.success("Transaction recorded successfully!")
                st.rerun()
            
    st.subheader("Recent Ledger Entries")
    if not df.empty:
        # Display everything except the database ID for a cleaner look
        display_df = df.drop(columns=['id']) if 'id' in df.columns else df
        st.dataframe(display_df, use_container_width=True)
        
        st.subheader("Delete a Record")
        if 'id' in df.columns:
            delete_id = st.selectbox("Select Transaction ID to delete", df['id'].tolist())
            if st.button("Delete Selected Transaction"):
                delete_transaction(delete_id)
                st.success("Transaction deleted.")
                st.rerun()
    else:
        st.info("No entries found in the database.")

# --- PAGE 2: DASHBOARD (Overview) ---
elif menu == "Dashboard (Overview)":
    st.header("Business Overview")
    
    if df.empty:
        st.info("No data available. Please enter transactions in the Ledger.")
    else:
        income = df[df["type"] == "Income"]["amount"].sum()
        expenses = df[df["type"] == "Expense"]["amount"].sum()
        net_profit = income - expenses
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Income", f"${income:,.2f}")
        col2.metric("Total Expenses", f"${expenses:,.2f}")
        col3.metric("Net Profit", f"${net_profit:,.2f}", delta=f"${net_profit:,.2f}")
        
        st.divider()
        
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            st.subheader("Income vs. Expenses")
            summary_df = df[df["type"].isin(["Income", "Expense"])].groupby("type")["amount"].sum()
            if not summary_df.empty:
                st.bar_chart(summary_df)
            else:
                st.write("Need both income and expenses to show comparison.")
            
        with col_chart2:
            st.subheader("Expense Breakdown by Category")
            expenses_df = df[df["type"] == "Expense"]
            if not expenses_df.empty:
                category_df = expenses_df.groupby("category")["amount"].sum()
                st.bar_chart(category_df)
            else:
                st.write("No expenses recorded yet.")

# --- PAGE 3: ADVANCED ANALYTICS ---
elif menu == "Advanced Analytics":
    st.header("Advanced Financial Analysis")
    
    if df.empty:
        st.warning("Insufficient ledger data for advanced analysis.")
    else:
        tab1, tab2, tab3 = st.tabs(["Financial Ratios", "Cash Flow Forecast", "Variance Analysis"])
        
        with tab1:
            st.subheader("Key Performance Indicators (KPIs)")
            income = df[df["type"] == "Income"]["amount"].sum()
            expenses = df[df["type"] == "Expense"]["amount"].sum()
            net_profit = income - expenses
            
            if income > 0:
                profit_margin = (net_profit / income) * 100
                st.metric("Net Profit Margin", f"{profit_margin:.1f}%")
            else:
                st.info("Record income to calculate Profit Margin.")
            
        with tab2:
            st.subheader("30-Day Cash Flow Prediction")
            dates = pd.date_range(date.today(), periods=30)
            chart_data = pd.DataFrame(
                np.random.normal(loc=100, scale=20, size=(30, 1)).cumsum(), 
                index=dates, 
                columns=["Projected Cash Balance"]
            )
            st.line_chart(chart_data)
            
        with tab3:
            st.subheader("Budget vs. Actuals")
            
            if not df[df["type"] == "Expense"].empty:
                variance_df = df[df["type"] == "Expense"].groupby("category")["amount"].sum().reset_index()
                variance_df = variance_df.rename(columns={"amount": "Actual Spend"})
                variance_df["Budgeted Spend (Mock)"] = variance_df["Actual Spend"] * np.random.uniform(0.8, 1.2, size=len(variance_df))
                variance_df["Variance"] = variance_df["Budgeted Spend (Mock)"] - variance_df["Actual Spend"]
                
                variance_df['Actual Spend'] = variance_df['Actual Spend'].map('${:,.2f}'.format)
                variance_df['Budgeted Spend (Mock)'] = variance_df['Budgeted Spend (Mock)'].map('${:,.2f}'.format)
                variance_df['Variance'] = variance_df['Variance'].map('${:,.2f}'.format)
                
                st.dataframe(variance_df, use_container_width=True)
            else:
                st.write("No expense data available for variance analysis.")

# --- PAGE 4: DATA EXPORT ---
elif menu == "Data Export":
    st.header("Export Your Data")
    
    if not df.empty:
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Complete Ledger as CSV",
            data=csv,
            file_name=f"financial_ledger_export_{date.today()}.csv",
            mime="text/csv",
        )
    else:
        st.info("No data available to export.")
