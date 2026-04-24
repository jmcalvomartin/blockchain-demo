from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ecc_core import (
    ECPoint,
    FiniteWeierstrassCurve,
    RealWeierstrassCurve,
    SECP256R1,
    format_point,
    p256_ecdh_demo,
)


st.set_page_config(
    page_title="Elliptic Curves Classroom Lab",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .hero {
        padding: 1.5rem 1.6rem;
        border-radius: 20px;
        background: linear-gradient(135deg, #0f172a 0%, #123c69 50%, #1d4ed8 100%);
        color: white;
        margin-bottom: 1.2rem;
        box-shadow: 0 14px 35px rgba(15, 23, 42, 0.18);
    }
    .hero h1 {
        margin: 0;
        font-size: 2.4rem;
    }
    .hero p {
        margin: 0.55rem 0 0 0;
        font-size: 1rem;
        opacity: 0.95;
    }
    .soft-box {
        background: #f8fbff;
        border: 1px solid #d7e8ff;
        border-radius: 16px;
        padding: 1rem 1.1rem;
        margin: 0.8rem 0;
    }
    .accent-box {
        background: linear-gradient(180deg, #fffdf5 0%, #fff8e8 100%);
        border-left: 5px solid #f59e0b;
        border-radius: 0 14px 14px 0;
        padding: 1rem 1.1rem;
        margin: 0.8rem 0;
    }
    .success-box {
        background: linear-gradient(180deg, #f3fff8 0%, #ebfff2 100%);
        border-left: 5px solid #16a34a;
        border-radius: 0 14px 14px 0;
        padding: 1rem 1.1rem;
        margin: 0.8rem 0;
    }
    .formula-box {
        background: #0f172a;
        color: #e2e8f0;
        border-radius: 14px;
        padding: 0.9rem 1rem;
        font-family: Consolas, monospace;
        margin: 0.8rem 0;
    }
    .actor {
        background: white;
        border: 1px solid #dbe4f0;
        border-radius: 18px;
        padding: 1rem;
        box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="hero">
    <h1>Elliptic Curves Classroom Lab</h1>
    <p>Herramienta visual para enseñar suma de puntos en curvas de Weierstrass y el intercambio de claves ECDH.</p>
</div>
""",
    unsafe_allow_html=True,
)


def build_real_curve_figure(curve: RealWeierstrassCurve, p, q, outcome, x_range=(-3.2, 3.2)) -> go.Figure:
    xs = np.linspace(x_range[0], x_range[1], 1200)
    y_top = []
    y_bottom = []
    for x in xs:
        rhs = curve.rhs(float(x))
        if rhs >= 0:
            y = math.sqrt(rhs)
            y_top.append(y)
            y_bottom.append(-y)
        else:
            y_top.append(np.nan)
            y_bottom.append(np.nan)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=y_top, mode="lines", line=dict(color="#2563eb", width=3), name="Curva"))
    fig.add_trace(go.Scatter(x=xs, y=y_bottom, mode="lines", line=dict(color="#2563eb", width=3), showlegend=False))

    px, py = p
    qx, qy = q
    fig.add_trace(
        go.Scatter(
            x=[px, qx],
            y=[py, qy],
            mode="markers+text",
            marker=dict(size=12, color=["#f97316", "#0f766e"]),
            text=["P", "Q"],
            textposition="top center",
            name="Puntos",
        )
    )

    if outcome["sum"] is not None:
        sx, sy = outcome["sum"]
        tx, ty = outcome["third_intersection"]
        slope = outcome["lambda"]
        intercept = py - slope * px
        line_x = np.linspace(x_range[0], x_range[1], 300)
        line_y = slope * line_x + intercept
        fig.add_trace(
            go.Scatter(x=line_x, y=line_y, mode="lines", line=dict(color="#f59e0b", dash="dash"), name="Secante / tangente")
        )
        fig.add_trace(
            go.Scatter(
                x=[tx, sx],
                y=[ty, sy],
                mode="markers+text",
                marker=dict(size=12, color=["#7c3aed", "#dc2626"]),
                text=["Tercer punto", "P + Q" if outcome["mode"] == "add" else "2P"],
                textposition="bottom center",
                name="Resultado",
            )
        )
    else:
        fig.add_vline(x=px, line_dash="dash", line_color="#f59e0b")

    fig.update_layout(
        title="Suma geométrica sobre los números reales",
        xaxis_title="x",
        yaxis_title="y",
        height=540,
        legend=dict(orientation="h"),
    )
    fig.update_xaxes(zeroline=True, zerolinecolor="#94a3b8")
    fig.update_yaxes(zeroline=True, zerolinecolor="#94a3b8", scaleanchor="x", scaleratio=1)
    return fig


def sample_real_points(curve: RealWeierstrassCurve) -> list[tuple[str, tuple[float, float]]]:
    samples: list[tuple[str, tuple[float, float]]] = []
    for x in np.linspace(-1.1, 2.8, 40):
        rhs = curve.rhs(float(x))
        if rhs > 0:
            y = math.sqrt(rhs)
            top = (round(float(x), 3), round(y, 3))
            bottom = (round(float(x), 3), round(-y, 3))
            samples.append((f"({top[0]}, {top[1]})", top))
            samples.append((f"({bottom[0]}, {bottom[1]})", bottom))
    return samples[:28]


def point_choices(points: list[ECPoint]) -> list[ECPoint]:
    return [point for point in points if not point.infinity]


def build_field_figure(curve: FiniteWeierstrassCurve, points: list[ECPoint], highlight: list[tuple[str, ECPoint]]) -> go.Figure:
    data_points = point_choices(points)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[p.x for p in data_points],
            y=[p.y for p in data_points],
            mode="markers",
            marker=dict(size=9, color="#93c5fd", line=dict(color="#1d4ed8", width=1)),
            name="Puntos de la curva",
        )
    )
    colors = ["#f97316", "#0f766e", "#dc2626", "#7c3aed"]
    for index, (label, point) in enumerate(highlight):
        if point.infinity:
            continue
        fig.add_trace(
            go.Scatter(
                x=[point.x],
                y=[point.y],
                mode="markers+text",
                marker=dict(size=14, color=colors[index % len(colors)]),
                text=[label],
                textposition="top center",
                name=label,
            )
        )
    fig.update_layout(
        title=f"Puntos de y² = x³ + {curve.a}x + {curve.b} sobre F_{curve.p}",
        xaxis_title="x",
        yaxis_title="y",
        height=500,
        legend=dict(orientation="h"),
    )
    fig.update_xaxes(dtick=1)
    fig.update_yaxes(dtick=1, scaleanchor="x", scaleratio=1)
    return fig


def build_multiple_table(curve: FiniteWeierstrassCurve, base_point: ECPoint, count: int) -> pd.DataFrame:
    rows = []
    for k, point in curve.multiples(base_point, count):
        rows.append({"k": k, "kG": format_point(point)})
        if point.infinity:
            break
    return pd.DataFrame(rows)


def short_hex(value: int, size: int = 20) -> str:
    text = hex(value)
    if len(text) <= size:
        return text
    return f"{text[:size]}...{text[-8:]}"


with st.sidebar:
    st.header("Controles globales")
    st.caption("La pestaña activa usa estos parámetros cuando corresponde.")
    real_a = st.slider("Curva real: a", min_value=-4.0, max_value=4.0, value=-1.0, step=0.5)
    real_b = st.slider("Curva real: b", min_value=-4.0, max_value=4.0, value=1.0, step=0.5)
    field_p = st.selectbox("Campo finito: primo p", options=[17, 19, 23, 29, 97], index=4)
    field_a = st.number_input("Campo finito: a", min_value=-20, max_value=20, value=2, step=1)
    field_b = st.number_input("Campo finito: b", min_value=-20, max_value=20, value=3, step=1)

real_curve = RealWeierstrassCurve(real_a, real_b)
field_curve = FiniteWeierstrassCurve(field_p, int(field_a), int(field_b))

if not real_curve.is_nonsingular():
    st.error("La curva real es singular. Cambie a y b para que 4a³ + 27b² ≠ 0.")
    st.stop()

if not field_curve.is_nonsingular():
    st.error("La curva sobre campo finito es singular. Cambie a, b o p.")
    st.stop()

field_points = field_curve.list_points()
available_points = point_choices(field_points)
default_p = next((point for point in available_points if point.x == 3 and point.y == 6), available_points[0])
default_q = next((point for point in available_points if point.x == 80 and point.y == 10), available_points[min(1, len(available_points) - 1)])

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "1. Suma geométrica",
        "2. Curva sobre Fp",
        "3. Laboratorio ECDH",
        "4. Uso actual",
    ]
)

with tab1:
    st.markdown(
        """
<div class="soft-box">
La idea visual es esta: la recta que pasa por <strong>P</strong> y <strong>Q</strong> corta la curva en un tercer punto. Luego reflejamos ese punto respecto al eje x.
</div>
""",
        unsafe_allow_html=True,
    )
    choices = sample_real_points(real_curve)
    point_map = {label: coords for label, coords in choices}
    labels = list(point_map.keys())
    col_left, col_right = st.columns([0.95, 1.25])
    with col_left:
        operation_mode = st.radio("Operación", options=["P + Q", "2P"], horizontal=True)
        label_p = st.selectbox("P", options=labels, index=0)
        label_q = st.selectbox("Q", options=labels, index=min(4, len(labels) - 1))
        point_p = point_map[label_p]
        point_q = point_map[label_q] if operation_mode == "P + Q" else point_p
        outcome = real_curve.add_points(point_p, point_q)

        st.markdown('<div class="formula-box">y² = x³ + ax + b</div>', unsafe_allow_html=True)
        st.write(f"Curva actual: `y² = x³ + ({real_curve.a})x + ({real_curve.b})`")
        st.write(f"P = `{point_p}`")
        st.write(f"Q = `{point_q}`")

        if outcome["sum"] is None:
            st.markdown(f'<div class="accent-box">{outcome["message"]}</div>', unsafe_allow_html=True)
        else:
            sx, sy = outcome["sum"]
            tx, ty = outcome["third_intersection"]
            slope = outcome["lambda"]
            if outcome["mode"] == "double":
                formula = f"λ = (3x₁² + a) / (2y₁) = {slope:.4f}"
            else:
                formula = f"λ = (y₂ - y₁) / (x₂ - x₁) = {slope:.4f}"
            st.markdown(f'<div class="formula-box">{formula}</div>', unsafe_allow_html=True)
            st.write(f"Tercer punto de la recta con la curva: `({tx:.4f}, {ty:.4f})`")
            st.write(f"Resultado final tras reflejar: `({sx:.4f}, {sy:.4f})`")
            st.markdown(f'<div class="success-box">{outcome["message"]}</div>', unsafe_allow_html=True)

    with col_right:
        st.plotly_chart(build_real_curve_figure(real_curve, point_p, point_q, outcome), use_container_width=True)

with tab2:
    col_left, col_right = st.columns([0.95, 1.25])
    labels = [format_point(point) for point in available_points]
    point_lookup = {format_point(point): point for point in available_points}

    with col_left:
        st.markdown(
            """
<div class="soft-box">
En criptografía no usamos la curva sobre los reales. Usamos puntos sobre un campo finito <strong>F<sub>p</sub></strong>.
</div>
""",
            unsafe_allow_html=True,
        )
        selected_p_label = st.selectbox("Punto P", options=labels, index=labels.index(format_point(default_p)) if format_point(default_p) in labels else 0)
        selected_q_label = st.selectbox("Punto Q", options=labels, index=labels.index(format_point(default_q)) if format_point(default_q) in labels else min(1, len(labels) - 1))
        selected_p = point_lookup[selected_p_label]
        selected_q = point_lookup[selected_q_label]
        result, trace = field_curve.add(selected_p, selected_q)
        st.write(f"Curva: `y² = x³ + {field_curve.a}x + {field_curve.b} (mod {field_curve.p})`")
        st.write(f"P = `{selected_p}`")
        st.write(f"Q = `{selected_q}`")
        if trace["lambda"] is None:
            st.markdown(f'<div class="formula-box">{trace["explanation"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                f'<div class="formula-box">λ = {trace["numerator"]} · ({trace["denominator_raw"]})⁻¹ mod {field_curve.p} = {trace["numerator"]} · {trace["denominator_inv"]} mod {field_curve.p} = {trace["lambda"]}</div>',
                unsafe_allow_html=True,
            )
        st.write(f"Resultado: `{format_point(result)}`")
        st.metric("Número total de puntos", len(field_points))
        st.metric("Orden de P", field_curve.order(selected_p))

        scalar = st.slider("Explorar múltiplos de P", min_value=2, max_value=20, value=8)
        multiple, scalar_trace = field_curve.scalar_multiply(scalar, selected_p)
        st.write(f"`{scalar}P = {format_point(multiple)}`")
        with st.expander("Ver pasos de multiplicación escalar"):
            for line in scalar_trace[:20]:
                st.write(line)

    with col_right:
        st.plotly_chart(
            build_field_figure(field_curve, field_points, [("P", selected_p), ("Q", selected_q), ("P+Q", result)]),
            use_container_width=True,
        )
        st.dataframe(build_multiple_table(field_curve, selected_p, 12), use_container_width=True, hide_index=True)

with tab3:
    st.markdown(
        """
<div class="soft-box">
ECDH usa una idea simple: Alice y Bob comparten una curva y un punto base <strong>G</strong>. Cada uno toma un secreto privado y publica un múltiplo de <strong>G</strong>.
</div>
""",
        unsafe_allow_html=True,
    )
    subgroup_candidates = []
    for point in available_points[:]:
        order = field_curve.order(point)
        if order > 8:
            subgroup_candidates.append((format_point(point), point, order))
    if not subgroup_candidates:
        st.warning("No he encontrado un punto base cómodo para esta curva. Cambie a, b o p.")
    else:
        labels_g = [item[0] for item in subgroup_candidates]
        chosen_g_label = st.selectbox("Punto base G", options=labels_g, index=0)
        chosen_g, subgroup_order = next((point, order) for label, point, order in subgroup_candidates if label == chosen_g_label)
        max_secret = max(2, subgroup_order - 1)
        alice_secret = st.slider("Secreto de Alice (a)", min_value=2, max_value=max_secret, value=min(5, max_secret))
        bob_secret = st.slider("Secreto de Bob (b)", min_value=2, max_value=max_secret, value=min(7, max_secret))

        alice_public, _ = field_curve.scalar_multiply(alice_secret, chosen_g)
        bob_public, _ = field_curve.scalar_multiply(bob_secret, chosen_g)
        shared_alice, _ = field_curve.scalar_multiply(alice_secret, bob_public)
        shared_bob, _ = field_curve.scalar_multiply(bob_secret, alice_public)

        actor1, actor2, actor3 = st.columns(3)
        actor1.markdown(
            f"""
<div class="actor">
<h4>Alice</h4>
<p>Privada: <strong>a = {alice_secret}</strong></p>
<p>Pública: <strong>A = aG = {format_point(alice_public)}</strong></p>
</div>
""",
            unsafe_allow_html=True,
        )
        actor2.markdown(
            f"""
<div class="actor">
<h4>Canal público</h4>
<p>Se comparten <strong>G</strong>, la curva y las claves públicas.</p>
<p>G = <strong>{format_point(chosen_g)}</strong></p>
<p>Orden de G = <strong>{subgroup_order}</strong></p>
</div>
""",
            unsafe_allow_html=True,
        )
        actor3.markdown(
            f"""
<div class="actor">
<h4>Bob</h4>
<p>Privada: <strong>b = {bob_secret}</strong></p>
<p>Pública: <strong>B = bG = {format_point(bob_public)}</strong></p>
</div>
""",
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
<div class="success-box">
Secreto compartido de Alice: <strong>aB = {format_point(shared_alice)}</strong><br>
Secreto compartido de Bob: <strong>bA = {format_point(shared_bob)}</strong>
</div>
""",
            unsafe_allow_html=True,
        )
        st.write("La igualdad funciona porque `a(bG) = b(aG) = (ab)G`.")

        left, right = st.columns([1.15, 1.0])
        with left:
            st.plotly_chart(
                build_field_figure(
                    field_curve,
                    field_points,
                    [("G", chosen_g), ("A", alice_public), ("B", bob_public), ("S", shared_alice)],
                ),
                use_container_width=True,
            )
        with right:
            st.dataframe(build_multiple_table(field_curve, chosen_g, min(subgroup_order, 18)), use_container_width=True, hide_index=True)

with tab4:
    st.markdown(
        """
<div class="soft-box">
La versión moderna no usa curvas “dibujadas a mano” ni parámetros inventados. Usa <strong>curvas estándar</strong>, claves <strong>efímeras</strong> y un <strong>KDF</strong> para convertir el punto compartido en claves de sesión.
</div>
""",
        unsafe_allow_html=True,
    )
    info_left, info_right = st.columns([1.0, 1.0])
    with info_left:
        st.subheader("Cómo se hace hoy")
        st.markdown(
            """
1. El protocolo elige una curva segura estándar.
2. Cada parte genera una clave privada aleatoria.
3. Cada parte calcula su clave pública.
4. Intercambian las claves públicas.
5. Ambas calculan el mismo secreto compartido.
6. Ese secreto pasa por un KDF y se obtienen claves simétricas.
"""
        )
        st.markdown(
            """
<div class="accent-box">
En la práctica actual, TLS 1.3 suele preferir <strong>X25519</strong>. También sigue siendo común <strong>secp256r1 / P-256</strong>, que sí está en forma de Weierstrass.
</div>
""",
            unsafe_allow_html=True,
        )
        st.write("Esta demo usa P-256 porque conecta directamente con la suma de puntos de Weierstrass.")

    with info_right:
        alice_demo = st.number_input("Privada efímera de Alice", min_value=1, max_value=10_000, value=1234, step=1)
        bob_demo = st.number_input("Privada efímera de Bob", min_value=1, max_value=10_000, value=4321, step=1)
        demo = p256_ecdh_demo(int(alice_demo), int(bob_demo))

        st.markdown(f"Curva estándar: `{SECP256R1['name']}`")
        st.write(f"Alice publica `A = aG` con `x = {short_hex(demo['alice_public'].x)}`")
        st.write(f"Bob publica `B = bG` con `x = {short_hex(demo['bob_public'].x)}`")
        st.write(f"Secreto compartido calculado por Alice: `x = {short_hex(demo['shared_a'].x)}`")
        st.write(f"Secreto compartido calculado por Bob: `x = {short_hex(demo['shared_b'].x)}`")
        st.caption("En producción no se usan secretos pequeños como 1234 o 4321. Aquí solo sirven para la demo.")

    st.subheader("Ideas didácticas para clase")
    st.markdown(
        """
- Empiece con la pestaña 1 para que vean la geometría.
- Pase a la pestaña 2 para explicar por qué en criptografía trabajamos módulo p.
- Use la pestaña 3 para que comprendan ECDH con números pequeños.
- Cierre con la pestaña 4 para conectar la intuición con TLS 1.3, mensajería segura y autenticación moderna.
"""
    )
