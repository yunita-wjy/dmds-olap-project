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
        location_df = pd.read_csv('data/location.csv')
        
        # Clean location data - remove rows with missing region or country
        location_df = location_df.dropna(subset=['region', 'country'])
        
        # Merge orders with products and location
        df = orders_df.merge(products_df, on='product_id', how='left')
        df = df.merge(location_df, on='location_id', how='left')
        
        # Remove rows where location merge failed
        df = df.dropna(subset=['region', 'country'])
        
        # Convert dates
        df['order_date'] = pd.to_datetime(df['order_date'])
        df['year'] = df['order_date'].dt.year
        df['month'] = df['order_date'].dt.month
        df['month_year'] = df['order_date'].dt.to_period('M')
        
        # Calculate profit margin
        df['profit_margin'] = (df['profit'] / df['sales']) * 100
        df['profit_margin'] = df['profit_margin'].replace([np.inf, -np.inf], 0)
        
        # Create discount ranges for analysis
        df['discount_range'] = pd.cut(df['discount'] * 100, 
                                    bins=[0, 10, 20, 30, 40, 100], 
                                    labels=['0-10%', '10-20%', '20-30%', '30-40%', '40%+'],
                                    include_lowest=True)
        
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
    regions = sorted(df['region'].dropna().unique()) if not df.empty else []
    countries = sorted(df['country'].dropna().unique()) if not df.empty else []
    
    return render_template('discount_profit_dashboard.html', 
                         years=years, 
                         categories=categories,
                         regions=regions,
                         countries=countries)

@app.route('/api/data')
def get_data():
    df = load_data()
    
    # Get filters
    year = request.args.get('year', type=int)
    category = request.args.get('category')
    subcategory = request.args.get('subcategory')
    region = request.args.get('region')
    country = request.args.get('country')
    
    # Apply filters
    filtered_df = df.copy()
    if year:
        filtered_df = filtered_df[filtered_df['year'] == year]
    if category and category != 'all':
        filtered_df = filtered_df[filtered_df['category'] == category]
    if subcategory and subcategory != 'all':
        filtered_df = filtered_df[filtered_df['sub_category'] == subcategory]
    if region and region != 'all':
        filtered_df = filtered_df[filtered_df['region'] == region]
    if country and country != 'all':
        filtered_df = filtered_df[filtered_df['country'] == country]
    
    return create_dashboard_data(filtered_df)

def create_dashboard_data(df):
    if df.empty:
        return jsonify({'error': 'No data available'})
    
    # Enhanced KPIs with Profit Margin
    total_sales = float(df['sales'].sum())
    total_profit = float(df['profit'].sum())
    profit_margin_pct = (total_profit / total_sales * 100) if total_sales > 0 else 0
    
    kpis = {
        'total_sales': total_sales,
        'total_profit': total_profit,
        'profit_margin': profit_margin_pct,
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
    
    # NEW: Profit by Discount Range Analysis
    profit_by_discount_range = df.groupby('discount_range').agg({
        'profit': ['mean', 'sum', 'count'],
        'sales': 'sum',
        'discount': 'mean'
    }).round(2)
    
    profit_by_discount_range.columns = ['avg_profit', 'total_profit', 'order_count', 'total_sales', 'avg_discount']
    profit_by_discount_range = profit_by_discount_range.reset_index()
    profit_by_discount_range['profit_margin'] = (profit_by_discount_range['total_profit'] / 
                                               profit_by_discount_range['total_sales'] * 100).round(2)
    
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
    
    # Enhanced Insights + Business Conclusions
    insights = generate_enhanced_insights(df, profit_by_discount_range)
    business_conclusions = generate_business_conclusions(df, profit_by_discount_range)
    
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
        'profit_by_discount_range': {
            'ranges': profit_by_discount_range['discount_range'].tolist(),
            'avg_profit': profit_by_discount_range['avg_profit'].tolist(),
            'total_profit': profit_by_discount_range['total_profit'].tolist(),
            'order_count': profit_by_discount_range['order_count'].tolist(),
            'profit_margin': profit_by_discount_range['profit_margin'].tolist()
        },
        'highest_profit': highest_profit.to_dict('records'),
        'lowest_profit': lowest_profit.to_dict('records'),
        'high_sales_low_profit': high_sales_low_profit.to_dict('records'),
        'monthly_trends': {
            'months': monthly_trends['month_year_str'].tolist(),
            'sales': monthly_trends['sales'].tolist(),
            'profit': monthly_trends['profit'].tolist()
        },
        'insights': insights,
        'business_conclusions': business_conclusions
    })

