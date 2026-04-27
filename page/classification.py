import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Collecte de Données", page_icon="📊", layout="wide")

st.title("📊 Collecte de Données de Vente")

# Initialisation session state
if 'form_type' not in st.session_state:
    st.session_state.form_type = None

# Boutons de navigation
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

# FORMULAIRE VENTE
if st.session_state.form_type == 'vente':
    st.subheader("🛍️ Enregistrer une Vente")
    
    conn = sqlite3.connect('data/ventes.db')
    produits_df = pd.read_sql("SELECT id, nom, prix_unitaire, stock FROM produits WHERE stock > 0", conn)
    clients_df = pd.read_sql("SELECT id, nom FROM clients", conn)
    conn.close()
    
    if produits_df.empty:
        st.error("❌ Aucun produit en stock ! Ajoutez d'abord des produits.")
    elif clients_df.empty:
        st.error("❌ Aucun client enregistré ! Ajoutez d'abord des clients.")
    else:
        with st.form("form_vente", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                produit_choisi = st.selectbox("📦 Produit", produits_df['nom'].tolist())
                client_choisi = st.selectbox("👤 Client", clients_df['nom'].tolist())
                quantite = st.number_input("🔢 Quantité", min_value=1, value=1)
                
            with col2:
                mode_paiement = st.selectbox("💳 Mode de paiement", 
                    ["Espèces", "Mobile Money", "Carte bancaire", "Virement", "Crédit"])
                region = st.selectbox("📍 Région", 
                    ["Centre", "Littoral", "Nord", "Sud", "Est", "Ouest"])
                vendeur = st.text_input("👨‍💼 Vendeur", value="Vendeur 1")
            
            remise = st.slider("💰 Remise (%)", 0, 50, 0)
            
            # Prix calculé
            prix_unitaire = float(produits_df[produits_df['nom'] == produit_choisi]['prix_unitaire'].iloc[0])
            prix_final = prix_unitaire * (1 - remise/100)
            total = prix_final * quantite
            
            st.info(f"💵 Prix unitaire: {prix_unitaire:,.0f} FCFA | Après remise: {prix_final:,.0f} FCFA | Total: **{total:,.0f} FCFA**")
            
            submitted = st.form_submit_button("✅ Enregistrer la vente", use_container_width=True)
            
            if submitted:
                conn = sqlite3.connect('data/ventes.db')
                c = conn.cursor()
                
                produit_id = int(produits_df[produits_df['nom'] == produit_choisi]['id'].iloc[0])
                
                try:
                    c.execute("""
                        INSERT INTO ventes (produit_id, quantite, prix_vente, remise, client, mode_paiement, region, vendeur) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (produit_id, quantite, prix_final, remise, client_choisi, mode_paiement, region, vendeur))
                    
                    c.execute("UPDATE produits SET stock = stock - ? WHERE id = ?", (quantite, produit_id))
                    
                    conn.commit()
                    st.success("✅ Vente enregistrée avec succès !")
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
                finally:
                    conn.close()

# FORMULAIRE PRODUIT
elif st.session_state.form_type == 'produit':
    st.subheader("📦 Ajouter un Produit")
    
    with st.form("form_produit", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nom = st.text_input("📝 Nom du produit", placeholder="Ex: Smartphone Galaxy")
            categorie = st.selectbox("🏷️ Catégorie", 
                ["Électronique", "Alimentation", "Vêtements", "Cosmétiques", "Meubles", "Autres"])
            prix_unitaire = st.number_input("💰 Prix unitaire (FCFA)", min_value=0, step=500, value=10000)
            
        with col2:
            cout_revient = st.number_input("📊 Coût de revient (FCFA)", min_value=0, step=500, value=5000)
            stock = st.number_input("📦 Stock initial", min_value=0, value=10)
        
        marge = prix_unitaire - cout_revient
        if prix_unitaire > 0:
            st.info(f"📈 Marge prévue: {marge:,.0f} FCFA ({(marge/prix_unitaire*100):.1f}%)")
        
        submitted = st.form_submit_button("✅ Enregistrer le produit", use_container_width=True)
        
        if submitted:
            if nom and prix_unitaire > 0:
                try:
                    conn = sqlite3.connect('data/ventes.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO produits (nom, categorie, prix_unitaire, cout_revient, stock) VALUES (?, ?, ?, ?, ?)",
                             (nom, categorie, prix_unitaire, cout_revient, stock))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Produit '{nom}' ajouté avec succès !")
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
            else:
                st.error("❌ Veuillez remplir le nom et le prix")

# FORMULAIRE CLIENT
elif st.session_state.form_type == 'client':
    st.subheader("👤 Ajouter un Client")
    
    with st.form("form_client", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            nom = st.text_input("👤 Nom complet / Entreprise", placeholder="Ex: Marie Dupont")
            email = st.text_input("📧 Email", placeholder="exemple@email.com")
            telephone = st.text_input("📱 Téléphone", placeholder="699887766")
            
        with col2:
            ville = st.text_input("🏙️ Ville", placeholder="Ex: Yaoundé")
            region = st.selectbox("📍 Région", ["Centre", "Littoral", "Nord", "Sud", "Est", "Ouest"])
            type_client = st.selectbox("🏢 Type", ["Particulier", "Entreprise", "Grossiste", "Détaillant"])
        
        submitted = st.form_submit_button("✅ Enregistrer le client", use_container_width=True)
        
        if submitted:
            if nom:
                try:
                    conn = sqlite3.connect('data/ventes.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO clients (nom, email, telephone, ville, region, type_client) VALUES (?, ?, ?, ?, ?, ?)",
                             (nom, email, telephone, ville, region, type_client))
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Client '{nom}' ajouté avec succès !")
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
            else:
                st.error("❌ Le nom est obligatoire")

# AFFICHAGE DES DONNÉES EXISTANTES
st.markdown("---")
st.subheader("📋 Données existantes")

tab1, tab2, tab3 = st.tabs(["🛍️ Ventes", "📦 Produits", "👥 Clients"])

with tab1:
    conn = sqlite3.connect('data/ventes.db')
    df = pd.read_sql("""
        SELECT v.id, p.nom as produit, v.quantite, v.prix_vente, 
               (v.quantite * v.prix_vente) as total, v.client, 
               v.mode_paiement, v.region, v.date_vente
        FROM ventes v
        JOIN produits p ON v.produit_id = p.id
        ORDER BY v.date_vente DESC
        LIMIT 50
    """, conn)
    conn.close()
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.metric("Nombre total de ventes", len(df))
    else:
        st.info("Aucune vente enregistrée")

with tab2:
    conn = sqlite3.connect('data/ventes.db')
    df = pd.read_sql("SELECT * FROM produits ORDER BY date_ajout DESC", conn)
    conn.close()
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aucun produit enregistré")

with tab3:
    conn = sqlite3.connect('data/ventes.db')
    df = pd.read_sql("SELECT * FROM clients ORDER BY date_inscription DESC", conn)
    conn.close()
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aucun client enregistré")

# Retour accueil
st.markdown("---")
if st.button("🏠 Retour à l'accueil", use_container_width=True):
    st.switch_page("app.py")
