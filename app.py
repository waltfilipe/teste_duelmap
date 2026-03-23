import os
import io
import base64
import pandas as pd
from mplsoccer import Pitch
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
import streamlit as st
import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events
st.set_page_config(page_title="Defensive & Duel Map", layout="wide")
# ==========================
# Dados / Eventos (mesma lista)
# ==========================
eventos = [
    ("DUEL WON", 41.71, 59.45),
    ("DUEL LOST", 18.61, 41.16),
    ("DUEL WON", 7.14, 55.46),
    ("AERIAL WON", 8.47, 43.82),
    ("FOUL", 56.84, 57.79),
    ("DUEL WON", 27.09, 73.08),
    ("FOULED", 56.84, 67.10),
    ("DUEL WON", 16.78, 65.10),
    ("DUEL WON", 20.44, 67.26),
    ("AERIAL WON", 25.76, 67.43),
    ("DUEL WON", 13.95, 36.51),
    ("DUEL WON", 23.76, 50.14),
    ("CLEARANCE", 19.77, 43.16),
    ("INTERCEPTION", 32.74, 49.48),
    ("DUEL WON", 27.58, 63.11),
    ("DUEL LOST", 15.62, 38.17),
    ("BLOCK", 14.62, 54.63),
    ("DUEL WON", 14.62, 58.29),
    ("CLEARANCE", 13.95, 41.16),
    ("AERIAL LOST", 12.29, 45.98),
]
df = pd.DataFrame(eventos, columns=["tipo", "x", "y"])
df["idx"] = range(len(df))
# ==========================
# PASTA VIDEOS + MAPEAMENTO EXPLÍCITO
# ==========================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "videos")
# Preencha aqui: key = índice do evento (mesmo índice da lista "eventos")
# value = nome exato do arquivo dentro da pasta "videos/"
EVENT_VIDEO_MAP = {
    0: "Duel Lost 1.mp4",
    1: "Duel Lost 2.mp4",
    2: "2_DUEL_WON.mp4",
    3: "3_AERIAL_WON.mp4",
    4: "4_Foul.mp4",
    5: "5_DUEL_WON.mp4",
    6: "6_Fouled.mp4",
    7: "7_DUEL_WON.mp4",
    8: "8_DUEL_WON.mp4",
    9: "9_AERIAL_WON.mp4",
    10: "10_DUEL_WON.mp4",
    11: "11_DUEL_WON.mp4",
    12: "12_CLEARANCE.mp4",
    13: "13_INTERCEPTION.mp4",
    14: "14_DUEL_WON.mp4",
    15: "Duel Lost 3.mp4",
    16: "16_BLOCK.mp4",
    17: "17_DUEL_WON.mp4",
    18: "18_CLEARANCE.mp4",
    19: "19_AERIAL_LOST.mp4",
}
# Dica: pode deixar alguns indices fora. Se faltar, o clique vai mostrar "sem vídeo".
def build_video_paths(df_in: pd.DataFrame, video_dir: str, mapping: dict) -> pd.DataFrame:
    filenames = []
    paths = []
    missing = []
    for i in df_in["idx"].tolist():
        fname = mapping.get(i)
        filenames.append(fname)
        if fname is None:
            paths.append(None)
            missing.append(i)
        else:
            full = os.path.join(video_dir, fname)
            if os.path.exists(full):
                paths.append(full)
            else:
                paths.append(None)
                missing.append(i)
    out = df_in.copy()
    out["video_filename"] = filenames
    out["video_path"] = paths
    if missing:
        st.warning(
            "Alguns eventos não têm vídeo mapeado/arquivo não encontrado: "
            + ", ".join(map(str, missing))
            + ". Clique nesses pontos vai informar que não existe vídeo."
        )
    return out
