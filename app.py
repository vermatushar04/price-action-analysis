import streamlit as st

from utils.loader import (
    STOCK_TICKERS,
    format_analysis,
    generate_heatmap,
    generate_monthly_avg_barchar,
    get_monthly_analysis,
)

st.set_page_config(page_title="Price Action Dashboard", layout="wide")  # make page wide

st.sidebar.title("Select Stock")
selected_ticker = st.sidebar.selectbox("Choose a stock:", STOCK_TICKERS)
st.title("Price Action Dashboard")
st.write(f"**Selected Stock:** {selected_ticker}")

tab1, tab2, tab3 = st.tabs(["📄 Price Action Data", "🔥 Heatmap", "📊 Bar Charts"])

@st.cache_data(ttl=60 * 60)
def get_formatted_table(stock: str):
    return format_analysis(get_monthly_analysis(stock))


with tab1:
    st.subheader("Price Action DataFrame")
    analysis = get_formatted_table(selected_ticker)
    st.dataframe(analysis)


with tab2:
    st.subheader("Heatmap")
    fig = generate_heatmap(selected_ticker)
    fig.update_layout(
        height=600,
        font=dict(size=16),
        # margin=dict(l=40, r=20, t=80, b=40)
    )
    st.plotly_chart(fig, )

with tab3:
    st.subheader("Bar Charts")
    fig = generate_monthly_avg_barchar(selected_ticker)
    st.plotly_chart(fig, use_container_width=True)