import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import base64
import json
import gc

st.set_page_config(
    page_title="ONPE - Dashboard Locales de Votación",
    page_icon="🗳️",
    layout="wide",
)

# ==============================
# Login — antes de cualquier contenido
# ==============================
_USERS = {
    "admin":  "admin",
    "viewer": "def123",
}

for _k, _v in [("logged_in", False), ("login_user", ""), ("_login_err", False)]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

if not st.session_state.logged_in:
    # ── Página de login centrada ──
    _, _lc, _ = st.columns([1, 1.2, 1])
    with _lc:
        with open("images/loading1.png", "rb") as _f:
            _login_logo = "data:image/png;base64," + base64.b64encode(_f.read()).decode()
        st.markdown(f"""
        <div style='text-align:center;padding:32px 0 16px;'>
          <img src="{_login_logo}" style='width:120px;height:120px;object-fit:contain;margin-bottom:8px;'>
          <div style='font-size:22px;font-weight:800;color:#003770;letter-spacing:-.5px;margin-top:6px;'>
            DEFENSORIA DEL PUEBLO
          </div>
          <div style='font-size:13px;color:#64748b;margin-top:4px;'>
            Sistema de Locales de Votación
          </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            _u = st.text_input("Usuario", placeholder="usuario")
            _p = st.text_input("Contraseña", type="password", placeholder="••••••••")
            _btn = st.form_submit_button("Ingresar", use_container_width=True)

        # Validación fuera del form para evitar conflicto con st.rerun()
        if _btn:
            if _USERS.get(_u.strip()) == _p:
                st.session_state.logged_in  = True
                st.session_state.login_user = _u.strip()
                st.session_state._login_err = False
                st.rerun()
            else:
                st.session_state._login_err = True
                st.rerun()

        if st.session_state._login_err:
            st.error("Usuario o contraseña incorrectos.")

    st.stop()

st.markdown("""
<style>
  /* Eliminar espacio superior del contenedor principal */
  .block-container                            { padding-top: 0 !important; }
  .stMainBlockContainer                       { padding-top: 0 !important; }
  section[data-testid="stMain"] > div:first-child { padding-top: 0 !important; }
  /* Header transparente y sin altura — los botones del sidebar siguen visibles */
  header[data-testid="stHeader"]              {
    background: transparent !important;
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
    overflow: visible !important;
  }
  [data-testid="stToolbar"]                   { display: none !important; }
  [data-testid="stDecoration"]                { display: none !important; }
  [data-testid="stStatusWidget"]              { display: none !important; }
  #MainMenu                                   { display: none !important; }
  /* Botones nativos del sidebar ocultos — se clickean por JS desde el botón custom */
  [data-testid="stSidebarCollapsedControl"],
  [data-testid="stSidebarCollapseButton"]     { display: none !important; }
  /* Selectboxes del filtro más compactos */
  div[data-testid="stSelectbox"] label { font-size: 9px !important; margin-bottom: 0 !important; line-height: 1 !important; }
  div[data-testid="stSelectbox"] > div > div { min-height: 24px !important; font-size: 10px !important; padding-top: 0 !important; padding-bottom: 0 !important; }
  div[data-testid="stSelectbox"] { margin-bottom: 0 !important; }
  div[data-testid="stSelectbox"] > div { gap: 0 !important; }
  /* Botón "Ver local" — intento CSS (respaldo) */
  [data-testid="stPopover"] button,
  [data-testid="stPopover"] > button {
    padding: 0px 4px !important;
    font-size: 9px !important;
    min-height: 0 !important;
    height: 16px !important;
    line-height: 1 !important;
  }
  /* ── Pestañas — aspecto tipo botón/pill bien visible ── */
  .stTabs [data-baseweb="tab-list"] {
    background: #e8edf3;
    border-radius: 10px;
    padding: 4px 6px;
    gap: 4px;
    border-bottom: none !important;
  }
  .stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 7px;
    padding: 6px 20px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #5a6a7a !important;
    border: none !important;
    transition: background .15s, color .15s;
  }
  .stTabs [data-baseweb="tab"]:hover {
    background: #d0d8e4 !important;
    color: #003770 !important;
  }
  .stTabs [aria-selected="true"] {
    background: #003770 !important;
    color: white !important;
    box-shadow: 0 2px 6px rgba(0,55,112,.30) !important;
  }
  .stTabs [data-baseweb="tab-highlight"] { display: none !important; }
  .stTabs [data-baseweb="tab-border"]    { display: none !important; }
