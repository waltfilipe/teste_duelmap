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


def _rgba_to_plotly_rgb(rgba):
    r, g, b, a = rgba
    r255 = int(r * 255)
    g255 = int(g * 255)
    b255 = int(b * 255)
    return f"rgb({r255},{g255},{b255})", float(a)


@st.cache_data(show_spinner=False)
def make_pitch_background(pitch_color="#f5f5f5", line_color="#4a4a4a"):
    """Renderiza o pitch via mplsoccer e devolve uma imagem (base64) para usar como fundo no Plotly."""
    pitch = Pitch(
        pitch_type="statsbomb",
        pitch_color=pitch_color,
        line_color=line_color,
    )

    # Dimensoes do sistema de coordenadas (StatsBomb: 120x80)
    pitch_length = getattr(pitch.dim, "pitch_length", 120)
    pitch_width = getattr(pitch.dim, "pitch_width", 80)

    fig, ax = pitch.draw(figsize=(12, 8))
    ax.set_axis_off()
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, pad_inches=0)
    plt.close(fig)

    encoded = base64.b64encode(buf.getvalue()).decode("utf-8")
    bg_src = f"data:image/png;base64,{encoded}"
    return bg_src, float(pitch_length), float(pitch_width)


def build_app_dataframe():
    # ==========================
    # Eventos (mesma ordem do seu codigo)
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
    return df


def apply_explicit_video_mapping(df):
    """
    Mapeamento EXPLICITO evento/icone -> nome do arquivo de video em videos/.

    Regra:
      - O i-ésimo evento da lista esta associado ao i-ésimo valor dessa lista.
      - Defina NOME do arquivo (ex: "event_12.mp4") ou None para "sem video".
    """

    # Coloque aqui os NOMES dos arquivos dentro da pasta `video/`.
    # Exemplo: "duel_won_0.mp4", "event_1.webm", etc.
    #
    # Dica: deixe uma string ou None para cada evento (na mesma ordem do vetor `eventos`).
    VIDEO_FILES = [
        None,  # 0
        None,  # 1
        None,  # 2
        None,  # 3
        None,  # 4
        None,  # 5
        None,  # 6
        None,  # 7
        None,  # 8
        None,  # 9
        None,  # 10
        None,  # 11
        None,  # 12
        None,  # 13
        None,  # 14
        None,  # 15
        None,  # 16
        None,  # 17
        None,  # 18
        None,  # 19
    ]

    if len(VIDEO_FILES) != len(df):
        st.error(
            f"VIDEO_FILES precisa ter {len(df)} entradas (tem {len(VIDEO_FILES)})."
        )
        st.stop()

    base_dir = os.path.abspath(os.path.dirname(__file__))
    video_dir = os.path.join(base_dir, "video")
    if not os.path.isdir(video_dir):
        st.error(
            f"Pasta `video/` nao encontrada em: {video_dir}. Coloque seus videos la."
        )
        st.stop()

    abs_paths = []
    missing = []
    for i, filename in enumerate(VIDEO_FILES):
        if filename is None:
            abs_paths.append(None)
            continue
        path = os.path.join(video_dir, filename)
        abs_paths.append(path)
        if not os.path.isfile(path):
            missing.append((i, filename))

    if missing:
        st.warning(
            "Alguns videos mapeados nao foram encontrados. Vou mostrar o mapa mesmo assim, mas esses eventos vao ficar sem video.\n"
            + "\n".join([f"evento {i}: {name}" for i, name in missing])
        )

    df["video_filename"] = VIDEO_FILES
    df["video_path"] = abs_paths
    return df


