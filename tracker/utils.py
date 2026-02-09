import pandas as pd
import numpy as np
from datetime import date
from .models import Transaction

def calculate_net_from_gross(gross):
    """
    Calculates monthly net income from annual gross salary based on UK tax rules.
    """
    pa = 12570
    if gross > 100000: pa = max(0, pa - (gross - 100000) / 2)
    taxable = max(0, gross - pa)
    
    tax = 0
    if taxable > 125140: tax += (taxable - 125140)*0.45 + (125140 - 37700)*0.40 + 37700*0.20
    elif taxable > 37700: tax += (taxable - 37700)*0.40 + 37700*0.20
    else: tax += taxable * 0.20
    
    ni = 0
    if gross > 12570: ni += (min(gross, 50270)-12570)*0.08
    if gross > 50270: ni += (gross - 50270)*0.02
    
    return (gross - tax - ni) / 12

def get_dashboard_context():
    """
    Aggregates data for the dashboard:
    - Current balance
    - Charts data (Plotly)
    - Recent history
    """
    transactions = Transaction.objects.all().values()
    df = pd.DataFrame(list(transactions))
    
    if df.empty:
        return {
            'balance': 0,
            'income': 0,
            'expenses': 0,
            'has_data': False
        }

    # Convert date to datetime if needed for pandas operations
    if 'date' in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df['month_year'] = df['date'].dt.to_period('M').astype(str)

    income = df[df["type"]=="Income"]["amount"].astype(float).sum()
    expenses = df[df["type"]=="Expense"]["amount"].astype(float).sum()
    balance = income - expenses
    
    return {
        'balance': balance,
        'income': income,
        'expenses': expenses,
        'has_data': True,
        'dataframe': df
    }
