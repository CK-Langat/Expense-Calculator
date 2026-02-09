from django.shortcuts import render, redirect
from .models import Transaction
from .utils import calculate_net_from_gross
import pandas as pd
import plotly.express as px
from django.db.models import Sum

def dashboard(request):
    if request.method == 'POST':
        date = request.POST.get('date')
        type = request.POST.get('type')
        category = request.POST.get('category')
        amount = float(request.POST.get('amount'))
        
        # Gross to Net calculation if needed
        if type == 'Income' and request.POST.get('is_gross') == 'on':
             amount = calculate_net_from_gross(amount)

        Transaction.objects.create(
            date=date,
            type=type,
            category=category,
            amount=amount
        )
        return redirect('dashboard')

    # Data for Charts & Summary
    transactions = Transaction.objects.all().order_by('-date')
    
    # Calculate totals
    income = transactions.filter(type='Income').aggregate(Sum('amount'))['amount__sum'] or 0
    expenses = transactions.filter(type='Expense').aggregate(Sum('amount'))['amount__sum'] or 0
    balance = income - expenses

    # Charts Logic
    ids = []
    graphJSONs = []
    
    if transactions.exists():
        df = pd.DataFrame(list(transactions.values()))
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.to_period('M').astype(str)

        # Cash Flow Bar Chart
        if not df.empty:
            cash_flow = df.groupby(['month', 'type'])['amount'].sum().reset_index()
            fig1 = px.bar(cash_flow, x='month', y='amount', color='type', barmode='group', 
                          title='Monthly Cash Flow', color_discrete_map={'Income': '#00CC96', 'Expense': '#EF553B'})
            import json
            from plotly.utils import PlotlyJSONEncoder
            
            # Expenses Pie Chart
            expenses_df = df[df['type'] == 'Expense']
            if not expenses_df.empty:
                fig2 = px.pie(expenses_df, values='amount', names='category', title='Expense Breakdown')
                # We will pass these to template as JSON
                context_charts = {
                   'cash_flow_json': json.dumps(fig1, cls=PlotlyJSONEncoder),
                   'expense_pie_json': json.dumps(fig2, cls=PlotlyJSONEncoder)
                }
            else:
                 context_charts = {'cash_flow_json': json.dumps(fig1, cls=PlotlyJSONEncoder), 'expense_pie_json': None}
        else:
            context_charts = {}
    else:
        context_charts = {}

    context = {
        'transactions': transactions,
        'income': income,
        'expenses': expenses,
        'balance': balance,
        **context_charts
    }
    return render(request, 'tracker/dashboard.html', context)

def delete_transaction(request, id):
    if request.method == 'POST':
        Transaction.objects.get(id=id).delete()
    return redirect('dashboard')
