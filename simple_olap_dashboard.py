import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify
import plotly.graph_objs as go
import plotly.utils
import json
from datetime import datetime

app = Flask(__name__)

# Load data
def load_data():
    try:
        orders_df = pd.read_csv('data/orders.csv')
        products_df = pd.read_csv('data/product.csv')
        
        # Merge orders with products
        df = orders_df.merge(products_df, on='product_id', how='left')
        
        # Convert dates
        df['order_date'] = pd.to_datetime(df['order_date'])
        df['year'] = df['order_date'].dt.year
        df['month'] = df['order_date'].dt.month
        df['month_year'] = df['order_date'].dt.to_period('M')
        
        # Calculate profit margin
        df['profit_margin'] = (df['profit'] / df['sales']) * 100
        df['profit_margin'] = df['profit_margin'].replace([np.inf, -np.inf], 0)
        
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

@app.route('/')
def dashboard():
    df = load_data()
    
    # Get filter options
    years = sorted(df['year'].unique()) if not df.empty else []
    categories = sorted(df['category'].dropna().unique()) if not df.empty else []
    
    return render_template('simple_dashboard.html', 
                         years=years, 
                         categories=categories)

@app.route('/api/data')
def get_data():
    df = load_data()
    
    # Get filters
    year = request.args.get('year', type=int)
    category = request.args.get('category')
    subcategory = request.args.get('subcategory')
    
    # Apply filters
    filtered_df = df.copy()
    if year:
        filtered_df = filtered_df[filtered_df['year'] == year]
    if category and category != 'all':
        filtered_df = filtered_df[filtered_df['category'] == category]
    if subcategory and subcategory != 'all':
        filtered_df = filtered_df[filtered_df['sub_category'] == subcategory]
    
    return create_dashboard_data(filtered_df)

def create_dashboard_data(df):
    if df.empty:
        return jsonify({'error': 'No data available'})
    
    # KPI Cards
    kpis = {
        'total_sales': float(df['sales'].sum()),
        'total_profit': float(df['profit'].sum()),
        'total_orders': int(len(df)),
        'avg_discount': float(df['discount'].mean() * 100)
    }
    
    # Top 10 Products by Sales
    top_sales = df.groupby('product_name')['sales'].sum().nlargest(10)
    
    # Top 10 Products by Profit  
    top_profit = df.groupby('product_name')['profit'].sum().nlargest(10)
    
    # Discount vs Profit (sample 1000 points for performance)
    sample_df = df.sample(min(1000, len(df))) if len(df) > 1000 else df
    
    # Average Discount per Category
    avg_discount_category = df.groupby('category')['discount'].mean() * 100
    
    # Profitability Analysis
    product_analysis = df.groupby('product_name').agg({
        'sales': 'sum',
        'profit': 'sum',
        'profit_margin': 'mean'
    }).reset_index()
    
    highest_profit = product_analysis.nlargest(5, 'profit')
    lowest_profit = product_analysis.nsmallest(5, 'profit')
    
    # High Sales Low Profit (top 20% sales, bottom 50% profit margin)
    sales_threshold = product_analysis['sales'].quantile(0.8)
    margin_threshold = product_analysis['profit_margin'].quantile(0.5)
    high_sales_low_profit = product_analysis[
        (product_analysis['sales'] >= sales_threshold) & 
        (product_analysis['profit_margin'] <= margin_threshold)
    ].nlargest(10, 'sales')
    
    # Time Analysis
    monthly_trends = df.groupby('month_year').agg({
        'sales': 'sum',
        'profit': 'sum'
    }).reset_index()
    monthly_trends['month_year_str'] = monthly_trends['month_year'].astype(str)
    
    # Insights
    insights = generate_insights(df)
    
    return jsonify({
        'kpis': kpis,
        'top_sales': {
            'products': top_sales.index.tolist(),
            'values': top_sales.values.tolist()
        },
        'top_profit': {
            'products': top_profit.index.tolist(),
            'values': top_profit.values.tolist()
        },
        'discount_profit_scatter': {
            'discount': (sample_df['discount'] * 100).tolist(),
            'profit': sample_df['profit'].tolist(),
            'product': sample_df['product_name'].tolist()
        },
        'avg_discount_category': {
            'categories': avg_discount_category.index.tolist(),
            'values': avg_discount_category.values.tolist()
        },
        'highest_profit': highest_profit.to_dict('records'),
        'lowest_profit': lowest_profit.to_dict('records'),
        'high_sales_low_profit': high_sales_low_profit.to_dict('records'),
        'monthly_trends': {
            'months': monthly_trends['month_year_str'].tolist(),
            'sales': monthly_trends['sales'].tolist(),
            'profit': monthly_trends['profit'].tolist()
        },
        'insights': insights
    })

@app.route('/api/subcategories/<category>')
def get_subcategories(category):
    df = load_data()
    if category == 'all':
        subcategories = []
    else:
        subcategories = sorted(df[df['category'] == category]['sub_category'].dropna().unique())
    return jsonify(subcategories)

def generate_insights(df):
    insights = []
    
    try:
        # Most profitable category
        category_profit = df.groupby('category')['profit'].sum()
        most_profitable_category = category_profit.idxmax()
        insights.append(f"Kategori paling menguntungkan: {most_profitable_category}")
        
        # Most profitable product
        product_profit = df.groupby('product_name')['profit'].sum()
        most_profitable_product = product_profit.idxmax()
        insights.append(f"Produk paling menguntungkan: {most_profitable_product}")
        
        # Biggest loss product
        biggest_loss_product = product_profit.idxmin()
        if product_profit.min() < 0:
            insights.append(f"Produk dengan kerugian terbesar: {biggest_loss_product}")
        
        # Highest discount category
        category_discount = df.groupby('category')['discount'].mean()
        highest_discount_category = category_discount.idxmax()
        insights.append(f"Kategori dengan rata-rata diskon tertinggi: {highest_discount_category} ({category_discount.max()*100:.1f}%)")
        
    except Exception as e:
        insights.append("Error generating insights")
    
    return insights

if __name__ == '__main__':
    app.run(debug=True, port=5000)