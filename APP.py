import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── CONFIGURAZIONE PAGINA ────────────────────────────────
st.set_page_config(
    page_title="Analisi GPS",
    page_icon="📊",
    layout="wide"
)

st.markdown("""
    <style>
    /* Sfondo principale */
    .stApp { background-color: #0e0e0e; }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #1a1a1a; }
    
    /* Testo generale bianco brillante */
    html, body, [class*="css"], p, label, span { color: #ffffff !important; }
    
    /* Titoli neon verde */
    h1, h2, h3 { color: #00ff88 !important; }
    
    /* Metriche */
    div[data-testid="metric-container"] { 
        background-color: #1a1a1a; 
        border-radius: 10px; 
        padding: 10px;
        border: 1px solid #00ff88;
    }
    
    /* Tendine e selectbox */
    .stSelectbox > div > div { 
        background-color: #1a1a1a !important; 
        color: #ffffff !important;
        border: 1px solid #00ff88 !important;
    }
    
    /* Multiselect */
    .stMultiSelect > div > div { 
        background-color: #1a1a1a !important;
        border: 1px solid #00ff88 !important;
    }
    
    /* Dataframe */
    .stDataFrame { border: 1px solid #00ff88; }

    /* Divider */
    hr { border-color: #00ff88 !important; }
    </style>
""", unsafe_allow_html=True)

# ── PALETTE NEON ─────────────────────────────────────────
COLORI_NEON = [
    '#00ff88',  # verde neon
    '#00aaff',  # blu acceso
    '#ff0000',  # rosso acceso
    '#ffaa00',  # arancio
    '#00ffff',  # ciano
    '#ffffff',  # bianco

]
TEMPLATE = 'plotly_dark'

# ── TITOLO ───────────────────────────────────────────────
st.title("📊 Analisi GPS Giocatori")

# ── CARICAMENTO DATI ─────────────────────────────────────
match = pd.read_csv("2026_04_12_Full Match.csv", sep=';', decimal=',', encoding='utf-8-sig')
training = pd.read_csv("2026_04_07_Full Training.csv", sep=';', decimal=',', encoding='utf-8-sig')
match = match[match['Player'] != 'Team Average'].reset_index(drop=True)
training = training[training['Player'] != 'Team Average'].reset_index(drop=True)

# Calcolo tempo sessione
match['TEMPO SESSIONE'] = (match['DISTANZA'] / match['DISTANZA AL MINUTO']).round(1)
training['TEMPO SESSIONE'] = (training['DISTANZA'] / training['DISTANZA AL MINUTO']).round(1)

# ── SIDEBAR - FILTRI ─────────────────────────────────────
st.sidebar.title("⚙️ Filtri")
sessione = st.sidebar.radio("Sessione", ["Partita", "Allenamento"])
df = match if sessione == "Partita" else training
giocatori = st.sidebar.multiselect(
    "Seleziona giocatori",
    options=df['Player'].tolist(),
    default=df['Player'].tolist()
)
df_filtrato = df[df['Player'].isin(giocatori)]

# ── SEMAFORO + INDICE AFFIANCATI ─────────────────────────
st.subheader("📊 Cruscotto rapido")
st.caption("🟢 OK = sotto la media  |  🟡 ATTENZIONE = sopra la media  |  🔴 ALTO CARICO = oltre il 20% della media")

media_acc = df['N ACC > 3 m/s2'].mean()
media_pot = df['POTENZA METABOLICA MEDIA'].mean()
media_dist = df['DISTANZA'].mean()
media_smax = df['SMax (kmh)'].mean()
media_hr = df['HrAvg'].mean()

# Calcolo indice
metriche_score = ['DISTANZA', 'N ACC > 3 m/s2', 'SMax (kmh)', 'POTENZA METABOLICA MEDIA']
df_score = df_filtrato.copy()
for col in metriche_score:
    min_val = df[col].min()
    max_val = df[col].max()
    df_score[col + '_norm'] = (df_filtrato[col] - min_val) / (max_val - min_val)
df_score['INDICE'] = df_score[[col + '_norm' for col in metriche_score]].mean(axis=1) * 100

col_sx, col_dx = st.columns(2)

with col_sx:
    st.markdown("### 🚦 Semaforo di carico")
    for _, row in df_filtrato.iterrows():
        acc = row['N ACC > 3 m/s2']
        pot = row['POTENZA METABOLICA MEDIA']
        if acc > media_acc * 1.2 and pot > media_pot * 1.2:
            semaforo = "🔴 ALTO CARICO"
        elif acc > media_acc or pot > media_pot:
            semaforo = "🟡 ATTENZIONE"
        else:
            semaforo = "🟢 OK"
        st.write(f"**{row['Player']}** — {semaforo}")

