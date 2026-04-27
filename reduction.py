import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Réduction Dimensionnalité", page_icon="📉", layout="wide")

st.title("📉 Réduction de Dimensionnalité (PCA)")
st.write("Analyse en Composantes Principales pour visualiser les données en 2D/3D")

conn = sqlite3.connect('data/ventes.db')
nb_ventes = pd.read_sql("SELECT COUNT(*) as count FROM ventes", conn)['count'][0]

if nb_ventes < 5:
    st.warning("⚠️ Minimum 5 ventes requises.")
    st.stop()

df_ventes = pd.read_sql("""
    SELECT v.*, p.nom as produit_nom, p.categorie, p.cout_revient
    FROM ventes v
    JOIN produits p ON v.produit_id = p.id
""", conn)
conn.close()

df_ventes['total_vente'] = df_ventes['quantite'] * df_ventes['prix_vente']
df_ventes['marge'] = df_ventes['total_vente'] - (df_ventes['cout_revient'] * df_ventes['quantite'])

# Agrégation par produit
df_prod = df_ventes.groupby('produit_nom').agg({
    'total_vente': 'sum',
    'quantite': 'sum',
    'marge': 'sum',
    'prix_vente': 'mean',
    'remise': 'mean'
}).reset_index()

# Ajouter catégorie
df_cat = df_ventes[['produit_nom', 'categorie']].drop_duplicates()
df_prod = df_prod.merge(df_cat, on='produit_nom', how='left')

st.info("""
💡 **L'ACP** permet de réduire plusieurs variables en 2-3 composantes principales 
tout en conservant le maximum d'information.
""")

# Features pour PCA
features = ['total_vente', 'quantite', 'marge', 'prix_vente', 'remise']
X = df_prod[features].values

# Standardisation
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# PCA
pca = PCA()
X_pca = pca.fit_transform(X_scaled)

# Variance expliquée
var_exp = pca.explained_variance_ratio_
var_cum = np.cumsum(var_exp)

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Variance Expliquée")
    
    var_df = pd.DataFrame({
        'Composante': [f'PC{i+1}' for i in range(len(var_exp))],
        'Variance (%)': (var_exp * 100).round(2),
        'Cumul (%)': (var_cum * 100).round(2)
    })
    st.dataframe(var_df, use_container_width=True)
    
    fig = px.bar(x=[f'PC{i+1}' for i in range(len(var_exp))], 
                y=var_exp * 100,
                title='Variance par Composante',
                labels={'x': 'Composante', 'y': 'Variance (%)'})
    fig.add_scatter(x=[f'PC{i+1}' for i in range(len(var_cum))], 
                   y=var_cum * 100, mode='lines+markers', name='Cumul')
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🎯 Visualisation 2D")
    
    df_prod['PC1'] = X_pca[:, 0]
    df_prod['PC2'] = X_pca[:, 1]
    
    fig = px.scatter(df_prod, x='PC1', y='PC2', color='categorie',
                    size='total_vente', hover_data=['produit_nom', 'total_vente', 'marge'],
                    title='Projection PCA',
                    labels={'PC1': 'Composante 1', 'PC2': 'Composante 2'})
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

# Heatmap des contributions
st.subheader("📈 Contribution des Variables")
composantes = pca.components_
features_names = ['CA', 'Quantité', 'Marge', 'Prix Moyen', 'Remise']

heatmap = pd.DataFrame(composantes[:2, :], columns=features_names, index=['PC1', 'PC2'])

fig = px.imshow(heatmap, text_auto='.2f', aspect='auto',
                title='Contribution aux composantes principales',
                color_continuous_scale='RdBu_r')
st.plotly_chart(fig, use_container_width=True)

# Résumé
st.subheader("📋 Résumé Produits (PCA)")
st.dataframe(df_prod[['produit_nom', 'categorie', 'total_vente', 'PC1', 'PC2']].round(2), 
            use_container_width=True)

# Export
csv = df_prod.to_csv(index=False).encode('utf-8')
st.download_button("📥 Télécharger résultats PCA (CSV)", csv, "pca_produits.csv", "text/csv")

st.markdown("---")
if st.button("🏠 Retour à l'accueil"):
    st.switch_page("app.py")
    
    
