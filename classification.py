import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Classification", page_icon="🔍", layout="wide")

st.title("🔍 Classification Non-Supervisée (K-Means)")
st.write("Segmentation intelligente des clients basée sur leur comportement d'achat")

conn = sqlite3.connect('data/ventes.db')
nb_ventes = pd.read_sql("SELECT COUNT(*) as count FROM ventes", conn)['count'][0]

if nb_ventes < 5:
    st.warning("⚠️ Minimum 5 ventes requises pour la classification.")
    st.stop()

df_ventes = pd.read_sql("""
    SELECT v.*, p.nom as produit_nom, p.categorie, p.cout_revient
    FROM ventes v
    JOIN produits p ON v.produit_id = p.id
""", conn)
conn.close()

df_ventes['total_vente'] = df_ventes['quantite'] * df_ventes['prix_vente']
df_ventes['marge'] = df_ventes['total_vente'] - (df_ventes['cout_revient'] * df_ventes['quantite'])

# Agrégation par client
df_clients = df_ventes.groupby('client').agg({
    'total_vente': ['sum', 'mean', 'count'],
    'quantite': 'sum',
    'marge': 'sum'
}).reset_index()
df_clients.columns = ['Client', 'CA_Total', 'Panier_Moyen', 'Nb_Achats', 'Qté_Totale', 'Marge_Totale']

if len(df_clients) < 2:
    st.warning("Pas assez de clients pour la segmentation.")
    st.stop()

# Features pour clustering
features = ['CA_Total', 'Panier_Moyen', 'Nb_Achats', 'Qté_Totale']
X = df_clients[features].values

# Standardisation
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Choix nombre clusters
col1, col2 = st.columns([1, 2])
with col1:
    n_clusters = st.slider("Nombre de segments", 2, min(5, len(df_clients)), 3)

# K-Means
kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
df_clients['Cluster'] = kmeans.fit_predict(X_scaled)

segment_names = {0: "🌟 Premium", 1: "📈 Réguliers", 2: "🔄 Occasionnels", 3: "💰 Gros", 4: "📉 Faibles"}
df_clients['Segment'] = df_clients['Cluster'].map(segment_names)
df_clients['Segment'] = df_clients['Segment'].fillna('📊 Segment ' + df_clients['Cluster'].astype(str))

with col2:
    fig = px.scatter(df_clients, x='CA_Total', y='Nb_Achats', color='Segment', 
                    size='Panier_Moyen', hover_data=['Client'],
                    title='Segmentation Clients',
                    labels={'CA_Total': 'CA Total (FCFA)', 'Nb_Achats': 'Nombre Achats'})
    st.plotly_chart(fig, use_container_width=True)

# Statistiques
st.subheader("📊 Caractéristiques des Segments")
stats = df_clients.groupby('Segment').agg({
    'Client': 'count',
    'CA_Total': ['sum', 'mean'],
    'Panier_Moyen': 'mean',
    'Nb_Achats': 'mean'
}).round(2)
stats.columns = ['Nb Clients', 'CA Total', 'CA Moyen/Client', 'Panier Moyen', 'Achats Moyens']
st.dataframe(stats, use_container_width=True)

# Graphiques
col1, col2 = st.columns(2)
with col1:
    fig = px.pie(df_clients, names='Segment', title='Répartition Clients')
    st.plotly_chart(fig, use_container_width=True)
with col2:
    fig = px.bar(stats.reset_index(), x='Segment', y='CA Total', title='CA par Segment', color='Segment')
    st.plotly_chart(fig, use_container_width=True)

# Top clients
st.subheader("🏆 Top 10 Clients")
top_clients = df_clients.nlargest(10, 'CA_Total')[['Client', 'Segment', 'CA_Total', 'Nb_Achats']]
st.dataframe(top_clients, use_container_width=True)

# Export
csv = df_clients.to_csv(index=False).encode('utf-8')
st.download_button("📥 Télécharger segmentation (CSV)", csv, "segments_clients.csv", "text/csv")

st.markdown("---")
if st.button("🏠 Retour à l'accueil"):
    st.switch_page("app.py")