with col_dx:
    st.markdown("### 🏅 Indice di performance")
    for _, row in df_score.sort_values('INDICE', ascending=False).iterrows():
        st.write(f"**{row['Player']}** — {row['INDICE']:.1f} / 100")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Distanza", f"{row['DISTANZA']} m")
        col2.metric("Accelerazioni", f"{int(row['N ACC > 3 m/s2'])}")
        col3.metric("Vel. Max", f"{row['SMax (kmh)']} km/h")
        col4.metric("Potenza", f"{row['POTENZA METABOLICA MEDIA']} W/kg")
        st.divider()

        # ── MEDIE DI RIFERIMENTO ─────────────────────────────────
with st.expander("📐 Medie di riferimento della sessione"):
    st.caption("Le medie sono calcolate sui giocatori presenti in questa sessione")
    medie = df[['DISTANZA', 'N ACC > 3 m/s2', 'SMax (kmh)', 
                'POTENZA METABOLICA MEDIA', 'HrAvg']].mean().round(1)
    medie.index = ['Distanza (m)', 'Accelerazioni intense', 
                   'Vel. Max (km/h)', 'Potenza metabolica (W/kg)', 'FC media (bpm)']
    st.dataframe(medie.rename('Media squadra'), use_container_width=True)
# Tabella dati
st.subheader(f"📋 Dati — {sessione}")
st.caption("⏱️ TEMPO SESSIONE include partita + intervallo + recupero")
st.dataframe(df_filtrato, use_container_width=True)

# ── GRAFICO DISTANZA ─────────────────────────────────────
fig = px.bar(
    df_filtrato,
    x='Player',
    y='DISTANZA',
    color='Player',
    text='DISTANZA',
    hover_data=['TEMPO SESSIONE', 'DISTANZA AL MINUTO'],
    color_discrete_sequence=COLORI_NEON,
    template=TEMPLATE,
    title=f'Distanza per giocatore — {sessione}'

)
fig.update_traces(textposition='outside')
fig.update_layout(showlegend=False)
st.plotly_chart(fig, use_container_width=True)

# ── GRAFICO CARICO FISICO CON MENU ───────────────────────
st.subheader(f"⚡ Carico fisico — {sessione}")
metrica_scelta = st.selectbox(
    "Scegli una metrica",
    ['N ACC > 3 m/s2', 'SMax (kmh)',
     'POTENZA METABOLICA MEDIA', 'SPESA ENERGETICA', 'HrAvg','DISTANZA']
)
fig2 = px.bar(
    df_filtrato,
    x='Player',
    y=metrica_scelta,
    color='Player',
    text=metrica_scelta,
    hover_data=['TEMPO SESSIONE', 'DISTANZA AL MINUTO'],
    color_discrete_sequence=COLORI_NEON,
    template=TEMPLATE,
    title=f'{metrica_scelta} per giocatore — {sessione}'
)
fig2.update_traces(textposition='outside')
fig2.update_layout(showlegend=False)
st.plotly_chart(fig2, use_container_width=True)

# ── CONFRONTO PARTITA VS ALLENAMENTO ────────────────────
st.subheader("⚔️ Confronto Partita vs Allenamento")
st.caption("Solo per i giocatori presenti in entrambe le sessioni: JAMMEH, MAMARANG, PAOLONI")

in_comune = ['JAMMEH', 'MAMARANG', 'PAOLONI']
match_comuni = match[match['Player'].isin(in_comune)].copy()
training_comuni = training[training['Player'].isin(in_comune)].copy()
match_comuni['Sessione'] = 'Partita'
training_comuni['Sessione'] = 'Allenamento'
confronto = pd.concat([match_comuni, training_comuni])

metrica_confronto = st.selectbox(
    "Scegli metrica da confrontare",
    ['DISTANZA', 'N ACC > 3 m/s2', 'SMax (kmh)',
     'POTENZA METABOLICA MEDIA', 'HrAvg'],
    key='confronto'
)
fig3 = px.bar(
    confronto,
    x='Player',
    y=metrica_confronto,
    color='Sessione',
    barmode='group',
    hover_data=['TEMPO SESSIONE', 'DISTANZA AL MINUTO'],
    text=metrica_confronto,
    color_discrete_sequence=['#00ff88', '#ff3366'],
    template=TEMPLATE,
    title=f'{metrica_confronto} — Partita vs Allenamento'
)
fig3.update_traces(textposition='outside')
st.plotly_chart(fig3, use_container_width=True)

