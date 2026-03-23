import streamlit as st
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import pandas as pd
from matplotlib.patches import FancyArrowPatch
from streamlit_image_coordinates import streamlit_image_coordinates
from io import BytesIO
import numpy as np
from PIL import Image
from matplotlib.lines import Line2D

# ==========================
# Page Configuration
# ==========================
st.set_page_config(layout="wide", page_title="Defensive & Duel Map (Clickable)")

st.title("Defensive & Duel Map")
st.caption("Clique nos ícones do campo para selecionar o evento (e tocar o vídeo, se existir).")

# ==========================
# Eventos (ADICIONE o caminho do vídeo em `video`)
# ==========================
eventos = [
    ("DUEL WON", 41.71, 59.45, None),
    ("DUEL LOST", 18.61, 41.16, "Duel Lost 1"),
    ("DUEL WON", 7.14, 55.46, None),
    ("AERIAL WON", 8.47, 43.82, None),
    ("FOUL", 56.84, 57.79, None),

    ("DUEL WON", 27.09, 73.08, None),
    ("FOULED", 56.84, 67.10, None),
    ("DUEL WON", 16.78, 65.10, None),
    ("DUEL WON", 20.44, 67.26, None),
    ("AERIAL WON", 25.76, 67.43, None),

    ("DUEL WON", 13.95, 36.51, None),
    ("DUEL WON", 23.76, 50.14, None),
    ("CLEARANCE", 19.77, 43.16, None),
    ("INTERCEPTION", 32.74, 49.48, None),
    ("DUEL WON", 27.58, 63.11, None),

    ("DUEL LOST", 15.62, 38.17, None),
    ("BLOCK", 14.62, 54.63, None),
    ("DUEL WON", 14.62, 58.29, None),
    ("CLEARANCE", 13.95, 41.16, None),
    ("AERIAL LOST", 12.29, 45.98, None),
]

df = pd.DataFrame(eventos, columns=["tipo", "x", "y", "video"])

def get_style(tipo, has_video):
    tipo = str(tipo).upper()

    lw = 0.5
    size = 120

    if tipo == "DUEL LOST":
        marker = "x"
        color = (1, 0, 0, 0.8)
        lw = 2.5
        size = 120
    elif tipo == "DUEL WON":
        marker = "o"
        color = (0, 0.6, 0, 0.9)
        size = 120
    elif tipo == "AERIAL WON":
        marker = "^"
        color = (0.2, 0.3, 1, 0.9)
        size = 140
    elif tipo == "AERIAL LOST":
        marker = "v"
        color = (1, 0, 0, 0.8)
        size = 140
    elif tipo == "FOULED":
        marker = "s"
        color = (1, 0.6, 0, 0.9)
        size = 120
    elif tipo == "FOUL":
        marker = "P"
        color = (0.6, 0.2, 0.2, 0.9)
        size = 140
    elif tipo == "INTERCEPTION":
        marker = "D"
        color = (0.3, 0.3, 0.3, 0.9)
        size = 120
    elif tipo == "CLEARANCE":
        marker = "h"
        color = (0, 0.8, 0.8, 0.9)
        size = 140
    elif tipo == "BLOCK":
        marker = "p"
        color = (0.6, 0.1, 0.6, 0.9)
        size = 140
    else:
        marker = "o"
        color = (0.5, 0.5, 0.5, 0.8)
        size = 120

    # Destaque para quem tem vídeo
    # (a face continua colorida; a borda vira preta/mais marcada)
    if has_video:
        lw = max(lw, 2.0)

    return marker, color, size, lw

# ==========================
# Main Layout
# ==========================
col_map, col_vid = st.columns([1, 1])

selected_event = None