df = build_video_paths(df, VIDEO_DIR, EVENT_VIDEO_MAP)
# ==========================
# Fundo do pitch -> imagem (para usar no Plotly)
# ==========================
pitch = Pitch(
    pitch_type="statsbomb",
    pitch_color="#f5f5f5",
    line_color="#4a4a4a",
)
pitch_length = getattr(pitch.dim, "pitch_length", 120)
pitch_width = getattr(pitch.dim, "pitch_width", 80)
bg_fig, bg_ax = pitch.draw(figsize=(12, 8))
bg_ax.set_axis_off()
bg_fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
buf = io.BytesIO()
bg_fig.savefig(buf, format="png", dpi=200, bbox_inches="tight", pad_inches=0)
plt.close(bg_fig)
encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
bg_src = f"data:image/png;base64,{encoded}"
# ==========================
# Estilos por tipo (mesma lógica do seu código)
# ==========================
tipo_style = {
    "DUEL WON":     dict(symbol="circle",       color=(0, 0.6, 0, 0.9),   size=120, lw=0.5),
    "DUEL LOST":    dict(symbol="x",           color=(1, 0, 0, 0.8),     size=120, lw=2.5),
    "AERIAL WON":   dict(symbol="triangle-up",   color=(0.2, 0.3, 1, 0.9), size=140, lw=0.5),
    "AERIAL LOST":  dict(symbol="triangle-down", color=(1, 0, 0, 0.8),     size=140, lw=0.5),
    "FOULED":       dict(symbol="square",      color=(1, 0.6, 0, 0.9),   size=120, lw=0.5),
    "FOUL":         dict(symbol="cross",       color=(0.6, 0.2, 0.2, 0.9), size=140, lw=0.5),
    "INTERCEPTION": dict(symbol="diamond",     color=(0.3, 0.3, 0.3, 0.9), size=120, lw=0.5),
    "CLEARANCE":    dict(symbol="hexagon",     color=(0, 0.8, 0.8, 0.9),   size=140, lw=0.5),
    "BLOCK":        dict(symbol="pentagon",    color=(0.6, 0.1, 0.6, 0.9), size=140, lw=0.5),
}
def rgba_to_plotly(color):
    r, g, b, a = color
    r255 = int(r * 255)
    g255 = int(g * 255)
    b255 = int(b * 255)
    return f"rgb({r255},{g255},{b255})", a
fig = go.Figure()
# Fundo do pitch
fig.add_layout_image(
    dict(
        source=bg_src,
        xref="x",
        yref="y",
        x=0,
        y=pitch_width,
        sizex=pitch_length,
        sizey=pitch_width,
        sizing="stretch",
        layer="below",
    )
)
# Pontos por tipo (separados por trace)
for tipo, style in tipo_style.items():
    mask = df["tipo"] == tipo
    if not mask.any():
        continue
    c_rgb, c_alpha = rgba_to_plotly(style["color"])
    sub = df.loc[mask]
    fig.add_trace(
        go.Scatter(
            x=sub["x"],
            y=sub["y"],
            mode="markers",
            name=tipo.title().replace("_", " "),
            marker=dict(
                symbol=style["symbol"],
                size=style["size"],
                sizemode="area",
                color=c_rgb,
                opacity=c_alpha,
                line=dict(width=style["lw"], color=c_rgb),
            ),
            customdata=sub["video_path"],  # aqui vai o caminho do vídeo
            hovertemplate="<b>%{text}</b><br>x=%{x:.2f}, y=%{y:.2f}<extra></extra>",
            text=[tipo.title().replace("_", " ")] * len(sub),
        )
    )
# Layout (eixos escondidos)
fig.update_xaxes(range=[0, pitch_length], visible=False, constrain="domain")
fig.update_yaxes(range=[0, pitch_width], visible=False, scaleanchor="x")
# Título
fig.update_layout(
    title=dict(text="Defensive & Duel Map", x=0.5),
    margin=dict(l=10, r=220, t=60, b=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    showlegend=True,
)
# Texto "Attack Direction" e seta (aprox. em coords de paper)
fig.add_annotation(
    text="Attack Direction",
    x=0.45, y=0.02,
    xref="paper", yref="paper",
    showarrow=False,
    font=dict(color="#333333", size=10),
)
fig.add_shape(
    type="path",
    path="M 0.40 0.05 L 0.50 0.05 L 0.485 0.045 L 0.485 0.055 Z",
    xref="paper", yref="paper",
    line=dict(color="#333333", width=2),
    fillcolor="#333333",
)
# ==========================
# Layout Streamlit: mapa + vídeo
# ==========================
left, right = st.columns([2.2, 1], gap="large")
with left:
    selected = plotly_events(
        fig,
        click_event=True,
        hover_event=False,
        select_event=False,
        override_height=650,
        key="duel_map_click",
    )
with right:
    st.write("Clique em um ponto do mapa para abrir o vídeo.")
    if selected:
        video_path = selected[0].get("customdata", None)
        if video_path:
            st.write(f"`{os.path.basename(video_path)}`")
            st.video(video_path)
        else:
            st.info("Clique detectado, mas esse evento não tem vídeo mapeado/arquivo encontrado.")
    else:
        st.info("Nenhum ponto selecionado.")
