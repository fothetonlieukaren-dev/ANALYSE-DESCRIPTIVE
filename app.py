import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta
import random

st.set_page_config(
    page_title="Gestion des Ventes - INF232 EC2",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

if not os.path.exists('data'):
    os.makedirs('data')

def init_database():
    conn = sqlite3.connect('data/ventes.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS produits
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nom TEXT NOT NULL,
                  categorie TEXT NOT NULL,
                  prix_unitaire REAL NOT NULL,
                  cout_revient REAL NOT NULL,
                  stock INTEGER NOT NULL,
                  date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS ventes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  produit_id INTEGER NOT NULL,
                  quantite INTEGER NOT NULL,
                  prix_vente REAL NOT NULL,
                  remise REAL DEFAULT 0,
                  client TEXT,
                  date_vente TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  mode_paiement TEXT,
                  region TEXT,
                  vendeur TEXT,
                  FOREIGN KEY (produit_id) REFERENCES produits (id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS clients
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  nom TEXT NOT NULL,
                  email TEXT,
                  telephone TEXT,
                  ville TEXT,
                  region TEXT,
                  type_client TEXT,
                  date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

init_database()

with st.sidebar:
    st.title("📋 INF232 EC2")
    st.markdown("---")
    
    st.info("""
    **🎓 TP Analyse de données**
    
    - 📊 Collecte de données
    - 📈 Analyse descriptive
    - 🔍 Classification
    - 📉 Réduction dimension
    """)
    
    st.markdown("---")
    st.subheader("📂 Navigation")
    
    if st.button("🏠 Accueil", use_container_width=True):
        st.switch_page("app.py")
    
    if st.button("📊 Collecte", use_container_width=True):
        st.switch_page("page/collecte.py")
    
    if st.button("📈 Analyse", use_container_width=True):
        st.switch_page("page/analyse.py")
    
    if st.button("🔍 Classification", use_container_width=True):
        st.switch_page("page/classification.py")
    
    if st.button("📉 Réduction", use_container_width=True):
        st.switch_page("page/reduction.py")
    
    st.markdown("---")
    
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
                ("Tech Solutions SARL", "tech@email.com", "677665544", "Douala", "Littoral", "Entreprise"),
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
                
                c.execute("""INSERT INTO ventes (produit_id, quantite, prix_vente, remise, client, mode_paiement, region, vendeur, date_vente) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                         (produit_id, quantite, prix_final, remise, client_nom, mode, region, vendeur, date_vente))
            
            conn.commit()
            st.success("✅ 50 ventes de démonstration ajoutées !")
            st.rerun()
        else:
            st.warning("Des données existent déjà !")
        conn.close()

st.title("🛍️ Application de Gestion des Ventes")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)

conn = sqlite3.connect('data/ventes.db')
total_ventes = pd.read_sql("SELECT COUNT(*) as count FROM ventes", conn)['count'][0]
ca_total = pd.read_sql("SELECT COALESCE(SUM(prix_vente * quantite), 0) as total FROM ventes", conn)['total'][0]
nb_produits = pd.read_sql("SELECT COUNT(*) as count FROM produits", conn)['count'][0]
nb_clients = pd.read_sql("SELECT COUNT(*) as count FROM clients", conn)['count'][0]
conn.close()

with col1:
    st.metric("📊 Total Ventes", f"{total_ventes:,}")
with col2:
    st.metric("💰 Chiffre d'Affaires", f"{ca_total:,.0f} FCFA")
with col3:
    st.metric("📦 Produits", f"{nb_produits:,}")
with col4:
    st.metric("👥 Clients", f"{nb_clients:,}")

st.markdown("---")

st.header("📋 Accéder aux modules")
st.write("Utilisez les boutons dans la barre latérale gauche pour naviguer.")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("### 📊 Collecte")
    if st.button("📊 Ouvrir", key="b1", use_container_width=True):
        st.switch_page("page/collecte.py")

with col2:
    st.markdown("### 📈 Analyse")
    if st.button("📈 Ouvrir", key="b2", use_container_width=True):
        st.switch_page("page/analyse.py")

with col3:
    st.markdown("### 🔍 Classification")
    if st.button("🔍 Ouvrir", key="b3", use_container_width=True):
        st.switch_page("page/classification.py")

with col4:
    st.markdown("### 📉 Réduction")
    if st.button("📉 Ouvrir", key="b4", use_container_width=True):
        st.switch_page("page/reduction.py")

st.markdown("---")

st.subheader("📋 Dernières ventes")

conn = sqlite3.connect('data/ventes.db')
dernieres_ventes = pd.read_sql("""
    SELECT v.id, p.nom as produit, v.quantite, v.prix_vente, 
           (v.quantite * v.prix_vente) as total, v.client, 
           v.date_vente, v.region
    FROM ventes v
    JOIN produits p ON v.produit_id = p.id
    ORDER BY v.date_vente DESC
    LIMIT 10
""", conn)
conn.close()

if not dernieres_ventes.empty:
    st.dataframe(dernieres_ventes, use_container_width=True)
else:
    st.info("ℹ️ Cliquez sur 'Charger données démo' dans la barre latérale.")
