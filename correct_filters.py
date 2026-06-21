# FILTER DROPDOWN YANG BENAR - GUNAKAN .unique()

# Category Filter
selected_category = st.selectbox(
    "Choose Category",
    df["category"].unique()  # PASTI pakai .unique()
)

# Sub-Category Filter  
selected_subcat = st.multiselect(
    "Filter Sub-Category", 
    df["sub_category"].unique(),  # PASTI pakai .unique()
    default=df["sub_category"].unique()
)

# Product Filter (setelah filter category/subcategory)
filtered_df = df[df["category"] == selected_category]
selected_product = st.selectbox(
    "Choose Product",
    filtered_df["product_name"].unique()  # PASTI pakai .unique()
)

# Date Range Filter
date_range = st.date_input(
    "Select Date Range",
    value=(df["order_date"].min(), df["order_date"].max()),
    min_value=df["order_date"].min(),
    max_value=df["order_date"].max()
)

# DATA ASLI DARI DATABASE:
# Categories: Furniture, Office Supplies, Technology
# Sub-categories: Accessories, Appliances, Art, Binders, Bookcases, Chairs, Copiers, Envelopes, Fasteners, Furnishings, Labels, Machines, Paper, Phones, Storage, Supplies, Tables