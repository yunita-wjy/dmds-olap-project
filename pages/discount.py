import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from data_loader import load_discount


st.set_page_config(page_title="Discount Analysis", layout="wide")


@st.cache_data
def load_data():
    df = load_discount()

    required_columns = {
        "order_id",
        "product_id",
        "location_id",
        "sales",
        "discount",
        "profit",
        "order_date",
        "product_name",
        "category",
        "sub_category",
        "country",
        "region",
    }
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing required SQL columns: {', '.join(sorted(missing))}")

    df = df.dropna(subset=["region", "country", "category", "sub_category"])

    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    df = df.dropna(subset=["order_date"])
    df["year"] = df["order_date"].dt.year
    df["month_year"] = df["order_date"].dt.to_period("M").astype(str)

    df["profit_margin"] = np.where(
        df["sales"].ne(0), df["profit"] / df["sales"] * 100, 0
    )
    df["profit_margin"] = df["profit_margin"].replace([np.inf, -np.inf], 0).fillna(0)

    df["discount_range"] = pd.cut(
        df["discount"] * 100,
        bins=[-0.01, 10, 20, 30, 40, 100],
        labels=["0-10%", "10-20%", "20-30%", "30-40%", "40%+"],
    )

    return df


def fmt_currency(value):
    return f"${value:,.0f}"


def format_table(df):
    numeric_columns = {
        "sales": "${:,.2f}",
        "profit": "${:,.2f}",
        "profit_margin": "{:.2f}%",
        "avg_profit": "${:,.2f}",
        "total_profit": "${:,.2f}",
        "total_sales": "${:,.2f}",
        "avg_discount": "{:.2f}%",
    }
    return df.style.format(
        {column: fmt for column, fmt in numeric_columns.items() if column in df.columns}
    )


def product_summary(df):
    return (
        df.groupby("product_name", as_index=False)
        .agg(
            sales=("sales", "sum"),
            profit=("profit", "sum"),
            profit_margin=("profit_margin", "mean"),
            avg_discount=("discount", lambda series: series.mean() * 100),
            order_count=("order_id", "count"),
        )
        .sort_values("sales", ascending=False)
    )


def discount_range_summary(df):
    summary = (
        df.groupby("discount_range", observed=False)
        .agg(
            avg_profit=("profit", "mean"),
            total_profit=("profit", "sum"),
            order_count=("order_id", "count"),
            total_sales=("sales", "sum"),
            avg_discount=("discount", lambda series: series.mean() * 100),
        )
        .reset_index()
    )
    summary["profit_margin"] = np.where(
        summary["total_sales"].ne(0),
        summary["total_profit"] / summary["total_sales"] * 100,
        0,
    )
    return summary.dropna(subset=["discount_range"])


def generate_insights(df, range_summary):
    if df.empty:
        return ["Tidak ada data pada filter yang dipilih."]

    insights = []
    category_profit = df.groupby("category")["profit"].sum()
    product_profit = df.groupby("product_name")["profit"].sum()
    category_discount = df.groupby("category")["discount"].mean() * 100

    insights.append(f"Kategori paling menguntungkan: {category_profit.idxmax()}.")
    insights.append(f"Produk paling menguntungkan: {product_profit.idxmax()}.")

    biggest_loss = product_profit.idxmin()
    if product_profit.min() < 0:
        insights.append(f"Produk dengan kerugian terbesar: {biggest_loss}.")

    insights.append(
        "Kategori dengan rata-rata diskon tertinggi: "
        f"{category_discount.idxmax()} ({category_discount.max():.1f}%)."
    )

    profitable_ranges = range_summary[range_summary["order_count"] > 0]
    if not profitable_ranges.empty:
        best_range = profitable_ranges.loc[profitable_ranges["avg_profit"].idxmax()]
        insights.append(
            "Rentang diskon paling menguntungkan: "
            f"{best_range['discount_range']} dengan rata-rata profit "
            f"{fmt_currency(best_range['avg_profit'])}."
        )

    return insights


