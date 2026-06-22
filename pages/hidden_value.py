import streamlit as st
import plotly.express as px
from data_loader import load_hidden_value
from analyze import analyze_hidden_value, classify_hidden_value, get_top_category

st.set_page_config(layout="wide")

st.title("Hidden High Value Analysis")

df = load_hidden_value()

# ---------------- FILTER ----------------
col_f1, col_f2 = st.columns(2)

with col_f1:
    category_list = df["category"].dropna().unique()
    # selected_category = st.multiselect("Select Category", category_list)
    selected_category = st.selectbox(
        "Select Category",
        ["All"] + list(category_list)
    )

# with col_f2:
#     metric = st.selectbox(
#         "Select Metric Focus",
#         ["Choose Option", "Total Profit", "Profit Margin"]
#     )

with col_f2:
    region_list = df["region"].dropna().unique()
    selected_region = st.multiselect("Select Region", region_list)

# apply filter
if selected_category != "All":
    df = df[df["category"] == selected_category]

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
# df["label"] = "Normal"
# df.loc[df.index.isin(df_hidden.index), "label"] = "Hidden Value"

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

colB.metric("Low-Frequency ≤", freq_th)

colC.metric("High-Profit ≥", f" ${round(avg_profit_th, 2)}")

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


# if contribution > 1:
#     st.caption("⚠️ Hidden products more than 100% of total profit, offsetting losses from other products.")

# st.write("Total Profit All:", f"${round(total_profit_all, 2)}")
# st.write("Hidden Profit:", f"${round(hidden_profit, 2)}")
# st.write("Other Products Profit (Non-Hidden):", f"${round(normal_profit, 2)}")

# Formatting & Coloring
def color_profit(value):
    if value < 0:
        return "red"
    else:
        return "green"


hidden_color = "blue" if hidden_profit > normal_profit else color_profit(hidden_profit)

st.markdown(f"**Total Profit All:** :{color_profit(total_profit_all)}[${total_profit_all:,.0f}]")
st.markdown(f"**Hidden Profit:** :{hidden_color}[${hidden_profit:,.0f}]")
st.markdown(f"**Non-Hidden Profit:** :{color_profit(normal_profit)}[${normal_profit:,.0f}]")

if contribution > 1:
    st.caption(f":yellow[⚠️ Hidden products more than 100% of total profit, offsetting losses from other products.]")
elif total_profit_all > 0:
    st.caption(f":green[Hidden products contribute {contribution * 100:.2f}% of total profit.]")
elif total_profit_all < 0:
    st.caption(f":blue[Hidden Products are offsetting overall losses.]")

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
if selected_category == "All":
    legend_col = "category"
else:
    legend_col = "sub_category"

col3, col4 = st.columns(2)

