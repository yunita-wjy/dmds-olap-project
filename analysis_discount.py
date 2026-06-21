import pandas as pd
import numpy as np
from scipy import stats

orders = pd.read_csv("data/orders.csv")

#  BUCKET ANALYSIS 
bins   = [0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 1.01]
labels = ["0-10%","10-20%","20-30%","30-40%","40-50%","50-60%","60-70%","70%+"]

orders["discount_bucket"] = pd.cut(orders["discount"], bins=bins, labels=labels, include_lowest=True)

def margin(x):
    s = orders.loc[x.index, "sales"].sum()
    return (x.sum() / s * 100) if s != 0 else 0

bucket = orders.groupby("discount_bucket", observed=True).agg(
    order_count = ("order_id", "count"),
    avg_profit  = ("profit",   "mean"),
    total_profit= ("profit",   "sum"),
    avg_sales   = ("sales",    "mean"),
    profit_margin_pct = ("profit", margin)
).round(2).reset_index()

print("=" * 65)
print("1. BUCKET ANALYSIS")
print("=" * 65)
print(bucket.to_string(index=False))

#KORELASI 
r, p = stats.pearsonr(orders["discount"], orders["profit"])
print(f"\n{'='*65}")
print("2. KORELASI DISCOUNT vs PROFIT")
print(f"{'='*65}")
print(f"Pearson r : {r:.4f}")
print(f"p-value   : {p:.4e}")
print(f"Interpretasi: {'korelasi negatif kuat' if r < -0.5 else 'korelasi negatif lemah-sedang' if r < 0 else 'korelasi positif'}")

# ELASTISITAS (linear regression) 
slope, intercept, r2, *_ = stats.linregress(orders["discount"], orders["profit"])
print(f"\n{'='*65}")
print("3. ELASTISITAS DISCOUNT → PROFIT")
print(f"{'='*65}")
print(f"Slope     : {slope:.4f}  → tiap diskon naik 0.01 (1%), profit berubah {slope*0.01:.4f}")
print(f"Intercept : {intercept:.4f}  → estimasi profit jika diskon = 0")
print(f"R²        : {r2:.4f}  → {r2*100:.1f}% variasi profit dijelaskan oleh diskon")

breakeven = -intercept / slope if slope != 0 else None
if breakeven:
    print(f"Break-even diskon : {breakeven*100:.1f}%  → di atas ini profit rata-rata negatif")

#SWEET SPOT & THRESHOLD 
best      = bucket.loc[bucket["total_profit"].idxmax(), "discount_bucket"]
neg_rows  = bucket[bucket["avg_profit"] < 0]
threshold = neg_rows.iloc[0]["discount_bucket"] if not neg_rows.empty else "tidak ada"

print(f"\n{'='*65}")
print("4. KESIMPULAN")
print(f"{'='*65}")
print(f"Sweet spot (total profit tertinggi) : {best}")
print(f"Threshold profit negatif pertama    : {threshold}")
