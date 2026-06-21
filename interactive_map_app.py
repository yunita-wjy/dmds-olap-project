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
city_coordinates = None

def generate_city_coordinates():
    """Generate realistic coordinates untuk cities di dataset"""
    # Mapping koordinat yang realistis untuk beberapa kota utama
    coord_mapping = {
        # US Cities
        'New York City': {'lat': 40.7128, 'lon': -74.0060, 'country': 'United States'},
        'Los Angeles': {'lat': 34.0522, 'lon': -118.2437, 'country': 'United States'},
        'Chicago': {'lat': 41.8781, 'lon': -87.6298, 'country': 'United States'},
        'Houston': {'lat': 29.7604, 'lon': -95.3698, 'country': 'United States'},
        'Seattle': {'lat': 47.6062, 'lon': -122.3321, 'country': 'United States'},
        'Philadelphia': {'lat': 39.9526, 'lon': -75.1652, 'country': 'United States'},
        'San Francisco': {'lat': 37.7749, 'lon': -122.4194, 'country': 'United States'},
        
        # European Cities  
        'London': {'lat': 51.5074, 'lon': -0.1278, 'country': 'United Kingdom'},
        'Paris': {'lat': 48.8566, 'lon': 2.3522, 'country': 'France'},
        'Berlin': {'lat': 52.5200, 'lon': 13.4050, 'country': 'Germany'},
        'Madrid': {'lat': 40.4168, 'lon': -3.7038, 'country': 'Spain'},
        'Rome': {'lat': 41.9028, 'lon': 12.4964, 'country': 'Italy'},
        
        # Asian Cities
        'Tokyo': {'lat': 35.6762, 'lon': 139.6503, 'country': 'Japan'},
        'Beijing': {'lat': 39.9042, 'lon': 116.4074, 'country': 'China'},
        'Shanghai': {'lat': 31.2304, 'lon': 121.4737, 'country': 'China'},
        'Mumbai': {'lat': 19.0760, 'lon': 72.8777, 'country': 'India'},
        'Delhi': {'lat': 28.7041, 'lon': 77.1025, 'country': 'India'},
        'Singapore': {'lat': 1.3521, 'lon': 103.8198, 'country': 'Singapore'},
        
        # Other regions
        'Sydney': {'lat': -33.8688, 'lon': 151.2093, 'country': 'Australia'},
        'Melbourne': {'lat': -37.8136, 'lon': 144.9631, 'country': 'Australia'},
        'Toronto': {'lat': 43.6532, 'lon': -79.3832, 'country': 'Canada'},
        'Vancouver': {'lat': 49.2827, 'lon': -123.1207, 'country': 'Canada'},
        'São Paulo': {'lat': -23.5558, 'lon': -46.6396, 'country': 'Brazil'},
        'Mexico City': {'lat': 19.4326, 'lon': -99.1332, 'country': 'Mexico'},
    }
    
    return coord_mapping

def load_data():
    """Load dan process semua data dengan geographic coordinates"""
    global merged_data, city_coordinates
    
    if merged_data is None:
        print("Loading profitability data...")
        
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
        
        # Calculate advanced metrics
        merged_data['profit_margin'] = np.where(merged_data['sales'] > 0, 
                                              (merged_data['profit'] / merged_data['sales']) * 100, 0)
        merged_data['is_profitable'] = merged_data['profit'] > 0
        merged_data['revenue_per_order'] = merged_data['sales']
        
        # High sales but low profit detection
        merged_data['is_high_sales_low_profit'] = (
            (merged_data['sales'] > merged_data['sales'].quantile(0.75)) & 
            (merged_data['profit_margin'] < merged_data['profit_margin'].quantile(0.25))
        )
        
        # Performance score calculation (0-100)
        merged_data['performance_score'] = calculate_performance_score(merged_data)
        
        # Add coordinates
        city_coordinates = generate_city_coordinates()
        add_coordinates_to_data()
        
        print(f"✅ Data loaded: {len(merged_data)} records")
        print(f"🏙️ Cities with coordinates: {len(city_coordinates)}")