</style>
""", unsafe_allow_html=True)

# JS: aplica estilos directamente al botón en el DOM padre (más confiable que CSS inyectado)
st.components.v1.html("""
<script>
(function() {
  function stylePopoverBtn() {
    var doc = window.parent.document;
    doc.querySelectorAll('[data-testid="stPopover"] button').forEach(function(btn) {
      // Reset total: parece texto/link, no botón
      btn.style.setProperty('background', 'none', 'important');
      btn.style.setProperty('border', 'none', 'important');
      btn.style.setProperty('box-shadow', 'none', 'important');
      btn.style.setProperty('padding', '0', 'important');
      btn.style.setProperty('margin', '0', 'important');
      btn.style.setProperty('min-height', '0', 'important');
      btn.style.setProperty('height', 'auto', 'important');
      btn.style.setProperty('font-size', '11px', 'important');
      btn.style.setProperty('font-weight', '500', 'important');
      btn.style.setProperty('color', '#2563eb', 'important');
      btn.style.setProperty('cursor', 'pointer', 'important');
      btn.style.setProperty('text-decoration', 'underline', 'important');
      btn.style.setProperty('line-height', '1.2', 'important');
    });
  }
  stylePopoverBtn();
  var obs = new MutationObserver(stylePopoverBtn);
  obs.observe(window.parent.document.body, { childList: true, subtree: true });
})();
</script>
""", height=0, scrolling=False)

# ── Contador de rerun: hace el HTML único en cada rerun → fuerza recreación del iframe ──
if "_run_id" not in st.session_state:
    st.session_state["_run_id"] = 0
st.session_state["_run_id"] += 1
_run_id = st.session_state["_run_id"]

# Consumir el flag de skip (se activa solo al cerrar sesión)
_skip_loading = st.session_state.pop("_skip_loading", False)

# ── Overlay de carga (se oculta vía JS cuando todo está listo) ──
with open("images/loading2.png", "rb") as _lf:
    _loading_src = "data:image/png;base64," + base64.b64encode(_lf.read()).decode()

st.components.v1.html(f"""<!-- {_run_id} -->
<script>
(function(){{
  var doc = window.parent.document;

  // Inyectar CSS una sola vez
  if (!doc.getElementById('st-ld-css')) {{
    var s = doc.createElement('style');
    s.id = 'st-ld-css';
    s.textContent = [
      '@keyframes flipY{{0%{{transform:perspective(600px) rotateY(0deg)}}100%{{transform:perspective(600px) rotateY(360deg)}}}}',
      '@keyframes ldots{{0%{{content:"."}}33%{{content:".."}}66%{{content:"..."}}}}',
      '#st-loading-overlay{{position:fixed;top:0;left:0;width:100vw;height:100vh;',
        'background:rgba(255,255,255,.93);z-index:99998;',
        'display:flex;flex-direction:column;align-items:center;justify-content:center;',
        'gap:24px;pointer-events:none;}}',
      '#st-loading-overlay img{{width:220px;height:220px;object-fit:contain;',
        'animation:flipY 1.6s linear infinite;}}',
      '#st-loading-overlay .ld-text{{font-family:Segoe UI,Arial,sans-serif;',
        'font-size:18px;font-weight:600;color:#003770;letter-spacing:3px;}}',
      '#st-loading-overlay .ld-dots{{display:inline-block;min-width:22px;',
        'animation:ldots 1.2s steps(1,end) infinite;}}'
    ].join('');
    doc.head.appendChild(s);
  }}

  // Crear o mostrar el overlay (solo si no se está cerrando sesión)
  var skip = {str(_skip_loading).lower()};
  if (skip) {{
    var el = doc.getElementById('st-loading-overlay');
    if (el) el.style.display = 'none';
  }} else {{
    var el = doc.getElementById('st-loading-overlay');
    if (!el) {{
      el = doc.createElement('div');
      el.id = 'st-loading-overlay';
      el.innerHTML = '<img src="{_loading_src}"><span class="ld-text">Loading<span class="ld-dots">.</span></span>';
      doc.body.appendChild(el);
    }} else {{
      el.style.display = 'flex';
    }}
  }}
}})();
</script>
""", height=0, scrolling=False)

# ==============================
# Constantes de layout responsive
# ==============================
_MAP_COL_W    = 3      # peso columna mapa  en st.columns([3, 2])
_PANEL_COL_W  = 2      # peso columna panel lateral
_MAP_W_RATIO  = 1      # proporción ancho  del mapa (relativa)
_MAP_H_RATIO  = 2.3   # proporción alto   del mapa (relativa)  → alto = ancho × (H/W)
_SIDEBAR_PX   = 260   # ancho real del sidebar siempre visible (px)
_MAP_H_MIN    = 380    # altura mínima del mapa (px)
_MAP_H_MAX    = 1100   # altura máxima del mapa (px)
_CHROME_PX    = 55     # px fijos totales  (tabs + padding, sin header)
_ZOOM_OFFSET  = 0.7      # incremento fijo sobre el zoom calculado (0 = sin cambio, +1 = más cerca, -1 = más lejos)

# Aspecto derivado de las dos proporciones independientes
_MAP_ASPECT = _MAP_H_RATIO / _MAP_W_RATIO

# Altura Python de respaldo (pantalla 1440×900, doble restricción: aspecto y vh)
_vh_est = 900
_map_h_by_aspect = (1440 - _SIDEBAR_PX) * _MAP_COL_W / (_MAP_COL_W + _PANEL_COL_W) * _MAP_ASPECT
_map_h_by_vh     = _vh_est - _CHROME_PX
_MAP_H = int(max(_MAP_H_MIN, min(_MAP_H_MAX, _map_h_by_aspect, _map_h_by_vh)))

# ==============================
# Carga con caché (solo lee el Excel 1 vez)
# ==============================
@st.cache_data
def _load_geojson():
    with open("data/DEPARTAMENTO.geojson", encoding="utf-8") as f:
        geo = json.load(f)
    for feat in geo.get("features", []):
        feat["properties"] = {k.upper(): v for k, v in feat["properties"].items()}
    return geo

@st.cache_data
def _load_geojson_dist():
    with open("data/DISTRITO.geojson", encoding="utf-8") as f:
        geo = json.load(f)
    for feat in geo.get("features", []):
        feat["properties"] = {k.upper(): v for k, v in feat["properties"].items()}
    return geo

@st.cache_data
def _build_geo_index():
    """Índice pre-construido del GeoJSON distrital para lookups O(1)."""
    geo = _load_geojson_dist()
    idx_dep  = {}   # dep              → [features]
    idx_prov = {}   # (dep, prov)      → [features]
    idx_dist = {}   # (dep, prov, dist)→ [features]
    for f in geo["features"]:
        p  = f["properties"]
        d  = p.get("NOMBDEP",  "").strip().upper()
        pr = p.get("NOMBPROV", "").strip().upper()
        di = p.get("NOMBDIST", "").strip().upper()
        idx_dep .setdefault(d,        []).append(f)
        idx_prov.setdefault((d, pr),  []).append(f)
        idx_dist.setdefault((d, pr, di), []).append(f)
    return idx_dep, idx_prov, idx_dist

def _bbox_from_features(features):
    """Retorna (minlat, maxlat, minlon, maxlon) desde una lista de features GeoJSON."""
    lats, lons = [], []
    for feat in features:
        geom = feat.get("geometry") or {}
        gtype = geom.get("type", "")
        coords = geom.get("coordinates", [])
        if gtype == "Polygon":
            rings = coords
        elif gtype == "MultiPolygon":
            rings = [ring for poly in coords for ring in poly]
        else:
            continue
        for ring in rings:
            for pt in ring:
                lons.append(pt[0])
                lats.append(pt[1])
    if not lats:
        return None
    return min(lats), max(lats), min(lons), max(lons)

def _zoom_from_span(span):
    base = (4 if span > 12 else 5 if span > 7 else 6 if span > 4
            else 7 if span > 2 else 8 if span > 1 else 9 if span > 0.4
            else 10 if span > 0.15 else 11)
    return base + _ZOOM_OFFSET

@st.cache_data
def _b64(path: str) -> str:
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()

@st.cache_data
def cargar_datos():
    df = pd.read_excel("data/ONPE_COSOLIDADO.xlsx", sheet_name="LOCAL_ONPE")
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        "DPTO / CONTINENTE": "DEPARTAMENTO",
        "PROVINCIA / PAÍS": "PROVINCIA",
        "DISTRITO / CIUDAD": "DISTRITO",
        "DIRECCIÓN DEL LOCAL": "DIRECCION",
    })
    df = df[df["Nacional_Internacional"] == "Nacional"].copy()
    df = df.dropna(subset=["LATITUD", "LONGITUD"])
    df["LATITUD"] = pd.to_numeric(df["LATITUD"], errors="coerce")
    df["LONGITUD"] = pd.to_numeric(df["LONGITUD"], errors="coerce")
    df = df.dropna(subset=["LATITUD", "LONGITUD"])
    return df

@st.cache_data
def cargar_datos_intl():
    df = pd.read_excel("data/ONPE_COSOLIDADO.xlsx", sheet_name="LOCAL_ONPE")
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        "DPTO / CONTINENTE": "CONTINENTE",
        "PROVINCIA / PAÍS": "PAIS",
        "DISTRITO / CIUDAD": "CIUDAD",
        "DIRECCIÓN DEL LOCAL": "DIRECCION",
    })
    df = df[df["Nacional_Internacional"] == "Internacional"].copy()
    df = df.dropna(subset=["LATITUD", "LONGITUD"])
    df["LATITUD"] = pd.to_numeric(df["LATITUD"], errors="coerce")
    df["LONGITUD"] = pd.to_numeric(df["LONGITUD"], errors="coerce")
    df = df.dropna(subset=["LATITUD", "LONGITUD"])
    return df

df_base = cargar_datos()
df_intl  = cargar_datos_intl()

# ==============================
# Constantes (se definen una vez, no cambian)
# ==============================
COLOR_MAP = {
    "*Sin Cobertura": [150, 150, 150, 200],   # plomo
    "Con Cobertura":  [56, 189, 248, 200],    # celeste
    "Fiscalizado":    [30, 80, 200, 200],     # azul
}

# Bordes geográficos en el mapa
_BORDER_COLOR_DIST  = [118, 157, 196]   # color borde distrito seleccionado  (RGBA)
_BORDER_COLOR_PROV  = [118, 157, 196]   # color borde distritos en provincia  (RGBA)
_BORDER_W_DIST      = 1                 # grosor borde distrito seleccionado  (px)
_BORDER_W_PROV      = 1                 # grosor borde distritos en provincia (px)

# Iconos: base64 cargado 1 sola vez con caché
_S = {"width": 128, "height": 128, "anchorY": 128, "mask": False}
ICON_MAP = {
    "*Sin Cobertura": {**_S, "url": _b64("images/sin.png")},
    "Con Cobertura":  {**_S, "url": _b64("images/ok.png")},
    "Fiscalizado":    {**_S, "url": _b64("images/fiscalizado.png")},
}
_DEFAULT_ICON = ICON_MAP["*Sin Cobertura"]

# ==============================
# Estado de sesión
# ==============================
for _k, _v in [("gc_cob", None), ("gc_loc", None), ("clicked_local", None),
               ("act_dep", "TODOS"), ("act_prov", "TODOS"), ("act_dist", "TODOS")]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ==============================
# Callbacks para gráficos (1 sola rerun por clic)
# ==============================
def _cb_donut():
    pts = getattr(getattr(st.session_state.get("donut_chart"), "selection", None), "points", [])
    st.session_state.gc_cob = pts[0]["label"] if pts else None


# ==============================
# Filtros aplicados — solo se actualizan al pulsar "Cargar mapa"
# ==============================
_act_dep  = st.session_state.act_dep
_act_prov = st.session_state.act_prov
_act_dist = st.session_state.act_dist

df_f = df_base
if _act_dep  != "TODOS": df_f = df_f[df_f["DEPARTAMENTO"] == _act_dep]
if _act_prov != "TODOS": df_f = df_f[df_f["PROVINCIA"]    == _act_prov]
if _act_dist != "TODOS": df_f = df_f[df_f["DISTRITO"]     == _act_dist]

dep  = _act_dep
prov = _act_prov
dist = _act_dist

# ==============================
# Fragmento de filtros — solo reruns el sidebar, no el mapa
# ==============================
@st.fragment
def _filtros_sidebar():
    _a_dep  = st.session_state.act_dep
    _a_prov = st.session_state.act_prov
    _a_dist = st.session_state.act_dist

    st.markdown("### 🔍 Filtros")

    dep_opts = ["TODOS"] + sorted(df_base["DEPARTAMENTO"].dropna().unique())
    _sel_dep = st.selectbox("Departamento", dep_opts,
                            index=dep_opts.index(_a_dep) if _a_dep in dep_opts else 0)
    _df_tmp = df_base if _sel_dep == "TODOS" else df_base[df_base["DEPARTAMENTO"] == _sel_dep]

    prov_opts = ["TODOS"] + sorted(_df_tmp["PROVINCIA"].dropna().unique())
    _sel_prov = st.selectbox("Provincia", prov_opts,
                             index=prov_opts.index(_a_prov) if _a_prov in prov_opts else 0)
    _df_tmp = _df_tmp if _sel_prov == "TODOS" else _df_tmp[_df_tmp["PROVINCIA"] == _sel_prov]

    dist_opts = ["TODOS"] + sorted(_df_tmp["DISTRITO"].dropna().unique())
    _sel_dist = st.selectbox("Distrito", dist_opts,
                             index=dist_opts.index(_a_dist) if _a_dist in dist_opts else 0)

    _has_changes = (_sel_dep != _a_dep or _sel_prov != _a_prov or _sel_dist != _a_dist)

    if st.button("🗺️ Cargar mapa", use_container_width=True,
                 type="primary" if _has_changes else "secondary", key="btn_load_map"):
        st.session_state.act_dep  = _sel_dep
        st.session_state.act_prov = _sel_prov
        st.session_state.act_dist = _sel_dist
        st.rerun(scope="app")


# ==============================
# Menú lateral fijo (siempre visible)
# ==============================
with st.sidebar:
    # ── Cabecera con título y reloj ──
    st.components.v1.html(f"""
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: transparent; }}
  .sb-hdr {{
    background: #003770;
    border-radius: 8px;
    padding: 10px 12px 8px;
    font-family: Segoe UI, Arial, sans-serif;
    text-align: center;
  }}
  .sb-title {{
    color: white;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: -.2px;
    line-height: 1.3;
  }}
  .sb-sub {{
    color: #93c5fd;
    font-size: 10px;
    margin-top: 3px;
  }}
  .sb-clock {{
    margin-top: 6px;
    border-top: 1px solid rgba(255,255,255,.15);
    padding-top: 5px;
  }}
  #sb-time {{
    font-family: 'Courier New', Consolas, monospace;
    font-size: 20px;
    font-weight: 700;
    color: #e0f0ff;
    letter-spacing: 3px;
    line-height: 1;
    text-shadow: 0 0 8px rgba(96,165,250,.6);
  }}
  #sb-fecha {{
    color: #93c5fd;
    font-size: 9px;
    letter-spacing: .4px;
    margin-top: 2px;
  }}
