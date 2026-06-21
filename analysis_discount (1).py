import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

orders   = pd.read_csv("data/orders.csv")
products = pd.read_csv("data/product.csv")
locations= pd.read_csv("data/location.csv")

# Join
df = orders.merge(products[["product_id","category"]], on="product_id", how="left")
df = df.merge(locations[["location_id","region"]], on="location_id", how="left")

bins   = [0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 1.01]
labels = ["0-10%","10-20%","20-30%","30-40%","40-50%","50-60%","60-70%","70%+"]
df["discount_bucket"] = pd.cut(df["discount"], bins=bins, labels=labels, include_lowest=True)

def agg(data):
    def margin(x):
        s = data.loc[x.index, "sales"].sum()
        return (x.sum() / s * 100) if s != 0 else 0
    return data.groupby("discount_bucket", observed=True).agg(
        order_count  = ("order_id", "count"),
        avg_profit   = ("profit",   "mean"),
        total_profit = ("profit",   "sum"),
        profit_margin_pct = ("profit", margin)
    ).round(2).reset_index()

# OVERALL 
overall = agg(df)
print("="*65)
print("1. OVERALL BUCKET")
print("="*65)
print(overall.to_string(index=False))

#  PER KATEGORI 
print("\n" + "="*65)
print("2. PER KATEGORI")
print("="*65)
cat_results = {}
for cat in df["category"].dropna().unique():
    sub = df[df["category"] == cat]
    res = agg(sub)
    cat_results[cat] = res
    print(f"\n-- {cat} --")
    print(res[["discount_bucket","order_count","avg_profit","total_profit","profit_margin_pct"]].to_string(index=False))

# PER REGION 
print("\n" + "="*65)
print("3. PER REGION")
print("="*65)
reg_results = {}
for reg in df["region"].dropna().unique():
    sub = df[df["region"] == reg]
    res = agg(sub)
    reg_results[reg] = res
    print(f"\n-- {reg} --")
    print(res[["discount_bucket","order_count","avg_profit","total_profit","profit_margin_pct"]].to_string(index=False))

#  KORELASI & ELASTISITAS 
r, p       = stats.pearsonr(df["discount"], df["profit"])
slope, intercept, r_val, *_ = stats.linregress(df["discount"], df["profit"])
r2         = r_val ** 2
breakeven  = -intercept / slope if slope != 0 else None
print(f"\n{'='*65}")
print("4. KORELASI & ELASTISITAS")
print(f"{'='*65}")
print(f"Pearson r  : {r:.4f}")
print(f"p-value    : {p:.4e}")
print(f"Slope      : tiap diskon +1%, profit berubah {slope*0.01:.4f}")
print(f"R²         : {r2:.4f} ({r2*100:.1f}% variasi profit dijelaskan diskon)")
if breakeven:
    print(f"Break-even : {breakeven*100:.1f}%")

# VISUALISASI 
colors = ["#2ecc71" if v >= 0 else "#e74c3c" for v in overall["avg_profit"]]
cats   = list(cat_results.keys())
regs   = list(reg_results.keys())

fig = plt.figure(figsize=(18, 14))
fig.suptitle("Discount Dependency Analysis", fontsize=16, fontweight="bold", y=0.98)
gs  = gridspec.GridSpec(3, 2, figure=fig, hspace=0.5, wspace=0.35)

# Plot helper
def bar_plot(ax, data, title, color=None):
    c = color if color else ["#2ecc71" if v >= 0 else "#e74c3c" for v in data["avg_profit"]]
    ax.bar(data["discount_bucket"].astype(str), data["avg_profit"], color=c)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
    ax.set_title(title, fontsize=10, fontweight="bold")
    ax.set_xlabel("Discount Bucket")
    ax.set_ylabel("Avg Profit")
    ax.tick_params(axis='x', rotation=30)

# Overall
ax0 = fig.add_subplot(gs[0, :])
ax0.bar(overall["discount_bucket"].astype(str), overall["total_profit"],
        color=["#2ecc71" if v >= 0 else "#e74c3c" for v in overall["total_profit"]])
ax0.axhline(0, color="black", linewidth=0.8, linestyle="--")
ax0.set_title("Overall — Total Profit per Discount Bucket", fontsize=11, fontweight="bold")
ax0.set_xlabel("Discount Bucket")
ax0.set_ylabel("Total Profit")
ax0.tick_params(axis='x', rotation=30)

# Per kategori
for i, cat in enumerate(cats[:4]):
    ax = fig.add_subplot(gs[1, i % 2]) if len(cats) <= 2 else fig.add_subplot(gs[1 + i//2, i % 2])
    bar_plot(ax, cat_results[cat], f"Kategori: {cat}")

# Per region (margin line)
ax_reg = fig.add_subplot(gs[2, :]) if len(regs) > 2 else fig.add_subplot(gs[2, 0])
for reg in regs:
    d = reg_results[reg]
    ax_reg.plot(d["discount_bucket"].astype(str), d["avg_profit"], marker="o", label=reg)
ax_reg.axhline(0, color="black", linewidth=0.8, linestyle="--")
ax_reg.set_title("Avg Profit per Discount Bucket — by Region", fontsize=10, fontweight="bold")
ax_reg.set_xlabel("Discount Bucket")
ax_reg.set_ylabel("Avg Profit")
ax_reg.tick_params(axis='x', rotation=30)
ax_reg.legend(fontsize=7, ncol=3)

# plt.savefig("data/discount_dependency_chart.png", dpi=150, bbox_inches="tight")
# print("\nChart disimpan ke data/discount_dependency_chart.png")
