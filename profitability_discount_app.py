from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
from datetime import datetime
import json
import plotly.graph_objs as go
import plotly.utils
import plotly.express as px

app = Flask(__name__)

# Global variables
merged_data = None

def load_data():
    """Load dan process data untuk profitability & discount analysis"""
    global merged_data
    
    if merged_data is None:
        print("Loading profitability analysis data...")
        
        # Load data
        orders_data = pd.read_csv("data/orders.csv")
        products_data = pd.read_csv("data/product.csv") 
        customers_data = pd.read_csv("data/customer.csv")
        locations_data = pd.read_csv("data/location.csv")
        
        # Parse dates
        orders_data['order_date'] = pd.to_datetime(orders_data['order_date'])
        orders_data['year'] = orders_data['order_date'].dt.year
        orders_data['quarter'] = orders_data['order_date'].dt.quarter
        orders_data['month'] = orders_data['order_date'].dt.month
        orders_data['month_name'] = orders_data['order_date'].dt.strftime('%B')
        
        # Merge all data
        merged_data = orders_data.merge(products_data, on="product_id")
        merged_data = merged_data.merge(customers_data, on="customer_id") 
        merged_data = merged_data.merge(locations_data, on="location_id")
        
        # Calculate advanced metrics
        merged_data['profit_margin'] = np.where(merged_data['sales'] > 0, 
                                              (merged_data['profit'] / merged_data['sales']) * 100, 0)
        
        # High Sales Low Profit Detection
        merged_data['is_high_sales'] = merged_data['sales'] > merged_data['sales'].quantile(0.75)
        merged_data['is_low_profit'] = merged_data['profit_margin'] < merged_data['profit_margin'].quantile(0.25)
        merged_data['is_high_sales_low_profit'] = merged_data['is_high_sales'] & merged_data['is_low_profit']
        
        # Discount Buckets
        merged_data['discount_bucket'] = pd.cut(
            merged_data['discount'], 
            bins=[0, 0.1, 0.2, 0.3, 1.0], 
            labels=['0-10%', '10-20%', '20-30%', '30%+'],
            include_lowest=True
        )
        
        # Performance Indicators
        merged_data['is_profitable'] = merged_data['profit'] > 0
        merged_data['is_loss_making'] = merged_data['profit'] < 0
        merged_data['efficiency_score'] = calculate_efficiency_score(merged_data)
        
        print(f"✅ Data loaded: {len(merged_data)} records")
        print(f"📊 High Sales Low Profit orders: {merged_data['is_high_sales_low_profit'].sum()}")
        print(f"💸 Loss-making orders: {merged_data['is_loss_making'].sum()}")

def calculate_efficiency_score(df):
    """Calculate efficiency score (0-100) berdasarkan sales vs profit vs discount"""
    # Normalize profit margin to 0-50 points
    profit_score = np.clip((df['profit_margin'] + 20) / 0.7, 0, 50)
    
    # Sales volume score (0-30 points)
    sales_normalized = (df['sales'] - df['sales'].min()) / (df['sales'].max() - df['sales'].min())
    sales_score = sales_normalized * 30
    
    # Discount penalty (0-20 points deduction)
    discount_penalty = df['discount'] * 20
    
    efficiency = profit_score + sales_score - discount_penalty
    return np.clip(efficiency, 0, 100)

def apply_filters(df, filters):
    """Apply filters to dataframe"""
    filtered_df = df.copy()
    
    for key, value in filters.items():
        if value and value not in ['All', '', None]:
            try:
                if key in ['year', 'quarter', 'month']:
                    filtered_df = filtered_df[filtered_df[key] == int(value)]
                else:
                    filtered_df = filtered_df[filtered_df[key] == value]
            except:
                continue
    
    return filtered_df

