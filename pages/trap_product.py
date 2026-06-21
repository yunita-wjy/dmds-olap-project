# import streamlit as st # pyright: ignore[reportMissingImports]
# import plotly.express as px
# from data_loader import load_trap_product
# from st_aggrid import AgGrid, GridOptionsBuilder

# st.set_page_config(layout="wide")

# st.title("Trap Product Analysis")

# df = load_trap_product()

# gb = GridOptionsBuilder.from_dataframe(df)
# gb.configure_selection(
#     selection_mode="single",
#     use_checkbox=False
# )

# response = AgGrid(
#     df,
#     gridOptions=gb.build(),
#     height=500
# )
# selected_rows = response["selected_rows"]

# # st.dataframe(df, use_container_width=True)

# top10 = df.sort_values(
#     by="frequency",
#     ascending=False
# ).head(20)

# fig = px.bar(
#     top10,
#     x="frequency",
#     y="product_name",
#     orientation="h",
#     title="Top 10 Products by Frequency"
# )

# st.plotly_chart(
#     fig,
#     use_container_width=True
# )

import streamlit as st
import plotly.express as px
from data_loader import load_trap_product
from st_aggrid import AgGrid, GridOptionsBuilder

# Menambahkan fungsi baru dari data_loader tanpa mengubah import asli di atas
from data_loader import load_bought_together

st.set_page_config(layout="wide")

st.title("Trap Product Analysis")

df = load_trap_product()

# 1. Membuat Layout 2 Kolom (Kiri: AgGrid, Kanan: Detail Produk Hari yang Sama)
col1, col2 = st.columns([1.8, 1.2])

with col1:
    st.write("### 📊 Daftar Produk Utama")

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_selection(
        selection_mode="single",
        use_checkbox=False
    )

    response = AgGrid(
        df,
        gridOptions=gb.build(),
        height=500
    )
    selected_rows = response["selected_rows"]

with col2:
    # 2. Logika Interaktif saat Baris AgGrid Diklik
    if selected_rows is not None and len(selected_rows) > 0:

        # Mengantisipasi perbedaan versi AgGrid (bisa berupa List atau DataFrame)
        if isinstance(selected_rows, list):
            row_data = selected_rows[0]
        else:
            row_data = selected_rows.iloc[0]

        selected_id = row_data['product_id']
        selected_name = row_data['product_name']

        st.write(f"### 🎯 Produk Utama: **{selected_name}**")
        st.caption("Berikut adalah produk lain yang dibeli konsumen pada hari yang sama:")

        # Ambil data dari fungsi data_loader
        df_together = load_bought_together(selected_id)

        if not df_together.empty:
            df_display = df_together[['product_name', 'frequency']].rename(
                columns={'product_name': 'Produk Pendamping', 'frequency': 'Frekuensi Hari Sama'}
            )
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("Tidak ada produk lain yang dibeli di hari yang sama.")

    else:
        # Tampilan awal sebelum pengguna melakukan klik
        st.write("### 🔍 Detail Pola Pembelian")
        st.info(
            "Silakan klik salah satu baris produk pada tabel AgGrid di sebelah kiri untuk melihat produk pendamping.")

# 3. Bagian Grafik Batas Bawah (Tetap Utuh)
st.write("---")

top10 = df.sort_values(
    by="frequency",
    ascending=False
).head(20)

fig = px.bar(
    top10,
    x="frequency",
    y="product_name",
    orientation="h",
    title="Top 10 Products by Frequency"
)

st.plotly_chart(
    fig,
    use_container_width=True
)