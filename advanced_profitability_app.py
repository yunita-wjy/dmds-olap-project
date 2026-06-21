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
merged_data = None

def load_data():
    """Load dan merge semua data CSV dengan optimasi"""
    global merged_data
    
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
        
        # Calculate advanced metrics
        merged_data['profit_margin'] = np.where(merged_data['sales'] > 0, 
                                              (merged_data['profit'] / merged_data['sales']) * 100, 0)
        merged_data['revenue_per_order'] = merged_data['sales']
        merged_data['is_profitable'] = merged_data['profit'] > 0
        merged_data['is_high_sales_low_profit'] = (
            (merged_data['sales'] > merged_data['sales'].quantile(0.75)) & 
            (merged_data['profit_margin'] < merged_data['profit_margin'].quantile(0.25))
        )
        
        # Discount buckets
        merged_data['discount_bucket'] = pd.cut(
            merged_data['discount'], 
            bins=[0, 0.1, 0.2, 0.3, 1.0], 
            labels=['0-10%', '10-20%', '20-30%', '30%+'],
            include_lowest=True
        )
        
        print(f"Data loaded: {len(merged_data)} records")
    
    return merged_data

def apply_filters(df, filters):
    """Apply filters dengan error handling"""
    filtered_df = df.copy()
    
    for key, value in filters.items():
        if value and value != 'All' and value != '':
            try:
                if key in ['year', 'quarter', 'month']:
                    filtered_df = filtered_df[filtered_df[key] == int(value)]
                else:
                    filtered_df = filtered_df[filtered_df[key] == value]
            except:
                continue
    
    return filtered_df

def analyze_location_details(df, location_type, location_value):
    """Analisis mendalam untuk lokasi tertentu"""
    if location_type == 'region':
        location_df = df[df['region'] == location_value]
    elif location_type == 'country':
        location_df = df[df['country'] == location_value]
    elif location_type == 'city':
        location_df = df[df['city'] == location_value]
    else:
        location_df = df
    
    if location_df.empty:
        return {}
    
    # Basic metrics
    total_sales = location_df['sales'].sum()
    total_profit = location_df['profit'].sum()
    total_orders = len(location_df)
    avg_profit_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
    
    # Top categories
    top_categories = location_df.groupby('category').agg({
        'sales': 'sum',
        'profit': 'sum',
        'order_id': 'count'
    }).sort_values('profit', ascending=False).head(3)
    
    # Top products  
    top_products = location_df.groupby('product_name').agg({
        'sales': 'sum',
        'profit': 'sum',
        'order_id': 'count'
    }).sort_values('profit', ascending=False).head(5)
    
    # Worst products
    worst_products = location_df.groupby('product_name').agg({
        'sales': 'sum',
        'profit': 'sum',
        'order_id': 'count'
    }).sort_values('profit', ascending=True).head(3)
    
    # Profitability analysis
    profitable_orders = location_df[location_df['profit'] > 0]
    loss_orders = location_df[location_df['profit'] <= 0]
    
    profitability_rate = len(profitable_orders) / len(location_df) * 100 if len(location_df) > 0 else 0
    
    # High sales low profit analysis
    high_sales_low_profit = location_df[location_df['is_high_sales_low_profit']]
    
    return {
        'basic_metrics': {
            'total_sales': round(total_sales, 2),
            'total_profit': round(total_profit, 2),
            'profit_margin': round(avg_profit_margin, 2),
            'total_orders': total_orders,
            'profitability_rate': round(profitability_rate, 2)
        },
        'top_categories': top_categories.reset_index().to_dict('records'),
        'top_products': top_products.reset_index().to_dict('records'),
        'worst_products': worst_products.reset_index().to_dict('records'),
        'problematic_sales': len(high_sales_low_profit),
        'loss_making_orders': len(loss_orders)
    }