def build_plotly_figure(df, bg_src, pitch_length, pitch_width):
    # Se os icones ficarem "espelhados" no eixo Y, mude para True.
    Y_FLIP = True

    def maybe_flip_y(y):
        return (pitch_width - y) if Y_FLIP else y

    tipo_style = {
        # Tamanhos maiores que os anteriores (Plotly usa "px", entao 14-18 podia ficar pouco visivel).
        "DUEL WON": dict(symbol="circle", color=(0, 0.6, 0, 0.9), size=22, lw=1.2),
        "DUEL LOST": dict(symbol="x", color=(1, 0, 0, 0.8), size=26, lw=3.2),
        "AERIAL WON": dict(symbol="triangle-up", color=(0.2, 0.3, 1, 0.9), size=28, lw=1.2),
        "AERIAL LOST": dict(symbol="triangle-down", color=(1, 0, 0, 0.8), size=28, lw=3.2),
        "FOULED": dict(symbol="square", color=(1, 0.6, 0, 0.9), size=24, lw=1.2),
        "FOUL": dict(symbol="cross", color=(0.6, 0.2, 0.2, 0.9), size=28, lw=3.2),
        "INTERCEPTION": dict(symbol="diamond", color=(0.3, 0.3, 0.3, 0.9), size=22, lw=1.2),
        "CLEARANCE": dict(symbol="hexagon", color=(0, 0.8, 0.8, 0.9), size=28, lw=1.2),
        "BLOCK": dict(symbol="pentagon", color=(0.6, 0.1, 0.6, 0.9), size=28, lw=1.2),
    }

    fig = go.Figure()

    # Fundo do pitch: x=0..pitch_length e y=0..pitch_width
    fig.add_layout_image(
        dict(
            source=bg_src,
            xref="x",
            yref="y",
            x=0,
            y=0,
            sizex=pitch_length,
            sizey=pitch_width,
            sizing="stretch",
            layer="below",
            xanchor="left",
            yanchor="bottom",
        )
    )

    for tipo, style in tipo_style.items():
        sub = df[df["tipo"] == tipo].copy()
        if sub.empty:
            continue

        sub["y_plot"] = sub["y"].apply(maybe_flip_y)
        sub["x_plot"] = sub["x"]

        rgb, alpha = _rgba_to_plotly_rgb(style["color"])

        fig.add_trace(
            go.Scatter(
                x=sub["x_plot"],
                y=sub["y_plot"],
                mode="markers",
                name=tipo.title().replace("_", " "),
                customdata=sub["idx"],
                marker=dict(
                    symbol=style["symbol"],
                    size=style["size"],
                    color=rgb,
                    opacity=alpha,
                    line=dict(width=style["lw"], color=rgb),
                ),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "x=%{x:.2f}, y=%{y:.2f}<br>"
                    "<extra></extra>"
                ),
                text=[tipo.title().replace("_", " ")] * len(sub),
            )
        )

    # Titulo + direcao (como no seu codigo, em coordenadas paper)
    fig.add_annotation(
        text="Attack Direction",
        x=0.45,
        y=0.02,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(color="#333333", size=10),
    )

    fig.add_shape(
        type="path",
        path="M 0.40 0.05 L 0.50 0.05 L 0.495 0.045 L 0.495 0.055 Z",
        xref="paper",
        yref="paper",
        line=dict(color="#333333", width=2),
        fillcolor="#333333",
    )

    # Desabilita zoom/pan e fixa ranges (evita "zoom automatico")
    fig.update_layout(
        title=dict(text="Defensive & Duel Map", x=0.5, xanchor="center"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=220, t=60, b=10),
        legend=dict(x=1.02, y=1, bgcolor="white", bordercolor="black"),
        dragmode=False,
    )

    fig.update_xaxes(
        range=[0, pitch_length],
        visible=False,
        fixedrange=True,
    )
    fig.update_yaxes(
        range=[0, pitch_width],
        visible=False,
        fixedrange=True,
    )

    return fig


df = build_app_dataframe()
df = apply_explicit_video_mapping(df)

bg_src, pitch_length, pitch_width = make_pitch_background()
fig = build_plotly_figure(df, bg_src, pitch_length, pitch_width)

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
    if not selected:
        st.info("Nenhum ponto selecionado.")
    else:
        # `selected[0]` vem de um clique no trace.
        raw = selected[0].get("customdata", None)
        if isinstance(raw, (list, tuple)) and raw:
            event_idx = raw[0]
        else:
            event_idx = raw

        if event_idx is None:
            st.warning("Clique detectado, mas nao foi possivel identificar o evento.")
        else:
            row = df.loc[int(event_idx)]
            video_path = row["video_path"]
            if not video_path:
                st.info(f"`{row['tipo']}`: video nao mapeado (coloque um arquivo em `VIDEO_FILES`).")
            else:
                if not os.path.isfile(video_path):
                    st.error(f"Arquivo nao encontrado: {video_path}")
                else:
                    st.write(f"{row['tipo']} - {os.path.basename(video_path)}")
                    st.video(video_path)