def get_product_drill_down(df, level='category', parent=None):
    """Get hierarchical product analysis: Category -> Subcategory -> Product"""
    
    if level == 'category':
        group_cols = ['category']
    elif level == 'subcategory':
        df = df[df['category'] == parent] if parent else df
        group_cols = ['category', 'sub_category']
    elif level == 'product':
        df = df[df['sub_category'] == parent] if parent else df
        group_cols = ['category', 'sub_category', 'product_name']
    
    # Aggregate with advanced metrics
    agg_data = df.groupby(group_cols).agg({
        'sales': ['sum', 'mean', 'count'],
        'profit': ['sum', 'mean'],
        'profit_margin': 'mean',
        'quantity': ['sum', 'mean'],
        'discount': ['mean', 'median', 'min', 'max'],
        'is_high_sales_low_profit': 'sum',
        'is_loss_making': 'sum',
        'efficiency_score': 'mean'
    }).round(2)
    
    # Flatten column names
    agg_data.columns = [f"{col[0]}_{col[1]}" if col[1] != '' else col[0] 
                       for col in agg_data.columns]
    
    agg_data = agg_data.reset_index()
    
    # Add performance indicators
    agg_data['warning_high_sales_low_profit'] = agg_data['is_high_sales_low_profit_sum'] > 0
    agg_data['warning_loss_making'] = agg_data['is_loss_making_sum'] > 0
    agg_data['performance_tier'] = pd.cut(
        agg_data['profit_margin_mean'], 
        bins=[-float('inf'), 0, 5, 15, float('inf')],
        labels=['Loss', 'Poor', 'Good', 'Excellent']
    )
    
    return agg_data.to_dict('records')

def get_discount_analysis(df):
    """Comprehensive discount analysis"""
    
    # Discount bucket analysis
    discount_bucket_analysis = df.groupby('discount_bucket').agg({
        'sales': 'sum',
        'profit': 'sum',
        'profit_margin': 'mean',
        'order_id': 'count',
        'is_high_sales_low_profit': 'sum',
        'efficiency_score': 'mean'
    }).reset_index()
    
    # Discount by category
    category_discount = df.groupby('category').agg({
        'discount': ['mean', 'median', 'min', 'max'],
        'profit': 'sum',
        'profit_margin': 'mean'
    }).round(3)
    category_discount.columns = [f"{col[0]}_{col[1]}" for col in category_discount.columns]
    category_discount = category_discount.reset_index()
    
    # Discount correlation analysis
    discount_correlation = {
        'discount_profit_corr': df['discount'].corr(df['profit']),
        'discount_margin_corr': df['discount'].corr(df['profit_margin']),
        'discount_sales_corr': df['discount'].corr(df['sales'])
    }
    
    # Problem discount ranges
    problem_discounts = df[df['is_high_sales_low_profit']].groupby('discount_bucket').agg({
        'order_id': 'count',
        'sales': 'sum',
        'profit': 'sum'
    }).reset_index()
    
    return {
        'bucket_analysis': discount_bucket_analysis.to_dict('records'),
        'category_analysis': category_discount.to_dict('records'),
        'correlations': discount_correlation,
        'problem_ranges': problem_discounts.to_dict('records')
    }

def get_high_sales_low_profit_analysis(df):
    """Analyze high sales but low profit scenarios"""
    
    # Filter problematic orders
    problem_orders = df[df['is_high_sales_low_profit']]
    
    if problem_orders.empty:
        return {'warning': 'No high sales low profit scenarios found'}
    
    # Analyze by category
    category_problems = problem_orders.groupby('category').agg({
        'sales': 'sum',
        'profit': 'sum',
        'profit_margin': 'mean',
        'discount': 'mean',
        'order_id': 'count'
    }).sort_values('sales', ascending=False).reset_index()
    
    # Analyze by product
    product_problems = problem_orders.groupby(['category', 'sub_category', 'product_name']).agg({
        'sales': 'sum',
        'profit': 'sum',
        'profit_margin': 'mean',
        'discount': 'mean',
        'order_id': 'count'
    }).reset_index().sort_values('sales', ascending=False)
    
    # Root cause analysis
    avg_discount = problem_orders['discount'].mean()
    avg_margin = problem_orders['profit_margin'].mean()
    
    root_causes = []
    if avg_discount > 0.25:
        root_causes.append("High discount rates (avg {:.1f}%)".format(avg_discount * 100))
    if avg_margin < 5:
        root_causes.append("Very low profit margins (avg {:.1f}%)".format(avg_margin))
    
    return {
        'total_problematic_orders': len(problem_orders),
        'total_sales_at_risk': problem_orders['sales'].sum(),
        'category_breakdown': category_problems.head(5).to_dict('records'),
        'product_breakdown': product_problems.head(10).to_dict('records'),
        'root_causes': root_causes,
        'avg_discount': avg_discount * 100,
        'avg_profit_margin': avg_margin
    }

