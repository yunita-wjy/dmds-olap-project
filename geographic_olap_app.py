from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
from datetime import datetime
import json

app = Flask(__name__)

# Global variables
merged_data = None

def load_data():
    """Load dan process data dengan koordinat geografis yang akurat"""
    global merged_data
    
    if merged_data is None:
        print("Loading geographic analysis data...")
        
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
        
        # Merge all data
        merged_data = orders_data.merge(products_data, on="product_id")
        merged_data = merged_data.merge(customers_data, on="customer_id") 
        merged_data = merged_data.merge(locations_data, on="location_id")
        
        # Calculate metrics
        merged_data['profit_margin'] = np.where(merged_data['sales'] > 0, 
                                              (merged_data['profit'] / merged_data['sales']) * 100, 0)
        merged_data['is_high_sales_low_profit'] = (
            (merged_data['sales'] > merged_data['sales'].quantile(0.75)) & 
            (merged_data['profit_margin'] < merged_data['profit_margin'].quantile(0.25))
        )
        
        # Add realistic coordinates
        add_realistic_coordinates()
        
        print(f"✅ Geographic data loaded: {len(merged_data)} records")

def add_realistic_coordinates():
    """Add realistic coordinates based on actual geographic data"""
    global merged_data
    
    # Real coordinates for major regions/countries
    region_coordinates = {
        'Central': {'lat': 39.8283, 'lon': -98.5795},  # US Center
        'East': {'lat': 40.7589, 'lon': -73.9851},     # New York area
        'South': {'lat': 31.3069, 'lon': -92.4426},    # Southern US
        'West': {'lat': 36.7783, 'lon': -119.4179},    # California area
    }
    
    country_coordinates = {
        'United States': {'lat': 39.8283, 'lon': -98.5795},
        'Canada': {'lat': 56.1304, 'lon': -106.3468},
        'Mexico': {'lat': 23.6345, 'lon': -102.5528},
        'United Kingdom': {'lat': 55.3781, 'lon': -3.4360},
        'Germany': {'lat': 51.1657, 'lon': 10.4515},
        'France': {'lat': 46.6034, 'lon': 1.8883},
        'Australia': {'lat': -25.2744, 'lon': 133.7751},
        'India': {'lat': 20.5937, 'lon': 78.9629},
        'China': {'lat': 35.8617, 'lon': 104.1954},
        'Japan': {'lat': 36.2048, 'lon': 138.2529},
        'Brazil': {'lat': -14.2350, 'lon': -51.9253},
        'South Korea': {'lat': 35.9078, 'lon': 127.7669},
    }
    
    city_coordinates = {
        'New York City': {'lat': 40.7128, 'lon': -74.0060},
        'Los Angeles': {'lat': 34.0522, 'lon': -118.2437},
        'Chicago': {'lat': 41.8781, 'lon': -87.6298},
        'Houston': {'lat': 29.7604, 'lon': -95.3698},
        'Philadelphia': {'lat': 39.9526, 'lon': -75.1652},
        'Phoenix': {'lat': 33.4484, 'lon': -112.0740},
        'San Antonio': {'lat': 29.4241, 'lon': -98.4936},
        'San Diego': {'lat': 32.7157, 'lon': -117.1611},
        'Dallas': {'lat': 32.7767, 'lon': -96.7970},
        'San Jose': {'lat': 37.3382, 'lon': -121.8863},
        'London': {'lat': 51.5074, 'lon': -0.1278},
        'Berlin': {'lat': 52.5200, 'lon': 13.4050},
        'Paris': {'lat': 48.8566, 'lon': 2.3522},
        'Tokyo': {'lat': 35.6762, 'lon': 139.6503},
        'Sydney': {'lat': -33.8688, 'lon': 151.2093},
        'Toronto': {'lat': 43.6532, 'lon': -79.3832},
        'Mumbai': {'lat': 19.0760, 'lon': 72.8777},
        'Shanghai': {'lat': 31.2304, 'lon': 121.4737},
        'Mexico City': {'lat': 19.4326, 'lon': -99.1332},
        'São Paulo': {'lat': -23.5558, 'lon': -46.6396},
    }
    
    # Assign coordinates with fallbacks
    def get_coordinates(row):
        city = row['city']
        country = row['country'] 
        region = row['region']
        
        # First try exact city match
        if city in city_coordinates:
            return city_coordinates[city]['lat'], city_coordinates[city]['lon']
        
        # Then try country with some random offset
        elif country in country_coordinates:
            base_lat = country_coordinates[country]['lat']
            base_lon = country_coordinates[country]['lon']
            # Add small random offset to avoid exact overlap
            offset_lat = np.random.uniform(-2, 2)
            offset_lon = np.random.uniform(-2, 2)
            return base_lat + offset_lat, base_lon + offset_lon
        
        # Finally try region (for US)
        elif region in region_coordinates:
            base_lat = region_coordinates[region]['lat']
            base_lon = region_coordinates[region]['lon']
            offset_lat = np.random.uniform(-3, 3)
            offset_lon = np.random.uniform(-3, 3)
            return base_lat + offset_lat, base_lon + offset_lon
        
        # Default fallback
        else:
            return np.random.uniform(-60, 60), np.random.uniform(-170, 170)
    
    coords = merged_data.apply(get_coordinates, axis=1, result_type='expand')
    merged_data['latitude'] = coords[0]
    merged_data['longitude'] = coords[1]

