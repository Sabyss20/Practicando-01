"""
App de Streamlit: Visualización sencilla de e-commerce (sin dataset)

Instrucciones rápidas para usar desde GitHub:
1) Crea un repo y sube este archivo como `app.py`.
2) Añade `requirements.txt` con:
   streamlit
   pandas
   altair
3) Conecta el repo en https://share.streamlit.io y selecciona `app.py`.

Funcionalidades:
- Catálogo manejado en `st.session_state` (sin archivos externos).
- Filtros en la barra lateral (categoría, rango de precio, búsqueda).
- Visualización de productos en tarjetas con botón "Añadir al carrito".
- Carrito persistente con editar cantidades y eliminar.
- Simulación básica de ventas (gráfica por categoría) para visualización.
- Descarga del carrito como JSON.
"""

from __future__ import annotations
import streamlit as st
import pandas as pd
import altair as alt
from dataclasses import dataclass, asdict
from typing import List
import json

st.set_page_config(page_title="E‑commerce Mini", page_icon="🛒", layout="wide")

# -------------------- Datos iniciales (sin dataset) --------------------
@dataclass
class Product:
    id: int
    nombre: str
    categoria: str
    precio: float
    stock: int
    descripcion: str


DEFAULT_PRODUCTS = [
    Product(1, "Camiseta básica", "Ropa", 19.99, 24, "Algodón 100% — cómoda y ligera"),
    Product(2, "Zapatillas Runner", "Calzado", 89.99, 10, "Agarre superior, amortiguación perfecta"),
    Product(3, "Mochila urbana", "Accesorios", 49.5, 15, "Resistente al agua, 20L"),
    Product(4, "Auriculares inalámbricos", "Electrónica", 129.0, 6, "Cancelación de ruido"),
    Product(5, "Taza térmica", "Hogar", 14.0, 40, "Mantiene la temperatura por horas"),
    Product(6, "Pantalón jeans", "Ropa", 39.9, 18, "Estilo clásico, corte recto"),
    Product(7, "Reloj deportivo", "Accesorios", 59.99, 8, "Resistente y ligero"),
    Product(8, "Cámara de acción", "Electrónica", 199.0, 4, "4K, resistente al agua hasta 30m"),
]

# -------------------- Session state --------------------
if "products" not in st.session_state:
    st.session_state.products = [asdict(p) for p in DEFAULT_PRODUCTS]
if "cart" not in st.session_state:
    st.session_state.cart = {}  # product_id -> cantidad
if "filters" not in st.session_state:
    st.session_state.filters = {"q": "", "categoria": "Todas", "min_price": None, "max_price": None}

# -------------------- Sidebar: filtros --------------------
with st.sidebar:
    st.title("🧭 Filtros")
    q = st.text_input("Buscar", value=st.session_state.filters["q"], placeholder="nombre o descripción")
    categorias = ["Todas"] + sorted(list({p["categoria"] for p in st.session_state.products}))
    categoria = st.selectbox("Categoría", categorias, index=categorias.index(st.session_state.filters.get("categoria", "Todas")))
    prices = [p["precio"] for p in st.session_state.products]
    min_price = st.number_input("Precio mínimo", min_value=0.0, value=float(min(prices)), step=1.0)
    max_price = st.number_input("Precio máximo", min_value=0.0, value=float(max(prices)), step=1.0)
    if st.button("🔁 Aplicar filtros"):
        st.session_state.filters.update({"q": q, "categoria": categoria, "min_price": min_price, "max_price": max_price})
    st.markdown("---")
    st.header("🛒 Carrito")
    if st.session_state.cart:
        total = 0.0
        for pid, qty in st.session_state.cart.items():
            prod = next((p for p in st.session_state.products if p["id"] == int(pid)), None)
            if prod:
                total += prod["precio"] * qty
        st.write(f"Items: {sum(st.session_state.cart.values())}")
        st.write(f"Total estimado: S/ {total:.2f}")
        if st.button("🧾 Descargar carrito (.json)"):
            cart_details = []
            for pid, qty in st.session_state.cart.items():
                prod = next((p for p in st.session_state.products if p["id"] == int(pid)), None)
                if prod:
                    cart_details.append({"id": prod["id"], "nombre": prod["nombre"], "precio": prod["precio"], "cantidad": qty})
            st.download_button("Descargar", data=json.dumps(cart_details, ensure_ascii=False, indent=2), file_name="carrito.json", mime="application/json")
    else:
        st.info("Tu carrito está vacío.")

    st.markdown("---")
    if st.button("🔄 Reiniciar demo"):
        st.session_state.products = [asdict(p) for p in DEFAULT_PRODUCTS]
        st.session_state.cart = {}
        st.session_state.filters = {"q": "", "categoria": "Todas", "min_price": None, "max_price": None}
        st.experimental_rerun()

# -------------------- Helpers --------------------

@st.cache_data
def products_to_df(products: List[dict]) -> pd.DataFrame:
    df = pd.DataFrame(products)
    return df