</style>
<div class="sb-hdr" id="sbh">
  <div class="sb-title">🗳️ Defensoria del Pueblo <br>Locales de Votación</div>
  <div class="sb-sub">Total cargados: <b style="color:#bfdbfe;">{len(df_base):,}</b></div>
  <div class="sb-clock">
    <div id="sb-time">00:00:00</div>
    <div id="sb-fecha"></div>
  </div>
</div>
<script>
  var DIAS  = ['Dom','Lun','Mar','Mié','Jue','Vie','Sáb'];
  var MESES = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
  function pad(n) {{ return String(n).padStart(2,'0'); }}
  function tick() {{
    var now = new Date(new Date().toLocaleString('en-US', {{timeZone:'America/Lima'}}));
    var t = document.getElementById('sb-time');
    if (t) t.textContent = pad(now.getHours())+':'+pad(now.getMinutes())+':'+pad(now.getSeconds());
    var fd = document.getElementById('sb-fecha');
    if (fd) fd.textContent = DIAS[now.getDay()]+' '+now.getDate()+' '+MESES[now.getMonth()]+' '+now.getFullYear();
  }}
  tick(); setInterval(tick, 1000);
  function sendH() {{
    var h = document.getElementById('sbh').getBoundingClientRect().height + 8;
    window.parent.postMessage({{type:'streamlit:setFrameHeight', height: h}}, '*');
  }}
  window.addEventListener('load', sendH);
  window.addEventListener('resize', sendH);
  setTimeout(sendH, 200);