def get_hierarchical_data(level='region', parent=None, filters=None):
    """Get data for hierarchical drill-down analysis"""
    df = merged_data.copy()
    
    # Apply filters if any
    if filters:
        for key, value in filters.items():
            if value and value != 'All':
                df = df[df[key] == value]
    
    # Apply parent filter for drill-down
    if parent:
        if level == 'country':
            df = df[df['region'] == parent]
        elif level == 'city':
            df = df[df['country'] == parent]
        elif level == 'product':
            df = df[df['city'] == parent]
    
    # Group by appropriate level
    if level == 'region':
        group_cols = ['region']
    elif level == 'country':
        group_cols = ['region', 'country']
    elif level == 'city':
        group_cols = ['region', 'country', 'city']
    elif level == 'product':
        group_cols = ['region', 'country', 'city', 'category', 'sub_category', 'product_name']
    
    # Aggregate data
    agg_data = df.groupby(group_cols).agg({
        'sales': 'sum',
        'profit': 'sum',
        'order_id': 'count',
        'discount': 'mean',
        'latitude': 'first',
        'longitude': 'first'
    }).reset_index()
    
    # Calculate metrics
    agg_data['profit_margin'] = np.where(agg_data['sales'] > 0,
                                        (agg_data['profit'] / agg_data['sales']) * 100, 0)
    
    # Add performance indicators
    agg_data['performance_tier'] = pd.cut(
        agg_data['profit_margin'], 
        bins=[-float('inf'), 0, 5, 15, float('inf')],
        labels=['Loss', 'Poor', 'Good', 'Excellent']
    )
    
    return agg_data.to_dict('records')

def get_location_deep_analysis(level, location_name, filters=None):
    """Deep dive analysis untuk location tertentu"""
    df = merged_data.copy()
    
    # Apply filters
    if filters:
        for key, value in filters.items():
            if value and value != 'All':
                df = df[df[key] == value]
    
    # Filter by location
    if level == 'region':
        location_df = df[df['region'] == location_name]
    elif level == 'country':
        location_df = df[df['country'] == location_name]
    elif level == 'city':
        location_df = df[df['city'] == location_name]
    else:
        location_df = df
    
    if location_df.empty:
        return {'error': 'No data found'}
    
    # Basic metrics
    total_sales = location_df['sales'].sum()
    total_profit = location_df['profit'].sum()
    total_orders = len(location_df)
    avg_profit_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
    avg_discount = location_df['discount'].mean() * 100
    
    # Top performers
    top_category = location_df.groupby('category')['profit'].sum().idxmax()
    top_subcategory = location_df.groupby('sub_category')['profit'].sum().idxmax()
    top_product = location_df.groupby('product_name')['profit'].sum().idxmax()
    worst_product = location_df.groupby('product_name')['profit'].sum().idxmin()
    
    # Problem analysis
    high_sales_low_profit_count = len(location_df[location_df['is_high_sales_low_profit']])
    loss_orders = len(location_df[location_df['profit'] < 0])
    
    # Category breakdown
    category_breakdown = location_df.groupby('category').agg({
        'sales': 'sum',
        'profit': 'sum',
        'profit_margin': 'mean',
        'order_id': 'count'
    }).sort_values('profit', ascending=False).head(5).to_dict('records')
    
    # Product performance
    product_performance = location_df.groupby(['category', 'sub_category', 'product_name']).agg({
        'sales': 'sum',
        'profit': 'sum',
        'profit_margin': 'mean'
    }).reset_index()
    
    top_products = product_performance.nlargest(5, 'profit').to_dict('records')
    worst_products = product_performance.nsmallest(3, 'profit').to_dict('records')
    
    # Business insights
    insights = generate_location_insights(location_df, avg_profit_margin, avg_discount)
    
    return {
        'location_info': {
            'name': location_name,
            'level': level,
            'total_sales': round(total_sales, 2),
            'total_profit': round(total_profit, 2),
            'profit_margin': round(avg_profit_margin, 2),
            'total_orders': total_orders,
            'avg_discount': round(avg_discount, 2)
        },
        'key_performers': {
            'top_category': top_category,
            'top_subcategory': top_subcategory,
            'top_product': top_product,
            'worst_product': worst_product
        },
        'problems': {
            'high_sales_low_profit': high_sales_low_profit_count,
            'loss_orders': loss_orders,
            'problem_rate': round((high_sales_low_profit_count / total_orders * 100), 2) if total_orders > 0 else 0
        },
        'category_breakdown': category_breakdown,
        'product_analysis': {
            'top_products': top_products,
            'worst_products': worst_products
        },
        'insights': insights
    }

