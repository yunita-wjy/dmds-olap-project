import pandas as pd
from data_loader import *

def analyze_discount():
    ...

def analyze_trap_product():
    ...

def analyze_hidden_value(df, metric):
    df["profit_margin"] = (
        df["total_profit"] / df["total_sales"] * 100
    )
    df["profit_margin"] = (df["profit_margin"]).round(2)

    df["price_per_unit"] = (df["total_sales"]/df["total_qty"]).round(2)
    df["profit_per_unit"] = (df["total_profit"]/df["total_qty"]).round(2)
    df["avg_profit_per_order"] = (df["total_profit"] / df["frequency"]).round(2)
    df["avg_sales_per_order"] = (df["total_sales"] / df["frequency"]).round(2)

    freq_th = df["frequency"].quantile(0.50)
    profit_th = df["total_profit"].quantile(0.95)
    margin_th = df["profit_margin"].quantile(0.90)
    avg_profit_th = df["avg_profit_per_order"].quantile(0.95)

    df_hidden = df.copy()

    if metric == "Total Profit":
        df_hidden = df_hidden[
            (df_hidden["frequency"] <= freq_th) &
            (df_hidden["total_profit"] >= profit_th)
            ]

    elif metric == "Profit Margin":
        df_hidden = df_hidden[
            (df_hidden["frequency"] <= freq_th) &
            (df_hidden["profit_margin"] >= margin_th)
            ]

    else:
        df_hidden = df[
            (df["frequency"] <= freq_th) &
            (df["avg_profit_per_order"] >= avg_profit_th)
            ]

    return df_hidden, freq_th, profit_th, margin_th, avg_profit_th

def classify_hidden_value(row, freq_th, avg_profit_th):
    if row["frequency"] <= freq_th and row["avg_profit_per_order"] >= avg_profit_th:
        return "Hidden High-Value"
    elif row["frequency"] > freq_th and row["avg_profit_per_order"] >= avg_profit_th:
        return "Core Product"
    elif row["frequency"] <= freq_th and row["avg_profit_per_order"] < avg_profit_th:
        return "Low Impact Niche"
    else:
        return "Volume Driver"


def get_top_category(df_hidden, region, col, metric):
    df_temp = df_hidden[df_hidden["region"] == region]

    if metric == "profit":
        top = df_temp.groupby(col)["total_profit"].sum().idxmax()

    elif metric == "count":
        top = df_temp.groupby(col)["product_id"].nunique().idxmax()

    return top

# print(df)
# df = load_hidden_value()
# df_hidden, freq_th, profit_th, margin_th, avg_profit_th = analyze_hidden_value(df, metric="Total Profit")
# print(df_hidden.columns)
# print(df_hidden.describe())
# print(df_hidden.sort_values(by="total_profit", ascending=False).head(10))
# print(df_hidden.sort_values(by="frequency", ascending=True).head(10))
# print(df_hidden["frequency"].value_counts())
# print(df_hidden.sort_values(by=["frequency", "total_profit"], ascending=[True, False]))