def get_root_cause_analysis(df):
    """Advanced root cause analysis untuk profit rendah"""
    
    # Loss-making analysis
    loss_orders = df[df['profit'] < 0]
    profitable_orders = df[df['profit'] > 0]
    
    if loss_orders.empty:
        loss_analysis = {'message': 'No loss-making orders found'}
    else:
        loss_analysis = {
            'total_loss_orders': len(loss_orders),
            'total_loss_amount': loss_orders['profit'].sum(),
            'worst_categories': loss_orders.groupby('category')['profit'].sum().sort_values().head(3).to_dict(),
            'worst_products': loss_orders.groupby('product_name')['profit'].sum().sort_values().head(5).to_dict(),
            'avg_discount_in_losses': loss_orders['discount'].mean() * 100
        }
    
    # Efficiency comparison
    efficiency_comparison = {
        'high_efficiency': len(df[df['efficiency_score'] > 75]),
        'medium_efficiency': len(df[(df['efficiency_score'] > 50) & (df['efficiency_score'] <= 75)]),
        'low_efficiency': len(df[df['efficiency_score'] <= 50]),
        'avg_discount_high_eff': df[df['efficiency_score'] > 75]['discount'].mean() * 100 if len(df[df['efficiency_score'] > 75]) > 0 else 0,
        'avg_discount_low_eff': df[df['efficiency_score'] <= 50]['discount'].mean() * 100 if len(df[df['efficiency_score'] <= 50]) > 0 else 0
    }
    
    return {
        'loss_analysis': loss_analysis,
        'efficiency_breakdown': efficiency_comparison
    }

def generate_business_insights(df):
    """Generate automated business insights"""
    insights = []
    
    # Category insights
    category_profit = df.groupby('category')['profit'].sum().sort_values(ascending=False)
    category_margin = df.groupby('category')['profit_margin'].mean().sort_values(ascending=False)
    
    insights.append({
        'type': 'success',
        'icon': 'fas fa-trophy',
        'title': 'Most Profitable Category',
        'message': f"{category_profit.index[0]} generates ${category_profit.iloc[0]:,.0f} total profit"
    })
    
    insights.append({
        'type': 'info', 
        'icon': 'fas fa-percentage',
        'title': 'Highest Margin Category',
        'message': f"{category_margin.index[0]} has {category_margin.iloc[0]:.1f}% average margin"
    })
    
    # Product insights
    product_profit = df.groupby('product_name')['profit'].sum()
    best_product = product_profit.idxmax()
    worst_product = product_profit.idxmin()
    
    insights.append({
        'type': 'success',
        'icon': 'fas fa-star',
        'title': 'Top Product',
        'message': f"{best_product[:50]}... (${product_profit[best_product]:,.0f})"
    })
    
    if product_profit[worst_product] < 0:
        insights.append({
            'type': 'danger',
            'icon': 'fas fa-exclamation-triangle', 
            'title': 'Biggest Loss Product',
            'message': f"{worst_product[:50]}... (${product_profit[worst_product]:,.0f} loss)"
        })
    
    # Discount insights
    high_discount_low_profit = len(df[(df['discount'] > 0.3) & (df['profit_margin'] < 5)])
    if high_discount_low_profit > 0:
        insights.append({
            'type': 'warning',
            'icon': 'fas fa-chart-line-down',
            'title': 'Discount Problem',
            'message': f"{high_discount_low_profit} orders with high discount (>30%) but low profit (<5%)"
        })
    
    # High Sales Low Profit
    hslp_count = df['is_high_sales_low_profit'].sum()
    if hslp_count > 0:
        insights.append({
            'type': 'warning',
            'icon': 'fas fa-exclamation-circle',
            'title': 'High Sales Low Profit Alert',
            'message': f"{hslp_count} orders appear successful but are actually inefficient"
        })
    
    return insights

@app.route('/')
def dashboard():
    return render_template('profitability_dashboard.html')

@app.route('/api/filters')
def get_filters():
    """Get filter options"""
    df = merged_data
    
    return jsonify({
        'countries': ['All'] + sorted(df['country'].unique().tolist()),
        'cities': ['All'] + sorted(df['city'].unique().tolist()),
        'categories': ['All'] + sorted(df['category'].unique().tolist()),
        'sub_categories': ['All'] + sorted(df['sub_category'].unique().tolist()),
        'products': ['All'] + sorted(df['product_name'].unique().tolist()[:100]),  # Limit for performance
        'years': ['All'] + sorted(df['year'].unique().tolist()),
    })