@app.route('/api/subcategories/<category>')
def get_subcategories(category):
    df = load_data()
    if category == 'all':
        subcategories = []
    else:
        subcategories = sorted(df[df['category'] == category]['sub_category'].dropna().unique())
    return jsonify(subcategories)

@app.route('/api/countries/<region>')
def get_countries(region):
    try:
        df = load_data()
        if df.empty:
            return jsonify([])
            
        if region == 'all':
            countries = sorted(df['country'].dropna().unique())
        else:
            # Filter by region and remove NaN values
            region_df = df[df['region'] == region]
            countries = sorted(region_df['country'].dropna().unique())
        
        # Convert to list
        countries_list = countries.tolist() if hasattr(countries, 'tolist') else list(countries)
        print(f"Region: {region}, Countries found: {len(countries_list)}, Countries: {countries_list[:5]}...")  # Debug
        return jsonify(countries_list)
        
    except Exception as e:
        print(f"Error in get_countries: {e}")
        return jsonify([])

def generate_enhanced_insights(df, profit_by_discount_range):
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
        
        # Discount range with highest profit
        best_discount_range = profit_by_discount_range.loc[profit_by_discount_range['avg_profit'].idxmax(), 'discount_range']
        best_avg_profit = profit_by_discount_range['avg_profit'].max()
        insights.append(f"Rentang diskon paling menguntungkan: {best_discount_range} (Avg Profit: ${best_avg_profit:,.2f})")
        
    except Exception as e:
        insights.append("Error generating insights")
    
    return insights

def generate_business_conclusions(df, profit_by_discount_range):
    conclusions = []
    
    try:
        # Analyze discount impact on profit
        correlation = df['discount'].corr(df['profit'])
        if correlation < -0.3:
            discount_impact = "NEGATIF KUAT"
        elif correlation < -0.1:
            discount_impact = "NEGATIF LEMAH"
        elif correlation > 0.1:
            discount_impact = "POSITIF"
        else:
            discount_impact = "TIDAK SIGNIFIKAN"
        
        conclusions.append(f"Pengaruh Discount terhadap Profit: {discount_impact} (Korelasi: {correlation:.3f})")
        
        # Find optimal discount range
        optimal_range = profit_by_discount_range.loc[profit_by_discount_range['avg_profit'].idxmax()]
        conclusions.append(f"Rentang Discount Optimal: {optimal_range['discount_range']} dengan rata-rata profit ${optimal_range['avg_profit']:,.2f}")
        
        # Find where profit starts declining significantly
        profit_decline_threshold = profit_by_discount_range['avg_profit'].max() * 0.7
        decline_ranges = profit_by_discount_range[profit_by_discount_range['avg_profit'] < profit_decline_threshold]
        if not decline_ranges.empty:
            first_decline = decline_ranges.iloc[0]['discount_range']
            conclusions.append(f"Profit mulai menurun signifikan pada rentang: {first_decline}")
        
        # Pricing strategy recommendation
        if optimal_range['discount_range'] in ['0-10%', '10-20%']:
            recommendation = "Strategi Low Discount - Pertahankan margin tinggi dengan diskon minimal"
        elif optimal_range['discount_range'] in ['20-30%']:
            recommendation = "Strategi Moderate Discount - Seimbangkan volume dan margin"
        else:
            recommendation = "Strategi High Volume - Fokus pada volume penjualan dengan margin tipis"
        
        conclusions.append(f"Rekomendasi Strategi: {recommendation}")
        
        # Profit margin insight
        overall_margin = (df['profit'].sum() / df['sales'].sum() * 100)
        best_margin = optimal_range['profit_margin']
        conclusions.append(f"Margin keseluruhan: {overall_margin:.1f}%, Margin optimal di rentang {optimal_range['discount_range']}: {best_margin:.1f}%")
        
    except Exception as e:
        conclusions.append("Error generating business conclusions")
    
    return conclusions

if __name__ == '__main__':
    app.run(debug=True, port=5001)