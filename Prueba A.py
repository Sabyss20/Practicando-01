"""
App de Streamlit: Visualización de Agenda de Reunión (sin dataset)

Cómo usarla desde GitHub (modo sencillo):
1) Crea un repo y sube este archivo como `app.py` (o mantenlo como está y ajusta en Streamlit).
2) (Opcional pero recomendado) Crea `requirements.txt` con:
   streamlit
   pandas
   altair
3) Ve a https://share.streamlit.io, conecta tu GitHub, elige tu repo y el archivo principal `app.py`.

Características:
- Sin dataset: todo se gestiona en `st.session_state`.
- Formulario para agregar ítems de la agenda (tema, responsable, hora inicio, duración, notas).
- Metadatos de la reunión (título, fecha, ubicación, anfitrión) en la barra lateral.
- Visualización tipo timeline (Altair) + tabla ordenada por hora de inicio.
- Botones para cargar ejemplo, limpiar agenda, descargar .ics y .json.
- Validaciones básicas (duración > 0, hora válida).
"""

from __future__ import annotations
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, date, time, timedelta
from io import StringIO

st.set_page_config(page_title="Agenda de Reunión", page_icon="📅", layout="wide")

# -------------------- Estado inicial --------------------
if "agenda" not in st.session_state:
    st.session_state.agenda = []  # lista de dicts {tema, responsable, inicio(time), duracion(int), notas}
if "meta" not in st.session_state:
    st.session_state.meta = {
        "titulo": "Reunión de seguimiento",
        "fecha": date.today(),
        "ubicacion": "Remoto",
        "anfitrion": "Equipo"
    }

# -------------------- Sidebar: metadatos --------------------
with st.sidebar:
    st.header("🧭 Detalles de la reunión")
    st.session_state.meta["titulo"] = st.text_input("Título", st.session_state.meta["titulo"])
    st.session_state.meta["fecha"] = st.date_input("Fecha", st.session_state.meta["fecha"])
    st.session_state.meta["ubicacion"] = st.text_input("Ubicación", st.session_state.meta["ubicacion"])
    st.session_state.meta["anfitrion"] = st.text_input("Anfitrión", st.session_state.meta["anfitrion"])

    st.markdown("---")
    col_sb1, col_sb2 = st.columns(2)
    with col_sb1:
        if st.button("📥 Cargar ejemplo"):
            st.session_state.agenda = [
                {"tema": "Bienvenida", "responsable": "Anfitrión", "inicio": time(9, 0), "duracion": 10, "notas": "Introducción breve"},
                {"tema": "Estado del proyecto", "responsable": "PM", "inicio": time(9, 10), "duracion": 25, "notas": "Riesgos y avances"},
                {"tema": "Bloque técnico", "responsable": "Dev Lead", "inicio": time(9, 35), "duracion": 30, "notas": "Demostración"},
                {"tema": "Q&A", "responsable": "Todos", "inicio": time(10, 5), "duracion": 15, "notas": "Preguntas"},
            ]
    with col_sb2:
        if st.button("🧹 Limpiar agenda"):
            st.session_state.agenda = []

# -------------------- Encabezado --------------------
left, right = st.columns([3, 2])
with left:
    st.title("📅 Agenda de Reunión")
    st.caption("Crea, visualiza y descarga la agenda sin necesidad de datasets.")
with right:
    st.metric("Total de ítems", len(st.session_state.agenda))

# -------------------- Formulario para agregar ítems --------------------
with st.form("add_item"):
    st.subheader("➕ Agregar ítem")
    c1, c2, c3, c4 = st.columns([2, 2, 1.2, 1])
    tema = c1.text_input("Tema", placeholder="p. ej., Revisión OKRs")
    responsable = c2.text_input("Responsable", placeholder="Nombre")
    inicio = c3.time_input("Hora de inicio", value=time(9, 0), step=300)
    duracion = c4.number_input("Duración (min)", min_value=1, max_value=480, value=15)
    notas = st.text_area("Notas (opcional)", placeholder="Contexto, objetivos, enlaces...")

    c5, c6 = st.columns([1, 6])
    submitted = c5.form_submit_button("Agregar", use_container_width=True)
    if submitted:
        if not tema.strip():
            st.warning("Por favor, indica el tema.")
        else:
            st.session_state.agenda.append({
                "tema": tema.strip(),
                "responsable": responsable.strip(),
                "inicio": inicio,
                "duracion": int(duracion),
                "notas": notas.strip(),
            })
            st.success("Ítem agregado.")

# -------------------- Preparar dataframe --------------------