with col_map:
    pitch = Pitch(
        pitch_type="statsbomb",
        pitch_color="#f5f5f5",
        line_color="#4a4a4a",
    )

    fig, ax = pitch.draw(figsize=(12, 8))

    # ===== Plot =====
    for _, row in df.iterrows():
        has_vid = row["video"] is not None
        marker, color, size, lw = get_style(row["tipo"], has_vid)

        # Borda: preta se tiver vídeo, senão mesma cor
        ec = "black" if has_vid else color

        ax.scatter(
            row.x,
            row.y,
            marker=marker,
            s=size,
            color=color,
            edgecolors=ec,
            linewidths=lw,
            zorder=3,
        )

    # ===== Legenda (opcional, mantendo seu estilo) =====
    legend_elements = [
        Line2D([0], [0], marker="o", color="w", label="Duel Won",
               markerfacecolor=(0, 0.6, 0, 0.9), markersize=10, linestyle="None"),
        Line2D([0], [0], marker="x", color="w", label="Duel Lost",
               markeredgecolor=(1, 0, 0, 0.8), markeredgewidth=2, markersize=10, linestyle="None"),
        Line2D([0], [0], marker="^", color="w", label="Aerial Won",
               markerfacecolor=(0.2, 0.3, 1, 0.9), markersize=10, linestyle="None"),
        Line2D([0], [0], marker="v", color="w", label="Aerial Lost",
               markerfacecolor=(1, 0, 0, 0.8), markersize=10, linestyle="None"),
        Line2D([0], [0], marker="D", color="w", label="Interception",
               markerfacecolor=(0.3, 0.3, 0.3, 0.9), markersize=10, linestyle="None"),
        Line2D([0], [0], marker="h", color="w", label="Clearance",
               markerfacecolor=(0, 0.8, 0.8, 0.9), markersize=10, linestyle="None"),
        Line2D([0], [0], marker="p", color="w", label="Block",
               markerfacecolor=(0.6, 0.1, 0.6, 0.9), markersize=10, linestyle="None"),
        Line2D([0], [0], marker="s", color="w", label="Fouled",
               markerfacecolor=(1, 0.6, 0, 0.9), markersize=10, linestyle="None"),
        Line2D([0], [0], marker="P", color="w", label="Foul",
               markerfacecolor=(0.6, 0.2, 0.2, 0.9), markersize=10, linestyle="None"),
    ]

    ax.legend(
        handles=legend_elements,
        loc="upper left",
        bbox_to_anchor=(1.02, 1),
        framealpha=1.0,
        facecolor="white",
        edgecolor="black",
        title="Eventos",
        fontsize=10,
    )

    # ===== Title =====
    ax.set_title("Defensive & Duel Map", fontsize=16, fontweight="bold", pad=15)

    # ===== Attack Direction =====
    arrow = FancyArrowPatch(
        (0.40, 0.05),
        (0.50, 0.05),
        transform=fig.transFigure,
        arrowstyle="-|>",
        mutation_scale=15,
        linewidth=2,
        color="#333333",
    )
    fig.patches.append(arrow)

    fig.text(
        0.45, 0.02,
        "Attack Direction",
        ha="center",
        va="center",
        fontsize=10,
        color="#333333",
    )

    fig.tight_layout()

    # ===== Convert plot to image for click tracking =====
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    buf.seek(0)
    img_obj = Image.open(buf)

    click = streamlit_image_coordinates(img_obj, width=700)

# ==========================
# Interaction Logic (clicar -> evento mais próximo)
# ==========================
if click is not None:
    real_w, real_h = img_obj.size
    disp_w, disp_h = click["width"], click["height"]

    # Mapeia o clique da imagem exibida -> pixels reais
    pixel_x = click["x"] * (real_w / disp_w)
    pixel_y = click["y"] * (real_h / disp_h)

    # Inverte Y para Matplotlib
    mpl_pixel_y = real_h - pixel_y

    # Converte pixels -> coordenadas do campo
    field_x, field_y = ax.transData.inverted().transform((pixel_x, mpl_pixel_y))

    # Distância até cada marcador
    dist = np.sqrt((df["x"] - field_x) ** 2 + (df["y"] - field_y) ** 2)

    # Ajuste fino do “raio” de seleção
    RADIUS = 5
    candidates = df[dist < RADIUS]

    if not candidates.empty:
        idx_min = (dist[dist < RADIUS]).idxmin()
        selected_event = df.loc[idx_min]

# ==========================
# Video Display & Stats
# ==========================
with col_vid:
    st.subheader("Video Analysis")

    if selected_event is not None:
        st.success(
            f"**Selected Event:** {selected_event['tipo']} at [X: {selected_event['x']}, Y: {selected_event['y']}]"
        )

        if selected_event["video"]:
            try:
                st.video(selected_event["video"])
            except Exception:
                st.error(f"Video file not found: {selected_event['video']}")
        else:
            st.warning("No video footage available for this selected event.")
    else:
        st.info("Clique em um ícone no campo para selecionar um evento.")
