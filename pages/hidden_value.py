import streamlit as st
import plotly.express as px
from data_loader import load_hidden_value
from analyze import analyze_hidden_value, classify_hidden_value

st.set_page_config(layout="wide")

st.title("Hidden High Value Analysis")

df = load_hidden_value()

# ---------------- FILTER ----------------
col_f1, col_f2 = st.columns(2)

with col_f1:
    category_list = df["category"].dropna().unique()
    selected_category = st.multiselect("Select Category", category_list)

# with col_f2:
#     metric = st.selectbox(
#         "Select Metric Focus",
#         ["Choose Option", "Total Profit", "Profit Margin"]
#     )

with col_f2:
    region_list = df["region"].dropna().unique()
    selected_region = st.multiselect("Select Region", region_list)

# apply filter
if selected_category:
    df = df[df["category"].isin(selected_category)]

if selected_region:
    df = df[df["region"].isin(selected_region)]

# ---------------- ANALYZE ----------------
df_hidden, freq_th, profit_th, margin_th, avg_profit_th = analyze_hidden_value(df, metric="avg_profit_per_order")
df["segment"] = df.apply(
    lambda row: classify_hidden_value(row, freq_th, avg_profit_th),
    axis=1
)

# if metric == "Total Profit":
#     y_col = "total_profit"
#     y_label = "Total Profit"
#     threshold = profit_th
# else:
#     y_col = "profit_margin"
#     y_label = "Profit Margin"
#     threshold = margin_th

# label hidden
df["label"] = "Normal"
df.loc[df.index.isin(df_hidden.index), "label"] = "Hidden Value"

# ---------------- KPI ----------------
st.markdown("### Key Metrics")

total_profit_all = df["total_profit"].sum()
hidden_profit = df_hidden["total_profit"].sum()
normal_profit = total_profit_all - hidden_profit
contribution = hidden_profit / total_profit_all

colA, colB, colC, colD = st.columns(4)

colA.metric("Hidden Products", df_hidden["product_id"].nunique())

# if metric == "Total Profit":
#     colB.metric("High-Profit ≥", round(profit_th, 2))
# else:
#     colB.metric("High-Margin ≥ (%)", round(margin_th, 2))

colC.metric("High-Profit ≥", round(avg_profit_th, 2))

colB.metric("Low-Frequency ≤", round(freq_th, 2))

# colD.metric("Hidden Profit Contribution (%)", f"{contribution*100:.2f}%")
if total_profit_all > 0:
    contribution = hidden_profit / total_profit_all
    colD.metric("Hidden Contribution (%)", f"{contribution * 100:.2f}%")
else:
    if normal_profit < 0:
        loss_coverage = hidden_profit / abs(normal_profit)
        colD.metric("Loss Coverage by Hidden (%)", f"{loss_coverage * 100:.2f}%")
    else:
        colD.metric("Loss Coverage by Hidden (%)", "-")

if contribution > 1:
    st.caption("⚠️ Hidden products more than 100% of total profit, offsetting losses from other products.")

st.write("Total Profit All:", round(total_profit_all, 2))
st.write("Hidden Profit:", round(hidden_profit, 2))
st.write("Other Products Profit (Non-Hidden):", round(normal_profit, 2))

st.markdown("---")

# ---------------- SCATTER ----------------
st.subheader("Product Distribution")

fig_scatter = px.scatter(
    df,
    x="frequency",
    y="avg_profit_per_order",
    color="segment",
    size="total_sales",
    hover_data=["product_name", "category", "total_profit"],
    title="Frequency vs Avg Profit per Order",
    color_discrete_map={
        "Hidden High-Value": "green",
        "Core Product": "#A0AEC0",
        "Low Impact Niche": "red",
        "Volume Driver": "blue"
    }
)

fig_scatter.add_vline(
    x=freq_th,
    line_color="gray",
    annotation_text=f"Freq ≤ {round(freq_th, 1)}",
    annotation_position="top right"
)

