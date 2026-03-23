import os
import re
import io
import base64

import streamlit as st
import pandas as pd
from mplsoccer import Pitch
import matplotlib.pyplot as plt

import plotly.graph_objects as go
from streamlit_plotly_events import plotly_events


st.set_page_config(page_title="Defensive & Duel Map", layout="wide")

# ==========================
# Dados / Eventos (mesmos do seu código)
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
# Carregar vídeos da pasta
# ==========================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
VIDEO_DIR = os.path.join(BASE_DIR, "videos")

exts = (".mp4", ".webm", ".mov", ".mkv", ".avi")
video_files = sorted([f for f in os.listdir(VIDEO_DIR) if f.lower().endswith(exts)])

def assign_videos_by_index(files, n_events):
    # Tentativa: se o nome do arquivo tiver número, usar como índice do evento.
    # Ex: event_0.mp4, frame12.webm, etc.
    number_map = {}
    for f in files:
        nums = re.findall(r"\d+", f)
        if nums:
            number_map[int(nums[0])] = f

    # Se parece que bateu, usa por índice; caso contrário, fallback por ordem.
    if all(i in number_map for i in range(n_events)):
        return [number_map[i] for i in range(n_events)]

    return files[:n_events] if len(files) >= n_events else None

assigned = assign_videos_by_index(video_files, len(df))
if assigned is None:
    st.error(
        f"Não encontrei vídeos suficientes em `videos/` (precisa {len(df)}, achei {len(video_files)}). "
        f"Atual: {video_files}"
    )
    st.stop()

df["video_filename"] = assigned
df["video_path"] = df["video_filename"].apply(lambda f: os.path.join(VIDEO_DIR, f))

# ==========================
# Fundo do pitch via mplsoccer -> imagem
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
# Plotly figure (clicável)
# ==========================
tipo_style = {
    "DUEL WON":     dict(symbol="circle",      color=(0, 0.6, 0, 0.9),   size=120, lw=0.5),
    "DUEL LOST":    dict(symbol="x",           color=(1, 0, 0, 0.8),     size=120, lw=2.5),
    "AERIAL WON":   dict(symbol="triangle-up",   color=(0.2, 0.3, 1, 0.9), size=140, lw=0.5),
    "AERIAL LOST":  dict(symbol="triangle-down", color=(1, 0, 0, 0.8),   size=140, lw=0.5),
    "FOULED":       dict(symbol="square",      color=(1, 0.6, 0, 0.9),   size=120, lw=0.5),
    "FOUL":         dict(symbol="cross",       color=(0.6, 0.2, 0.2, 0.9), size=140, lw=0.5),
    "INTERCEPTION": dict(symbol="diamond",     color=(0.3, 0.3, 0.3, 0.9), size=120, lw=0.5),
    "CLEARANCE":    dict(symbol="hexagon",     color=(0, 0.8, 0.8, 0.9), size=140, lw=0.5),
    "BLOCK":        dict(symbol="pentagon",    color=(0.6, 0.1, 0.6, 0.9), size=140, lw=0.5),
}

def rgba_to_plotly(color):
    r, g, b, a = color
    # color em 0..1
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

# Pontos (um trace por tipo, pra legendas e clique ficarem claros)
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
                sizemode="area",     # aproxima o "s=size" do matplotlib (área)
                color=c_rgb,
                opacity=c_alpha,
                line=dict(width=style["lw"], color=c_rgb),
            ),
            customdata=sub["video_path"],
            hovertemplate=(
                "<b>%{text}</b><br>"
                "x=%{x:.2f}, y=%{y:.2f}<br>"
                "<extra></extra>"
            ),
            text=[tipo.title().replace("_", " ")] * len(sub),
        )
    )

# Título + seta (como no seu)
fig.update_layout(
    title=dict(text="Defensive & Duel Map", x=0.5),
    margin=dict(l=10, r=220, t=60, b=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    legend=dict(x=1.02, y=1, bgcolor="white", bordercolor="black"),
)

# Esconde eixos
fig.update_xaxes(range=[0, pitch_length], visible=False, constrain="domain")
fig.update_yaxes(range=[0, pitch_width], visible=False, scaleanchor="x")

# Texto da direção (paper coords)
fig.add_annotation(
    text="Attack Direction",
    x=0.45, y=0.02,
    xref="paper", yref="paper",
    showarrow=False,
    font=dict(color="#333333", size=10),
)

# Seta (paper coords) aproximada
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
            # Mostra metadados e vídeo
            st.write(f"`{os.path.basename(video_path)}`")
            st.video(video_path)
        else:
            st.info("Clique detectado, mas não veio o vídeo associado.")
    else:
        st.info("Nenhum ponto selecionado.")
