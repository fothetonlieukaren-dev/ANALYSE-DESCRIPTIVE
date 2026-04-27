import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import os
import random
import warnings
warnings.filterwarnings('ignore')

# Configuration
st.set_page_config(
    page_title="Gestion des Ventes - INF232 EC2",
    page_icon="🛍️",
    layout="wide"
)

# Créer dossier data
if not os.path.exists('data'):
    os.makedirs('data')

# Base de données
def init_db():
    conn = sqlite3.connect('data/ventes.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS produits
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, categorie TEXT,
                  prix_unitaire REAL, cout_revient REAL, stock INTEGER, date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS ventes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, produit_id INTEGER, quantite INTEGER,
                  prix_vente REAL, remise REAL DEFAULT 0, client TEXT,
                  date_vente TIMESTAMP DEFAULT CURRENT_TIMESTAMP, mode_paiement TEXT,
                  region TEXT, vendeur TEXT, FOREIGN KEY (produit_id) REFERENCES produits (id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS clients
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, email TEXT, telephone TEXT,
                  ville TEXT, region TEXT, type_client TEXT, date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# Sidebar
with st.sidebar:
    st.title("📋 INF232 EC2")
    st.markdown("---")
    
    # Navigation par selectbox
    page = st.selectbox("📂 Navigation", [
        "🏠 Accueil",
        "📊 Collecte de données",
        "📈 Analyse descriptive",
        "🔍 Classification",
        "📉 Réduction dimension"
    ])
    
    st.markdown("---")
    
    # Données démo
    if st.button("📥 Charger données démo", use_container_width=True):
        conn = sqlite3.connect('data/ventes.db')
        c = conn.cursor()
        nb = pd.read_sql("SELECT COUNT(*) as count FROM produits", conn)['count'][0]
        
        if nb == 0:
            produits_demo = [
                ("Smartphone Pro Max", "Électronique", 250000, 180000, 25),
                ("Riz Basmati 5kg", "Alimentation", 8500, 6000, 100),
                ("T-shirt Premium", "Vêtements", 12000, 7000, 50),
                ("Crème visage bio", "Cosmétiques", 15000, 9000, 30),
                ("Bureau en bois massif", "Meubles", 250000, 150000, 10),
                ("Ordinateur portable", "Électronique", 450000, 350000, 8),
                ("Huile d'olive 1L", "Alimentation", 6000, 4000, 60),
                ("Jean slim", "Vêtements", 18000, 10000, 35),
                ("Parfum de luxe", "Cosmétiques", 35000, 20000, 15),
                ("Lampe design LED", "Meubles", 45000, 25000, 20)
            ]
            for prod in produits_demo:
                c.execute("INSERT INTO produits (nom, categorie, prix_unitaire, cout_revient, stock) VALUES (?, ?, ?, ?, ?)", prod)
            
            clients_demo = [
                ("Marie Dupont", "marie@email.com", "699887766", "Yaoundé", "Centre", "Particulier"),
                ("Tech Solutions", "tech@email.com", "677665544", "Douala", "Littoral", "Entreprise"),
                ("Jean Michel", "jean@email.com", "688554433", "Garoua", "Nord", "Grossiste"),
                ("Sarah Koné", "sarah@email.com", "699443322", "Bafoussam", "Ouest", "Détaillant"),
                ("Global Trading", "global@email.com", "677332211", "Douala", "Littoral", "Entreprise"),
                ("Pierre Amougou", "pierre@email.com", "688221100", "Ebolowa", "Sud", "Particulier"),
                ("Alice Banga", "alice@email.com", "699009988", "Bertoua", "Est", "Particulier"),
                ("Distribution Pro", "dist@email.com", "677887766", "Yaoundé", "Centre", "Grossiste")
            ]
            for client in clients_demo:
                c.execute("INSERT INTO clients (nom, email, telephone, ville, region, type_client) VALUES (?, ?, ?, ?, ?, ?)", client)
            
            date_debut = datetime.now() - timedelta(days=30)
            for i in range(50):
                produit_id = random.randint(1, 10)
                client_nom = random.choice([cl[0] for cl in clients_demo])
                quantite = random.randint(1, 5)
                remise = random.choice([0, 0, 0, 5, 10])
                mode = random.choice(["Espèces", "Mobile Money", "Carte bancaire"])
                region = random.choice([cl[4] for cl in clients_demo])
                vendeur = random.choice(["Alice", "Bob", "Charlie"])
                prix_base = [p[2] for p in produits_demo][produit_id-1]
                prix_final = prix_base * (1 - remise/100)
                date_vente = date_debut + timedelta(days=random.randint(0, 30))
                c.execute("INSERT INTO ventes (produit_id, quantite, prix_vente, remise, client, mode_paiement, region, vendeur, date_vente) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         (produit_id, quantite, prix_final, remise, client_nom, mode, region, vendeur, date_vente))
            conn.commit()
            st.success("✅ 50 ventes de démonstration ajoutées !")
            st.rerun()
        else:
            st.warning("Des données existent déjà !")
        conn.close()
    
    st.info("INF232 EC2 - Analyse de données")

# ==================== PAGE ACCUEIL ====================
if page == "🏠 Accueil":
    st.title("🛍️ Application de Gestion des Ventes")
    st.markdown("---")
    
    conn = sqlite3.connect('data/ventes.db')
    total_ventes = pd.read_sql("SELECT COUNT(*) as count FROM ventes", conn)['count'][0]
    ca_total = pd.read_sql("SELECT COALESCE(SUM(prix_vente * quantite), 0) as total FROM ventes", conn)['total'][0]
    nb_produits = pd.read_sql("SELECT COUNT(*) as count FROM produits", conn)['count'][0]
    nb_clients = pd.read_sql("SELECT COUNT(*) as count FROM clients", conn)['count'][0]
    conn.close()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Total Ventes", f"{total_ventes:,}")
    with col2:
        st.metric("💰 Chiffre d'Affaires", f"{ca_total:,.0f} FCFA")
    with col3:
        st.metric("📦 Produits", f"{nb_produits:,}")
    with col4:
        st.metric("👥 Clients", f"{nb_clients:,}")
    
    st.markdown("---")
    st.header("Bienvenue !")
    st.write("""
    Cette application permet de :
    - 📊 **Collecter** des données de ventes
    - 📈 **Analyser** les performances
    - 🔍 **Classifier** les clients
    - 📉 **Réduire** les dimensions
    
    👈 Utilisez le menu de navigation à gauche pour commencer !
    """)

# ==================== PAGE COLLECTE ====================
elif page == "📊 Collecte de données":
    st.title("📊 Collecte de Données de Vente")
    
    if 'form_type' not in st.session_state:
        st.session_state.form_type = None
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🛍️ Nouvelle Vente", use_container_width=True):
            st.session_state.form_type = 'vente'
    with col2:
        if st.button("📦 Nouveau Produit", use_container_width=True):
            st.session_state.form_type = 'produit'
    with col3:
        if st.button("👤 Nouveau Client", use_container_width=True):
            st.session_state.form_type = 'client'
    
    st.markdown("---")
    
    if st.session_state.form_type == 'vente':
        st.subheader("🛍️ Enregistrer une Vente")
        conn = sqlite3.connect('data/ventes.db')
        produits_df = pd.read_sql("SELECT id, nom, prix_unitaire, stock FROM produits WHERE stock > 0", conn)
        clients_df = pd.read_sql("SELECT id, nom FROM clients", conn)
        conn.close()
        
        if produits_df.empty:
            st.error("❌ Aucun produit en stock !")
        elif clients_df.empty:
            st.error("❌ Aucun client enregistré !")
        else:
            with st.form("form_vente", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    produit_choisi = st.selectbox("📦 Produit", produits_df['nom'].tolist())
                    client_choisi = st.selectbox("👤 Client", clients_df['nom'].tolist())
                    quantite = st.number_input("🔢 Quantité", min_value=1, value=1)
                with col2:
                    mode_paiement = st.selectbox("💳 Mode de paiement", ["Espèces", "Mobile Money", "Carte bancaire", "Virement", "Crédit"])
                    region = st.selectbox("📍 Région", ["Centre", "Littoral", "Nord", "Sud", "Est", "Ouest"])
                    vendeur = st.text_input("👨‍💼 Vendeur", value="Vendeur 1")
                remise = st.slider("💰 Remise (%)", 0, 50, 0)
                
                prix_unitaire = float(produits_df[produits_df['nom'] == produit_choisi]['prix_unitaire'].iloc[0])
                prix_final = prix_unitaire * (1 - remise/100)
                total = prix_final * quantite
                st.info(f"💵 Prix: {prix_unitaire:,.0f} | Final: {prix_final:,.0f} | Total: **{total:,.0f} FCFA**")
                
                if st.form_submit_button("✅ Enregistrer", use_container_width=True):
                    conn = sqlite3.connect('data/ventes.db')
                    c = conn.cursor()
                    produit_id = int(produits_df[produits_df['nom'] == produit_choisi]['id'].iloc[0])
                    c.execute("INSERT INTO ventes (produit_id, quantite, prix_vente, remise, client, mode_paiement, region, vendeur) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                             (produit_id, quantite, prix_final, remise, client_choisi, mode_paiement, region, vendeur))
                    c.execute("UPDATE produits SET stock = stock - ? WHERE id = ?", (quantite, produit_id))
                    conn.commit()
                    conn.close()
                    st.success("✅ Vente enregistrée !")
                    st.balloons()
    
    elif st.session_state.form_type == 'produit':
        st.subheader("📦 Ajouter un Produit")
        with st.form("form_produit", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nom = st.text_input("📝 Nom du produit")
                categorie = st.selectbox("🏷️ Catégorie", ["Électronique", "Alimentation", "Vêtements", "Cosmétiques", "Meubles", "Autres"])
                prix_unitaire = st.number_input("💰 Prix unitaire (FCFA)", min_value=0, step=500, value=10000)
            with col2:
                cout_revient = st.number_input("📊 Coût de revient (FCFA)", min_value=0, step=500, value=5000)
                stock = st.number_input("📦 Stock initial", min_value=0, value=10)
            if st.form_submit_button("✅ Enregistrer", use_container_width=True):
                if nom and prix_unitaire > 0:
                    conn = sqlite3.connect('data/ventes.db')
                    conn.cursor().execute("INSERT INTO produits (nom, categorie, prix_unitaire, cout_revient, stock) VALUES (?, ?, ?, ?, ?)",
                                          (nom, categorie, prix_unitaire, cout_revient, stock))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Produit '{nom}' ajouté !")
    
    elif st.session_state.form_type == 'client':
        st.subheader("👤 Ajouter un Client")
        with st.form("form_client", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nom = st.text_input("👤 Nom complet")
                email = st.text_input("📧 Email")
                telephone = st.text_input("📱 Téléphone")
            with col2:
                ville = st.text_input("🏙️ Ville")
                region = st.selectbox("📍 Région", ["Centre", "Littoral", "Nord", "Sud", "Est", "Ouest"])
                type_client = st.selectbox("🏢 Type", ["Particulier", "Entreprise", "Grossiste", "Détaillant"])
            if st.form_submit_button("✅ Enregistrer", use_container_width=True):
                if nom:
                    conn = sqlite3.connect('data/ventes.db')
                    conn.cursor().execute("INSERT INTO clients (nom, email, telephone, ville, region, type_client) VALUES (?, ?, ?, ?, ?, ?)",
                                          (nom, email, telephone, ville, region, type_client))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Client '{nom}' ajouté !")
    
    # Affichage données
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["🛍️ Ventes", "📦 Produits", "👥 Clients"])
    with tab1:
        conn = sqlite3.connect('data/ventes.db')
        df = pd.read_sql("SELECT v.id, p.nom as produit, v.quantite, v.prix_vente, (v.quantite*v.prix_vente) as total, v.client, v.date_vente FROM ventes v JOIN produits p ON v.produit_id=p.id ORDER BY v.date_vente DESC LIMIT 50", conn)
        conn.close()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aucune vente")
    with tab2:
        conn = sqlite3.connect('data/ventes.db')
        df = pd.read_sql("SELECT * FROM produits", conn)
        conn.close()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aucun produit")
    with tab3:
        conn = sqlite3.connect('data/ventes.db')
        df = pd.read_sql("SELECT * FROM clients", conn)
        conn.close()
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Aucun client")

# ==================== PAGE ANALYSE ====================
elif page == "📈 Analyse descriptive":
    st.title("📈 Analyse Descriptive des Ventes")
    
    conn = sqlite3.connect('data/ventes.db')
    nb = pd.read_sql("SELECT COUNT(*) as count FROM ventes", conn)['count'][0]
    
    if nb == 0:
        st.warning("⚠️ Aucune donnée. Chargez les données démo dans la barre latérale.")
    else:
        df = pd.read_sql("SELECT v.*, p.nom as produit_nom, p.categorie, p.cout_revient FROM ventes v JOIN produits p ON v.produit_id=p.id", conn)
        conn.close()
        
        df['total_vente'] = df['quantite'] * df['prix_vente']
        df['marge'] = df['total_vente'] - (df['cout_revient'] * df['quantite'])
        df['date_vente'] = pd.to_datetime(df['date_vente'])
        
        total_ca = df['total_vente'].sum()
        total_marge = df['marge'].sum()
        panier_moyen = df['total_vente'].mean()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 CA Total", f"{total_ca:,.0f} FCFA")
        with col2:
            st.metric("📊 Marge", f"{total_marge:,.0f} FCFA")
        with col3:
            st.metric("🛒 Panier Moyen", f"{panier_moyen:,.0f} FCFA")
        with col4:
            st.metric("🔢 Transactions", len(df))
        
        st.markdown("---")
        
        tab1, tab2 = st.tabs(["📈 Évolution", "🏷️ Catégories"])
        
        with tab1:
            df_jour = df.groupby(df['date_vente'].dt.date).agg({'total_vente': 'sum', 'id': 'count'}).reset_index()
            df_jour.columns = ['Date', 'CA', 'Nb_Ventes']
            
            col1, col2 = st.columns(2)
            with col1:
                fig = px.line(df_jour, x='Date', y='CA', title='CA Journalier')
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = px.bar(df_jour, x='Date', y='Nb_Ventes', title='Ventes par Jour')
                st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            df_cat = df.groupby('categorie').agg({'total_vente': 'sum', 'marge': 'sum'}).reset_index()
            
            col1, col2 = st.columns(2)
            with col1:
                fig = px.pie(df_cat, values='total_vente', names='categorie', title='CA par Catégorie')
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = px.bar(df_cat, x='categorie', y='marge', title='Marge par Catégorie', color='categorie')
                st.plotly_chart(fig, use_container_width=True)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Télécharger données (CSV)", csv, "ventes.csv", "text/csv")

# ==================== PAGE CLASSIFICATION ====================
elif page == "🔍 Classification":
    st.title("🔍 Classification Non-Supervisée (K-Means)")
    
    conn = sqlite3.connect('data/ventes.db')
    nb = pd.read_sql("SELECT COUNT(*) as count FROM ventes", conn)['count'][0]
    
    if nb < 5:
        st.warning("⚠️ Minimum 5 ventes requises.")
    else:
        df = pd.read_sql("SELECT v.*, p.nom as produit_nom, p.categorie, p.cout_revient FROM ventes v JOIN produits p ON v.produit_id=p.id", conn)
        conn.close()
        
        df['total_vente'] = df['quantite'] * df['prix_vente']
        df['marge'] = df['total_vente'] - (df['cout_revient'] * df['quantite'])
        
        df_clients = df.groupby('client').agg({'total_vente': ['sum', 'mean', 'count'], 'quantite': 'sum', 'marge': 'sum'}).reset_index()
        df_clients.columns = ['Client', 'CA_Total', 'Panier_Moyen', 'Nb_Achats', 'Qté_Totale', 'Marge_Totale']
        
        if len(df_clients) >= 2:
            features = ['CA_Total', 'Panier_Moyen', 'Nb_Achats', 'Qté_Totale']
            X = df_clients[features].values
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            n_clusters = st.slider("Nombre de segments", 2, min(5, len(df_clients)), 3)
            
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            df_clients['Cluster'] = kmeans.fit_predict(X_scaled)
            
            segment_names = {0: "🌟 Premium", 1: "📈 Réguliers", 2: "🔄 Occasionnels", 3: "💰 Gros", 4: "📉 Faibles"}
            df_clients['Segment'] = df_clients['Cluster'].map(segment_names)
            
            fig = px.scatter(df_clients, x='CA_Total', y='Nb_Achats', color='Segment', size='Panier_Moyen', hover_data=['Client'], title='Segmentation Clients')
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📊 Caractéristiques des Segments")
            stats = df_clients.groupby('Segment').agg({'Client': 'count', 'CA_Total': ['sum', 'mean'], 'Panier_Moyen': 'mean'}).round(2)
            stats.columns = ['Nb Clients', 'CA Total', 'CA Moyen', 'Panier Moyen']
            st.dataframe(stats, use_container_width=True)

# ==================== PAGE RÉDUCTION ====================
elif page == "📉 Réduction dimension":
    st.title("📉 Réduction de Dimensionnalité (PCA)")
    
    conn = sqlite3.connect('data/ventes.db')
    nb = pd.read_sql("SELECT COUNT(*) as count FROM ventes", conn)['count'][0]
    
    if nb < 5:
        st.warning("⚠️ Minimum 5 ventes requises.")
    else:
        df = pd.read_sql("SELECT v.*, p.nom as produit_nom, p.categorie, p.cout_revient FROM ventes v JOIN produits p ON v.produit_id=p.id", conn)
        conn.close()
        
        df['total_vente'] = df['quantite'] * df['prix_vente']
        df['marge'] = df['total_vente'] - (df['cout_revient'] * df['quantite'])
        
        df_prod = df.groupby('produit_nom').agg({'total_vente': 'sum', 'quantite': 'sum', 'marge': 'sum', 'prix_vente': 'mean', 'remise': 'mean'}).reset_index()
        df_cat = df[['produit_nom', 'categorie']].drop_duplicates()
        df_prod = df_prod.merge(df_cat, on='produit_nom', how='left')
        
        features = ['total_vente', 'quantite', 'marge', 'prix_vente', 'remise']
        X = df_prod[features].values
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        pca = PCA()
        X_pca = pca.fit_transform(X_scaled)
        var_exp = pca.explained_variance_ratio_
        
        col1, col2 = st.columns(2)
        with col1:
            var_df = pd.DataFrame({'Composante': [f'PC{i+1}' for i in range(len(var_exp))], 'Variance (%)': (var_exp*100).round(2)})
            st.dataframe(var_df, use_container_width=True)
            fig = px.bar(x=[f'PC{i+1}' for i in range(len(var_exp))], y=var_exp*100, title='Variance par Composante')
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            df_prod['PC1'] = X_pca[:, 0]
            df_prod['PC2'] = X_pca[:, 1]
            fig = px.scatter(df_prod, x='PC1', y='PC2', color='categorie', size='total_vente', hover_data=['produit_nom'], title='Projection PCA')
            st.plotly_chart(fig, use_container_width=True)
            