</script>
""", height=115, scrolling=False)

    _filtros_sidebar()

    st.divider()
    st.markdown("### 🗺️ Visualización")
    _tc1, _tc2 = st.columns(2)
    with _tc1:
        _usar_iconos    = st.toggle("🖼️ Iconos", value=False)
    with _tc2:
        _mostrar_calles = st.toggle("🗺️ Calles", value=False)

    st.divider()
    st.caption(f"**{len(df_f):,}** locales visibles")

    _gc_labels = []
    if st.session_state.gc_cob:
        _gc_labels.append(f"Cobertura: **{st.session_state.gc_cob}**")
    if st.session_state.gc_loc:
        _gc_labels.append(f"{st.session_state.gc_loc[0]}: **{st.session_state.gc_loc[1]}**")
    if _gc_labels:
        st.caption("Filtro activo: " + " · ".join(_gc_labels))
        if st.button("✕ Limpiar filtro", key="clear_gc"):
            st.session_state.gc_cob = None
            st.session_state.gc_loc = None
            st.rerun()

    st.divider()
    st.caption(f"👤 **{st.session_state.login_user}**")
    if st.button("🚪 Cerrar sesión", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.login_user = ""
        st.session_state["_skip_loading"] = True
        st.rerun()

# Aplicar filtros de gráfico — con validación para evitar df vacío
if st.session_state.gc_cob:
    if st.session_state.gc_cob in df_f["COBERTURA"].values:
        df_f = df_f[df_f["COBERTURA"] == st.session_state.gc_cob]
    else:
        st.session_state.gc_cob = None  # valor ya no existe en el subconjunto actual

if st.session_state.gc_loc:
    _col, _val = st.session_state.gc_loc
    if _col in df_f.columns and _val in df_f[_col].values:
        df_f = df_f[df_f[_col] == _val]
    else:
        st.session_state.gc_loc = None  # valor ya no existe en el subconjunto actual

_modo_viz  = "🖼️ Iconos" if _usar_iconos else "🔵 Puntos"
_map_style = ("https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json"
              if _mostrar_calles else
              "https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json")

# ==============================
# Preparar datos del mapa (fuera de tabs, usado en ambas)
# ==============================
gc.collect()  # liberar memoria de reruns anteriores antes de construir df_plot

_cols_base = ["LATITUD", "LONGITUD", "COBERTURA", "NOMBRE DEL LOCAL",
              "DEPARTAMENTO", "PROVINCIA", "DISTRITO", "DIRECCION",
              "MESAS", "ELECTORES", "TIPO TECNOLOGIA"]
df_plot = df_f[_cols_base]  # vista, sin .copy()

# GMAPS_URL solo cuando hay local seleccionado (se construye bajo demanda en el popover)
# icon_data solo si se necesita (modo Iconos)
if _modo_viz == "🖼️ Iconos":
    df_plot = df_plot.copy()  # necesario para añadir columna
    df_plot["icon_data"] = [ICON_MAP.get(c, _DEFAULT_ICON) for c in df_plot["COBERTURA"]]

_mask_sin  = df_plot["COBERTURA"] == "*Sin Cobertura"
_mask_con  = df_plot["COBERTURA"] == "Con Cobertura"
_mask_fisc = df_plot["COBERTURA"] == "Fiscalizado"
df_sin  = df_plot[_mask_sin]
df_con  = df_plot[_mask_con]
df_fisc = df_plot[_mask_fisc]

# Cargar GeoJSONs + índice (cacheados, reutilizados en ambas pestañas)
_geo_dep_main = _load_geojson()
_idx_dep, _idx_prov, _idx_dist = _build_geo_index()

# Zoom y centro: si hay filtro geográfico → bbox del polígono GeoJSON
#                si es TODOS            → bbox de los puntos visibles
_main_bbox = None
if dist != "TODOS" and dep != "TODOS":
    _main_bbox = _bbox_from_features(_idx_dist.get((dep.strip().upper(),
                 prov.strip().upper() if prov != "TODOS" else "", dist.strip().upper()), []))
elif prov != "TODOS" and dep != "TODOS":
    _main_bbox = _bbox_from_features(_idx_prov.get((dep.strip().upper(), prov.strip().upper()), []))
elif dep != "TODOS":
    _main_bbox = _bbox_from_features([f for f in _geo_dep_main["features"]
                 if f["properties"].get("NOMBDEP", "").strip().upper() == dep.strip().upper()])

if _main_bbox:
    # Centrar en la capa geográfica seleccionada (ignora qué puntos están visibles)
    _bml, _bmx, _bnl, _bnx = _main_bbox
    clat, clon = (_bml + _bmx) / 2, (_bnl + _bnx) / 2
    zoom = _zoom_from_span(max(_bmx - _bml, _bnx - _bnl))
elif len(df_plot) > 0:
    # Sin filtro geográfico: centrar en los puntos visibles
    _minlat, _maxlat = df_plot["LATITUD"].min(), df_plot["LATITUD"].max()
    _minlon, _maxlon = df_plot["LONGITUD"].min(), df_plot["LONGITUD"].max()
    clat = (_minlat + _maxlat) / 2
    clon = (_minlon + _maxlon) / 2
    zoom = _zoom_from_span(max(_maxlat - _minlat, _maxlon - _minlon))
else:
    clat, clon, zoom = -9.19, -75.015, 5 + _ZOOM_OFFSET

# Capa de sombreado para el mapa principal
_main_shade_layers = []
if dist != "TODOS" and dep != "TODOS":
    _d  = dep.strip().upper()
    _p  = prov.strip().upper() if prov != "TODOS" else ""
    _di = dist.strip().upper()
    _sf = _idx_dist.get((_d, _p, _di), [])
    if _sf:
        _geo_sf = {"type": "FeatureCollection", "features": _sf}
        _main_shade_layers.append(pdk.Layer("GeoJsonLayer", _geo_sf,
                                             stroked=False, filled=True, get_fill_color=[200, 100, 0, 40]))
        _main_shade_layers.append(pdk.Layer("GeoJsonLayer", _geo_sf,
                                             stroked=True, filled=False,
                                             get_line_color=_BORDER_COLOR_DIST,
                                             line_width_min_pixels=_BORDER_W_DIST))
elif prov != "TODOS" and dep != "TODOS":
    _d, _p = dep.strip().upper(), prov.strip().upper()
    _sf = _idx_prov.get((_d, _p), [])
    if _sf:
        _geo_sf = {"type": "FeatureCollection", "features": _sf}
        _main_shade_layers.append(pdk.Layer("GeoJsonLayer", _geo_sf,
                                             stroked=False, filled=True, get_fill_color=[0, 160, 80, 30]))
        _main_shade_layers.append(pdk.Layer("GeoJsonLayer", _geo_sf,
                                             stroked=True, filled=False,
                                             get_line_color=_BORDER_COLOR_PROV,
                                             line_width_min_pixels=_BORDER_W_PROV))
elif dep != "TODOS":
    _d = dep.strip().upper()
    _sf_dep = [f for f in _geo_dep_main["features"]
               if f["properties"].get("NOMBDEP", "").strip().upper() == _d]
    if _sf_dep:
        _main_shade_layers.append(pdk.Layer("GeoJsonLayer", {"type": "FeatureCollection", "features": _sf_dep},
                                             stroked=False, filled=True, get_fill_color=[0, 80, 200, 22]))
    _sf_dist = _idx_dep.get(_d, [])
    if _sf_dist:
        _main_shade_layers.append(pdk.Layer("GeoJsonLayer", {"type": "FeatureCollection", "features": _sf_dist},
                                             stroked=True, filled=False,
                                             get_line_color=_BORDER_COLOR_PROV,
                                             line_width_min_pixels=_BORDER_W_PROV))

# ── Escala según nivel de filtro activo ──
if dist != "TODOS":
    _icon_size, _icon_scale = 11, 3
    _pt_px = 15
elif prov != "TODOS":
    _icon_size, _icon_scale = 5, 3
    _pt_px = 9
elif dep != "TODOS":
    _icon_size, _icon_scale = 4, 3
    _pt_px = 7
else:
    _icon_size, _icon_scale = 3, 4
    _pt_px = 6

_ikw = dict(get_position=["LONGITUD", "LATITUD"], get_icon="icon_data",
            get_size=_icon_size, size_scale=_icon_scale,
            pickable=True, auto_highlight=True)

_skw = dict(get_position=["LONGITUD", "LATITUD"],
            get_radius=1,
            radius_min_pixels=_pt_px,
            radius_max_pixels=_pt_px,
            pickable=True, auto_highlight=True,
            stroked=False, filled=True)

if _modo_viz == "🔵 Puntos":
    _layers_puntos = [
        pdk.Layer("ScatterplotLayer", df_sin,  get_fill_color=COLOR_MAP["*Sin Cobertura"], **_skw),
        pdk.Layer("ScatterplotLayer", df_con,  get_fill_color=COLOR_MAP["Con Cobertura"],  **_skw),
        pdk.Layer("ScatterplotLayer", df_fisc, get_fill_color=COLOR_MAP["Fiscalizado"],    **_skw),
    ]
else:
    _layers_puntos = [
        pdk.Layer("IconLayer", df_sin,  **_ikw),
        pdk.Layer("IconLayer", df_con,  **_ikw),
        pdk.Layer("IconLayer", df_fisc, **_ikw),
    ]

_gc_cob_key = st.session_state.gc_cob or ""
_gc_loc_key = f"{st.session_state.gc_loc}" if st.session_state.gc_loc else ""
_main_map_key = f"map_deck|{dep}|{prov}|{dist}|{_gc_cob_key}|{_gc_loc_key}|{_modo_viz}"

def _cb_map():
    sel = st.session_state.get(_main_map_key)
    for objs in getattr(getattr(sel, "selection", None), "objects", {}).values():
        if objs:
            st.session_state.clicked_local = objs[0]
            return

deck = pdk.Deck(
    layers=[
        pdk.Layer("GeoJsonLayer", "data/peru_departamental_simple.geojson",
                  stroked=True, filled=True,
                  get_fill_color=[200, 200, 200, 30],
                  get_line_color=[120, 120, 120],
                  line_width_min_pixels=1),
        *_main_shade_layers,
        *_layers_puntos,
    ],
    initial_view_state=pdk.ViewState(latitude=clat, longitude=clon, zoom=zoom, pitch=0),
    map_style=_map_style,
    tooltip={
        "html": (
            "<b>{NOMBRE DEL LOCAL}</b><br/>"
            "{DEPARTAMENTO} › {PROVINCIA} › {DISTRITO}<br/>"
            "<i>{DIRECCION}</i><br/>"
            "Mesas: <b>{MESAS}</b> | Electores: <b>{ELECTORES}</b><br/>"
            "Cobertura: <b>{COBERTURA}</b> | Tecnología: <b>{TIPO TECNOLOGIA}</b>"
        ),
        "style": {"backgroundColor": "#67678a", "color": "white",
                  "fontSize": "12px", "borderRadius": "6px", "padding": "10px 14px"},
    },
)

# ==============================
# Fila: botón menú + pestañas
# ==============================
_c_menubtn, _c_tabs = st.columns([0.04, 0.96], gap="small")

with _c_menubtn:
    st.components.v1.html("""