@app.route('/api/kpis')
def get_kpis():
    """Get main KPIs with current filters"""
    # Get filters
    filters = {}
    for key in ['country', 'city', 'category', 'sub_category', 'product_name', 'year', 'quarter', 'month']:
        value = request.args.get(key)
        if value and value != 'All':
            filters[key] = value
    
    df = apply_filters(merged_data, filters)
    
    if df.empty:
        return jsonify({'error': 'No data found for selected filters'})
    
    # Calculate KPIs
    total_sales = df['sales'].sum()
    total_profit = df['profit'].sum()
    profit_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
    total_orders = len(df)
    avg_discount = df['discount'].mean() * 100
    
    # Additional metrics
    profitable_orders = len(df[df['profit'] > 0])
    profitability_rate = (profitable_orders / total_orders * 100) if total_orders > 0 else 0
    
    return jsonify({
        'total_sales': round(total_sales, 2),
        'total_profit': round(total_profit, 2),
        'profit_margin': round(profit_margin, 2),
        'total_orders': total_orders,
        'avg_discount': round(avg_discount, 2),
        'profitability_rate': round(profitability_rate, 2)
    })

@app.route('/api/product-drill-down')
def product_drill_down():
    """Product hierarchy drill-down"""
    level = request.args.get('level', 'category')
    parent = request.args.get('parent')
    
    # Get filters
    filters = {}
    for key in ['country', 'city', 'year', 'quarter', 'month']:
        value = request.args.get(key)
        if value and value != 'All':
            filters[key] = value
    
    df = apply_filters(merged_data, filters)
    data = get_product_drill_down(df, level, parent)
    
    return jsonify({
        'level': level,
        'parent': parent,
        'data': data
    })

@app.route('/api/discount-analysis')
def discount_analysis():
    """Comprehensive discount analysis"""
    # Get filters
    filters = {}
    for key in ['country', 'city', 'category', 'year']:
        value = request.args.get(key)
        if value and value != 'All':
            filters[key] = value
    
    df = apply_filters(merged_data, filters)
    analysis = get_discount_analysis(df)
    
    return jsonify(analysis)

@app.route('/api/high-sales-low-profit')
def high_sales_low_profit():
    """High Sales Low Profit analysis"""
    # Get filters
    filters = {}
    for key in ['country', 'city', 'year']:
        value = request.args.get(key)
        if value and value != 'All':
            filters[key] = value
    
    df = apply_filters(merged_data, filters)
    analysis = get_high_sales_low_profit_analysis(df)
    
    return jsonify(analysis)

@app.route('/api/root-cause-analysis')
def root_cause_analysis():
    """Root cause analysis for profit issues"""
    # Get filters
    filters = {}
    for key in ['country', 'city', 'category', 'year']:
        value = request.args.get(key)
        if value and value != 'All':
            filters[key] = value
    
    df = apply_filters(merged_data, filters)
    analysis = get_root_cause_analysis(df)
    
    return jsonify(analysis)

@app.route('/api/business-insights')
def business_insights():
    """Generate business insights"""
    # Get filters
    filters = {}
    for key in ['country', 'city', 'category', 'year']:
        value = request.args.get(key)
        if value and value != 'All':
            filters[key] = value
    
    df = apply_filters(merged_data, filters)
    insights = generate_business_insights(df)
    
    return jsonify(insights)

@app.route('/api/time-analysis')
def time_analysis():
    """Time-based analysis"""
    level = request.args.get('level', 'month')
    
    # Get filters (excluding time filters)
    filters = {}
    for key in ['country', 'city', 'category']:
        value = request.args.get(key)
        if value and value != 'All':
            filters[key] = value
    
    df = apply_filters(merged_data, filters)
    
    if level == 'year':
        time_data = df.groupby('year').agg({
            'sales': 'sum',
            'profit': 'sum',
            'profit_margin': 'mean',
            'discount': 'mean'
        }).reset_index()
    elif level == 'quarter':
        time_data = df.groupby(['year', 'quarter']).agg({
            'sales': 'sum',
            'profit': 'sum', 
            'profit_margin': 'mean',
            'discount': 'mean'
        }).reset_index()
        time_data['period'] = time_data['year'].astype(str) + '-Q' + time_data['quarter'].astype(str)
    else:  # month
        time_data = df.groupby(['year', 'month']).agg({
            'sales': 'sum',
            'profit': 'sum',
            'profit_margin': 'mean', 
            'discount': 'mean'
        }).reset_index()
        time_data['period'] = time_data['year'].astype(str) + '-' + time_data['month'].astype(str).str.zfill(2)
    
    return jsonify({
        'level': level,
        'data': time_data.to_dict('records')
    })

if __name__ == '__main__':
    load_data()
    app.run(debug=True, port=5005)