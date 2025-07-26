import streamlit as st
import pandas as pd
import os
import glob
import base64
import plotly.graph_objects as go
from PIL import Image

# --- 初期設定 ---
st.set_page_config(layout="wide")


# --- 背景画像読込 ---
def load_background_image(image_path):
    with open(image_path, "rb") as f:
        return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"


# --- マーカー設定関数 ---
def get_symbol_by_hittype(Hittype):
    symbol_map = {
        "ゴロ": "circle",
        "フライ": "square",
        "ライナー": "triangle-up",
    }
    return symbol_map.get(Hittype, "diamond")


def get_color_by_pitchtype(Pitchtype):
    color_map = {
        "4S": "red",
        "CB": "purple",
        "SL": "blue",
        "CH": "yellow",
        "SP": "orange",
        "CT": "skyblue",
        "2S": "pink",
    }
    return color_map.get(Pitchtype, "gray")


# --- パス設定 ---
image_path = "baseballfield.jpg"
folder_path = "試合データ"

# --- エラーチェック ---
if not os.path.exists(image_path) or not os.path.exists(folder_path):
    st.error("背景画像または試合データフォルダが見つかりません。")
    st.stop()

# --- 背景画像ロード ---
image_source = load_background_image(image_path)

# --- CSV読み込み ---
csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
df_list = []

for file in csv_files:
    df = pd.read_csv(file, encoding="cp932")
    df["ファイル名"] = os.path.basename(file)
    df_list.append(df)

df_batter = pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()
df_batter["PitchType"] = df_batter["PitchType"].astype(str).str.strip().str.upper()

# --- UI ---
st.title("打球方向 可視化アプリ（CSV入力版）")
st.subheader("打球データはCSVから自動で読み込まれます")

batters = df["Batter"].dropna().unique()

# 打者選択
selected_batter = st.selectbox("打者を選択", options=batters)

# 対右・対左フィルター
LR_filter = st.selectbox("対右or対左", options=["対右投手", "対左投手"])
df["PitcherLR"] = df["PitcherLR"].astype(str).str.strip().str.upper()
if LR_filter == "対右投手":
    df_batter = df_batter[df_batter["PitcherLR"] == "R"]
elif LR_filter == "対左投手":
    df_batter = df_batter[df_batter["PitcherLR"] == "L"]

# 球種フィルター
pitch_filter = st.selectbox(
    "球種フィルター", options=["すべて", "ストレート", "スライダー系", "チェンジ系"]
)

# データフィルタリング
df["PitchType"] = df["PitchType"].astype(str).str.strip().str.upper()

df_batter = df[df["Batter"] == selected_batter]
if pitch_filter == "ストレート":
    df_batter = df_batter[df_batter["PitchType"] == "4S"]
elif pitch_filter == "スライダー系":
    df_batter = df_batter[df_batter["PitchType"].isin(["SL", "CT"])]
elif pitch_filter == "チェンジ系":
    df_batter = df_batter[df_batter["PitchType"].isin(["CH", "SP"])]

# ストライクカウントフィルター
Strikes_filter = st.selectbox(
    "カウント", options=["すべて", "0ストライク", "1ストライク", "2ストライク"]
)
df_batter["Strikes"] = df_batter["Strikes"].astype(str).str.strip().str.upper()
if Strikes_filter == "0ストライク":
    df_batter = df_batter[df_batter["Strikes"] == "0"]
elif Strikes_filter == "1ストライク":
    df_batter = df_batter[df_batter["Strikes"] == "1"]
elif Strikes_filter == "2ストライク":
    df_batter = df_batter[df_batter["Strikes"] == "2"]

# コース・高さフィルター
PitchCourse_filter = st.selectbox("投球コース", options=["すべて", "内", "真中", "外"])
df_batter["PitchCourse"] = df_batter["PitchCourse"].astype(str).str.strip().str.upper()
if PitchCourse_filter == "内":
    df_batter = df_batter[df_batter["PitchCourse"] == "I"]
elif PitchCourse_filter == "真中":
    df_batter = df_batter[df_batter["PitchCourse"] == "M"]
elif PitchCourse_filter == "外":
    df_batter = df_batter[df_batter["PitchCourse"] == "O"]

PitchHeight_filter = st.selectbox(
    "投球高さ", options=["すべて", "低め", "真中", "高め"]
)
df_batter["PitchHeight"] = df_batter["PitchHeight"].astype(str).str.strip().str.upper()
if PitchHeight_filter == "低め":
    df_batter = df_batter[df_batter["PitchHeight"] == "L"]
elif PitchHeight_filter == "真中":
    df_batter = df_batter[df_batter["PitchHeight"] == "M"]
elif PitchHeight_filter == "高め":
    df_batter = df_batter[df_batter["PitchHeight"] == "H"]

# 走者状況フィルター
Runners_filter = st.selectbox("走者状況", options=["すべて", "なし", "1塁", "得点圏"])
df_batter["Runners"] = df_batter["Runners"].astype(str).str.strip().str.upper()
if Runners_filter == "なし":
    df_batter = df_batter[df_batter["Runners"] == "111"]
elif Runners_filter == "1塁":
    df_batter = df_batter[df_batter["Runners"] == "211"]
elif Runners_filter == "得点圏":
    df_batter = df_batter[
        df_batter["Runners"].isin(["121", "122", "221", "212", "222", "112"])
    ]


# --- Plotly描画 ---
fig = go.Figure()

fig.update_layout(
    xaxis=dict(range=[0, 1273], showgrid=False, zeroline=False),
    yaxis=dict(range=[1279, 0], showgrid=False, zeroline=False),
    width=700,
    height=702,
    plot_bgcolor="white",
    images=[
        dict(
            source=image_source,
            xref="x",
            yref="y",
            x=0,
            y=0,
            sizex=1273,
            sizey=1279,
            sizing="stretch",
            opacity=1,
            layer="below",
        )
    ],
)

# --- CSVデータを描画 ---
if not df_batter.empty:
    df_batter["打球X"] = pd.to_numeric(df_batter["X"], errors="coerce")
    df_batter["打球Y"] = pd.to_numeric(df_batter["Y"], errors="coerce")
    fig.add_trace(
        go.Scatter(
            x=df_batter["打球X"],
            y=df_batter["打球Y"],
            mode="markers+text",
            marker=dict(
                size=22,
                color=[get_color_by_pitchtype(pt) for pt in df_batter["PitchType"]],
                symbol=[get_symbol_by_hittype(ht) for ht in df_batter["HitType"]],
            ),
            text=[
                f"{b} / {p} / {h}"
                for b, p, h in zip(
                    df_batter["Batter"], df_batter["PitchType"], df_batter["HitType"]
                )
            ],
            name="CSVデータ",
        )
    )

    # 原点から直線
    for _, row in df_batter.iterrows():
        fig.add_trace(
            go.Scatter(
                x=[632, row["打球X"]],
                y=[1069, row["打球Y"]],
                mode="lines",
                line=dict(color=get_color_by_pitchtype(row["PitchType"]), width=3),
                showlegend=False,
                hoverinfo="skip",
            )
        )

# --- 描画 ---
st.plotly_chart(fig, use_container_width=True)