def to_dataframe(agenda: list[dict]) -> pd.DataFrame:
    if not agenda:
        return pd.DataFrame(columns=["Tema", "Responsable", "Inicio", "Fin", "Duración (min)", "Notas"])    
    rows = []
    base_date: date = st.session_state.meta.get("fecha", date.today())
    for item in agenda:
        start_dt = datetime.combine(base_date, item["inicio"])  # datetime
        end_dt = start_dt + timedelta(minutes=item["duracion"])
        rows.append({
            "Tema": item["tema"],
            "Responsable": item.get("responsable", ""),
            "Inicio": start_dt,
            "Fin": end_dt,
            "Duración (min)": item["duracion"],
            "Notas": item.get("notas", ""),
        })
    df = pd.DataFrame(rows).sort_values("Inicio").reset_index(drop=True)
    return df

agenda_df = to_dataframe(st.session_state.agenda)

# -------------------- Visualización --------------------
st.subheader("🕒 Timeline de la agenda")

if agenda_df.empty:
    st.info("Aún no hay ítems. Agrega alguno con el formulario de arriba o presiona **Cargar ejemplo** en la barra lateral.")
else:
    # Altair timeline: eje X = tiempo, eje Y = tema
    chart = alt.Chart(agenda_df).mark_bar().encode(
        x=alt.X("Inicio:T", title="Hora", axis=alt.Axis(format="%H:%M")),
        x2="Fin:T",
        y=alt.Y("Tema:N", sort=None, title="Tema"),
        tooltip=[
            alt.Tooltip("Tema:N"),
            alt.Tooltip("Responsable:N"),
            alt.Tooltip("Inicio:T", format="%H:%M"),
            alt.Tooltip("Fin:T", format="%H:%M"),
            alt.Tooltip("Duración (min):Q"),
            alt.Tooltip("Notas:N")
        ]
    ).properties(height=40*max(1, len(agenda_df)), width="container")
    st.altair_chart(chart, use_container_width=True)

# -------------------- Tabla --------------------
st.subheader("📋 Detalle de la agenda")
if not agenda_df.empty:
    # Mostrar columnas amigables
    show_df = agenda_df.copy()
    show_df["Inicio"] = show_df["Inicio"].dt.strftime("%H:%M")
    show_df["Fin"] = show_df["Fin"].dt.strftime("%H:%M")
    st.dataframe(show_df, use_container_width=True, hide_index=True)

# -------------------- Descargas --------------------
col_d1, col_d2, col_d3 = st.columns([1,1,3])


def export_json(df: pd.DataFrame) -> str:
    if df.empty:
        return "[]"
    # serializar campos de tiempo como ISO
    data = []
    for _, r in df.iterrows():
        data.append({
            "tema": r["Tema"],
            "responsable": r["Responsable"],
            "inicio": r["Inicio"].isoformat(),
            "fin": r["Fin"].isoformat(),
            "duracion_min": int(r["Duración (min)"]),
            "notas": r["Notas"],
        })
    import json
    return json.dumps(data, ensure_ascii=False, indent=2)


def export_ics(df: pd.DataFrame) -> str:
    """Genera un calendario ICS básico con cada ítem como evento."""
    meta = st.session_state.meta
    def fmt(dt: datetime) -> str:
        return dt.strftime("%Y%m%dT%H%M%S")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Agenda Streamlit//ES",
        f"X-WR-CALNAME:{meta.get('titulo','Agenda')}",
        f"X-WR-TIMEZONE:UTC",
    ]

    if not df.empty:
        now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        for _, r in df.iterrows():
            uid = f"{fmt(r['Inicio'])}-{hash(r['Tema'])}@agenda"
            desc_parts = []
            if r["Responsable"]:
                desc_parts.append(f"Responsable: {r['Responsable']}")
            if r["Notas"]:
                desc_parts.append(r["Notas"])
            desc = "\\n".join(desc_parts)
            lines += [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{now}",
                f"DTSTART:{r['Inicio'].strftime('%Y%m%dT%H%M%S')}",
                f"DTEND:{r['Fin'].strftime('%Y%m%dT%H%M%S')}",
                f"SUMMARY:{r['Tema']}",
                f"LOCATION:{meta.get('ubicacion','')}",
                f"DESCRIPTION:{desc}",
                "END:VEVENT",
            ]
    lines.append("END:VCALENDAR")
    return "\n".join(lines)

with col_d1:
    if not agenda_df.empty:
        ics_text = export_ics(agenda_df)
        st.download_button(
            "📆 Descargar .ics", data=ics_text, file_name="agenda.ics", mime="text/calendar"
        )

with col_d2:
    json_text = export_json(agenda_df)
    st.download_button(
        "🗂️ Descargar .json", data=json_text, file_name="agenda.json", mime="application/json"
    )

# -------------------- Notas finales --------------------
with st.expander("📖 Tips de uso"):
    st.markdown(
        """
        - **Orden**: los ítems se ordenan automáticamente por hora de inicio.
        - **Edición**: por simplicidad, borra con *Limpiar agenda* y vuelve a cargar; 
          o agrega otro ítem corrigiendo el anterior si lo deseas.
        - **Compartir**: sube este archivo a GitHub y despliega en Streamlit Community Cloud.
        - **Archivos extra**: agrega un `README.md` y `requirements.txt` (ver arriba) para una mejor experiencia.
        """
    )