def filter_products(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    q = filters.get("q", "").lower()
    cat = filters.get("categoria", "Todas")
    min_p = filters.get("min_price")
    max_p = filters.get("max_price")
    out = df.copy()
    if q:
        out = out[out["nombre"].str.lower().str.contains(q) | out["descripcion"].str.lower().str.contains(q)]
    if cat and cat != "Todas":
        out = out[out["categoria"] == cat]
    if min_p is not None:
        out = out[out["precio"] >= float(min_p)]
    if max_p is not None:
        out = out[out["precio"] <= float(max_p)]
    return out


# -------------------- Main UI --------------------
st.title("🛍️ Mini E‑commerce — Demo interactiva")
st.caption("Catálogo editable en memoria. Sin base de datos; ideal para pruebas y diseño rápido.")

# show quick stats
products_df = products_to_df(st.session_state.products)
col1, col2, col3 = st.columns(3)
col1.metric("Productos", len(products_df))
col2.metric("Categorías", len(products_df["categoria"].unique()))
col3.metric("Stock total", int(products_df["stock"].sum()))

# Filtered view
fdf = filter_products(products_df, st.session_state.filters)

st.subheader("Catálogo")
if fdf.empty:
    st.info("No hay productos que coincidan con los filtros.")
else:
    # Display products as cards (simple)
    def show_product_card(p):
        st.markdown("---")
        cols = st.columns([1, 3, 1])
        with cols[0]:
            st.image("https://via.placeholder.com/120x120.png?text=Producto", width=120)
        with cols[1]:
            st.write(f"**{p['nombre']}**")
            st.write(f"_{p['categoria']}_")
            st.write(p['descripcion'])
            st.write(f"**S/ {p['precio']:.2f}** — Stock: {p['stock']}")
        with cols[2]:
            qty = st.number_input(f"Cantidad##{p['id']}", min_value=1, max_value=p['stock'], value=1, key=f"qty_{p['id']}")
            if st.button("Añadir al carrito", key=f"add_{p['id']}"):
                pid = str(p['id'])
                st.session_state.cart[pid] = st.session_state.cart.get(pid, 0) + int(qty)
                st.success(f"Agregado {qty} x {p['nombre']} al carrito")

    for _, row in fdf.iterrows():
        show_product_card(row)

# -------------------- Carrito detallado --------------------
st.subheader("Carrito")
if not st.session_state.cart:
    st.info("Tu carrito está vacío. Añade productos desde el catálogo.")
else:
    cart_rows = []
    for pid, qty in st.session_state.cart.items():
        prod = next((p for p in st.session_state.products if p['id'] == int(pid)), None)
        if prod:
            cart_rows.append({
                'id': prod['id'],
                'nombre': prod['nombre'],
                'precio': prod['precio'],
                'cantidad': qty,
                'subtotal': prod['precio'] * qty
            })
    cart_df = pd.DataFrame(cart_rows)
    cart_df = cart_df[['id','nombre','precio','cantidad','subtotal']]
    st.dataframe(cart_df, use_container_width=True)

    c1, c2 = st.columns([1,2])
    total = cart_df['subtotal'].sum()
    with c2:
        st.write(f"### Total: S/ {total:.2f}")
        if st.button("🧾 Simular compra"):
            # disminuir stock (simulación)
            for _, r in cart_df.iterrows():
                prod = next((p for p in st.session_state.products if p['id'] == int(r['id'])), None)
                if prod:
                    prod['stock'] = max(0, prod['stock'] - int(r['cantidad']))
            st.session_state.cart = {}
            st.success("Compra simulada: stock actualizado y carrito vaciado.")
            st.experimental_rerun()
    with c1:
        # allow editing quantities or removing
        st.write("Editar carrito")
        for _, r in cart_df.iterrows():
            cols = st.columns([2,1,1])
            with cols[0]:
                st.write(r['nombre'])
            with cols[1]:
                new_q = st.number_input(f"q_edit_{r['id']}", min_value=0, value=int(r['cantidad']), key=f"edit_{r['id']}")
            with cols[2]:
                if st.button(f"Actualizar##{r['id']}"):
                    if new_q <= 0:
                        del st.session_state.cart[str(r['id'])]
                    else:
                        st.session_state.cart[str(r['id'])] = int(new_q)
                    st.experimental_rerun()

# -------------------- Visualizaciones de negocio (simuladas) --------------------
st.subheader("Insights rápidos")
# Simular ventas por categoría (aleatorio basado en stock y precio para demo)
demo_df = products_df.copy()
demo_df['ventas_sim'] = (demo_df['precio'] * (demo_df['stock'] * 0.2)).round(2)

chart = alt.Chart(demo_df).mark_bar().encode(
    x=alt.X('categoria:N', title='Categoría'),
    y=alt.Y('ventas_sim:Q', title='Ventas estimadas (S/)'),
    tooltip=['nombre','categoria','precio','stock','ventas_sim']
).properties(height=300)

st.altair_chart(chart, use_container_width=True)

# -------------------- Tips y despliegue --------------------
with st.expander("Cómo desplegar en Streamlit Community Cloud"):
    st.markdown(
        """
        1. Crea un repositorio en GitHub y sube `app.py`.
        2. Añade `requirements.txt` con `streamlit`, `pandas`, `altair`.
        3. Ve a https://share.streamlit.io y conecta tu GitHub.
        4. Selecciona el repo y `app.py`, y despliega.
        
        ¿Quieres que te genere también el `requirements.txt` y un `README.md` listo para push?"""
    )
