import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Analyse Descriptive", page_icon="📈", layout="wide")

st.title("📈 Analyse Descriptive des Ventes")

conn = sqlite3.connect('data/ventes.db')
nb_ventes = pd.read_sql("SELECT COUNT(*) as count FROM ventes", conn)['count'][0]

if nb_ventes == 0:
    st.warning("⚠️ Aucune donnée de vente disponible.")
    st.stop()

df_ventes = pd.read_sql("""
    SELECT v.*, p.nom as produit_nom, p.categorie, p.cout_revient
    FROM ventes v
    JOIN produits p ON v.produit_id = p.id
""", conn)
conn.close()

df_ventes['total_vente'] = df_ventes['quantite'] * df_ventes['prix_vente']
df_ventes['marge'] = df_ventes['total_vente'] - (df_ventes['cout_revient'] * df_ventes['quantite'])
df_ventes['date_vente'] = pd.to_datetime(df_ventes['date_vente'])

# KPIs
total_ca = df_ventes['total_vente'].sum()
total_marge = df_ventes['marge'].sum()
panier_moyen = df_ventes['total_vente'].mean()
nb_transactions = len(df_ventes)
taux_marge = (total_marge / total_ca * 100) if total_ca > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("💰 CA Total", f"{total_ca:,.0f} FCFA")
with col2:
    st.metric("📊 Marge", f"{total_marge:,.0f} FCFA")
with col3:
    st.metric("🛒 Panier Moyen", f"{panier_moyen:,.0f} FCFA")
with col4:
    st.metric("📈 Taux Marge", f"{taux_marge:.1f}%")
with col5:
    st.metric("🔢 Transactions", nb_transactions)

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Évolution", "🏷️ Catégories", "🌍 Régions", "📊 Corrélations"])

with tab1:
    st.subheader("Évolution des ventes")
    
    df_jour = df_ventes.groupby(df_ventes['date_vente'].dt.date).agg({
        'total_vente': 'sum',
        'id': 'count'
    }).reset_index()
    df_jour.columns = ['Date', 'CA', 'Nb_Ventes']
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.line(df_jour, x='Date', y='CA', title='CA Journalier')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(df_jour, x='Date', y='Nb_Ventes', title='Ventes par Jour')
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Analyse par Catégorie")
    
    df_cat = df_ventes.groupby('categorie').agg({
        'total_vente': 'sum',
        'marge': 'sum',
        'id': 'count'
    }).reset_index()
    df_cat.columns = ['Catégorie', 'CA', 'Marge', 'Nb_Ventes']
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.pie(df_cat, values='CA', names='Catégorie', title='CA par Catégorie')
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(df_cat, x='Catégorie', y='Marge', title='Marge par Catégorie', color='Catégorie')
        st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("🏆 Top 10 Produits")
    df_top = df_ventes.groupby('produit_nom').agg({
        'total_vente': 'sum',
        'quantite': 'sum'
    }).sort_values('total_vente', ascending=False).head(10).reset_index()
    
    fig = px.bar(df_top, x='produit_nom', y='total_vente', title='Top 10 Produits', color='quantite')
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Analyse Géographique")
    
    df_region = df_ventes.groupby('region').agg({
        'total_vente': 'sum',
        'id': 'count'
    }).reset_index()
    df_region.columns = ['Région', 'CA', 'Nb_Ventes']
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.pie(df_region, values='CA', names='Région', title='CA par Région')
        fig.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(df_region, x='Région', y='CA', title='CA par Région', color='Région')
        st.plotly_chart(fig, use_container_width=True)
    
    # Mode de paiement
    st.subheader("💳 Modes de Paiement")
    df_paiement = df_ventes.groupby('mode_paiement').agg({
        'total_vente': 'sum',
        'id': 'count'
    }).reset_index()
    df_paiement.columns = ['Mode', 'CA', 'Nombre']
    
    col1, col2 = st.columns(2)
    with col1:
        fig = px.pie(df_paiement, values='CA', names='Mode', title='CA par Mode')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.dataframe(df_paiement, use_container_width=True)

with tab4:
    st.subheader("📊 Matrice de Corrélation")
    
    vars_num = df_ventes[['quantite', 'prix_vente', 'remise', 'total_vente', 'marge']]
    corr = vars_num.corr()
    
    fig = px.imshow(corr, text_auto='.2f', aspect='auto', title='Corrélations', color_continuous_scale='RdBu_r')
    st.plotly_chart(fig, use_container_width=True)
    
    st.info("""
    💡 **Interprétation :**
    - **1.0** = Corrélation positive parfaite
    - **0.0** = Pas de corrélation
    - **-1.0** = Corrélation négative parfaite
    """)

# Export
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    csv = df_ventes.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Télécharger données (CSV)", csv, "ventes.csv", "text/csv")
with col2:
    if st.button("🏠 Retour à l'accueil"):
        st.switch_page("app.py")