def add_coordinates_to_data():
    """Add latitude and longitude to cities"""
    global merged_data
    
    # Add coordinates based on city mapping
    merged_data['latitude'] = merged_data['city'].map(lambda x: 
        city_coordinates.get(x, {}).get('lat', np.random.uniform(-60, 60)))
    merged_data['longitude'] = merged_data['city'].map(lambda x: 
        city_coordinates.get(x, {}).get('lon', np.random.uniform(-180, 180)))

def calculate_performance_score(df):
    """Calculate business performance score (0-100) untuk setiap transaksi"""
    # Normalisasi profit margin ke 0-40 points
    profit_score = np.clip((df['profit_margin'] + 50) / 1.5, 0, 40)
    
    # Sales volume score (0-30 points)  
    sales_normalized = (df['sales'] - df['sales'].min()) / (df['sales'].max() - df['sales'].min())
    sales_score = sales_normalized * 30
    
    # Efficiency score (0-30 points) - high sales with good margin
    efficiency_score = np.where(
        (df['sales'] > df['sales'].median()) & (df['profit_margin'] > 5), 30,
        np.where(df['profit_margin'] > 0, 15, 0)
    )
    
    # Penalty untuk high discount
    discount_penalty = np.clip(df['discount'] * 20, 0, 10)
    
    total_score = profit_score + sales_score + efficiency_score - discount_penalty
    return np.clip(total_score, 0, 100)

def analyze_city_performance(df, city_name):
    """Detailed analysis untuk city tertentu"""
    city_data = df[df['city'] == city_name]
    
    if city_data.empty:
        return {}
    
    # Basic metrics
    total_sales = city_data['sales'].sum()
    total_profit = city_data['profit'].sum()
    total_orders = len(city_data)
    avg_profit_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
    avg_performance = city_data['performance_score'].mean()
    
    # Top categories
    top_categories = city_data.groupby('category').agg({
        'sales': 'sum',
        'profit': 'sum',
        'order_id': 'count'
    }).sort_values('profit', ascending=False).head(3)
    
    # Top products
    top_products = city_data.groupby('product_name').agg({
        'sales': 'sum', 
        'profit': 'sum',
        'order_id': 'count'
    }).sort_values('profit', ascending=False).head(5)
    
    # Problem analysis
    high_sales_low_profit_count = len(city_data[city_data['is_high_sales_low_profit']])
    loss_orders = len(city_data[city_data['profit'] < 0])
    
    # Customer segments
    segment_analysis = city_data.groupby('segment').agg({
        'profit': 'sum',
        'sales': 'sum'
    }).sort_values('profit', ascending=False)
    
    # Discount analysis
    avg_discount = city_data['discount'].mean()
    high_discount_orders = len(city_data[city_data['discount'] > 0.3])
    
    return {
        'basic_metrics': {
            'city': city_name,
            'country': city_data['country'].iloc[0],
            'total_sales': round(total_sales, 2),
            'total_profit': round(total_profit, 2), 
            'profit_margin': round(avg_profit_margin, 2),
            'total_orders': total_orders,
            'avg_performance_score': round(avg_performance, 2)
        },
        'top_categories': top_categories.reset_index().to_dict('records'),
        'top_products': top_products.reset_index().to_dict('records'),
        'segments': segment_analysis.reset_index().to_dict('records'),
        'problems': {
            'high_sales_low_profit': high_sales_low_profit_count,
            'loss_orders': loss_orders,
            'avg_discount': round(avg_discount * 100, 2),
            'high_discount_orders': high_discount_orders
        },
        'insights': generate_city_insights(city_data, avg_performance, avg_profit_margin)
    }

def generate_city_insights(city_data, performance_score, profit_margin):
    """Generate business insights untuk city"""
    insights = []
    
    if performance_score > 75:
        insights.append("🟢 Excellent performance - Top performing city")
    elif performance_score > 50:
        insights.append("🟡 Good performance - Above average results") 
    else:
        insights.append("🔴 Poor performance - Needs attention")
    
    if profit_margin > 15:
        insights.append("💰 High profitability - Efficient operations")
    elif profit_margin < 5:
        insights.append("⚠️ Low profitability - Cost optimization needed")
    
    high_discount_rate = (city_data['discount'] > 0.3).mean()
    if high_discount_rate > 0.3:
        insights.append("📉 High discount dependency - Review pricing strategy")
    
    loss_rate = (city_data['profit'] < 0).mean()
    if loss_rate > 0.2:
        insights.append("🚨 High loss rate - Investigate loss-making products")
    
    return insights