def cross_dimensional_analysis(df, dim1, dim2):
    """Analisis cross-dimensional untuk insight mendalam"""
    cross_analysis = df.groupby([dim1, dim2]).agg({
        'sales': 'sum',
        'profit': 'sum',
        'profit_margin': 'mean',
        'order_id': 'count'
    }).reset_index()
    
    # Find best and worst combinations
    best_combo = cross_analysis.loc[cross_analysis['profit'].idxmax()] if not cross_analysis.empty else None
    worst_combo = cross_analysis.loc[cross_analysis['profit'].idxmin()] if not cross_analysis.empty else None
    
    return {
        'data': cross_analysis.to_dict('records'),
        'best_combination': best_combo.to_dict() if best_combo is not None else {},
        'worst_combination': worst_combo.to_dict() if worst_combo is not None else {}
    }

@app.route('/')
def dashboard():
    return render_template('advanced_dashboard.html')

@app.route('/api/filters')
def get_filters():
    """Get all available filter values"""
    df = load_data()
    
    filters = {
        'regions': ['All'] + sorted(df['region'].unique().tolist()),
        'countries': ['All'] + sorted(df['country'].unique().tolist()),
        'cities': ['All'] + sorted(df['city'].unique().tolist()),
        'categories': ['All'] + sorted(df['category'].unique().tolist()),
        'sub_categories': ['All'] + sorted(df['sub_category'].unique().tolist()),
        'segments': ['All'] + sorted(df['segment'].unique().tolist()),
        'years': ['All'] + sorted(df['year'].unique().tolist()),
        'ship_modes': ['All'] + sorted(df['ship_mode'].unique().tolist())
    }
    
    return jsonify(filters)

@app.route('/api/location_details')
def get_location_details():
    """Get detailed analysis for specific location"""
    df = load_data()
    
    location_type = request.args.get('type', 'region')
    location_value = request.args.get('value', '')
    
    # Apply current filters first
    filters = {}
    for key in ['region', 'country', 'city', 'category', 'sub_category', 'segment', 'year']:
        filters[key] = request.args.get(key)
    
    filtered_df = apply_filters(df, filters)
    
    # Get location analysis
    analysis = analyze_location_details(filtered_df, location_type, location_value)
    
    return jsonify(analysis)

@app.route('/api/data')
def get_data():
    """Get filtered data dan KPIs dengan analisis mendalam"""
    df = load_data()
    
    # Get filters from request
    filters = {}
    for key in ['region', 'country', 'city', 'category', 'sub_category', 'segment', 'year', 'quarter', 'month']:
        filters[key] = request.args.get(key)
    
    # Apply filters
    filtered_df = apply_filters(df, filters)
    
    if filtered_df.empty:
        return jsonify({'error': 'No data found for selected filters'})
    
    # Calculate advanced KPIs
    total_sales = filtered_df['sales'].sum()
    total_profit = filtered_df['profit'].sum()
    avg_profit_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
    total_orders = len(filtered_df)
    
    # Profitability analysis
    profitable_orders = len(filtered_df[filtered_df['profit'] > 0])
    loss_orders = len(filtered_df[filtered_df['profit'] <= 0])
    profitability_rate = (profitable_orders / total_orders * 100) if total_orders > 0 else 0
    
    # High sales but low profit analysis
    high_sales_low_profit_count = len(filtered_df[filtered_df['is_high_sales_low_profit']])
    
    # Geographic analysis with detailed insights
    geo_analysis = filtered_df.groupby(['region', 'country', 'city']).agg({
        'sales': 'sum',
        'profit': 'sum',
        'profit_margin': 'mean',
        'order_id': 'count'
    }).reset_index()
    
    # Product analysis berdasarkan filter aktif
    product_analysis = filtered_df.groupby(['category', 'sub_category', 'product_name']).agg({
        'sales': 'sum',
        'profit': 'sum',
        'profit_margin': 'mean',
        'order_id': 'count'
    }).reset_index()
    
    # Context-aware top/bottom products
    top_products = product_analysis.nlargest(10, 'profit')[['product_name', 'profit', 'sales', 'profit_margin']].to_dict('records')
    bottom_products = product_analysis.nsmallest(10, 'profit')[['product_name', 'profit', 'sales', 'profit_margin']].to_dict('records')
    
    # High sales low profit products
    high_sales_low_profit_products = filtered_df[filtered_df['is_high_sales_low_profit']].groupby('product_name').agg({
        'sales': 'sum',
        'profit': 'sum',
        'profit_margin': 'mean'
    }).sort_values('sales', ascending=False).head(5).reset_index().to_dict('records')
    
    # Discount analysis
    discount_analysis = filtered_df.groupby('discount_bucket').agg({
        'sales': 'sum',
        'profit': 'sum',
        'profit_margin': 'mean',
        'order_id': 'count'
    }).reset_index()
    
    # Cross-dimensional insights
    region_category = cross_dimensional_analysis(filtered_df, 'region', 'category')
    category_segment = cross_dimensional_analysis(filtered_df, 'category', 'segment')
    
    # Loss analysis
    loss_analysis = filtered_df[filtered_df['profit'] < 0].groupby('category').agg({
        'profit': 'sum',
        'sales': 'sum',
        'order_id': 'count'
    }).sort_values('profit').reset_index().to_dict('records')
    
    # Generate advanced insights
    insights = generate_advanced_insights(filtered_df, geo_analysis, product_analysis)
    
    return jsonify({
        'kpis': {
            'total_sales': round(total_sales, 2),
            'total_profit': round(total_profit, 2),
            'profit_margin': round(avg_profit_margin, 2),
            'total_orders': total_orders,
            'profitability_rate': round(profitability_rate, 2),
            'loss_orders': loss_orders,
            'high_sales_low_profit_count': high_sales_low_profit_count
        },
        'geographic': geo_analysis.to_dict('records'),
        'products': {
            'top_products': top_products,
            'bottom_products': bottom_products,
            'high_sales_low_profit': high_sales_low_profit_products
        },
        'discount_analysis': discount_analysis.to_dict('records'),
        'cross_dimensional': {
            'region_category': region_category,
            'category_segment': category_segment
        },
        'loss_analysis': loss_analysis,
        'insights': insights,
        'filter_context': get_active_filters_text(filters)
    })