fig_scatter.add_hline(
    y=avg_profit_th,
    line_color="gray",
    annotation_text=f"Profit ≥ {round(avg_profit_th, 1)}",
    annotation_position="top left"
)

fig_scatter.update_layout(
    xaxis_title="Frequency",
    yaxis_title="Profit per order",
)

st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown("---")

# ---------------- BAR CHARTS ----------------
col1, col2 = st.columns(2)

st.markdown(f"**Hidden Products contribute {contribution * 100:.2f}% of total profit**")

# BAR 1 - PROFIT
df_bar_profit = df_hidden.groupby("sub_category", as_index=False)["total_profit"].sum()
df_bar_profit = df_bar_profit.sort_values(by="total_profit", ascending=True)

fig_bar_profit = px.bar(
    df_bar_profit,
    x="total_profit",
    y="sub_category",
    orientation="h",
    color="total_profit",
    color_continuous_scale="Blues",
    title="Total Profit by Sub-Category"
)

fig_bar_profit.update_traces(
    texttemplate='%{x:,.0f}',
    textposition='outside'
)

with col1:
    st.plotly_chart(fig_bar_profit, use_container_width=True)

# BAR 2 - COUNT
df_bar_count = df_hidden.groupby("sub_category")["product_id"].nunique().reset_index(name="hidden_product_count")
df_bar_count = df_bar_count.sort_values(by="hidden_product_count", ascending=True)

fig_bar_count = px.bar(
    df_bar_count,
    x="hidden_product_count",
    y="sub_category",
    orientation="h",
    color="hidden_product_count",
    color_continuous_scale="Greens",
    title="Hidden Product Count by Sub-Category"
)

fig_bar_count.update_traces(
    texttemplate='%{x}',
    textposition='outside'
)

with col2:
    st.plotly_chart(fig_bar_count, use_container_width=True)

st.markdown("---")

# ---------------- REGION + ? ----------------
col3, col4 = st.columns(2)

# REGION
# aggregate legend sub-category
df_region = df_hidden.groupby(["region", "sub_category"]).agg(
    hidden_count=("product_id", "nunique"),
    total_profit=("total_profit", "sum")
).reset_index()
df_region = df_region.sort_values(by="total_profit", ascending=False)

# calculate total profit
df_region_total = df_hidden.groupby("region").agg(
    total_hidden=("product_id", "nunique"),
    total_profit=("total_profit", "sum")
).reset_index()

# hitung persen per region
df_region["pct"] = df_region.groupby("region")["hidden_count"] \
    .transform(lambda x: x / x.sum())

fig_region = px.bar(
    df_region,
    x="region",
    y="hidden_count",
    color="sub_category",
    title="Hidden Value Distribution by Region",
    barmode="stack"
)

for i, row in df_region_total.iterrows():
    fig_region.add_annotation(
        x=row["region"],
        y=row["total_hidden"],
        text=f"{row['total_hidden']}<br>Profit: {row['total_profit']:,.0f}",
        showarrow=False,
        yshift=10
    )

# X REGION
fig_region = px.bar(
    df_region,
    x="region",
    y="pct",
    color="sub_category",
    barmode="stack",
    title="Sub-Category Composition per Region (100%)",
    text=df_region["pct"].apply(lambda x: f"{x:.0%}")
)

fig_region.update_layout(yaxis_tickformat=".0%")
fig_region.update_traces(textposition="inside")

# X SUB-CATEGORY
# hitung persen per sub-category
df_region["pct_subcat"] = df_region.groupby("sub_category")["hidden_count"] \
    .transform(lambda x: x / x.sum())

fig_subcat = px.bar(
    df_region,
    x="sub_category",
    y="pct_subcat",
    color="region",
    barmode="stack",
    title="Region Contribution per Sub-Category (100%)",
    text=df_region["pct_subcat"].apply(lambda x: f"{x:.0%}")
)