def generate_business_conclusions(df, range_summary):
    if df.empty:
        return ["Tidak ada business conclusion karena filter tidak menghasilkan data."]

    conclusions = []
    correlation = df["discount"].corr(df["profit"])
    if pd.isna(correlation):
        impact = "TIDAK TERBACA"
        correlation_text = "n/a"
    elif correlation < -0.3:
        impact = "NEGATIF KUAT"
        correlation_text = f"{correlation:.3f}"
    elif correlation < -0.1:
        impact = "NEGATIF LEMAH"
        correlation_text = f"{correlation:.3f}"
    elif correlation > 0.1:
        impact = "POSITIF"
        correlation_text = f"{correlation:.3f}"
    else:
        impact = "TIDAK SIGNIFIKAN"
        correlation_text = f"{correlation:.3f}"

    conclusions.append(
        f"Pengaruh discount terhadap profit: {impact} "
        f"(korelasi: {correlation_text})."
    )

    profitable_ranges = range_summary[range_summary["order_count"] > 0]
    if profitable_ranges.empty:
        conclusions.append("Belum ada rentang discount yang dapat dievaluasi.")
        return conclusions

    optimal_range = profitable_ranges.loc[profitable_ranges["avg_profit"].idxmax()]
    conclusions.append(
        "Rentang discount optimal: "
        f"{optimal_range['discount_range']} dengan rata-rata profit "
        f"{fmt_currency(optimal_range['avg_profit'])}."
    )

    decline_threshold = profitable_ranges["avg_profit"].max() * 0.7
    decline_ranges = profitable_ranges[profitable_ranges["avg_profit"] < decline_threshold]
    if not decline_ranges.empty:
        conclusions.append(
            "Profit mulai menurun signifikan pada rentang: "
            f"{decline_ranges.iloc[0]['discount_range']}."
        )

    if str(optimal_range["discount_range"]) in ["0-10%", "10-20%"]:
        recommendation = "Strategi low discount untuk menjaga margin."
    elif str(optimal_range["discount_range"]) == "20-30%":
        recommendation = "Strategi moderate discount untuk menyeimbangkan volume dan margin."
    else:
        recommendation = "Strategi high volume dengan kontrol margin yang ketat."

    total_sales = df["sales"].sum()
    overall_margin = (df["profit"].sum() / total_sales * 100) if total_sales else 0
    conclusions.append(f"Rekomendasi strategi: {recommendation}")
    conclusions.append(
        f"Margin keseluruhan: {overall_margin:.1f}%, sedangkan margin pada "
        f"rentang optimal {optimal_range['discount_range']}: "
        f"{optimal_range['profit_margin']:.1f}%."
    )

    return conclusions


def show_list(items):
    for item in items:
        st.markdown(f"- {item}")


st.title("Discount-Profit Analysis")

try:
    df = load_data()
except Exception as exc:
    st.error(f"Data gagal dimuat: {exc}")
    st.stop()

if df.empty:
    st.error("Tidak ada data yang tersedia.")
    st.stop()

st.subheader("Filters")
filter_col1, filter_col2, filter_col3 = st.columns(3)
filter_col4, filter_col5 = st.columns(2)

with filter_col1:
    selected_years = st.multiselect(
        "Year",
        sorted(df["year"].dropna().unique()),
        default=sorted(df["year"].dropna().unique()),
    )

with filter_col2:
    selected_categories = st.multiselect(
        "Category",
        sorted(df["category"].dropna().unique()),
        default=sorted(df["category"].dropna().unique()),
    )

category_scope = (
    df[df["category"].isin(selected_categories)] if selected_categories else df
)
with filter_col3:
    selected_subcategories = st.multiselect(
        "Sub-Category",
        sorted(category_scope["sub_category"].dropna().unique()),
        default=sorted(category_scope["sub_category"].dropna().unique()),
    )

with filter_col4:
    selected_regions = st.multiselect(
        "Region",
        sorted(df["region"].dropna().unique()),
        default=sorted(df["region"].dropna().unique()),
    )

region_scope = df[df["region"].isin(selected_regions)] if selected_regions else df
with filter_col5:
    selected_countries = st.multiselect(
        "Country",
        sorted(region_scope["country"].dropna().unique()),
        default=sorted(region_scope["country"].dropna().unique()),
    )

filtered_df = df.copy()
if selected_years:
    filtered_df = filtered_df[filtered_df["year"].isin(selected_years)]
if selected_categories:
    filtered_df = filtered_df[filtered_df["category"].isin(selected_categories)]
if selected_subcategories:
    filtered_df = filtered_df[filtered_df["sub_category"].isin(selected_subcategories)]
if selected_regions:
    filtered_df = filtered_df[filtered_df["region"].isin(selected_regions)]
if selected_countries:
    filtered_df = filtered_df[filtered_df["country"].isin(selected_countries)]

st.caption(f"Showing {len(filtered_df):,} records from the selected filters.")

if filtered_df.empty:
    st.warning("Filter yang dipilih tidak menghasilkan data.")
    st.stop()

total_sales = filtered_df["sales"].sum()
total_profit = filtered_df["profit"].sum()
profit_margin_pct = (total_profit / total_sales * 100) if total_sales else 0
avg_discount = filtered_df["discount"].mean() * 100

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Total Sales", fmt_currency(total_sales))
kpi2.metric("Total Profit", fmt_currency(total_profit))
kpi3.metric("Profit Margin", f"{profit_margin_pct:.1f}%")
kpi4.metric("Total Orders", f"{len(filtered_df):,}")
kpi5.metric("Average Discount", f"{avg_discount:.1f}%")

range_summary = discount_range_summary(filtered_df)
products = product_summary(filtered_df)