def generate_location_insights(df, profit_margin, avg_discount):
    """Generate actionable business insights"""
    insights = []
    
    # Performance insights
    if profit_margin > 15:
        insights.append({
            'type': 'success',
            'icon': 'fas fa-trophy',
            'title': 'High Profitability',
            'message': f'Excellent {profit_margin:.1f}% profit margin - well above industry average'
        })
    elif profit_margin < 5:
        insights.append({
            'type': 'danger', 
            'icon': 'fas fa-exclamation-triangle',
            'title': 'Low Profitability',
            'message': f'Poor {profit_margin:.1f}% profit margin - requires immediate attention'
        })
    
    # Discount insights
    if avg_discount > 25:
        insights.append({
            'type': 'warning',
            'icon': 'fas fa-percentage',
            'title': 'High Discount Dependency',
            'message': f'{avg_discount:.1f}% average discount may be hurting profitability'
        })
    elif avg_discount < 10:
        insights.append({
            'type': 'info',
            'icon': 'fas fa-dollar-sign',
            'title': 'Conservative Pricing',
            'message': f'Low {avg_discount:.1f}% discount rate - potential for strategic promotions'
        })
    
    # Volume insights
    loss_rate = (df['profit'] < 0).mean() * 100
    if loss_rate > 20:
        insights.append({
            'type': 'danger',
            'icon': 'fas fa-chart-line-down',
            'title': 'High Loss Rate',
            'message': f'{loss_rate:.1f}% of orders are loss-making - investigate product mix'
        })
    
    # Category concentration
    top_category_share = df.groupby('category')['sales'].sum().max() / df['sales'].sum() * 100
    if top_category_share > 60:
        insights.append({
            'type': 'warning',
            'icon': 'fas fa-chart-pie',
            'title': 'Category Concentration Risk',
            'message': f'Over-dependent on one category ({top_category_share:.1f}% of sales)'
        })
    
    return insights

@app.route('/')
def dashboard():
    return render_template('geographic_olap_dashboard.html')

@app.route('/api/geographic-data')
def geographic_data():
    """Get hierarchical geographic data for OLAP drilling"""
    level = request.args.get('level', 'region')
    parent = request.args.get('parent')
    
    # Get filters
    filters = {}
    for key in ['category', 'segment', 'year']:
        value = request.args.get(key)
        if value and value != 'All':
            filters[key] = value
    
    data = get_hierarchical_data(level, parent, filters)
    
    return jsonify({
        'level': level,
        'parent': parent,
        'data': data,
        'filters_applied': filters
    })

@app.route('/api/location-analysis')
def location_analysis():
    """Deep analysis untuk location yang dipilih"""
    level = request.args.get('level', 'region')
    location = request.args.get('location')
    
    if not location:
        return jsonify({'error': 'Location parameter required'}), 400
    
    # Get filters
    filters = {}
    for key in ['category', 'segment', 'year']:
        value = request.args.get(key)
        if value and value != 'All':
            filters[key] = value
    
    analysis = get_location_deep_analysis(level, location, filters)
    
    return jsonify(analysis)

@app.route('/api/drill-down-path')
def drill_down_path():
    """Get drill-down path untuk breadcrumb navigation"""
    region = request.args.get('region')
    country = request.args.get('country')  
    city = request.args.get('city')
    
    path = []
    
    if region:
        path.append({'level': 'region', 'name': region, 'active': not country})
    if country:
        path.append({'level': 'country', 'name': country, 'active': not city})
    if city:
        path.append({'level': 'city', 'name': city, 'active': True})
    
    return jsonify(path)

@app.route('/api/performance-comparison')
def performance_comparison():
    """Compare performance across different locations"""
    level = request.args.get('level', 'region')
    
    comparison_data = get_hierarchical_data(level)
    
    # Sort by profit and add rankings
    sorted_data = sorted(comparison_data, key=lambda x: x['profit'], reverse=True)
    
    for i, item in enumerate(sorted_data):
        item['rank'] = i + 1
        item['performance_score'] = min(100, max(0, item['profit_margin'] * 2))
    
    return jsonify({
        'level': level,
        'rankings': sorted_data[:10],  # Top 10
        'bottom_performers': sorted_data[-5:] if len(sorted_data) > 5 else []
    })

if __name__ == '__main__':
    load_data()
    app.run(debug=True, port=5004)