def generate_advanced_insights(df, geo_df, product_df):
    """Generate advanced business insights"""
    insights = {}
    
    if df.empty:
        return insights
    
    # Performance insights
    if not geo_df.empty:
        best_region = geo_df.loc[geo_df['profit'].idxmax()]
        worst_region = geo_df.loc[geo_df['profit'].idxmin()]
        
        insights['best_location'] = f"{best_region['city']}, {best_region['country']} (${best_region['profit']:,.0f})"
        insights['worst_location'] = f"{worst_region['city']}, {worst_region['country']} (${worst_region['profit']:,.0f})"
    
    # Problem identification
    high_sales_low_profit = len(df[df['is_high_sales_low_profit']])
    total_orders = len(df)
    problem_rate = (high_sales_low_profit / total_orders * 100) if total_orders > 0 else 0
    
    insights['efficiency_issue'] = f"{high_sales_low_profit} orders ({problem_rate:.1f}%) have high sales but low profit"
    
    # Profitability by category
    category_profit = df.groupby('category')['profit_margin'].mean().sort_values(ascending=False)
    if not category_profit.empty:
        insights['most_efficient_category'] = f"{category_profit.index[0]} ({category_profit.iloc[0]:.1f}% margin)"
        insights['least_efficient_category'] = f"{category_profit.index[-1]} ({category_profit.iloc[-1]:.1f}% margin)"
    
    # Discount impact
    discount_impact = df.groupby('discount_bucket').agg({
        'profit_margin': 'mean',
        'order_id': 'count'
    }).sort_values('profit_margin', ascending=False)
    
    if not discount_impact.empty:
        insights['optimal_discount_range'] = discount_impact.index[0]
    
    # Loss analysis
    loss_orders = df[df['profit'] < 0]
    if not loss_orders.empty:
        biggest_loss_category = loss_orders.groupby('category')['profit'].sum().idxmin()
        insights['biggest_loss_source'] = biggest_loss_category
    
    return insights

def get_active_filters_text(filters):
    """Generate human readable filter description"""
    active_filters = []
    for key, value in filters.items():
        if value and value != 'All' and value != '':
            active_filters.append(f"{key.title()}: {value}")
    
    return ", ".join(active_filters) if active_filters else "All Data"

