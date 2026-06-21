from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
from datetime import datetime
import json
import plotly.graph_objs as go
import plotly.utils
import plotly.express as px

app = Flask(__name__)

# Global variables untuk cache data
orders_data = None
products_data = None
customers_data = None
locations_data = None
merged_data = None

def load_data():
    """Load dan merge semua data CSV"""
    global orders_data, products_data, customers_data, locations_data, merged_data
    
    if merged_data is None:
        print("Loading data...")
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
        
        # Calculate profit margin
        merged_data['profit_margin'] = (merged_data['profit'] / merged_data['sales']) * 100
        merged_data['profit_margin'] = merged_data['profit_margin'].fillna(0)
        
        print(f"Data loaded: {len(merged_data)} records")
    
    return merged_data

def apply_filters(df, filters):
    """Apply filters to dataframe"""
    filtered_df = df.copy()
    
    for key, value in filters.items():
        if value and value != 'All':
            if key == 'year':
                filtered_df = filtered_df[filtered_df['year'] == int(value)]
            elif key == 'quarter':
                filtered_df = filtered_df[filtered_df['quarter'] == int(value)]
            elif key == 'month':
                filtered_df = filtered_df[filtered_df['month'] == int(value)]
            else:
                filtered_df = filtered_df[filtered_df[key] == value]
    
    return filtered_df

@app.route('/')
def dashboard():
    return render_template('profitability_dashboard.html')

@app.route('/api/filters')
def get_filters():
    """Get all available filter values"""
    df = load_data()
    
    filters = {
        'regions': sorted(df['region'].unique().tolist()),
        'countries': sorted(df['country'].unique().tolist()),
        'cities': sorted(df['city'].unique().tolist()),
        'categories': sorted(df['category'].unique().tolist()),
        'sub_categories': sorted(df['sub_category'].unique().tolist()),
        'products': sorted(df['product_name'].unique().tolist()),
        'segments': sorted(df['segment'].unique().tolist()),
        'years': sorted(df['year'].unique().tolist()),
        'quarters': [1, 2, 3, 4],
        'months': list(range(1, 13))
    }
    
    return jsonify(filters)

@app.route('/api/data')
def get_data():
    """Get filtered data and KPIs"""
    df = load_data()
    
    # Get filters from request
    filters = {}
    for key in ['region', 'country', 'city', 'category', 'sub_category', 'product_name', 'segment', 'year', 'quarter', 'month']:
        filters[key] = request.args.get(key)
    
    # Apply filters
    filtered_df = apply_filters(df, filters)
    
    # Calculate KPIs
    total_sales = filtered_df['sales'].sum()
    total_profit = filtered_df['profit'].sum()
    avg_profit_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
    total_orders = len(filtered_df)
    
    # Geographic analysis
    geo_analysis = filtered_df.groupby(['region', 'country', 'city']).agg({
        'sales': 'sum',
        'profit': 'sum',
        'order_id': 'count'
    }).reset_index()
    geo_analysis['profit_margin'] = (geo_analysis['profit'] / geo_analysis['sales'] * 100).fillna(0)
    
    # Product analysis
    product_analysis = filtered_df.groupby(['category', 'sub_category', 'product_name']).agg({
        'sales': 'sum',
        'profit': 'sum',
        'order_id': 'count'
    }).reset_index()
    product_analysis['profit_margin'] = (product_analysis['profit'] / product_analysis['sales'] * 100).fillna(0)
    
    # Top/Bottom products
    top_products = product_analysis.nlargest(10, 'profit')[['product_name', 'profit', 'sales']].to_dict('records')
    bottom_products = product_analysis.nsmallest(10, 'profit')[['product_name', 'profit', 'sales']].to_dict('records')
    
    # Time analysis
    time_analysis = filtered_df.groupby(['year', 'quarter', 'month']).agg({
        'sales': 'sum',
        'profit': 'sum',
        'order_id': 'count'
    }).reset_index()
    
    # Customer segment analysis
    segment_analysis = filtered_df.groupby('segment').agg({
        'sales': 'sum',
        'profit': 'sum',
        'order_id': 'count'
    }).reset_index()
    segment_analysis['profit_margin'] = (segment_analysis['profit'] / segment_analysis['sales'] * 100).fillna(0)
    
    # Category analysis
    category_analysis = filtered_df.groupby('category').agg({
        'sales': 'sum',
        'profit': 'sum',
        'order_id': 'count'
    }).reset_index()
    category_analysis['profit_margin'] = (category_analysis['profit'] / category_analysis['sales'] * 100).fillna(0)
    
    # Discount analysis
    discount_analysis = filtered_df.groupby('category').agg({
        'discount': 'mean',
        'profit': 'sum'
    }).reset_index()
    
    # Generate insights
    insights = generate_insights(filtered_df, category_analysis, geo_analysis, product_analysis)
    
    return jsonify({
        'kpis': {
            'total_sales': round(total_sales, 2),
            'total_profit': round(total_profit, 2),
            'profit_margin': round(avg_profit_margin, 2),
            'total_orders': total_orders
        },
        'geographic': geo_analysis.to_dict('records'),
        'products': product_analysis.to_dict('records'),
        'top_products': top_products,
        'bottom_products': bottom_products,
        'time_series': time_analysis.to_dict('records'),
        'segments': segment_analysis.to_dict('records'),
        'categories': category_analysis.to_dict('records'),
        'discounts': discount_analysis.to_dict('records'),
        'insights': insights
    })