<button id="sb-menu-btn" title="Mostrar / ocultar menú lateral" style="
  background:#003770; color:white; border:none; border-radius:7px;
  width:36px; height:36px; font-size:20px; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  box-shadow:0 2px 8px rgba(0,55,112,.35); margin-top:4px;">&#9776;</button>
<script>
document.getElementById('sb-menu-btn').onclick = function() {
  var doc = window.parent.document;
  var close = doc.querySelector('[data-testid="stSidebarCollapseButton"] button');
  var open  = doc.querySelector('[data-testid="stSidebarCollapsedControl"] button');
  if (close) close.click();
  else if (open) open.click();
};
</script>
""", height=44)

with _c_tabs:
    tab_locales, tab_calor, tab_intl = st.tabs([
        "🗺️ Locales de Votación",
        "🔥 Mapa de Calor — Electores",
        "🌍 Internacional",
    ])

# ── Tab 1: mapa (col. izquierda) + KPIs y gráficos (col. derecha) ─────────────
with tab_locales:

    # — Cálculos KPI —
    _total   = len(df_f)
    _mesas   = int(df_f["MESAS"].sum())
    _elec    = int(df_f["ELECTORES"].sum())
    _sin     = int((df_f["COBERTURA"] == "*Sin Cobertura").sum())
    _con     = int((df_f["COBERTURA"] == "Con Cobertura").sum())
    _fisc    = int((df_f["COBERTURA"] == "Fiscalizado").sum())
    _t       = max(_total, 1)

    col_map, col_panel = st.columns([_MAP_COL_W, _PANEL_COL_W], gap="medium")

    # ── Columna izquierda: mapa ───────────────────────────────────────────────
    with col_map:
        _sel = st.session_state.clicked_local

        # Leyenda + popover ENCIMA del mapa (no empujan contenido al scroll)
        _leg_col, _pop_col = st.columns([3, 1])
        with _leg_col:
            st.markdown(
                "<span style='font-size:12px;'><b>Leyenda:</b> "
                f"<img src='{ICON_MAP['*Sin Cobertura']['url']}' height='17' style='vertical-align:middle'> Sin Cobertura &nbsp;"
                f"<img src='{ICON_MAP['Con Cobertura']['url']}' height='17' style='vertical-align:middle'> Con Cobertura &nbsp;"
                f"<img src='{ICON_MAP['Fiscalizado']['url']}' height='17' style='vertical-align:middle'> Fiscalizado</span>",
                unsafe_allow_html=True,
            )
        with _pop_col:
            if _sel:
                _gmaps = f"https://www.google.com/maps?q={_sel.get('LATITUD')},{_sel.get('LONGITUD')}"
                with st.popover("📍 Ver local"):
                    st.markdown(f"**{_sel.get('NOMBRE DEL LOCAL','')}**")
                    st.markdown(
                        f"{_sel.get('DEPARTAMENTO','')} › {_sel.get('PROVINCIA','')} › {_sel.get('DISTRITO','')}"
                    )
                    st.caption(f"Mesas: {_sel.get('MESAS','')} | Electores: {_sel.get('ELECTORES','')}")
                    st.caption(f"Cobertura: {_sel.get('COBERTURA','')} | Tecnología: {_sel.get('TIPO TECNOLOGIA','')}")
                    st.markdown(
                        f'<a href="{_gmaps}" target="_blank" style="display:inline-block;margin-top:6px;'
                        f'padding:6px 14px;background:#2563eb;color:white;border-radius:6px;'
                        f'text-decoration:none;font-size:13px;font-weight:600;">🗺️ Abrir en Google Maps</a>',
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("Clic en el mapa →")

        st.pydeck_chart(deck, height=_MAP_H,
                        on_select=_cb_map, key=_main_map_key)

        # JS: ajusta la altura del mapa al viewport real (aspecto Y altura disponible)
        _col_frac = _MAP_COL_W / (_MAP_COL_W + _PANEL_COL_W)
        st.components.v1.html(f"""