@app.route('/')
def index():
    return render_template('interactive_dashboard.html')

@app.route('/api/map-data')
def map_data():
    """Data untuk map visualization"""
    df = merged_data.copy()
    
    # Aggregate by city untuk map
    city_summary = df.groupby(['city', 'country', 'region']).agg({
        'sales': 'sum',
        'profit': 'sum', 
        'profit_margin': 'mean',
        'performance_score': 'mean',
        'order_id': 'count',
        'latitude': 'first',
        'longitude': 'first'
    }).reset_index()
    
    city_summary['profit_margin'] = city_summary['profit_margin'].round(2)
    city_summary['performance_score'] = city_summary['performance_score'].round(1)
    
    # Add size untuk bubble map
    city_summary['bubble_size'] = np.sqrt(city_summary['sales']) / 10
    
    return jsonify(city_summary.to_dict('records'))

@app.route('/api/city-details')
def city_details():
    """Detailed analysis ketika city diklik di map"""
    city_name = request.args.get('city', '').strip()
    
    if not city_name:
        return jsonify({"error": "City name required"}), 400
    
    analysis = analyze_city_performance(merged_data, city_name)
    
    if not analysis:
        return jsonify({"error": f"No data found for city: {city_name}"}), 404
    
    return jsonify(analysis)

@app.route('/api/regional-comparison')
def regional_comparison():
    """Comparison analysis antar region"""
    metric = request.args.get('metric', 'profit')
    
    regional_data = merged_data.groupby('region').agg({
        'sales': 'sum',
        'profit': 'sum',
        'profit_margin': 'mean', 
        'performance_score': 'mean',
        'order_id': 'count'
    }).reset_index()
    
    regional_data = regional_data.sort_values(metric, ascending=False)
    
    return jsonify({
        'data': regional_data.to_dict('records'),
        'best_region': regional_data.iloc[0]['region'],
        'worst_region': regional_data.iloc[-1]['region']
    })

@app.route('/api/performance-clusters')
def performance_clusters():
    """Cluster cities berdasarkan performance"""
    city_performance = merged_data.groupby('city').agg({
        'performance_score': 'mean',
        'profit_margin': 'mean',
        'sales': 'sum'
    }).reset_index()
    
    # Simple clustering berdasarkan performance score
    city_performance['cluster'] = pd.cut(
        city_performance['performance_score'],
        bins=[0, 40, 70, 100],
        labels=['Poor', 'Average', 'Excellent']
    )
    
    cluster_summary = city_performance.groupby('cluster').agg({
        'city': 'count',
        'performance_score': 'mean',
        'profit_margin': 'mean'
    }).reset_index()
    
    return jsonify({
        'clusters': cluster_summary.to_dict('records'),
        'cities': city_performance.to_dict('records')
    })

@app.route('/api/problem-cities')
def problem_cities():
    """Cities dengan performance issues"""
    city_problems = merged_data.groupby('city').agg({
        'profit': 'sum',
        'sales': 'sum',
        'profit_margin': 'mean',
        'performance_score': 'mean'
    }).reset_index()
    
    # Identify problem cities
    problem_cities = city_problems[
        (city_problems['profit_margin'] < 5) | 
        (city_problems['performance_score'] < 40)
    ].sort_values('performance_score')
    
    return jsonify(problem_cities.head(10).to_dict('records'))

@app.route('/api/cross-dimensional-map')
def cross_dimensional_map():
    """Cross dimensional analysis dengan geographic context"""
    dim1 = request.args.get('dim1', 'region')
    dim2 = request.args.get('dim2', 'category') 
    metric = request.args.get('metric', 'profit')
    
    cross_analysis = merged_data.groupby([dim1, dim2, 'city']).agg({
        'sales': 'sum',
        'profit': 'sum',
        'profit_margin': 'mean',
        'latitude': 'first',
        'longitude': 'first'
    }).reset_index()
    
    return jsonify(cross_analysis.to_dict('records'))

if __name__ == '__main__':
    load_data()
    app.run(debug=True, port=5003)