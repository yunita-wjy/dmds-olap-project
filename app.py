from flask import Flask, render_template, jsonify, request
import pandas as pd
import numpy as np
from scipy import stats
import mysql.connector
import json
import plotly.graph_objs as go
import plotly.utils
# from dbconfig.mysql_config import mydb
# Sementara comment untuk testing

app = Flask(__name__)

def get_orders_from_db():
    """Ambil data orders dari MySQL atau fallback ke CSV"""
    # Sementara langsung pakai CSV
    orders = pd.read_csv("data/orders.csv")
    products = pd.read_csv("data/product.csv")
    customers = pd.read_csv("data/customer.csv")
    locations = pd.read_csv("data/location.csv")
    
    # Merge data
    df = orders.merge(products, on="product_id")
    df = df.merge(customers, on="customer_id")
    df = df.merge(locations, on="location_id")
    
    return df

def calculate_discount_analysis(orders_df):
    """Hitung analisis discount (sama seperti analysis_discount.py tapi dari DB)"""
    
    # Bucket Analysis
    bins = [0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 1.01]
    labels = ["0-10%","10-20%","20-30%","30-40%","40-50%","50-60%","60-70%","70%+"]
    
    orders_df["discount_bucket"] = pd.cut(orders_df["discount"], bins=bins, labels=labels, include_lowest=True)
    
    def margin(x):
        s = orders_df.loc[x.index, "sales"].sum()
        return (x.sum() / s * 100) if s != 0 else 0
    
    bucket_analysis = orders_df.groupby("discount_bucket", observed=True).agg(
        order_count = ("order_id", "count"),
        avg_profit  = ("profit", "mean"),
        total_profit= ("profit", "sum"),
        avg_sales   = ("sales", "mean"),
        profit_margin_pct = ("profit", margin)
    ).round(2).reset_index()
    
    # Korelasi
    r, p = stats.pearsonr(orders_df["discount"], orders_df["profit"])
    
    # Elastisitas  
    slope, intercept, r2, *_ = stats.linregress(orders_df["discount"], orders_df["profit"])
    breakeven = -intercept / slope if slope != 0 else None
    
    # Sweet spot & threshold
    best_bucket = bucket_analysis.loc[bucket_analysis["total_profit"].idxmax(), "discount_bucket"]
    neg_rows = bucket_analysis[bucket_analysis["avg_profit"] < 0]
    threshold_bucket = neg_rows.iloc[0]["discount_bucket"] if not neg_rows.empty else "tidak ada"
    
    return {
        'bucket_analysis': bucket_analysis.to_dict('records'),
        'correlation': {'r': r, 'p': p},
        'elasticity': {'slope': slope, 'intercept': intercept, 'r2': r2, 'breakeven': breakeven},
        'insights': {'best_bucket': best_bucket, 'threshold_bucket': threshold_bucket}
    }

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/discount-analysis')
def api_discount_analysis():
    try:
        orders_df = get_orders_from_db()
        analysis = calculate_discount_analysis(orders_df)
        return jsonify(analysis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/bucket-analysis')
def api_bucket_chart():
    try:
        orders_df = get_orders_from_db()
        analysis = calculate_discount_analysis(orders_df)
        
        buckets = [item['discount_bucket'] for item in analysis['bucket_analysis']]
        profits = [item['total_profit'] for item in analysis['bucket_analysis']]
        
        fig = go.Figure(data=[
            go.Bar(x=buckets, y=profits, name='Total Profit',
                   marker_color=['green' if p > 0 else 'red' for p in profits])
        ])
        
        fig.update_layout(
            title="Profit per Discount Bucket",
            xaxis_title="Discount Range",
            yaxis_title="Total Profit"
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/charts/correlation-scatter')
def api_correlation_chart():
    try:
        orders_df = get_orders_from_db()
        
        fig = go.Figure(data=[
            go.Scatter(x=orders_df['discount'], y=orders_df['profit'], 
                      mode='markers', name='Orders',
                      marker=dict(size=5, opacity=0.6))
        ])
        
        # Add trendline
        z = np.polyfit(orders_df['discount'], orders_df['profit'], 1)
        p = np.poly1d(z)
        fig.add_trace(go.Scatter(x=orders_df['discount'], y=p(orders_df['discount']),
                                mode='lines', name='Trendline', line=dict(color='red')))
        
        fig.update_layout(
            title="Korelasi Discount vs Profit",
            xaxis_title="Discount",
            yaxis_title="Profit"
        )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)