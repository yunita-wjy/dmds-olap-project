import pandas as pd
from data_loader import *


df_hidden = load_hidden_value()
df_hidden = df_hidden[["product_id", "frequency","total_profit"]]
df = df_hidden[(df_hidden["frequency"] < 3) & (df_hidden["total_profit"] > 183)]

print(df_hidden.columns)
print(df_hidden.describe())
print(df_hidden.sort_values(by="total_profit", ascending=False).head(10))
print(df_hidden.sort_values(by="frequency", ascending=True).head(10))
print(df_hidden["frequency"].value_counts())
print(df.sort_values(by="total_profit", ascending=False))

def analyze_discount():
    ...

def analyze_trap_product():
    ...

def analyze_hidden_value():
    ...

