import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf

MONTHS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]

STOCK_TICKERS = [
    "^CNXREALTY",  # NIFTY REALTY
    "ANANTRAJ.NS",
    "BRIGADE.NS",
    "DLF.NS",
    "SOBHA.NS",
    "RAYMOND.NS",
    "PHOENIXLTD.NS",
    "PRESTIGE.NS",
    "LODHA.NS",
    "GODREJPROP.NS",
    "OBEROIRLTY.NS",
]


def calc_annual_return(monthly_returns: pd.Series):
    return monthly_returns.add(1, fill_value=0.0).prod() - 1.0  # type: ignore


def add_monthly_contributions(df: pd.DataFrame):
    def get_monthly_contrib(monthly_series: pd.Series):
        return np.log1p(monthly_series[MONTHS]) / np.log1p(
            monthly_series["annual_returns"]
        )

    contrib = df.apply(get_monthly_contrib, axis=1).add_suffix("_contrib")
    return df.join(contrib)


def add_avg_monthly_return(df: pd.DataFrame):
    avg_monthly_returns = (
        df[MONTHS].mean(axis=0).rename("monthly_avg").to_frame().transpose()
    )
    return pd.concat([df, avg_monthly_returns])


@st.cache_data(ttl=60 * 60)
def get_monthly_analysis(
    stock: str, stock_data: pd.Series | None = None
) -> pd.DataFrame:
    if stock_data is None:
        stock_data = download_stock_data(stock)

    return (
        stock_data.to_frame("close")
        .resample("ME")
        .last()
        .assign(
            month=lambda df_: df_.index.strftime("%b"),  # type: ignore
            year=lambda df_: df_.index.strftime("%Y"),  # type: ignore
            monthly_returns=lambda df_: df_["close"].pct_change(),
        )
        .astype({"month": pd.CategoricalDtype(MONTHS, ordered=True)})
        .pivot_table(
            index="year", columns="month", values="monthly_returns", observed=True
        )
        .assign(
            annual_returns=lambda df_: df_.loc[:, "Jan":"Dec"].agg(
                calc_annual_return, axis=1
            ),
            first_half_avg=lambda df_: df_.loc[:, "Jan":"Jun"].mean(axis=1),
            second_half_avg=lambda df_: df_.loc[:, "Jul":"Dec"].mean(axis=1),
        )
        .pipe(add_monthly_contributions)
        .pipe(add_avg_monthly_return)
    )


def format_analysis(analysis: pd.DataFrame):
    return (
        analysis[
            [
                *MONTHS[:6],
                "first_half_avg",
                *MONTHS[6:],
                "second_half_avg",
                "annual_returns",
                *[f"{month}_contrib" for month in MONTHS],
            ]
        ]
        .rename(
            columns={
                "annual_returns": "Total Annual Returns",
                "first_half_avg": "Avg returns till June",
                "second_half_avg": "Avg returns after June",
                **{f"{month}_contrib": f"{month} Contribution" for month in MONTHS},
            },
            index={
                "monthly_avg": "Avg Monthly Returns",
            },
        )
        .mul(100)
        .round(2)
    )


@st.cache_data(ttl=60 * 60 * 24)
def download_stock_data(stock: str) -> pd.Series:
    stock_data = yf.download(
        stock,
        period="max",
        multi_level_index=False,
        auto_adjust=True,
    )["Close"]  # type: ignore

    return stock_data


def convert_to_csv(stocks):
    for stock in stocks:
        analysis = get_monthly_analysis(stock)
        formatted_analysis = format_analysis(analysis)
        formatted_analysis.to_csv(
            f"../data/{stock}_analysis.csv",
            index=True,
        )
        print(f"Analysis saved to {stock}_analysis.csv")


def convert_to_excel(stocks):
    with pd.ExcelWriter(
        "../data/price_action_analysis.xlsx", engine="xlsxwriter"
    ) as writer:
        for stock in stocks:
            analysis = get_monthly_analysis(stock)
            formatted_analysis = format_analysis(analysis)
            formatted_analysis.to_excel(writer, index=True, sheet_name=stock[:31])
    print("Analysis saved to ../data/price_action_analysis.xlsx")


def generate_heatmap(stock: str, stock_data: pd.Series | None = None):
    if stock_data is None:
        stock_data = download_stock_data(stock)

    res = (
        stock_data.to_frame("close")
        .resample("ME")
        .last()
        .assign(
            month=lambda df_: df_.index.strftime("%b"),  # type: ignore
            year=lambda df_: df_.index.strftime("%Y"),  # type: ignore
            monthly_returns=lambda df_: df_["close"].pct_change(),
        )
        .astype({"month": pd.CategoricalDtype(MONTHS, ordered=True)})
        .pivot_table(
            index="year", columns="month", values="monthly_returns", observed=True
        )
        .mul(100)
        .round(2)
    )

    fig = px.imshow(
        res,
        color_continuous_scale="RdYlGn",
        origin="upper",
        aspect="auto",
        text_auto=".2f",
        labels=dict(month="Month", year="Year", color="Return (%)"),
    )
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Year")
    fig.update_layout(
        title=f"Historical Monthly Returns of {stock}",
        coloraxis_colorbar_ticksuffix="%",
    )
    return fig


def generate_monthly_avg_barchar(stock: str, stock_data: pd.Series | None = None):
    if stock_data is None:
        stock_data = download_stock_data(stock)

    res = (
        get_monthly_analysis(stock, stock_data)
        .mul(100)
        .round(2)
        .loc["monthly_avg", MONTHS]
    )  # type: ignore
    

    fig = px.bar(
        x=res.index,
        y=res.values,
        labels={"x": "Month", "y": "Avg Monthly Returns (%)"},
        title=f"Average Monthly Returns for {stock}",
        color=res.values,
        color_continuous_scale="RdYlGn",
        text=res.apply(lambda x: f"{x:.2f}%"),
    )
    # fig.update_layout(yaxis_tickformat=".02%")
    return fig