# ── RADAR CHART - PROFILO FISICO ─────────────────────────
st.subheader(f"🕸️ Profilo fisico — {sessione}")
st.caption("I valori sono normalizzati da 0 a 1 per confrontare metriche diverse tra loro")

metriche_radar = ['DISTANZA', 'N ACC > 3 m/s2', 'SMax (kmh)',
                  'HrAvg', 'POTENZA METABOLICA MEDIA']

df_norm = df_filtrato.copy()
for col in metriche_radar:
    min_val = df[col].min()
    max_val = df[col].max()
    df_norm[col] = (df_filtrato[col] - min_val) / (max_val - min_val)

fig4 = go.Figure()
for i, (_, row) in enumerate(df_norm.iterrows()):
    valori = [row[m] for m in metriche_radar]
    valori += valori[:1]
    fig4.add_trace(go.Scatterpolar(
        r=valori,
        theta=metriche_radar + [metriche_radar[0]],
        fill='toself',
        name=row['Player'],
        line=dict(color=COLORI_NEON[i % len(COLORI_NEON)])
    ))
fig4.update_layout(
    polar=dict(
        bgcolor='#1a1a1a',
        radialaxis=dict(visible=True, range=[0, 1], color='#ffffff'),
        angularaxis=dict(color='#ffffff')
    ),
    paper_bgcolor='#0e0e0e',
    font=dict(color='#ffffff'),
    title=f'Profilo fisico — {sessione}'
)
st.plotly_chart(fig4, use_container_width=True)



# ── VALUTAZIONE GIOCATORE ────────────────────────────────
st.subheader("📝 Valutazione giocatore")
st.caption("Seleziona un giocatore per leggere la sua valutazione automatica")

giocatore_scelto = st.selectbox("Scegli giocatore", df_filtrato['Player'].tolist(), key='commento')
row = df_filtrato[df_filtrato['Player'] == giocatore_scelto].iloc[0]

media_dist = df['DISTANZA'].mean()
media_smax = df['SMax (kmh)'].mean()
media_hr = df['HrAvg'].mean()

commento = f"**{giocatore_scelto}** ha percorso **{row['DISTANZA']} metri**, "
commento += "sopra la media della squadra. " if row['DISTANZA'] > media_dist else "sotto la media della squadra. "
commento += f"Ha effettuato **{row['N ACC > 3 m/s2']} accelerazioni intense**, "
commento += "dato elevato che indica alto impegno neuro-muscolare. " if row['N ACC > 3 m/s2'] > media_acc else "nella norma per la sessione. "
commento += f"La velocità massima raggiunta è **{row['SMax (kmh)']} km/h**, "
commento += "tra le più alte del gruppo. " if row['SMax (kmh)'] > media_smax else "nella media del gruppo. "
commento += f"La frequenza cardiaca media di **{row['HrAvg']} bpm** "
commento += "suggerisce un alto stress cardiaco nella sessione. " if row['HrAvg'] > media_hr * 1.1 else "indica una buona efficienza cardiovascolare. " if row['HrAvg'] < media_hr * 0.9 else "è nella norma. "
commento += f"Potenza metabolica media: **{row['POTENZA METABOLICA MEDIA']} W/kg**. "
commento += "Carico complessivo **elevato** — si consiglia monitoraggio nel recupero." if row['POTENZA METABOLICA MEDIA'] > media_pot * 1.1 else "Carico complessivo **nella norma**."

st.info(commento)

# ── ALERT AUTOMATICI ─────────────────────────────────────
st.subheader("🚨 Alert automatici")
st.caption("Osservazioni basate sull'analisi dei dati GPS della sessione")

for _, row in df_filtrato.iterrows():
    alerts = []
    if row['N ACC > 3 m/s2'] > media_acc * 1.2:
        alerts.append("⚠️ Accelerazioni molto elevate — monitorare affaticamento muscolare")
    if row['DISTANZA'] > media_dist * 1.15:
        alerts.append("🏃 Distanza sopra la media — alto volume di lavoro")
    if row['SMax (kmh)'] > media_smax * 1.1:
        alerts.append("⚡ Velocità massima elevata — ottima capacità di sprint")
    if row['HrAvg'] < media_hr * 0.85:
        alerts.append("💚 FC media bassa — ottima efficienza cardiovascolare")
    if row['HrAvg'] > media_hr * 1.15:
        alerts.append("❤️ FC media alta — alto stress cardiaco nella sessione")

    if alerts:
        st.markdown(f"**{row['Player']}**")
        for a in alerts:
            st.write(f"  {a}")
    else:
        st.write(f"**{row['Player']}** — ✅ Nessun alert")
