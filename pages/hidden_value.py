import streamlit as st
import plotly.express as px
from data_loader import load_hidden_value
from analyze import analyze_hidden_value

st.title("Hidden High Value Analysis")

df = load_hidden_value()

# ------------- FILTER -----------------
# Category
category_list = df["category"].dropna().unique()
selected_category = st.multiselect("Select Category", category_list)
# Profit / Margin
metric = st.selectbox(
    "Select Metric Focus",
    ["Total Profit", "Profit Margin"]
)

if selected_category:
    df = df[df["category"].isin(selected_category)]


# ANALYZE
df_hidden, freq_th, profit_th, margin_th = analyze_hidden_value(df, metric)
if metric == "Total Profit":
    y_col = "total_profit"
    y_label = "Profit"
    threshold = profit_th
else:
    y_col = "profit_margin"
    y_label = "Margin"
    threshold = margin_th


# ------------- VISUALIZE -----------------
st.subheader("Product Distribution")
# st.scatter_chart(
#     df,
#     x="frequency",
#     y=y_col
# )


# 1. SCATTER
# tandain hidden value
df["label"] = "Normal"
df.loc[df.index.isin(df_hidden.index), "label"] = "Hidden Value"

fig = px.scatter(
    df,
    x="frequency",
    y=y_col,
    color="label",
    hover_data=["product_name", "category", "total_profit"]
)

# garis threshold
fig.add_vline(
    x=freq_th,
    annotation_text=f"Freq ≤ {freq_th:.1f}",
    annotation_position="top right"
)

fig.add_hline(
    y=threshold,
    annotation_text=f"{y_label} ≥ {threshold:.1f}",
    annotation_position="top left"
)

st.plotly_chart(fig, use_container_width=True)

# 2. BAR CHART
df_bar = df_hidden.groupby("sub_category", as_index=False)["total_profit"].sum()
df_bar = df_bar.sort_values(by="total_profit", ascending=True)
# top_n = 10
# df_bar = df_bar.head(top_n)

fig = px.bar(
    df_bar,
    x="total_profit",
    y="sub_category",
    orientation="h",
    title="Top Hidden Value Products by Sub-Category",
    hover_data=["total_profit"]
)

fig.update_traces(
    texttemplate='%{x:,.0f}',
    textposition='outside'
)

fig.update_layout(
    yaxis_title="Sub-Category",
    xaxis_title="Total Profit",
    title_x=0.5
)

fig = px.bar(
    df_bar,
    x="total_profit",
    y="sub_category",
    orientation="h",
    color="total_profit",
    color_continuous_scale="Blues"
)

st.plotly_chart(fig, use_container_width=True)

df_bar2 = df_hidden.groupby("sub_category")["product_id"].nunique().reset_index(name="hidden_product_count")
df_bar2 = df_bar2.sort_values(by="hidden_product_count", ascending=True)
fig = px.bar(
    df_bar2,
    x="hidden_product_count",
    y="sub_category",
    orientation="h",
    title="Number of Hidden Value Products by Sub-Category",
    color="hidden_product_count",
    color_continuous_scale="Blues"
)

fig.update_traces(
    texttemplate='%{x}',
    textposition='outside'
)

fig.update_layout(
    yaxis_title="Sub-Category",
    xaxis_title="Number of Hidden Products",
    title_x=0.5
)

st.plotly_chart(fig, use_container_width=True)

df_drilldown = df_hidden[["sub_category", "frequency", "total_profit","total_sales", "profit_margin", "product_name"]]
selected = st.selectbox("Choose Sub-Category", df_bar["sub_category"])

st.dataframe(
    df_drilldown[df_drilldown["sub_category"] == selected]
    .sort_values(by=["frequency", "total_profit"], ascending=[True, False])
)