st.subheader("Discount and Profit")
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    sample_df = (
        filtered_df.sample(1000, random_state=42)
        if len(filtered_df) > 1000
        else filtered_df
    )
    fig_scatter = px.scatter(
        sample_df,
        x=sample_df["discount"] * 100,
        y="profit",
        color="category",
        size="sales",
        hover_data=["product_name", "region", "country"],
        labels={"x": "Discount (%)", "profit": "Profit"},
        title="Discount vs Profit",
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with chart_col2:
    fig_range = px.bar(
        range_summary,
        x="discount_range",
        y="avg_profit",
        color="profit_margin",
        hover_data=["total_profit", "total_sales", "order_count", "profit_margin"],
        labels={
            "discount_range": "Discount Range",
            "avg_profit": "Average Profit",
            "profit_margin": "Profit Margin (%)",
        },
        title="Average Profit by Discount Range",
    )
    st.plotly_chart(fig_range, use_container_width=True)

st.subheader("Top Products")
top_col1, top_col2 = st.columns(2)

with top_col1:
    top_sales = products.nlargest(10, "sales").sort_values("sales")
    fig_top_sales = px.bar(
        top_sales,
        x="sales",
        y="product_name",
        orientation="h",
        title="Top 10 Products by Sales",
        labels={"sales": "Sales", "product_name": "Product"},
    )
    st.plotly_chart(fig_top_sales, use_container_width=True)

with top_col2:
    top_profit = products.nlargest(10, "profit").sort_values("profit")
    fig_top_profit = px.bar(
        top_profit,
        x="profit",
        y="product_name",
        orientation="h",
        title="Top 10 Products by Profit",
        labels={"profit": "Profit", "product_name": "Product"},
    )
    st.plotly_chart(fig_top_profit, use_container_width=True)

st.subheader("Category and Location")
category_col, region_col = st.columns(2)

with category_col:
    category_discount = (
        filtered_df.groupby("category", as_index=False)["discount"].mean()
    )
    category_discount["avg_discount"] = category_discount["discount"] * 100
    fig_category = px.bar(
        category_discount,
        x="category",
        y="avg_discount",
        title="Average Discount by Category",
        labels={"category": "Category", "avg_discount": "Average Discount (%)"},
    )
    st.plotly_chart(fig_category, use_container_width=True)

with region_col:
    region_profit = (
        filtered_df.groupby("region", as_index=False)["profit"]
        .sum()
        .sort_values("profit", ascending=False)
    )
    fig_region = px.pie(
        region_profit,
        names="region",
        values="profit",
        title="Profit Distribution by Region",
    )
    st.plotly_chart(fig_region, use_container_width=True)

st.subheader("Monthly Trend")
monthly_data = (
    filtered_df.groupby("month_year", as_index=False)
    .agg(sales=("sales", "sum"), profit=("profit", "sum"))
    .sort_values("month_year")
)
fig_trend = go.Figure()
fig_trend.add_trace(
    go.Scatter(
        x=monthly_data["month_year"],
        y=monthly_data["sales"],
        mode="lines+markers",
        name="Sales",
    )
)
fig_trend.add_trace(
    go.Scatter(
        x=monthly_data["month_year"],
        y=monthly_data["profit"],
        mode="lines+markers",
        name="Profit",
        yaxis="y2",
    )
)
fig_trend.update_layout(
    title="Monthly Sales and Profit Trends",
    xaxis_title="Month",
    yaxis=dict(title="Sales", side="left"),
    yaxis2=dict(title="Profit", side="right", overlaying="y"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
st.plotly_chart(fig_trend, use_container_width=True)

st.subheader("Detailed Analysis")
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "High Profit Products",
        "Low Profit Products",
        "High Sales Low Profit",
        "Discount Ranges",
    ]
)

with tab1:
    st.dataframe(
        format_table(products.nlargest(10, "profit")),
        use_container_width=True,
        hide_index=True,
    )

with tab2:
    st.dataframe(
        format_table(products.nsmallest(10, "profit")),
        use_container_width=True,
        hide_index=True,
    )

with tab3:
    sales_threshold = products["sales"].quantile(0.8)
    margin_threshold = products["profit_margin"].quantile(0.5)
    high_sales_low_profit = products[
        (products["sales"] >= sales_threshold)
        & (products["profit_margin"] <= margin_threshold)
    ].nlargest(10, "sales")
    st.dataframe(
        format_table(high_sales_low_profit),
        use_container_width=True,
        hide_index=True,
    )

with tab4:
    st.dataframe(format_table(range_summary), use_container_width=True, hide_index=True)

st.subheader("Insights")
insight_col, conclusion_col = st.columns(2)

with insight_col:
    st.markdown("**Analytical Insights**")
    show_list(generate_insights(filtered_df, range_summary))

with conclusion_col:
    st.markdown("**Business Conclusions**")
    show_list(generate_business_conclusions(filtered_df, range_summary))