# REGION
# aggregate legend sub-category
df_region = df_hidden.groupby(["region", legend_col]).agg(
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

df_region["label"] = df_region.apply(
    lambda r: f"{r['total_profit'] / 1000:.1f}K",
    axis=1
)

# Sorting
region_order = df_region_total.sort_values(
    by="total_hidden", ascending=False
)["region"].tolist()

fig_region = px.bar(
    df_region,
    y="region",
    x="hidden_count",
    color="total_profit",
    orientation="h",
    # text=legend_col,
    category_orders={"region": region_order},
    title="Hidden Value Distribution by Region",
    hover_data={
        legend_col: True,
        "hidden_count": True,
        "total_profit": ":,.0f"
    }
)

for i, row in df_region_total.iterrows():
    fig_region.add_annotation(
        y=row["region"],
        x=row["total_hidden"],
        text=f"Count: {row['total_hidden']} | Profit: {row['total_profit']:,.0f}",
        showarrow=False,
        xshift=75
    )

# X REGION
fig_subcatreg = px.bar(
    df_region,
    x="region",
    y="pct",
    color=legend_col,
    barmode="stack",
    title="Sub-Category Composition per Region (100%)",
    text=df_region["pct"].apply(lambda x: f"{x:.0%}")
)

fig_subcatreg.update_layout(yaxis_tickformat=".0%")
fig_subcatreg.update_traces(textposition="inside")

# X SUB-CATEGORY
# hitung persen per sub-category
# df_region["pct_subcat"] = df_region.groupby(legend_col)["hidden_count"] \
#     .transform(lambda x: x / x.sum())
#
# fig_subcat = px.bar(
#     df_region,
#     x=legend_col,
#     y="pct_subcat",
#     color="region",
#     barmode="stack",
#     title="Region Contribution per Sub-Category (100%)",
#     text=df_region["pct_subcat"].apply(lambda x: f"{x:.0%}")
# )
#
# fig_subcat.update_layout(yaxis_tickformat=".0%")
# fig_subcat.update_traces(textposition="inside")

fig_unit = px.scatter(
    df_hidden,
    x="avg_profit_per_order",
    y="profit_margin",
    color=legend_col,
    title="AVG Profit vs Margin"
)

with col3:
    st.plotly_chart(fig_region, use_container_width=True)

with col4:
    st.plotly_chart(fig_subcatreg, use_container_width=True)

# SUMMARY:
top_region = df_region.groupby("region")["hidden_count"].sum().idxmax()
top_region_count = df_region_total.loc[df_region_total["total_hidden"].idxmax()]
top_region_profit = df_region_total.loc[df_region_total["total_profit"].idxmax()]

top_cat_count = get_top_category(df_hidden, top_region_count["region"], legend_col, metric="count")
top_cat_profit = get_top_category(df_hidden, top_region_profit["region"], legend_col, metric="profit")

st.caption(
    f"""
Region with most hidden products: **{top_region_count['region']}**  → Dominated by: **{top_cat_count}**

Region with highest hidden profit: **{top_region_profit['region']}**  → Main contributor: **{top_cat_profit}**
"""
)

# ----------------- TYPE & VARIANT -------------------
st.markdown("---")
df_type_clean = df_hidden[df_hidden["type"] != "not have"]
df_variant_clean = df_hidden[df_hidden["variant"] != "not have"]

df_attr_coverage = df_hidden.groupby("category").agg(
    total_products=("product_id", "nunique"),
    with_type=("product_id", lambda x: x[df_hidden.loc[x.index, "type"] != "not have"].nunique())
).reset_index()

df_attr_coverage["coverage_pct"] = df_attr_coverage["with_type"] / df_attr_coverage["total_products"]

fig_cov = px.bar(
    df_attr_coverage,
    x="category",
    y="coverage_pct",
    title="Attribute Availability by Category",
    text=df_attr_coverage["coverage_pct"].apply(lambda x: f"{x:.0%}")
)

fig_cov.update_layout(yaxis_tickformat=".0%")

# st.plotly_chart(fig_cov, use_container_width=True)

# TYPE
unknown_type_count = df_hidden[df_hidden["type"] == "not have"]["product_id"].nunique()
total_type_count = df_hidden["product_id"].nunique()
unknown_type_pct = unknown_type_count / total_type_count if total_type_count > 0 else 0

df_type = df_type_clean.groupby("type").agg(
    hidden_count=("product_id", "nunique"),
    total_profit=("total_profit", "sum")
).reset_index()

df_type = df_type.sort_values(by="hidden_count", ascending=True)

fig_type = px.bar(
    df_type,
    x="hidden_count",
    y="type",
    orientation="h",
    color="total_profit",
    color_continuous_scale="Blues",
    title="Hidden Products by Type"
)

fig_type.update_traces(
    text=df_type["hidden_count"],
    textposition="outside"
)

# VARIANT
unknown_variant_count = df_hidden[df_hidden["variant"] == "not have"]["product_id"].nunique()
total_variant_count = df_hidden["product_id"].nunique()
unknown_variant_pct = unknown_variant_count / total_variant_count if total_variant_count > 0 else 0

df_variant = df_variant_clean.groupby("variant").agg(
    hidden_count=("product_id", "nunique"),
    total_profit=("total_profit", "sum")
).reset_index()

df_variant = df_variant.sort_values(by="hidden_count", ascending=True)

fig_variant = px.bar(
    df_variant,
    x="hidden_count",
    y="variant",
    orientation="h",
    color="total_profit",
    color_continuous_scale="Greens",
    title="Hidden Products by Variant",
    hover_data={
        "hidden_count": True,
        # "type": True,
        "variant": True,
        "total_profit": True
    }
)

fig_variant.update_traces(
    text=df_variant["hidden_count"],
    textposition="outside"
)

col5, col6 = st.columns(2)

with col5:
    st.plotly_chart(fig_type, use_container_width=True)
with col6:
    st.plotly_chart(fig_variant, use_container_width=True)

# st.caption("~75% of products have identifiable type/variant attributes")

if not df_type.empty:
    top_type = df_type.sort_values(by="hidden_count", ascending=False).iloc[0]
else:
    top_type = None

if not df_variant.empty:
    top_variant = df_variant.sort_values(by="hidden_count", ascending=False).iloc[0]
else:
    top_variant = None

st.caption(
    f"""
Most common hidden product type: **{top_type['type'] if top_type is not None else '-'}** 
({top_type['hidden_count'] if top_type is not None else 0} products)

Most common variant: **{top_variant['variant'] if top_variant is not None else '-'}** 
({top_variant['hidden_count'] if top_variant is not None else 0} products)

⚠️ Missing attributes:
- Type Unknown: **{unknown_type_count} products ({unknown_type_pct:.0%})**
- Variant Unknown: **{unknown_variant_count} products ({unknown_variant_pct:.0%})**
"""
)

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

st.markdown("---")
st.subheader("Hidden Value Products Detail")
available_subcat = sorted(df_hidden["sub_category"].dropna().unique())
selected = st.selectbox(
    "Choose Sub-Category",
    # df_bar_profit["sub_category"]
    available_subcat
)
# selected_subcat = st.multiselect(
#     "Filter Sub-Category",
#     df_bar_profit["sub_category"].unique(),
#     default=df_bar_profit["sub_category"].unique()
# )

df_show = (df_drilldown[df_drilldown["Sub-Cat"] == selected]
           .sort_values(by=["Freq", "Margin (%)", "Avg Profit"], ascending=[True, False, False])
           .reset_index(drop=True))
df_show.insert(0, "No", df_show.index + 1)

st.dataframe(
    df_show,
    use_container_width=True,
    column_config={
        "No": st.column_config.NumberColumn("No", width="small"),
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

# ---------------- TYPE: Hidden vs Non-Hidden ----------------
show_type_section = (
        selected_category != "All" or len(selected_region) > 0
)

if show_type_section:
    st.subheader("Hidden vs Non-Hidden by Type")

    df["hv_flag"] = df["segment"].apply(
        lambda x: "hidden" if x == "Hidden High-Value" else "non_hidden"
    )

    # exclude missing
    df_type_compare = df[df["type"].notna() & (df["type"] != "not have")]
    df_type_compare = df_type_compare[df_type_compare["sub_category"] == selected]

    # aggregate
    df_type_compare = df_type_compare.groupby(["type", "hv_flag"]).agg(
        product_count=("product_id", "nunique")
    ).reset_index()

    # pivot biar jadi hidden vs non-hidden
    df_type_pivot = df_type_compare.pivot(
        index="type",
        columns="hv_flag",
        values="product_count"
    ).fillna(0).reset_index()

    # rename kolom biar aman
    df_type_pivot.columns.name = None

    # hitung ratio
    df_type_pivot["total"] = df_type_pivot["hidden"] + df_type_pivot["non_hidden"]
    df_type_pivot["hidden_ratio"] = df_type_pivot["hidden"] / df_type_pivot["total"]

    # sort biar insightful
    df_type_pivot = df_type_pivot.sort_values(by="hidden_ratio", ascending=True)

    fig_type_compare = px.bar(
        df_type_pivot,
        x="type",
        y=["hidden", "non_hidden"],
        barmode="stack",
        title="Hidden vs Non-Hidden Distribution by Type",
    )

    fig_type_compare.update_layout(
        yaxis_title="Product Count",
        xaxis_title="Type"
    )

    fig_ratio = px.bar(
        df_type_pivot,
        x="hidden_ratio",
        y="type",
        orientation="h",
        title="Hidden Ratio by Type",
        text=df_type_pivot["hidden_ratio"].apply(lambda x: f"{x:.0%}")
    )

    fig_ratio.update_layout(
        xaxis_tickformat=".0%",
        xaxis_title="Hidden Ratio"
    )

    fig_ratio.update_traces(textposition="outside")

    col7, col8 = st.columns(2)

    with col7:
        st.plotly_chart(fig_type_compare, use_container_width=True)

    with col8:
        st.plotly_chart(fig_ratio, use_container_width=True)


# ----------------- HISTOGRAM ----------------------
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

# ------------- TESTING ---------------
# fig_scatter = px.scatter(
#     df,
#     x="frequency",
#     y="avg_profit_per_order",
#     color="segment",
#     hover_data=["product_name", "category", "sub_category"],
#     title="Frequency vs Avg Profit per Order"
# )
#
# # Tambahin garis threshold (biar jadi 4 kuadran)
# fig_scatter.add_vline(x=freq_th, line_dash="dash", line_color="red")
# fig_scatter.add_hline(y=avg_profit_th, line_dash="dash", line_color="green")
#
# st.plotly_chart(fig_scatter, use_container_width=True)
