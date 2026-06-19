import pandas as pd
from data_loader import *

def analyze_discount():
    ...

def analyze_trap_product():
    ...

def analyze_hidden_value(df, metric):
    df["profit_margin"] = (
        df["total_profit"] / df["total_sales"]
    )

    freq_th = df["frequency"].quantile(0.25)
    profit_th = df["total_profit"].quantile(0.75)
    margin_th = df["profit_margin"].quantile(0.75)
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

    return df_hidden, freq_th, profit_th, margin_th

# print(df)
# print(df_hidden.columns)
# print(df_hidden.describe())
# print(df_hidden.sort_values(by="total_profit", ascending=False).head(10))
# print(df_hidden.sort_values(by="frequency", ascending=True).head(10))
# print(df_hidden["frequency"].value_counts())
# print(df.sort_values(by=["frequency", "total_profit"], ascending=[True, False]))