def generate_insights(df, category_df, geo_df, product_df):
    """Generate automatic insights"""
    insights = {}
    
    if not df.empty:
        # Most profitable region
        if not geo_df.empty:
            top_region = geo_df.loc[geo_df['profit'].idxmax()]
            insights['most_profitable_region'] = f"{top_region['region']} (${top_region['profit']:,.0f})"
        
        # Most profitable category
        if not category_df.empty:
            top_category = category_df.loc[category_df['profit'].idxmax()]
            insights['most_profitable_category'] = f"{top_category['category']} (${top_category['profit']:,.0f})"
        
        # Most profitable product
        if not product_df.empty:
            top_product = product_df.loc[product_df['profit'].idxmax()]
            insights['most_profitable_product'] = f"{top_product['product_name'][:50]}... (${top_product['profit']:,.0f})"
        
        # Least profitable product
        if not product_df.empty:
            bottom_product = product_df.loc[product_df['profit'].idxmin()]
            insights['least_profitable_product'] = f"{bottom_product['product_name'][:50]}... (${bottom_product['profit']:,.0f})"
        
        # Best performing segment
        segment_profit = df.groupby('segment')['profit'].sum()
        if not segment_profit.empty:
            best_segment = segment_profit.idxmax()
            insights['best_segment'] = f"{best_segment} (${segment_profit[best_segment]:,.0f})"
    
    return insights

@app.route('/api/charts/geographic_map')
def geographic_map():
    """Generate geographic heatmap"""
    df = load_data()
    
    # Get filters
    filters = {}
    for key in ['region', 'country', 'city', 'category', 'sub_category', 'segment', 'year']:
        filters[key] = request.args.get(key)
    
    filtered_df = apply_filters(df, filters)
    
    # Group by country for map
    country_data = filtered_df.groupby('country').agg({
        'sales': 'sum',
        'profit': 'sum',
        'order_id': 'count'
    }).reset_index()
    
    metric = request.args.get('metric', 'profit')
    
    fig = px.choropleth(
        country_data,
        locations='country',
        color=metric,
        locationmode='country names',
        hover_data=['sales', 'profit', 'order_id'],
        color_continuous_scale='RdYlBu_r' if metric == 'profit' else 'Blues',
        title=f'{metric.title()} by Country'
    )
    
    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=True),
        title={'x': 0.5}
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.route('/api/charts/profit_by_category')
def profit_by_category():
    """Profit by category chart"""
    df = load_data()
    
    filters = {}
    for key in ['region', 'country', 'segment', 'year']:
        filters[key] = request.args.get(key)
    
    filtered_df = apply_filters(df, filters)
    
    category_data = filtered_df.groupby('category').agg({
        'profit': 'sum',
        'sales': 'sum'
    }).reset_index()
    
    fig = px.bar(
        category_data,
        x='category',
        y='profit',
        title='Profit by Category',
        color='profit',
        color_continuous_scale='RdYlGn'
    )
    
    fig.update_layout(showlegend=False)
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.route('/api/charts/time_trends')
def time_trends():
    """Time series trends"""
    df = load_data()
    
    filters = {}
    for key in ['region', 'category', 'segment']:
        filters[key] = request.args.get(key)
    
    filtered_df = apply_filters(df, filters)
    
    # Monthly trends
    monthly_data = filtered_df.groupby(['year', 'month']).agg({
        'sales': 'sum',
        'profit': 'sum'
    }).reset_index()
    
    monthly_data['date'] = pd.to_datetime(monthly_data[['year', 'month']].assign(day=1))
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=monthly_data['date'],
        y=monthly_data['sales'],
        name='Sales',
        line=dict(color='blue')
    ))
    
    fig.add_trace(go.Scatter(
        x=monthly_data['date'],
        y=monthly_data['profit'],
        name='Profit',
        yaxis='y2',
        line=dict(color='green')
    ))
    
    fig.update_layout(
        title='Sales and Profit Trends',
        xaxis_title='Date',
        yaxis=dict(title='Sales', side='left'),
        yaxis2=dict(title='Profit', side='right', overlaying='y'),
        hovermode='x'
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.route('/api/charts/segment_analysis')
def segment_analysis():
    """Customer segment analysis"""
    df = load_data()
    
    filters = {}
    for key in ['region', 'category', 'year']:
        filters[key] = request.args.get(key)
    
    filtered_df = apply_filters(df, filters)
    
    segment_data = filtered_df.groupby('segment').agg({
        'profit': 'sum',
        'sales': 'sum',
        'order_id': 'count'
    }).reset_index()
    
    fig = px.pie(
        segment_data,
        values='profit',
        names='segment',
        title='Profit Distribution by Customer Segment'
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

if __name__ == '__main__':
    app.run(debug=True, port=5001)