fig_subcat.update_layout(yaxis_tickformat=".0%")
fig_subcat.update_traces(textposition="inside")

fig_unit = px.scatter(
    df_hidden,
    x="price_per_unit",
    y="profit_per_unit",
    color="sub_category",
    title="Price vs Profit per Unit"
)
df_region_pivot = df_region.pivot_table(
    index="region",
    columns="sub_category",
    values="pct",
    fill_value=0
)

df_subcat_pivot = df_region.pivot_table(
    index="sub_category",
    columns="region",
    values="pct_subcat",
    fill_value=0
)

with col3:
    st.plotly_chart(fig_region, use_container_width=True)

with col4:
    st.plotly_chart(fig_subcat, use_container_width=True)

st.plotly_chart(fig_unit, use_container_width=True)

# ---------------- DRILLDOWN ----------------
column_mapping = {
    "product_name": "Product",
    "sub_category": "Sub-Cat",
    "frequency": "Freq",
    "total_sales": "Sales",
    "total_profit": "Profit",
    "avg_profit_per_order": "Avg Profit",
    "profit_margin": "Margin (%)",
    "price_per_unit": "Price/Unit",
    "profit_per_unit": "Profit/Unit"
}

df_drilldown = df_hidden[[
    "product_name",
    "sub_category",
    "frequency",
    "total_sales",
    "total_profit",
    "avg_profit_per_order",
    "profit_margin",
    "price_per_unit",
    "profit_per_unit"
]].rename(columns=column_mapping)

st.subheader("Hidden Value Products Detail")

selected = st.selectbox(
    "Choose Sub-Category",
    df_bar_profit["sub_category"]
)
# selected_subcat = st.multiselect(
#     "Filter Sub-Category",
#     df_bar_profit["sub_category"].unique(),
#     default=df_bar_profit["sub_category"].unique()
# )

st.dataframe(
    df_drilldown[df_drilldown["Sub-Cat"] == selected]
    .sort_values(by=["Freq", "Margin (%)", "Avg Profit"], ascending=[True, False, False]),
    use_container_width=True,
    column_config={
        "Product": st.column_config.TextColumn("Product", width="large"),
        "Sales": st.column_config.NumberColumn(format="%,.0f"),
        "Profit": st.column_config.NumberColumn(format="%,.0f"),
        "Avg Profit": st.column_config.NumberColumn(format="%,.0f"),
        "Margin (%)": st.column_config.NumberColumn(format="%.1f"),
        "Price/Unit": st.column_config.NumberColumn(format="%,.0f"),
        "Profit/Unit": st.column_config.NumberColumn(format="%,.0f"),
    },
    hide_index=True
)

# Histogram Frequency
fig_freq = px.histogram(
    df,
    x="frequency",
    nbins=40,
    title="Distribution of Product Frequency"
)

# Histogram Avg Profit
fig_avg_profit = px.histogram(
    df,
    x="avg_profit_per_order",
    nbins=30,
    title="Distribution of Avg Profit per Order"
)

# Tambahin threshold line
fig_freq.add_vline(x=freq_th, line_dash="dash", line_color="red")
fig_avg_profit.add_vline(x=avg_profit_th, line_dash="dash", line_color="red")

col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(fig_freq, use_container_width=True)

with col2:
    st.plotly_chart(fig_avg_profit, use_container_width=True)

fig_scatter = px.scatter(
    df,
    x="frequency",
    y="avg_profit_per_order",
    color="segment",
    hover_data=["product_name", "category", "sub_category"],
    title="Frequency vs Avg Profit per Order"
)

# Tambahin garis threshold (biar jadi 4 kuadran)
fig_scatter.add_vline(x=freq_th, line_dash="dash", line_color="red")
fig_scatter.add_hline(y=avg_profit_th, line_dash="dash", line_color="green")

st.plotly_chart(fig_scatter, use_container_width=True)