@app.route('/api/charts/geographic_map_detailed')
def geographic_map_detailed():
    """Enhanced geographic map dengan detailed info"""
    df = load_data()
    
    # Get filters
    filters = {}
    for key in ['category', 'segment', 'year']:
        filters[key] = request.args.get(key)
    
    filtered_df = apply_filters(df, filters)
    
    # City level analysis untuk detailed map
    city_data = filtered_df.groupby(['city', 'country', 'region']).agg({
        'sales': 'sum',
        'profit': 'sum',
        'profit_margin': 'mean',
        'order_id': 'count'
    }).reset_index()
    
    # Add geographical coordinates (simplified - in real app use proper geocoding)
    city_data['lat'] = np.random.uniform(-60, 70, len(city_data))
    city_data['lon'] = np.random.uniform(-180, 180, len(city_data))
    
    metric = request.args.get('metric', 'profit')
    
    # Create enhanced scatter map
    fig = px.scatter_mapbox(
        city_data,
        lat='lat',
        lon='lon',
        size='sales',
        color=metric,
        hover_data=['city', 'country', 'sales', 'profit', 'profit_margin', 'order_id'],
        color_continuous_scale='RdYlBu_r' if metric == 'profit' else 'Blues',
        mapbox_style='open-street-map',
        title=f'{metric.title()} by City',
        zoom=1
    )
    
    fig.update_layout(height=500)
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.route('/api/charts/cross_dimensional')
def cross_dimensional_chart():
    """Cross dimensional analysis heatmap"""
    df = load_data()
    
    dim1 = request.args.get('dim1', 'region')
    dim2 = request.args.get('dim2', 'category')
    metric = request.args.get('metric', 'profit')
    
    # Apply filters
    filters = {}
    for key in ['year', 'segment']:
        filters[key] = request.args.get(key)
    
    filtered_df = apply_filters(df, filters)
    
    # Create pivot for heatmap
    pivot_data = filtered_df.pivot_table(
        values=metric,
        index=dim1,
        columns=dim2,
        aggfunc='sum',
        fill_value=0
    )
    
    fig = px.imshow(
        pivot_data,
        title=f'{metric.title()} by {dim1.title()} × {dim2.title()}',
        color_continuous_scale='RdYlBu_r' if metric == 'profit' else 'Blues'
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.route('/api/charts/profit_margin_analysis')
def profit_margin_analysis():
    """Detailed profit margin analysis"""
    df = load_data()
    
    # Apply filters
    filters = {}
    for key in ['region', 'category', 'year']:
        filters[key] = request.args.get(key)
    
    filtered_df = apply_filters(df, filters)
    
    # Profit margin by category
    margin_analysis = filtered_df.groupby('category').agg({
        'profit_margin': 'mean',
        'sales': 'sum',
        'profit': 'sum'
    }).reset_index()
    
    fig = px.scatter(
        margin_analysis,
        x='sales',
        y='profit_margin',
        size='profit',
        color='category',
        title='Sales vs Profit Margin by Category',
        labels={'profit_margin': 'Profit Margin (%)', 'sales': 'Total Sales'}
    )
    
    # Add quadrant lines
    median_sales = margin_analysis['sales'].median()
    median_margin = margin_analysis['profit_margin'].median()
    
    fig.add_hline(y=median_margin, line_dash="dash", line_color="gray")
    fig.add_vline(x=median_sales, line_dash="dash", line_color="gray")
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

@app.route('/api/charts/discount_profit_scatter')
def discount_profit_scatter():
    """Discount vs Profit scatter plot analysis"""
    df = load_data()
    
    # Apply filters
    filters = {}
    for key in ['region', 'category', 'year']:
        filters[key] = request.args.get(key)
    
    filtered_df = apply_filters(df, filters)
    
    # Sample data untuk performance (take every 10th row)
    sample_df = filtered_df.iloc[::10].copy()
    
    fig = px.scatter(
        sample_df,
        x='discount',
        y='profit',
        color='category',
        size='sales',
        title='Discount vs Profit Analysis',
        labels={'discount': 'Discount Rate', 'profit': 'Profit ($)'}
    )
    
    # Add trend line
    fig.add_scatter(
        x=sample_df['discount'],
        y=np.poly1d(np.polyfit(sample_df['discount'], sample_df['profit'], 1))(sample_df['discount']),
        mode='lines',
        name='Trend',
        line=dict(color='red', dash='dash')
    )
    
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

if __name__ == '__main__':
    app.run(debug=True, port=5002)