<script>(function(){{
  const COL_FRAC      = {_col_frac:.4f};
  const ASPECT        = {_MAP_ASPECT};
  const SIDEBAR_W     = {_SIDEBAR_PX};
  const H_MIN         = {_MAP_H_MIN};
  const H_MAX         = {_MAP_H_MAX};
  const CHROME        = {_CHROME_PX};

  function calcH(){{
    try {{
      const vw       = window.parent.innerWidth;
      const vh       = window.parent.innerHeight;
      const colW     = (vw - SIDEBAR_W) * COL_FRAC;
      const byAspect = colW * ASPECT;
      const byVh     = vh - CHROME;
      const h = Math.round(Math.max(H_MIN, Math.min(H_MAX, byAspect, byVh)));
      window.parent.document
        .querySelectorAll('[data-testid="stDeckGlJsonChart"]')
        .forEach(el => {{ el.style.height = h + "px"; }});
    }} catch(e) {{}}
  }}
  calcH();
  window.parent.addEventListener("resize", calcH);
}})();</script>
""", height=0)

    # ── Columna derecha: tarjetas KPI + gráficos ─────────────────────────────
    with col_panel:

        # — Tarjetas KPI (grid 2 columnas) —
        def _card(label, value, color, subtitle="", bar_items=None):
            bars_html = ""
            if bar_items:
                for name, val, pct, bcolor in bar_items:
                    bars_html += f"""
                    <div style='font-size:10px;font-weight:600;display:flex;justify-content:space-between;color:#374151;margin-top:4px;'>
                      <span>{name} ({val:,})</span><span>{pct:.0f}%</span>
                    </div>
                    <div style='background:#e5e7eb;height:4px;border-radius:4px;margin-bottom:2px;'>
                      <div style='background:{bcolor};width:{min(pct,100):.1f}%;height:4px;border-radius:4px;'></div>
                    </div>"""
            sub_html = f"<div style='font-size:10px;color:#6b7280;margin-top:3px;'>{subtitle}</div>" if subtitle else ""
            return f"""
            <div style='font-family:Segoe UI,Arial;background:#f3f4f6;border-radius:10px;
                        padding:12px 14px;position:relative;'>
              <div style='position:absolute;top:0;left:0;width:4px;height:100%;background:{color};
                          border-radius:6px 0 0 6px;'></div>
              <div style='margin-left:8px;'>
                <div style='font-size:10px;font-weight:600;color:#64748b;text-transform:uppercase;
                            letter-spacing:.5px;margin-bottom:3px;'>{label}</div>
                <div style='font-size:22px;font-weight:800;color:#111827;line-height:1.1;'>{value}</div>
                {sub_html}{bars_html}
              </div>
            </div>"""

        def _bar_item_rows(items):
            return "".join(
                f"""<div style='font-size:10px;font-weight:600;display:flex;justify-content:space-between;
                              color:#374151;margin-top:4px;'>
                      <span>{n} ({v:,})</span><span>{p:.0f}%</span>
                    </div>
                    <div style='background:#e5e7eb;height:4px;border-radius:4px;margin-bottom:2px;'>
                      <div style='background:{bc};width:{min(p,100):.1f}%;height:4px;border-radius:4px;'></div>
                    </div>"""
                for n, v, p, bc in items
            )

        _tec_items = [
            (t, int(cnt), cnt / _t * 100, "#0891b2")
            for t, cnt in df_f["TIPO TECNOLOGIA"].value_counts().head(3).items()
        ]

        _kpi_html = f"""
        <div id='kpi' style='display:grid;grid-template-columns:1fr 1fr;gap:8px;
                             font-family:Segoe UI,Arial;padding:0;margin:0;'>
          {_card("Locales",   f"{_total:,}",  "#2563eb",
                 subtitle=f"{dep if dep != 'TODOS' else 'Nacional'}")}
          {_card("Mesas",     f"{_mesas:,}",  "#7c3aed")}
          {_card("Electores", f"{_elec:,}",   "#059669")}
          <div style='font-family:Segoe UI,Arial;background:#f3f4f6;border-radius:10px;
                      padding:12px 14px;position:relative;'>
            <div style='position:absolute;top:0;left:0;width:4px;height:100%;background:#f59e0b;
                        border-radius:6px 0 0 6px;'></div>
            <div style='margin-left:8px;'>
              <div style='font-size:10px;font-weight:600;color:#64748b;text-transform:uppercase;
                          letter-spacing:.5px;margin-bottom:3px;'>Cobertura</div>
              {_bar_item_rows([
                  ("Sin cobertura.", _sin,  _sin/_t*100,  "#363636"),
                  ("Con cobertura.", _con,  _con/_t*100,  "#00b4e1"),
                  ("Fiscalizacion.", _fisc, _fisc/_t*100, "#0703e7"),
              ])}
            </div>
          </div>
          <div style='grid-column:1/-1;font-family:Segoe UI,Arial;background:#f3f4f6;
                      border-radius:10px;padding:12px 14px;position:relative;'>
            <div style='position:absolute;top:0;left:0;width:4px;height:100%;background:#0891b2;
                        border-radius:6px 0 0 6px;'></div>
            <div style='margin-left:8px;'>
              <div style='font-size:10px;font-weight:600;color:#64748b;text-transform:uppercase;
                          letter-spacing:.5px;margin-bottom:3px;'>Tecnología</div>
              {_bar_item_rows(_tec_items)}
            </div>
          </div>
        </div>
        <script>
          function sendH(){{
            var el = document.getElementById('kpi');
            var h = el.getBoundingClientRect().height;
            if (h < 10) h = el.scrollHeight;
            window.parent.postMessage({{type:'streamlit:setFrameHeight', height: h + 16}}, '*');
          }}
          window.addEventListener('load', sendH);
          window.addEventListener('resize', sendH);
          setTimeout(sendH, 100); setTimeout(sendH, 400); setTimeout(sendH, 900);
        </script>"""
        st.components.v1.html(_kpi_html, height=340, scrolling=False)

        # — Donut cobertura —
        cob_df = df_f["COBERTURA"].value_counts().reset_index()
        cob_df.columns = ["Cobertura", "Locales"]
        color_seq = [f"rgb({COLOR_MAP.get(c,[150,150,150])[0]},"
                     f"{COLOR_MAP.get(c,[150,150,150])[1]},"
                     f"{COLOR_MAP.get(c,[150,150,150])[2]})"
                     for c in cob_df["Cobertura"]]

        fig_donut = px.pie(cob_df, names="Cobertura", values="Locales",
                           hole=0.55, title="Cobertura",
                           color_discrete_sequence=color_seq)
        fig_donut.update_layout(margin=dict(t=36, b=0, l=0, r=0), height=220,
                                 legend=dict(orientation="h", y=-0.12),
                                 clickmode="event+select")
        st.plotly_chart(fig_donut,
                        on_select=_cb_donut, key="donut_chart")


# ── Tab 2: mapa de calor por electores (Perú completo) ────────────────────────
with tab_calor:
    col_hm, col_hm_charts = st.columns([2, 1], gap="medium")

    with col_hm:
        st.subheader("Densidad de Electores")

        # Auto-calcular radio e intensidad según el zoom de la selección actual:
        # - Mayor zoom (más cerca) → radio más pequeño, más intensidad
        # - Menor zoom (vista nacional) → radio mayor, menos intensidad
        _auto_radius    = max(5,   min(80,  int(35 * (5.0 / zoom) ** 1.2)))
        _auto_intensity = max(0.5, min(50.0, round(20.0 * (zoom / 5.0) ** 0.8, 1)))

        # Resetear sliders cuando cambia el filtro geográfico
        _hm_fkey = f"{dep}|{prov}|{dist}"
        if st.session_state.get("_hm_fkey") != _hm_fkey:
            st.session_state["_hm_fkey"] = _hm_fkey
            for _k in ("hm_radius", "hm_intensity"):
                st.session_state.pop(_k, None)

        _sc1, _sc2, _sc3 = st.columns(3)
        _hm_radius = _sc1.slider("Radio (px)", min_value=5, max_value=80,
                                  value=_auto_radius, step=5, key="hm_radius",
                                  help="Auto-ajustado al zoom — puedes modificarlo manualmente")
        _hm_intensity = _sc2.slider("Intensidad", min_value=0.5, max_value=50.0,
                                     value=_auto_intensity, step=0.5, key="hm_intensity",
                                     help="Auto-ajustado al zoom — puedes modificarlo manualmente")
        _hm_threshold = _sc3.slider("Umbral", min_value=0.01, max_value=0.50,
                                     value=0.01, step=0.01, key="hm_threshold",
                                     help="Opacidad mínima para pintar — baja para ver más puntos, sube para filtrar ruido")

        # Usa df_f (filtrado) para que los selectores redefinan el área del mapa
        _hm_src = df_f[["LATITUD", "LONGITUD", "ELECTORES"]].dropna().copy()
        # Normalización por percentil dentro del subconjunto filtrado
        if len(_hm_src) > 1:
            _hm_src["PESO"] = _hm_src["ELECTORES"].rank(pct=True).mul(100)
        else:
            _hm_src["PESO"] = 50.0

        # Vista centrada en el polígono seleccionado (bbox del GeoJSON, no de los puntos)
        _geo_bbox = None
        if dist != "TODOS" and dep != "TODOS":
            _dep_n  = dep.strip().upper()
            _prov_n = prov.strip().upper() if prov != "TODOS" else ""
            _dist_n = dist.strip().upper()
            _geo_bbox = _bbox_from_features(_idx_dist.get((_dep_n, _prov_n, _dist_n), []))
        elif prov != "TODOS" and dep != "TODOS":
            _dep_n, _prov_n = dep.strip().upper(), prov.strip().upper()
            _geo_bbox = _bbox_from_features(_idx_prov.get((_dep_n, _prov_n), []))
        elif dep != "TODOS":
            _dep_n = dep.strip().upper()
            _geo_bbox = _bbox_from_features([
                f for f in _geo_dep_main["features"]
                if f["properties"].get("NOMBDEP", "").strip().upper() == _dep_n
            ])

        if _geo_bbox:
            _bminlat, _bmaxlat, _bminlon, _bmaxlon = _geo_bbox
            _hm_lat  = (_bminlat + _bmaxlat) / 2
            _hm_lon  = (_bminlon + _bmaxlon) / 2
            _hm_zoom = _zoom_from_span(max(_bmaxlat - _bminlat, _bmaxlon - _bminlon))
        else:
            _hm_lat, _hm_lon, _hm_zoom = clat, clon, zoom

        _hm_layer = pdk.Layer(
            "HeatmapLayer",
            data=_hm_src,
            get_position=["LONGITUD", "LATITUD"],
            get_weight="PESO",
            aggregation="SUM",
            radiusPixels=_hm_radius,
            intensity=_hm_intensity,
            threshold=_hm_threshold,
            color_range=[
                [224, 247, 255, 0  ],   # transparente
                [56,  189, 248, 130],   # celeste
                [34,  197, 170, 170],   # celeste-verde
                [16,  185, 129, 200],   # verde
                [5,   150, 105, 220],   # verde oscuro
                [30,  80,  200, 245],   # azul intenso
            ],
        )

        # Capas: sombreado (debajo del calor) → heatmap → contornos (encima)
        _hm_layers = []

        # Sombreado según nivel activo
        if dist != "TODOS" and dep != "TODOS":
            _dep_n  = dep.strip().upper()
            _prov_n = prov.strip().upper() if prov != "TODOS" else ""
            _dist_n = dist.strip().upper()
            _sel_feats = _idx_dist.get((_dep_n, _prov_n, _dist_n), [])
            if _sel_feats:
                _hm_layers.append(pdk.Layer(
                    "GeoJsonLayer", {"type": "FeatureCollection", "features": _sel_feats},
                    stroked=False, filled=True, get_fill_color=[200, 100, 0, 40],
                ))
        elif prov != "TODOS" and dep != "TODOS":
            _dep_n, _prov_n = dep.strip().upper(), prov.strip().upper()
            _sel_feats = _idx_prov.get((_dep_n, _prov_n), [])
            if _sel_feats:
                _hm_layers.append(pdk.Layer(
                    "GeoJsonLayer", {"type": "FeatureCollection", "features": _sel_feats},
                    stroked=False, filled=True, get_fill_color=[0, 160, 80, 30],
                ))
        elif dep != "TODOS":
            _dep_n = dep.strip().upper()
            _sel_feats = [f for f in _geo_dep_main["features"]
                          if f["properties"].get("NOMBDEP", "").strip().upper() == _dep_n]
            if _sel_feats:
                _hm_layers.append(pdk.Layer(
                    "GeoJsonLayer", {"type": "FeatureCollection", "features": _sel_feats},
                    stroked=False, filled=True, get_fill_color=[0, 80, 200, 22],
                ))

        _hm_layers.append(_hm_layer)

        # Bordes distritales (finos, debajo)
        _hm_layers.append(pdk.Layer(
            "GeoJsonLayer", "data/DISTRITO.geojson",
            stroked=True, filled=False,
            get_line_color=[80, 80, 80],
            get_line_width=300,
            line_width_min_pixels=1,
            line_width_max_pixels=3,
        ))

        # Bordes departamentales (gruesos, encima)
        _hm_layers.append(pdk.Layer(
            "GeoJsonLayer", "data/DEPARTAMENTO.geojson",
            stroked=True, filled=False,
            get_line_color=[20, 20, 20],
            get_line_width=2000,
            line_width_min_pixels=3,
            line_width_max_pixels=10,
        ))

        # key cambia con el filtro → fuerza re-render y aplica el nuevo initial_view_state
        _hm_key = f"heatmap_deck|{dep}|{prov}|{dist}"

        _hm_deck = pdk.Deck(
            layers=_hm_layers,
            initial_view_state=pdk.ViewState(
                latitude=_hm_lat, longitude=_hm_lon, zoom=_hm_zoom, pitch=0
            ),
            map_style=_map_style,
        )

        _filtro_activo = dep != "TODOS" or prov != "TODOS" or dist != "TODOS"
        st.pydeck_chart(_hm_deck, height=_MAP_H, key=_hm_key)
        if _filtro_activo:
            st.caption(f"Zona: {' › '.join(x for x in [dep, prov, dist] if x != 'TODOS')} — Verde = pocos electores · Rojo = alta concentración.")
        else:
            st.caption("Vista nacional. Usa los filtros del sidebar para acercar a una zona. Verde = pocos electores · Rojo = alta concentración.")

    with col_hm_charts:
        st.subheader("Top por Electores")

        _grp = (df_f.groupby(["DEPARTAMENTO", "PROVINCIA"])["ELECTORES"]
                .sum().reset_index())
        _top_dep = _grp.groupby("DEPARTAMENTO")["ELECTORES"].sum().nlargest(8).index
        _grp_top = _grp[_grp["DEPARTAMENTO"].isin(_top_dep)]

        if _grp_top.empty:
            st.info("Sin datos para el treemap con los filtros actuales.")
        else:
            fig_tree = px.treemap(
                _grp_top,
                path=["DEPARTAMENTO", "PROVINCIA"],
                values="ELECTORES",
                color="ELECTORES",
                color_continuous_scale="Reds",
                title="Electores por Depto. / Provincia",
            )
            fig_tree.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=280,
                                    coloraxis_showscale=False)
            st.plotly_chart(fig_tree)

        _dist_elec = (df_f.groupby("DISTRITO")["ELECTORES"]
                      .sum().nlargest(10).reset_index().sort_values("ELECTORES"))
        fig_dist = px.bar(_dist_elec, x="ELECTORES", y="DISTRITO", orientation="h",
                          title="Top 10 Distritos por Electores",
                          color="ELECTORES", color_continuous_scale="OrRd")
        fig_dist.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=320,
                                showlegend=False, coloraxis_showscale=False,
                                yaxis_title="", xaxis_title="Electores")
        st.plotly_chart(fig_dist)

# ── Tab 3: Locales Internacionales ───────────────────────────────────────────
with tab_intl:
    col_im, col_ip = st.columns([_MAP_COL_W, _PANEL_COL_W], gap="medium")

    with col_im:
        # Filtros internos al tab (continente → país)
        _fi1, _fi2 = st.columns(2)
        with _fi1:
            _i_cont_opts = ["TODOS"] + sorted(df_intl["CONTINENTE"].dropna().unique())
            _i_cont = st.selectbox("Continente", _i_cont_opts, key="i_cont")
        _df_fi = df_intl if _i_cont == "TODOS" else df_intl[df_intl["CONTINENTE"] == _i_cont]
        with _fi2:
            _i_pais_opts = ["TODOS"] + sorted(_df_fi["PAIS"].dropna().unique())
            _i_pais = st.selectbox("País", _i_pais_opts, key="i_pais")
        _df_fi = _df_fi if _i_pais == "TODOS" else _df_fi[_df_fi["PAIS"] == _i_pais]

        # Zoom y centro según puntos visibles
        if len(_df_fi) > 0:
            _ilat_c = (_df_fi["LATITUD"].min() + _df_fi["LATITUD"].max()) / 2
            _ilon_c = (_df_fi["LONGITUD"].min() + _df_fi["LONGITUD"].max()) / 2
            _ispn   = max(_df_fi["LATITUD"].max()  - _df_fi["LATITUD"].min(),
                          _df_fi["LONGITUD"].max() - _df_fi["LONGITUD"].min())
            _izoom  = _zoom_from_span(_ispn) if _ispn > 0.5 else 4.0
        else:
            _ilat_c, _ilon_c, _izoom = 20.0, 10.0, 1.5

        # Agregar por ciudad: suma de ELECTORES y MESAS, conteo de locales
        # → cada burbuja representa una ciudad/sede; su tamaño = total de electores
        _df_agg = (
            _df_fi
            .groupby(["CONTINENTE", "PAIS", "CIUDAD", "LATITUD", "LONGITUD"], as_index=False)
            .agg(ELECTORES=("ELECTORES", "sum"),
                 MESAS=("MESAS", "sum"),
                 LOCALES=("ELECTORES", "count"))
        )

        # Radio proporcional a la SUMA de ELECTORES (escala √ para suavizar outliers)
        # Normalizado dentro del subconjunto visible → siempre hay contraste relativo
        _max_e = _df_agg["ELECTORES"].max() if len(_df_agg) > 0 and _df_agg["ELECTORES"].max() > 0 else 1
        _df_agg["_radio"] = (_df_agg["ELECTORES"] / _max_e).pow(0.5) * 120_000  # metros

        _ideck = pdk.Deck(
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    _df_agg,
                    get_position=["LONGITUD", "LATITUD"],
                    get_radius="_radio",
                    radius_min_pixels=5,
                    radius_max_pixels=80,
                    get_fill_color=[20, 184, 166, 170],   # teal semitransparente
                    get_line_color=[255, 255, 255, 150],
                    stroked=True,
                    line_width_min_pixels=1,
                    filled=True,
                    pickable=True,
                    auto_highlight=True,
                ),
            ],
            initial_view_state=pdk.ViewState(latitude=_ilat_c, longitude=_ilon_c, zoom=_izoom, pitch=0),
            map_style=_map_style,
            tooltip={
                "html": (
                    "{CONTINENTE} › <b>{PAIS}</b> › {CIUDAD}<br/>"
                    "Locales: <b>{LOCALES}</b><br/>"
                    "Mesas: <b>{MESAS}</b> | Electores: <b>{ELECTORES}</b>"
                ),
                "style": {"backgroundColor": "#67678a", "color": "white",
                          "fontSize": "12px", "borderRadius": "6px", "padding": "10px 14px"},
            },
        )

        _ikey = f"intl_deck|{_i_cont}|{_i_pais}"
        st.pydeck_chart(_ideck, height=_MAP_H, key=_ikey)
        st.caption(f"**{len(_df_agg):,}** ciudades — **{len(_df_fi):,}** locales — burbuja = suma de electores por ciudad")

    with col_ip:
        # KPIs
        _it  = len(_df_fi)
        _im  = int(_df_fi["MESAS"].sum())     if "MESAS"     in _df_fi.columns else 0
        _ie  = int(_df_fi["ELECTORES"].sum()) if "ELECTORES" in _df_fi.columns else 0

        st.markdown(f"""
        <div style='display:grid;grid-template-columns:1fr 1fr;gap:8px;font-family:Segoe UI,Arial;margin-bottom:10px;'>
          <div style='background:#f3f4f6;border-radius:10px;padding:12px 14px;border-left:4px solid #2563eb;'>
            <div style='font-size:10px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.5px;'>Locales</div>
            <div style='font-size:22px;font-weight:800;color:#111827;'>{_it:,}</div>
          </div>
          <div style='background:#f3f4f6;border-radius:10px;padding:12px 14px;border-left:4px solid #7c3aed;'>
            <div style='font-size:10px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.5px;'>Mesas</div>
            <div style='font-size:22px;font-weight:800;color:#111827;'>{_im:,}</div>
          </div>
          <div style='background:#f3f4f6;border-radius:10px;padding:12px 14px;border-left:4px solid #059669;grid-column:1/-1;'>
            <div style='font-size:10px;font-weight:600;color:#64748b;text-transform:uppercase;letter-spacing:.5px;'>Electores</div>
            <div style='font-size:22px;font-weight:800;color:#111827;'>{_ie:,}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Top países por electores
        _i_pais_df = (_df_fi.groupby("PAIS")["ELECTORES"]
                      .sum().nlargest(15).reset_index().sort_values("ELECTORES"))
        if not _i_pais_df.empty:
            fig_ipais = px.bar(_i_pais_df, x="ELECTORES", y="PAIS", orientation="h",
                               title="Electores por País (top 15)",
                               color="ELECTORES", color_continuous_scale="Teal")
            fig_ipais.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=420,
                                     showlegend=False, coloraxis_showscale=False,
                                     yaxis_title="", xaxis_title="Electores")
            st.plotly_chart(fig_ipais)

# ==============================
# Tabla detalle (colapsable)
# ==============================
with st.expander(f"Ver tabla de datos ({len(df_f):,} registros)"):
    cols_show = ["DEPARTAMENTO", "PROVINCIA", "DISTRITO", "NOMBRE DEL LOCAL",
                 "TIPO LOCAL", "DIRECCION", "MESAS", "ELECTORES",
                 "TIPO TECNOLOGIA", "COBERTURA", "LATITUD", "LONGITUD"]
    cols_show = [c for c in cols_show if c in df_f.columns]
    st.dataframe(df_f[cols_show].reset_index(drop=True), height=300)

# ── Ocultar overlay: el script se ejecuta cuando el iframe carga (todo ya renderizado) ──
st.components.v1.html(f"""<!-- hide:{_run_id} -->
<script>
(function(){{
  var doc = window.parent ? window.parent.document : document;
  function hide() {{
    var el = doc.getElementById('st-loading-overlay');
    if (el) el.style.display = 'none';
  }}
  // Intento inmediato + reintentos por si pydeck aún está montando
  hide();
  setTimeout(hide, 400);
  setTimeout(hide, 900);
}})();
</script>
""", height=0, scrolling=False)
