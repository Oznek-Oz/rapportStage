import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
import ast
import re
import folium
from streamlit_folium import folium_static

warnings.filterwarnings('ignore')

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Offres d'Emploi",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titre principal
st.title("📊 Analyse Temporelle des Offres d'Emploi")
st.markdown("---")

# Fonction pour nettoyer les données avec plusieurs valeurs
def nettoyer_valeurs_multiples(serie):
    """
    Nettoie les colonnes qui peuvent contenir plusieurs valeurs séparées par des virgules
    et retourne une liste de valeurs uniques
    """
    if serie.dtype == object:
        # Essayer de convertir les chaînes qui ressemblent à des listes
        def convertir_valeurs(x):
            if pd.isna(x):
                return []
            if isinstance(x, str):
                # Si c'est une chaîne qui ressemble à une liste
                if x.startswith('[') and x.endswith(']'):
                    try:
                        return list(set(ast.literal_eval(x)))
                    except:
                        # Si l'évaluation échoue, traiter comme une chaîne normale
                        pass
                
                # Séparer par des virgules et nettoyer
                valeurs = [v.strip().lower() for v in x.split(',') if v.strip()]
                return list(set(valeurs))
            return []
        
        return serie.apply(convertir_valeurs)
    return serie

# Fonction pour préparer les données (version optimisée pour Streamlit)
@st.cache_data
def prepare_temporal_dataframe(df):
    """
    Prépare le DataFrame pour l'analyse temporelle des offres d'emploi
    """
    df_temporal = df.copy()
    
    # Nettoyer les colonnes avec des valeurs multiples
    for col in ['lieu', 'type_contrat']:
        if col in df_temporal.columns:
            df_temporal[col] = nettoyer_valeurs_multiples(df_temporal[col])
    
    # Convertir les colonnes de dates en datetime
    df_temporal['date_publication'] = pd.to_datetime(df_temporal['date_publication'], errors='coerce')
    df_temporal['date_expiration'] = pd.to_datetime(df_temporal['date_expiration'], errors='coerce')
    
    # Filtrer les dates invalides
    df_temporal = df_temporal.dropna(subset=['date_publication'])
    
    # Filtrer les dates réalistes
    current_date = datetime.now()
    df_temporal = df_temporal[
        (df_temporal['date_publication'] >= '2010-01-01') & 
        (df_temporal['date_publication'] <= current_date)
    ]
    
    # Créer des colonnes temporelles dérivées
    df_temporal['annee_publication'] = df_temporal['date_publication'].dt.year
    df_temporal['mois_publication'] = df_temporal['date_publication'].dt.month
    df_temporal['jour_publication'] = df_temporal['date_publication'].dt.day
    df_temporal['jour_semaine_publication'] = df_temporal['date_publication'].dt.day_name()
    df_temporal['nom_mois'] = df_temporal['date_publication'].dt.month_name()
    df_temporal['semaine_annee'] = df_temporal['date_publication'].dt.isocalendar().week
    df_temporal['trimestre_publication'] = df_temporal['date_publication'].dt.quarter
    
    # Créer des périodes d'analyse
    df_temporal['annee_mois'] = df_temporal['date_publication'].dt.to_period('M')
    df_temporal['annee_trimestre'] = df_temporal['date_publication'].dt.to_period('Q')
    df_temporal['date_seule'] = df_temporal['date_publication'].dt.date
    
    # Calculer durée de validité et ancienneté
    df_temporal['duree_validite_jours'] = (
        df_temporal['date_expiration'] - df_temporal['date_publication']
    ).dt.days
    
    df_temporal['jours_depuis_publication'] = (
        current_date - df_temporal['date_publication']
    ).dt.days
    
    # Catégoriser par ancienneté
    def categoriser_anciennete(jours):
        if pd.isna(jours):
            return 'Inconnu'
        elif jours <= 7:
            return 'Très récent (≤7j)'
        elif jours <= 30:
            return 'Récent (≤30j)'
        elif jours <= 90:
            return 'Modéré (≤90j)'
        else:
            return 'Ancien (>90j)'
    
    df_temporal['categorie_anciennete'] = df_temporal['jours_depuis_publication'].apply(categoriser_anciennete)
    
    return df_temporal

# Fonctions d'interprétation des graphiques
def interpreter_evolution_mensuelle(df_mensuel):
    """
    Interprète le graphique d'évolution mensuelle
    """
    # Calculer quelques statistiques pour l'interprétation
    moyenne = df_mensuel['nb_offres'].mean()
    max_offres = df_mensuel['nb_offres'].max()
    min_offres = df_mensuel['nb_offres'].min()
    mois_max = df_mensuel.loc[df_mensuel['nb_offres'].idxmax(), 'mois_str']
    mois_min = df_mensuel.loc[df_mensuel['nb_offres'].idxmin(), 'mois_str']
    
    interpretation = f"""
    **Interprétation de l'évolution mensuelle:**
    
    - 📈 **Tendance générale**: La moyenne est de {moyenne:.1f} offres par mois
    - 🎯 **Pic d'activité**: {max_offres} offres en {mois_max} (meilleur mois)
    - 📉 **Période calme**: {min_offres} offres en {mois_min} (mois le moins actif)
    - 🔍 **Variation**: Écart de {max_offres - min_offres} offres entre le mois le plus actif et le moins actif
    
    **Analyse:**
    """
    
    if max_offres / min_offres > 3:
        interpretation += "Variation saisonnière très marquée, avec des pics d'embauche prononcés à certaines périodes."
    elif max_offres / min_offres > 2:
        interpretation += "Variation saisonnière modérée, avec des périodes plus favorables au recrutement."
    else:
        interpretation += "Activité relativement stable tout au long de l'année, sans variation saisonnière marquée."
    
    return interpretation

def interpreter_jour_semaine(df_jour):
    """
    Interprète le graphique de répartition par jour de la semaine
    """
    jours_francais = {
        'Monday': 'Lundi',
        'Tuesday': 'Mardi',
        'Wednesday': 'Mercredi',
        'Thursday': 'Jeudi',
        'Friday': 'Vendredi',
        'Saturday': 'Samedi',
        'Sunday': 'Dimanche'
    }
    
    jour_max = df_jour.idxmax()
    jour_min = df_jour.idxmin()
    max_offres = df_jour.max()
    min_offres = df_jour.min()
    
    interpretation = f"""
    **Interprétation de la répartition par jour de la semaine:**
    
    - 📅 **Jour le plus actif**: {jours_francais.get(jour_max, jour_max)} avec {max_offres} offres
    - 📅 **Jour le moins actif**: {jours_francais.get(jour_min, jour_min)} avec {min_offres} offres
    - 📊 **Écart**: Différence de {max_offres - min_offres} offres entre le jour le plus et le moins actif
    
    **Analyse:**
    """
    
    if 'Saturday' in jour_max or 'Sunday' in jour_max:
        interpretation += "Activité importante en weekend, ce qui est inhabituel pour les offres d'emploi."
    elif 'Friday' in jour_max:
        interpretation += "Le vendredi est le jour privilégié pour publier des offres, probablement pour une visibilité en fin de semaine."
    elif 'Monday' in jour_max:
        interpretation += "Le lundi est le jour privilégié, permettant de démarrer la semaine avec de nouvelles offres."
    else:
        interpretation += "Répartition relativement équilibrée sur la semaine de travail, avec une légère préférence pour " + jours_francais.get(jour_max, jour_max) + "."
    
    return interpretation

def interpreter_repartition_mensuelle(df_mois_annee, annee):
    """
    Interprète le graphique de répartition mensuelle pour une année
    """
    mois_max = df_mois_annee.loc[df_mois_annee['nb_offres'].idxmax(), 'mois_nom']
    mois_min = df_mois_annee.loc[df_mois_annee['nb_offres'].idxmin(), 'mois_nom']
    max_offres = df_mois_annee['nb_offres'].max()
    min_offres = df_mois_annee['nb_offres'].min()
    
    interpretation = f"""
    **Interprétation de la répartition mensuelle pour {annee}:**
    
    - 📈 **Mois le plus actif**: {mois_max} avec {max_offres} offres
    - 📉 **Mois le moins actif**: {mois_min} avec {min_offres} offres
    - 📊 **Écart**: Différence de {max_offres - min_offres} offres
    
    **Analyse:**
    """
    
    if mois_max in ['Déc', 'Jan', 'Fév']:
        interpretation += "Pic d'activité en fin d'année/début d'année, correspondant souvent à des budgets annuels ou des préparations de projets."
    elif mois_max in ['Juin', 'Juillet', 'Août']:
        interpretation += "Pic d'activité estival, peut-être lié à des emplois saisonniers ou à des recrutements pré-rentrée."
    elif mois_max in ['Sep', 'Oct']:
        interpretation += "Pic d'activité à la rentrée, période traditionnelle de recrutement après la pause estivale."
    else:
        interpretation += f"Activité maximale en {mois_max}, sans pattern saisonnier évident."
    
    return interpretation

def interpreter_top_entreprises(top_entreprises, periode):
    """
    Interprète le graphique des top entreprises
    """
    total_offres = top_entreprises.sum()
    part_top10 = top_entreprises.head(10).sum() / total_offres * 100
    entreprise_dominante = top_entreprises.index[0]
    part_dominante = top_entreprises.iloc[0] / total_offres * 100
    
    interpretation = f"""
    **Interprétation du top des entreprises pour {periode}:**
    
    - 🏢 **Entreprise la plus active**: {entreprise_dominante} avec {top_entreprises.iloc[0]} offres
    - 📊 **Part du top 10**: {part_top10:.1f}% des offres totales
    - 🎯 **Concentration**: {part_dominante:.1f}% des offres proviennent de {entreprise_dominante}
    
    **Analyse:**
    """
    
    if part_dominante > 30:
        interpretation += "Marché très concentré autour d'un acteur dominant, qui représente une part importante des offres."
    elif part_top10 > 70:
        interpretation += "Marché concentré où quelques entreprises dominent le paysage de recrutement."
    else:
        interpretation += "Marché diversifié avec une répartition équilibrée entre plusieurs entreprises."
    
    return interpretation

def interpreter_comparaison_annees(df_annees, annees_comparaison):
    """
    Interprète le graphique de comparaison d'années
    """
    interpretations = []
    
    for annee in annees_comparaison:
        df_annee = df_annees[df_annees['annee'] == annee]
        total_annee = df_annee['nb_offres'].sum()
        moyenne_annee = df_annee['nb_offres'].mean()
        max_mois = df_annee['nb_offres'].max()
        
        interpretations.append(f"- **{annee}**: {total_annee} offres totales, moyenne de {moyenne_annee:.1f}/mois, pic à {max_mois} offres")
    
    # Calculer l'évolution entre les années
    if len(annees_comparaison) > 1:
        premiere_annee = min(annees_comparaison)
        derniere_annee = max(annees_comparaison)
        
        total_premiere = df_annees[df_annees['annee'] == premiere_annee]['nb_offres'].sum()
        total_derniere = df_annees[df_annees['annee'] == derniere_annee]['nb_offres'].sum()
        
        evolution = ((total_derniere - total_premiere) / total_premiere * 100) if total_premiere > 0 else 0
        
        trend = "hausse" if evolution > 0 else "baisse"
        interpretation_evolution = f"\n**Évolution {premiere_annee}-{derniere_annee}**: {abs(evolution):.1f}% de {trend}"
    else:
        interpretation_evolution = ""
    
    interpretation = f"""
    **Interprétation de la comparaison d'années:**
    
    **Récapitulatif par année:**
    {"".join(interpretations)}
    {interpretation_evolution}
    
    **Analyse:**
    """
    
    if len(annees_comparaison) > 1:
        if evolution > 20:
            interpretation += "Forte croissance du marché de l'emploi sur la période, indiquant un contexte économique favorable."
        elif evolution > 5:
            interpretation += "Croissance modérée du marché de l'emploi."
        elif evolution < -10:
            interpretation += "Contraction significative du marché de l'emploi, pouvant indiquer un ralentissement économique."
        elif evolution < 0:
            interpretation += "Légère contraction du marché de l'emploi."
        else:
            interpretation += "Stabilité relative du marché de l'emploi sur la période."
    else:
        interpretation += "Pour une analyse plus complète, sélectionnez plusieurs années à comparer."
    
    return interpretation

##############################################
# Fonction pour le géocodage des villes
@st.cache_data
def geocode_ville(ville, pays="Cameroon"):
    """
    Géocode une ville en utilisant Nominatim et retourne ses coordonnées
    """
    try:
        geolocator = Nominatim(user_agent="mon_analyseur_emploi")
        location = geolocator.geocode(f"{ville}, {pays}", timeout=10)
        if location:
            return [location.latitude, location.longitude]
        return None
    except Exception as e:
        st.warning(f"Erreur de géocodage pour {ville}: {str(e)}")
        return None

# Fonction pour préparer les données géographiques
def prepare_geographic_dataframe(df_principal, df_villes_regions):
    """
    Prépare les DataFrames pour l'analyse géographique des offres d'emploi
    Utilise un fichier villes-régions qui contient déjà le compte d'offres par ville
    """
    st.info("Préparation des données géographiques...")
    
    # Copier les DataFrames pour ne pas modifier les originaux
    df_geo_principal = df_principal.copy()
    df_villes_regions_clean = df_villes_regions.copy()
    
    # Nettoyer et standardiser les noms de villes
    def nettoyer_nom_ville(nom):
        if pd.isna(nom):
            return ['Non spécifié']
        if isinstance(nom, (list, np.ndarray)):
            # Si c'est une liste ou un array, retourner tous les éléments nettoyés
            a = [str(item).title().strip() for item in nom if pd.notna(item) and str(item).strip() != '']
            return a
        # Si c'est une chaîne simple, la retourner dans une liste
        b = str(nom).title().strip()
        return b

    # Appliquer le nettoyage et exploser les listes
    df_geo_principal['lieu_clean'] = df_geo_principal['lieu']
    df_geo_principal = df_geo_principal.explode('lieu_clean')
    #df_villes_regions_clean['villes'] = df_villes_regions_clean['villes'].apply(nettoyer_nom_ville)
    #df_villes_regions_clean['regions'] = df_villes_regions_clean['regions'].apply(nettoyer_nom_ville)
    
    # Enrichissement du DataFrame principal avec les régions
    df_geo_enrichi = df_geo_principal.merge(
        df_villes_regions_clean[['villes', 'regions', 'count']], 
        left_on='lieu_clean', 
        right_on='villes', 
        how='left'
    )
    
    # Gérer les villes non trouvées
    df_geo_enrichi['regions'] = df_geo_enrichi['regions'].fillna('Région inconnue')
    df_geo_enrichi['count'] = df_geo_enrichi['count'].fillna(0)
    df_geo_enrichi['lieu_final'] = df_geo_enrichi['lieu_clean'].fillna('Lieu non spécifié')
    
    # Utiliser les données du fichier villes-régions pour les agrégations par ville
    df_par_ville = df_villes_regions_clean.copy()
    df_par_ville.rename(columns={
        'villes': 'ville', 
        'regions': 'region', 
        'count': 'nb_offres'
    }, inplace=True)
    
    # Ajouter des informations complémentaires à partir du DataFrame principal
    if 'compagnie' in df_geo_enrichi.columns:
        df_entreprises = df_geo_enrichi.groupby(['lieu_clean', 'regions'])['compagnie'].nunique().reset_index()
        df_entreprises.rename(columns={'lieu_clean': 'ville', 'regions': 'region'}, inplace=True)
        df_par_ville = df_par_ville.merge(df_entreprises, on=['ville', 'region'], how='left')
        df_par_ville.rename(columns={'compagnie': 'nb_entreprises'}, inplace=True)
    else:
        df_par_ville['nb_entreprises'] = 0
    
    # Ajouter les informations de dates si disponibles
    if 'date_publication' in df_geo_enrichi.columns:
        df_dates = df_geo_enrichi.groupby(['lieu_clean', 'regions'])['date_publication'].agg(['min', 'max']).reset_index()
        df_dates.rename(columns={'lieu_clean': 'ville', 'regions': 'region'}, inplace=True)
        df_par_ville = df_par_ville.merge(df_dates, on=['ville', 'region'], how='left')
        df_par_ville.rename(columns={'min': 'premiere_offre', 'max': 'derniere_offre'}, inplace=True)
        
        # Calculer des métriques supplémentaires
        df_par_ville['duree_activite_jours'] = (
            pd.to_datetime(df_par_ville['derniere_offre']) - 
            pd.to_datetime(df_par_ville['premiere_offre'])
        ).dt.days + 1
        
        df_par_ville['offres_par_jour'] = df_par_ville['nb_offres'] / df_par_ville['duree_activite_jours']
        df_par_ville['offres_par_jour'] = df_par_ville['offres_par_jour'].replace([np.inf, -np.inf], 0)
    else:
        df_par_ville['premiere_offre'] = pd.NaT
        df_par_ville['derniere_offre'] = pd.NaT
        df_par_ville['duree_activite_jours'] = 0
        df_par_ville['offres_par_jour'] = 0
    
    # Trier par nombre d'offres
    df_par_ville = df_par_ville.sort_values('nb_offres', ascending=False).reset_index(drop=True)
    
    # Agrégations par région à partir des données villes-régions
    df_par_region = df_villes_regions_clean.groupby('regions').agg({
        'count': 'sum',  # Somme des offres par région
        'villes': 'count'  # Nombre de villes par région
    }).reset_index()
    
    # Ajouter le nombre d'entreprises par région
    if 'compagnie' in df_geo_enrichi.columns:
        df_entreprises_region = df_geo_enrichi.groupby('regions')['compagnie'].nunique().reset_index()
        df_par_region = df_par_region.merge(df_entreprises_region, on='regions', how='left')
    else:
        df_par_region['compagnie'] = 0
    
    df_par_region.rename(columns={
        'count': 'nb_offres', 
        'villes': 'nb_villes', 
        'compagnie': 'nb_entreprises',
        'regions': 'region'
    }, inplace=True)
    
    # Calculer des ratios
    df_par_region['offres_par_ville'] = df_par_region['nb_offres'] / df_par_region['nb_villes']
    df_par_region['offres_par_ville'] = df_par_region['offres_par_ville'].replace([np.inf, -np.inf], 0)
    
    df_par_region['entreprises_par_ville'] = df_par_region['nb_entreprises'] / df_par_region['nb_villes']
    df_par_region['entreprises_par_ville'] = df_par_region['entreprises_par_ville'].replace([np.inf, -np.inf], 0)
    
    df_par_region = df_par_region.sort_values('nb_offres', ascending=False).reset_index(drop=True)
    
    # Classement et catégorisation des villes
    if len(df_par_ville) > 0:
        q25 = df_par_ville['nb_offres'].quantile(0.25)
        q50 = df_par_ville['nb_offres'].quantile(0.50)
        q75 = df_par_ville['nb_offres'].quantile(0.75)
        
        def categoriser_ville(nb_offres):
            if nb_offres >= q75:
                return 'Très actif (>Q75)'
            elif nb_offres >= q50:
                return 'Actif (Q50-Q75)'
            elif nb_offres >= q25:
                return 'Modéré (Q25-Q50)'
            else:
                return 'Peu actif (<Q25)'
        
        df_par_ville['categorie_activite'] = df_par_ville['nb_offres'].apply(categoriser_ville)
        
        # Rang national et régional
        df_par_ville['rang_national'] = df_par_ville['nb_offres'].rank(method='dense', ascending=False)
        df_par_ville['rang_regional'] = df_par_ville.groupby('region')['nb_offres'].rank(method='dense', ascending=False)
    else:
        df_par_ville['categorie_activite'] = ''
        df_par_ville['rang_national'] = 0
        df_par_ville['rang_regional'] = 0
    
    # Analyses temporelles par géographie
    df_geo_temporel = None
    if 'date_publication' in df_geo_enrichi.columns:
        df_geo_enrichi['annee_mois'] = pd.to_datetime(df_geo_enrichi['date_publication']).dt.to_period('M')
        
        df_geo_temporel = df_geo_enrichi.groupby(['lieu_final', 'regions', 'annee_mois']).agg({
            'lien': 'count'
        }).reset_index()
        df_geo_temporel.columns = ['ville', 'region', 'periode', 'nb_offres']
        df_geo_temporel['periode_str'] = df_geo_temporel['periode'].astype(str)
    
    # Calculer les statistiques de concentration
    total_offres = df_par_ville['nb_offres'].sum()
    top_10_offres = df_par_ville.head(10)['nb_offres'].sum()
    concentration_top10 = (top_10_offres / total_offres) * 100 if total_offres > 0 else 0
    
    # Coefficient de Gini pour mesurer l'inégalité de distribution
    def calculer_gini(values):
        sorted_values = np.sort(values)
        n = len(sorted_values)
        cumsum = np.cumsum(sorted_values)
        return (n + 1 - 2 * sum(cumsum) / cumsum[-1]) / n if cumsum[-1] > 0 else 0
    
    gini_coefficient = calculer_gini(df_par_ville['nb_offres'].values)
    
    # Insights
    insights = {
        'ville_plus_active': df_par_ville.iloc[0]['ville'] if len(df_par_ville) > 0 else 'Aucune',
        'nb_offres_ville_top': df_par_ville.iloc[0]['nb_offres'] if len(df_par_ville) > 0 else 0,
        'region_plus_active': df_par_region.iloc[0]['region'] if len(df_par_region) > 0 else 'Aucune',
        'nb_regions_actives': len(df_par_region[df_par_region['nb_offres'] > 0]),
        'nb_villes_actives': len(df_par_ville[df_par_ville['nb_offres'] > 0]),
        'concentration_top10_pct': round(concentration_top10, 2),
        'gini_coefficient': round(gini_coefficient, 3),
        'total_offres': total_offres
    }
    
    return {
        'df_principal_enrichi': df_geo_enrichi,
        'df_par_ville': df_par_ville,
        'df_par_region': df_par_region,
        'df_geo_temporel': df_geo_temporel,
        'insights': insights
    }

# Fonction pour afficher l'analyse géographique dans Streamlit
def afficher_analyse_geographique(df_geo_data):
    """
    Affiche l'analyse géographique dans le dashboard Streamlit
    """
    st.header("🌍 Analyse Géographique des Offres d'Emploi")
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_offres = df_geo_data['df_par_ville']['nb_offres'].sum()
        st.metric("📋 Total Offres", total_offres)
    
    with col2:
        nb_villes = len(df_geo_data['df_par_ville'])
        st.metric("🏙️ Villes Actives", nb_villes)
    
    with col3:
        nb_regions = len(df_geo_data['df_par_region'])
        st.metric("🗺️ Régions Actives", nb_regions)
    
    with col4:
        ville_top = df_geo_data['df_par_ville'].iloc[0]['ville']
        offres_top = df_geo_data['df_par_ville'].iloc[0]['nb_offres']
        st.metric("🏆 Ville Leader", f"{ville_top} ({offres_top})")
    
    # Onglets pour les différentes analyses
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Par Ville", "🗺️ Par Région", "📈 Évolution", "🧭 Carte"])
    
    with tab1:
        st.subheader("📊 Répartition par Ville")
        
        # Top 10 villes
        top_villes = df_geo_data['df_par_ville'].head(10)
        
        fig_villes = px.bar(
            top_villes, 
            x='ville', 
            y='nb_offres',
            color='region',
            title="Top 10 Villes par Nombre d'Offres",
            labels={'ville': 'Ville', 'nb_offres': "Nombre d'Offres", 'region': 'Région'}
        )
        fig_villes.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_villes, use_container_width=True)
        
        # Tableau détaillé
        with st.expander("📋 Voir le tableau détaillé des villes"):
            st.dataframe(df_geo_data['df_par_ville'][['ville', 'region', 'nb_offres', 'nb_entreprises', 'categorie_activite']])
    
    with tab2:
        st.subheader("🗺️ Répartition par Région")
        
        # Graphique par région
        fig_regions = px.bar(
            df_geo_data['df_par_region'], 
            x='region', 
            y='nb_offres',
            title="Répartition des Offres par Région",
            labels={'region': 'Région', 'nb_offres': "Nombre d'Offres"}
        )
        fig_regions.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_regions, use_container_width=True)
        
        # Graphique en camembert
        col1, col2 = st.columns(2)
        
        with col1:
            fig_pie = px.pie(
                df_geo_data['df_par_region'], 
                values='nb_offres', 
                names='region',
                title="Part des Offres par Région"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Métriques par région
            st.subheader("📈 Métriques par Région")
            st.dataframe(df_geo_data['df_par_region'][['region', 'nb_offres', 'nb_villes', 'nb_entreprises']])
    
    with tab3:
        st.subheader("📈 Évolution Temporelle par Zone Géographique")
        
        if df_geo_data['df_geo_temporel'] is not None:
            # Sélecteur de région
            regions_disponibles = df_geo_data['df_geo_temporel']['region'].unique()
            region_selectionnee = st.selectbox("Choisir une région", regions_disponibles)
            
            # Filtrer les données
            df_region = df_geo_data['df_geo_temporel'][df_geo_data['df_geo_temporel']['region'] == region_selectionnee]
            
            # Graphique d'évolution
            fig_evolution_region = px.line(
                df_region, 
                x='periode_str', 
                y='nb_offres',
                color='ville',
                title=f"Évolution des Offres dans la région {region_selectionnee}",
                labels={'periode_str': 'Période', 'nb_offres': "Nombre d'Offres", 'ville': 'Ville'}
            )
            st.plotly_chart(fig_evolution_region, use_container_width=True)
        else:
            st.info("❌ Données temporelles non disponibles pour l'analyse géographique")
    
    with tab4:
        st.subheader("🧭 Carte Interactive des Offres d'Emploi")
        villes_et_regions = pd.read_csv("df_ville_region_count.csv")
       
        # Créer la carte avec folium
        if 'latitude' in villes_et_regions.columns:
            # Calculer le centre de la carte (moyenne des coordonnées)
            center_lat = villes_et_regions['latitude'].mean()
            center_lon = villes_et_regions['longitude'].mean()
            
            # Créer la carte
            m = folium.Map(location=[center_lat, center_lon], 
                         zoom_start=6,
                         tiles='CartoDB positron')
            
            # Ajouter une légende
            legend_html = '''
                <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white;
                            padding: 10px; border-radius: 5px; box-shadow: 0 0 15px rgba(0,0,0,0.2);">
                <h4>Nombre d'offres</h4>
                <i class="fa fa-circle" style="color: red"></i> > 100<br>
                <i class="fa fa-circle" style="color: orange"></i> 50-100<br>
                <i class="fa fa-circle" style="color: yellow"></i> 20-50<br>
                <i class="fa fa-circle" style="color: green"></i> < 20
                </div>
            '''
            m.get_root().html.add_child(folium.Element(legend_html))
            
            # Ajouter les marqueurs pour chaque ville
            for idx, row in villes_et_regions.iterrows():
                if pd.notna(row['latitude']) and pd.notna(row['longitude']):
                    # Déterminer la couleur en fonction du nombre d'offres
                    if row['count'] > 5000:
                        color = 'red'
                    elif row['count'] > 1900:
                        color = 'orange'
                    elif row['count'] > 1800:
                        color = 'yellow'
                    else:
                        color = 'green'
                    
                    # Créer le popup avec les informations
                    popup_html = f"""
                    <div style="width: 200px;">
                        <h4>{row['villes']}</h4>
                        <b>Région:</b> {row['regions']}<br>
                        <b>Nombre d'offres:</b> {row['count']}<br>
                    </div>
                    """
                    
                    # Ajouter le marqueur
                    folium.CircleMarker(
                        location=[row['latitude'], row['longitude']],
                        radius=min(10, max(8, row['count']/10)),  # Taille proportionnelle au nombre d'offres
                        popup=folium.Popup(popup_html, max_width=300),
                        color=color,
                        fill=True,
                        fill_color=color
                    ).add_to(m)
            
            # Afficher la carte
            st.write("📍 Carte interactive des offres d'emploi au Cameroun")
            folium_static(m)
            
            # Ajouter des métriques
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🎯 Villes géocodées", 
                         f"{df_geo_data['df_par_ville']['latitude'].notna().sum()}/{len(df_geo_data['df_par_ville'])}")
            with col2:
                st.metric("🌍 Régions représentées", 
                         len(df_geo_data['df_par_ville']['region'].unique()))
            with col3:
                st.metric("📊 Total des offres", 
                         df_geo_data['df_par_ville']['nb_offres'].sum())
        
        # Afficher le tableau des villes
        with st.expander("📋 Voir le détail des villes"):
            st.dataframe(
                df_geo_data['df_par_ville'][['ville', 'region', 'nb_offres', 'rang_national', 'latitude', 'longitude']]
                .sort_values('nb_offres', ascending=False)
            )

# Fonction pour l'analyse temporelle-géographique
def afficher_analyse_temporelle_geographique(df_geo_data):
    """
    Affiche l'analyse temporelle-géographique dans le dashboard
    """
    st.header("📊 Analyse Temporelle-Géographique")
    
    if df_geo_data['df_geo_temporel'] is None:
        st.warning("❌ Données temporelles non disponibles pour cette analyse")
        return
    
    # Options d'analyse
    type_analyse = st.radio(
        "Type d'analyse",
        ["Évolution par région", "Comparaison régions", "Heatmap temporelle"],
        horizontal=True
    )
    
    if type_analyse == "Évolution par région":
        # Sélecteur de région
        regions_disponibles = df_geo_data['df_geo_temporel']['region'].unique()
        region_selectionnee = st.selectbox("Choisir une région", regions_disponibles, key="region_temp")
        
        # Filtrer les données
        df_region = df_geo_data['df_geo_temporel'][df_geo_data['df_geo_temporel']['region'] == region_selectionnee]
        
        # Pivot pour avoir une colonne par ville
        df_pivot = df_region.pivot_table(
            index='periode_str', 
            columns='ville', 
            values='nb_offres', 
            fill_value=0
        ).reset_index()
        
        # Graphique d'évolution
        fig = px.line(
            df_pivot, 
            x='periode_str', 
            y=df_pivot.columns[1:],
            title=f"Évolution des Offres par Ville dans {region_selectionnee}",
            labels={'value': "Nombre d'Offres", 'periode_str': 'Période', 'variable': 'Ville'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Heatmap par ville
        fig_heatmap = px.imshow(
            df_pivot.set_index('periode_str').T,
            aspect="auto",
            title=f"Heatmap des Offres par Ville dans {region_selectionnee}",
            labels={'x': 'Période', 'y': 'Ville', 'color': "Nombre d'Offres"}
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    elif type_analyse == "Comparaison régions":
        # Agrégation par région et période
        df_region_periode = df_geo_data['df_geo_temporel'].groupby(['region', 'periode_str']).agg({
            'nb_offres': 'sum'
        }).reset_index()
        
        # Graphique de comparaison
        fig = px.line(
            df_region_periode, 
            x='periode_str', 
            y='nb_offres',
            color='region',
            title="Comparaison de l'Évolution des Offres par Région",
            labels={'periode_str': 'Période', 'nb_offres': "Nombre d'Offres", 'region': 'Région'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    elif type_analyse == "Heatmap temporelle":
        # Agrégation par région et période
        df_region_periode = df_geo_data['df_geo_temporel'].groupby(['region', 'periode_str']).agg({
            'nb_offres': 'sum'
        }).reset_index()
        
        # Pivot pour la heatmap
        df_pivot = df_region_periode.pivot_table(
            index='region', 
            columns='periode_str', 
            values='nb_offres', 
            fill_value=0
        )
        
        # Heatmap
        fig = px.imshow(
            df_pivot,
            aspect="auto",
            title="Heatmap Temporelle des Offres par Région",
            labels={'x': 'Période', 'y': 'Région', 'color': "Nombre d'Offres"}
        )
        st.plotly_chart(fig, use_container_width=True)

##############################################


# Interface de téléchargement de fichier
st.sidebar.header("📁 Chargement des données")
uploaded_file = st.sidebar.file_uploader(
    "Choisir le fichier CSV des offres d'emploi",
    type=['csv'],
    help="Téléchargez votre fichier CSV contenant les offres d'emploi"
)

##############################################
# Ajouter une section pour l'upload du fichier villes-régions
st.sidebar.header("🌍 Données Géographiques")
uploaded_geo_file = st.sidebar.file_uploader(
        "Charger le fichier villes-régions (CSV)",
        type=['csv'],
        help="Fichier avec colonnes: villes, regions"
    )
##############################################

if uploaded_file is not None:
    try:
        # Charger les données
        df = pd.read_csv(uploaded_file)
        df_temporal = prepare_temporal_dataframe(df)
        
        st.success(f"✅ Données chargées avec succès ! {len(df_temporal)} offres analysables")
        
        # Sidebar pour les filtres
        st.sidebar.header("🎯 Filtres d'analyse")
        
        # Informations générales sur les données
        date_min = df_temporal['date_publication'].min().date()
        date_max = df_temporal['date_publication'].max().date()
        
        st.sidebar.info(f"📅 Période disponible: {date_min} à {date_max}")
        
        ##############################################
        if uploaded_geo_file is not None:
            try:
                # Charger les données géographiques
                df_villes_regions = pd.read_csv(uploaded_geo_file)
                
                # Vérifier que le fichier contient les colonnes attendues
                ##########################################################""""
                cols = list(df_villes_regions.columns)
                if not all(col in cols for col in ['villes', 'regions', 'count']):
                    st.error("Le fichier géographique doit contenir les colonnes: 'villes', 'regions', 'count'")
                else:
                    st.success(f"✅ Fichier géographique chargé avec succès ! {len(df_villes_regions)} villes-régions")
                    # Préparer les données géographiques avec la fonction corrigée
                    with st.spinner("Préparation des analyses géographiques..."):
                        df_geo_data = prepare_geographic_dataframe(df_temporal, df_villes_regions)
                    st.success("✅ Analyses géographiques prêtes !")
                    # Afficher les insights géographiques
                    st.subheader("📊 Insights Géographiques")
                    col1, col2, col3 = st.columns(3)
                    
                    
                    with col1:
                        st.metric("Ville la plus active", 
                                f"{df_geo_data['insights']['ville_plus_active']} "
                                f"({df_geo_data['insights']['nb_offres_ville_top']} offres)")
                    
                    with col2:
                        st.metric("Région la plus active", df_geo_data['insights']['region_plus_active'])
                    
                    with col3:
                        st.metric("Concentration top 10", f"{df_geo_data['insights']['concentration_top10_pct']}%")
                    
                    # Ajouter des onglets pour les analyses détaillées
                    tab_geo, tab_temp_geo = st.tabs(["🌍 Analyse Géographique", "📊 Analyse Temporelle-Géographique"])
                    
                    with tab_geo:
                        afficher_analyse_geographique(df_geo_data)
                    
                    with tab_temp_geo:
                        afficher_analyse_temporelle_geographique(df_geo_data)
                        
            except Exception as e:
                st.error(f"Erreur lors du chargement des données géographiques: {str(e)}")
                st.info("Assurez-vous que votre fichier villes-régions est correctement formaté")
        ##############################################


        # === SECTION 1: FILTRES TEMPORELS ===
        st.sidebar.subheader("📅 Filtres temporels")
        
        # Filtre par période
        periode_analyse = st.sidebar.selectbox(
            "Type d'analyse",
            ["Vue d'ensemble", "Par année", "Par mois spécifique", "Par trimestre", 
             "Par jour de la semaine", "Par période personnalisée", "Comparaison d'années"]
        )
        
        # Filtres conditionnels selon le type d'analyse
        if periode_analyse == "Par année":
            annees_disponibles = sorted(df_temporal['annee_publication'].unique())
            annee_selectionnee = st.sidebar.selectbox("Choisir l'année", annees_disponibles)
            df_filtre = df_temporal[df_temporal['annee_publication'] == annee_selectionnee]
            titre_periode = f"Année {annee_selectionnee}"
            
        elif periode_analyse == "Par mois spécifique":
            col1, col2 = st.sidebar.columns(2)
            with col1:
                annee_mois = st.selectbox("Année", sorted(df_temporal['annee_publication'].unique()))
            with col2:
                mois_noms = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
                mois_nom = st.selectbox("Mois", mois_noms)
                mois_num = mois_noms.index(mois_nom) + 1
            
            df_filtre = df_temporal[
                (df_temporal['annee_publication'] == annee_mois) & 
                (df_temporal['mois_publication'] == mois_num)
            ]
            titre_periode = f"{mois_nom} {annee_mois}"
            
        elif periode_analyse == "Par trimestre":
            col1, col2 = st.sidebar.columns(2)
            with col1:
                annee_trim = st.selectbox("Année", sorted(df_temporal['annee_publication'].unique()))
            with col2:
                trimestre = st.selectbox("Trimestre", [1, 2, 3, 4])
            
            df_filtre = df_temporal[
                (df_temporal['annee_publication'] == annee_trim) & 
                (df_temporal['trimestre_publication'] == trimestre)
            ]
            titre_periode = f"T{trimestre} {annee_trim}"
            
        elif periode_analyse == "Par période personnalisée":
            col1, col2 = st.sidebar.columns(2)
            with col1:
                date_debut = st.date_input("Date début", value=date_min, min_value=date_min, max_value=date_max)
            with col2:
                date_fin = st.date_input("Date fin", value=date_max, min_value=date_min, max_value=date_max)
            
            df_filtre = df_temporal[
                (df_temporal['date_publication'].dt.date >= date_debut) & 
                (df_temporal['date_publication'].dt.date <= date_fin)
            ]
            titre_periode = f"Du {date_debut} au {date_fin}"
            
        elif periode_analyse == "Comparaison d'années":
            annees_disponibles = sorted(df_temporal['annee_publication'].unique())
            annees_comparaison = st.sidebar.multiselect(
                "Choisir les années à comparer", 
                annees_disponibles, 
                default=annees_disponibles[-2:] if len(annees_disponibles) >= 2 else annees_disponibles
            )
            df_filtre = df_temporal[df_temporal['annee_publication'].isin(annees_comparaison)]
            titre_periode = f"Comparaison {', '.join(map(str, annees_comparaison))}"
            
        else:  # Vue d'ensemble
            df_filtre = df_temporal.copy()
            titre_periode = "Toute la période"
        
        # === FILTRES ADDITIONNELS ===
        st.sidebar.subheader("🔍 Filtres additionnels")
        
        # Filtre par lieu - avec gestion des valeurs multiples
        if 'lieu' in df_filtre.columns:
            # Extraire tous les lieux uniques
            tous_lieux = set()
            for lieux in df_filtre['lieu'].dropna():
                if isinstance(lieux, list):
                    tous_lieux.update(lieux)
                else:
                    tous_lieux.add(lieux)
            
            lieux_disponibles = sorted(tous_lieux)
            lieux_selectionnes = st.sidebar.multiselect("Filtrer par lieu", lieux_disponibles)
            
            if lieux_selectionnes:
                df_filtre = df_filtre[df_filtre['lieu'].apply(
                    lambda x: any(lieu in x for lieu in lieux_selectionnes) if isinstance(x, list) else x in lieux_selectionnes
                )]
        
        # Filtre par type de contrat - avec gestion des valeurs multiples
        if 'type_contrat' in df_filtre.columns:
            # Extraire tous les types de contrat uniques
            tous_contrats = set()
            for contrats in df_filtre['type_contrat'].dropna():
                if isinstance(contrats, list):
                    tous_contrats.update(contrats)
                else:
                    tous_contrats.add(contrats)
            
            contrats_disponibles = sorted(tous_contrats)
            contrat_selectionne = st.sidebar.multiselect("Filtrer par type de contrat", contrats_disponibles)
            
            if contrat_selectionne:
                df_filtre = df_filtre[df_filtre['type_contrat'].apply(
                    lambda x: any(contrat in x for contrat in contrat_selectionne) if isinstance(x, list) else x in contrat_selectionne
                )]
        
        # === AFFICHAGE DES RÉSULTATS ===
        st.header(f"📈 Analyse pour : {titre_periode}")
        
        # Métriques principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📋 Total offres", len(df_filtre))
            st.caption("Nombre total d'offres d'emploi dans la période sélectionnée")
        
        with col2:
            if 'compagnie' in df_filtre.columns:
                nb_entreprises = df_filtre['compagnie'].nunique()
                st.metric("🏢 Entreprises", nb_entreprises)
                st.caption("Nombre d'entreprises différentes publiant des offres")
        
        with col3:
            if 'lieu' in df_filtre.columns:
                # Compter les lieux uniques (en prenant en compte les listes)
                tous_lieux = set()
                for lieux in df_filtre['lieu'].dropna():
                    if isinstance(lieux, list):
                        tous_lieux.update(lieux)
                    else:
                        tous_lieux.add(lieux)
                nb_lieux = len(tous_lieux)
                st.metric("📍 Lieux", nb_lieux)
                st.caption("Nombre de lieux de travail différents mentionnés")
        
        with col4:
            duree_moyenne = df_filtre['duree_validite_jours'].mean()
            if not pd.isna(duree_moyenne):
                st.metric("⏱️ Durée moy. validité", f"{duree_moyenne:.0f} jours")
                st.caption("Durée moyenne de validité des offres (jours)")
            else:
                st.metric("⏱️ Durée moy. validité", "N/A")
                st.caption("Données de durée non disponibles")
        
        # === GRAPHIQUES SELON LE TYPE D'ANALYSE ===
        if periode_analyse == "Vue d'ensemble":
            st.info("""
            **📊 Vue d'ensemble** - Cette analyse présente une vision globale de toutes les offres d'emploi 
            sur l'ensemble de la période disponible. Elle permet d'identifier les tendances générales 
            et les patterns temporels dans la publication des offres.
            """)
            
            # Graphiques pour vue d'ensemble
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Évolution mensuelle")
                st.caption("Nombre d'offres publiées par mois - Permet d'identifier les tendances saisonnières")
                df_mensuel = df_filtre.groupby(df_filtre['date_publication'].dt.to_period('M')).size().reset_index()
                df_mensuel.columns = ['mois', 'nb_offres']
                df_mensuel['mois_str'] = df_mensuel['mois'].astype(str)
                
                fig_evolution = px.line(
                    df_mensuel, x='mois_str', y='nb_offres',
                    title="Nombre d'offres par mois",
                    labels={'mois_str': 'Mois', 'nb_offres': 'Nombre d\'offres'}
                )
                fig_evolution.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_evolution, use_container_width=True)
                
                # Interprétation
                with st.expander("🔍 Interprétation de l'évolution mensuelle"):
                    st.markdown(interpreter_evolution_mensuelle(df_mensuel))
            
            with col2:
                st.subheader("📅 Répartition par jour de la semaine")
                st.caption("Distribution des publications selon les jours de la semaine - Permet d'identifier les jours les plus actifs")
                jour_ordre = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                df_jour = df_filtre['jour_semaine_publication'].value_counts().reindex(jour_ordre)
                
                fig_jour = px.bar(
                    x=df_jour.index, y=df_jour.values,
                    title="Offres par jour de la semaine",
                    labels={'x': 'Jour', 'y': 'Nombre d\'offres'}
                )
                st.plotly_chart(fig_jour, use_container_width=True)
                
                # Interprétation
                with st.expander("🔍 Interprétation de la répartition par jour"):
                    st.markdown(interpreter_jour_semaine(df_jour))
        
        elif periode_analyse == "Par année":
            st.info(f"""
            **📊 Analyse par année** - Cette analyse se concentre sur l'année {annee_selectionnee}. 
            Elle permet d'examiner en détail l'activité de publication pour cette année spécifique, 
            en identifiant les mois les plus actifs et les patterns saisonniers.
            """)
            
            # Analyses spécifiques à l'année
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"📊 Évolution mensuelle - {annee_selectionnee}")
                st.caption(f"Répartition mensuelle des offres pour l'année {annee_selectionnee}")
                df_mois_annee = df_filtre.groupby('mois_publication').size().reset_index()
                df_mois_annee.columns = ['mois', 'nb_offres']
                mois_noms = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun',
                            'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
                df_mois_annee['mois_nom'] = df_mois_annee['mois'].apply(lambda x: mois_noms[x-1])
                
                fig_mois = px.bar(
                    df_mois_annee, x='mois_nom', y='nb_offres',
                    title=f"Répartition mensuelle {annee_selectionnee}",
                    labels={'mois_nom': 'Mois', 'nb_offres': 'Nombre d\'offres'}
                )
                st.plotly_chart(fig_mois, use_container_width=True)
                
                # Interprétation
                with st.expander("🔍 Interprétation de la répartition mensuelle"):
                    st.markdown(interpreter_repartition_mensuelle(df_mois_annee, annee_selectionnee))
            
            with col2:
                st.subheader("📈 Moyenne par jour du mois")
                st.caption(f"Nombre moyen d'offres publiées chaque jour du mois pour {annee_selectionnee}")
                df_filtre_copy = df_filtre.copy()
                df_filtre_copy['jour'] = df_filtre_copy['date_publication'].dt.day
                moyenne_par_jour = df_filtre_copy.groupby('jour').size().reset_index()
                moyenne_par_jour.columns = ['jour', 'nb_offres']
                
                fig_jour_mois = px.line(
                    moyenne_par_jour, x='jour', y='nb_offres',
                    title=f"Offres par jour du mois - {annee_selectionnee}",
                    labels={'jour': 'Jour du mois', 'nb_offres': 'Nombre d\'offres'}
                )
                st.plotly_chart(fig_jour_mois, use_container_width=True)
                
                # Interprétation
                with st.expander("🔍 Interprétation des offres par jour du mois"):
                    jour_max = moyenne_par_jour.loc[moyenne_par_jour['nb_offres'].idxmax(), 'jour']
                    jour_min = moyenne_par_jour.loc[moyenne_par_jour['nb_offres'].idxmin(), 'jour']
                    st.markdown(f"""
                    **Interprétation des offres par jour du mois:**
                    
                    - 📅 **Jour le plus actif**: {jour_max} du mois
                    - 📅 **Jour le moins actif**: {jour_min} du mois
                    
                    **Analyse:**
                    Les jours en début et milieu de mois sont souvent plus actifs pour les publications d'offres,
                    tandis que la fin du mois peut être moins propice aux recrutements.
                    """)
            
            # Statistiques additionnelles pour l'année
            st.subheader("📋 Statistiques détaillées")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write("**Mois le plus actif:**")
                mois_max = df_filtre.groupby('nom_mois').size().idxmax()
                nb_offres_max = df_filtre.groupby('nom_mois').size().max()
                st.info(f"{mois_max} ({nb_offres_max} offres)")
                st.caption("Mois avec le plus grand nombre d'offres publiées")
            
            with col2:
                st.write("**Moyenne par mois:**")
                moyenne_mensuelle = len(df_filtre) / df_filtre['mois_publication'].nunique()
                st.info(f"{moyenne_mensuelle:.1f} offres/mois")
                st.caption("Nombre moyen d'offres publiées par mois")
            
            with col3:
                st.write("**Moyenne par jour:**")
                nb_jours = (df_filtre['date_publication'].max() - df_filtre['date_publication'].min()).days + 1
                moyenne_quotidienne = len(df_filtre) / nb_jours
                st.info(f"{moyenne_quotidienne:.2f} offres/jour")
                st.caption("Nombre moyen d'offres publiées par jour")
        
        elif periode_analyse == "Par mois spécifique":
            st.info(f"""
            **📊 Analyse par mois** - Cette analyse se concentre sur {mois_nom} {annee_mois}. 
            Elle permet d'examiner en détail l'activité de publication pour ce mois spécifique, 
            en identifiant les jours les plus actifs et les entreprises les plus prolifiques.
            """)
            
            # Analyses pour un mois spécifique
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"📅 Offres par jour - {titre_periode}")
                st.caption(f"Répartition journalière des offres pour {mois_nom} {annee_mois}")
                df_jours = df_filtre.groupby('jour_publication').size().reset_index()
                df_jours.columns = ['jour', 'nb_offres']
                
                fig_jours = px.bar(
                    df_jours, x='jour', y='nb_offres',
                    title=f"Répartition par jour - {titre_periode}",
                    labels={'jour': 'Jour du mois', 'nb_offres': 'Nombre d\'offres'}
                )
                st.plotly_chart(fig_jours, use_container_width=True)
                
                # Interprétation
                with st.expander("🔍 Interprétation des offres par jour"):
                    jour_max = df_jours.loc[df_jours['nb_offres'].idxmax(), 'jour']
                    jour_min = df_jours.loc[df_jours['nb_offres'].idxmin(), 'jour']
                    st.markdown(f"""
                    **Interprétation des offres par jour:**
                    
                    - 📅 **Jour le plus actif**: {jour_max} avec {df_jours['nb_offres'].max()} offres
                    - 📅 **Jour le moins actif**: {jour_min} avec {df_jours['nb_offres'].min()} offres
                    
                    **Analyse:**
                    Les variations journalières peuvent être influencées par des événements spécifiques,
                    des jours fériés, ou simplement des patterns aléatoires de publication.
                    """)
            
            with col2:
                st.subheader("🏢 Top entreprises du mois")
                st.caption(f"Entreprises ayant publié le plus d'offres en {mois_nom} {annee_mois}")
                if 'compagnie' in df_filtre.columns:
                    top_entreprises = df_filtre['compagnie'].value_counts().head(10)
                    fig_entreprises = px.bar(
                        x=top_entreprises.values, y=top_entreprises.index,
                        orientation='h',
                        title="Top 10 entreprises",
                        labels={'x': 'Nombre d\'offres', 'y': 'Entreprise'}
                    )
                    st.plotly_chart(fig_entreprises, use_container_width=True)
                    
                    # Interprétation
                    with st.expander("🔍 Interprétation du top entreprises"):
                        st.markdown(interpreter_top_entreprises(top_entreprises, f"{mois_nom} {annee_mois}"))
        
        elif periode_analyse == "Comparaison d'années":
            st.info(f"""
            **📊 Comparaison d'années** - Cette analyse compare les tendances de publication entre 
            les années sélectionnées. Elle permet d'identifier les évolutions, les patterns récurrents 
            et les changements dans les pratiques de recrutement au fil des années.
            """)
            
            # Comparaison entre années
            st.subheader("📊 Comparaison par années")
            st.caption("Évolution mensuelle comparée entre les années sélectionnées")
            
            df_annees = df_filtre.groupby(['annee_publication', 'mois_publication']).size().reset_index()
            df_annees.columns = ['annee', 'mois', 'nb_offres']
            
            fig_comparaison = px.line(
                df_annees, x='mois', y='nb_offres', color='annee',
                title="Évolution mensuelle par année",
                labels={'mois': 'Mois', 'nb_offres': 'Nombre d\'offres', 'annee': 'Année'}
            )
            st.plotly_chart(fig_comparaison, use_container_width=True)
            
            # Interprétation
            with st.expander("🔍 Interprétation de la comparaison d'années"):
                st.markdown(interpreter_comparaison_annees(df_annees, annees_comparaison))
            
            # Tableau comparatif
            st.subheader("📋 Tableau comparatif")
            st.caption("Statistiques comparées entre les années sélectionnées")
            pivot_annees = df_filtre.groupby('annee_publication').agg({
                'lien': 'count',
                'compagnie': 'nunique' if 'compagnie' in df_filtre.columns else lambda x: 0,
                'lieu': 'nunique' if 'lieu' in df_filtre.columns else lambda x: 0,
                'duree_validite_jours': 'mean'
            }).round(2)
            
            pivot_annees.columns = ['Nb offres', 'Nb entreprises', 'Nb lieux', 'Durée moy. validité']
            st.dataframe(pivot_annees)
        
        # === SECTION ANALYSE AVANCÉE ===
        st.header("🔍 Analyses avancées")
        st.info("""
        **Analyses avancées** - Cette section propose des analyses plus détaillées et spécialisées, 
        incluant des visualisations complexes comme les heatmaps, les tops, les tendances, 
        et l'accès aux données brutes filtrées.
        """)
        
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Heatmap", "🏆 Top analyses", "📈 Tendances", "📋 Données brutes"])
        
        with tab1:
            st.subheader("🗓️ Heatmap des publications")
            st.caption("Visualisation heatmap montrant l'intensité des publications par mois et jour de la semaine")
            if len(df_filtre) > 0:
                # Créer une heatmap jour/mois
                df_heatmap = df_filtre.groupby(['mois_publication', 'jour_semaine_publication']).size().reset_index()
                df_heatmap.columns = ['mois', 'jour_semaine', 'nb_offres']
                
                pivot_heatmap = df_heatmap.pivot(index='mois', columns='jour_semaine', values='nb_offres').fillna(0)
                
                fig_heatmap = px.imshow(
                    pivot_heatmap,
                    title="Heatmap: Mois vs Jour de la semaine",
                    labels={'x': 'Jour de la semaine', 'y': 'Mois', 'color': 'Nb offres'}
                )
                st.plotly_chart(fig_heatmap, use_container_width=True)
                
                # Interprétation
                with st.expander("🔍 Interprétation de la heatmap"):
                    # Trouver la combinaison mois/jour la plus active
                    max_value = pivot_heatmap.max().max()
                    max_mois = pivot_heatmap.max(axis=1).idxmax()
                    max_jour = pivot_heatmap.idxmax(axis=1)[max_mois]
                    
                    st.markdown(f"""
                    **Interprétation de la heatmap:**
                    
                    - 🔥 **Période la plus active**: {max_jour} du mois {max_mois} avec {max_value} offres
                    - 📅 **Patterns saisonniers**: Les couleurs montrent les variations d'activité selon les mois et jours
                    
                    **Analyse:**
                    La heatmap révèle les combinaisons mois/jour les plus propices aux publications d'offres.
                    Les zones plus chaudes (couleurs plus foncées) indiquent des périodes d'activité intense,
                    tandis que les zones plus froides montrent des périodes plus calmes.
                    """)
        
        with tab2:
            st.subheader("🏆 Top analyses")
            st.caption("Classements des entreprises et lieux les plus actifs")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'compagnie' in df_filtre.columns:
                    st.subheader("🏢 Top 10 entreprises")
                    st.caption("Entreprises ayant publié le plus d'offres")
                    top_entreprises = df_filtre['compagnie'].value_counts().head(10)
                    st.dataframe(top_entreprises.reset_index())
                    
                    # Interprétation
                    with st.expander("🔍 Interprétation du top entreprises"):
                        st.markdown(interpreter_top_entreprises(top_entreprises, titre_periode))
            
            with col2:
                if 'lieu' in df_filtre.columns:
                    st.subheader("📍 Top 10 lieux")
                    st.caption("Lieux les plus fréquemment mentionnés dans les offres")
                    # Pour les lieux, nous devons exploser les listes
                    df_lieux_exploded = df_filtre.explode('lieu')
                    top_lieux = df_lieux_exploded['lieu'].value_counts().head(10)
                    st.dataframe(top_lieux.reset_index())
                    
                    # Interprétation
                    with st.expander("🔍 Interprétation du top lieux"):
                        lieu_dominant = top_lieux.index[0]
                        part_dominant = top_lieux.iloc[0] / top_lieux.sum() * 100
                        
                        st.markdown(f"""
                        **Interprétation du top lieux:**
                        
                        - 📍 **Lieu dominant**: {lieu_dominant} avec {top_lieux.iloc[0]} mentions
                        - 🎯 **Part du top 3**: {top_lieux.head(3).sum() / top_lieux.sum() * 100:.1f}% des mentions totales
                        
                        **Analyse:**
                        La concentration géographique des offres révèle les bassins d'emploi principaux.
                        Une forte concentration sur quelques lieux peut indiquer une centralisation de l'activité économique.
                        """)
        
        with tab3:
            st.subheader("📈 Analyse de tendances")
            st.caption("Tendances temporelles avec moyenne mobile pour identifier les patterns à long terme")
            
            # Calcul de la tendance
            if len(df_filtre) > 30:  # Assez de données pour une tendance
                df_tendance = df_filtre.groupby(df_filtre['date_publication'].dt.date).size().reset_index()
                df_tendance.columns = ['date', 'nb_offres']
                
                # Moyenne mobile sur 7 jours
                df_tendance['moyenne_mobile'] = df_tendance['nb_offres'].rolling(window=7, min_periods=1).mean()
                
                fig_tendance = go.Figure()
                fig_tendance.add_trace(go.Scatter(
                    x=df_tendance['date'], y=df_tendance['nb_offres'],
                    mode='markers', name='Offres quotidiennes', opacity=0.6
                ))
                fig_tendance.add_trace(go.Scatter(
                    x=df_tendance['date'], y=df_tendance['moyenne_mobile'],
                    mode='lines', name='Moyenne mobile (7j)', line=dict(width=3)
                ))
                fig_tendance.update_layout(title="Tendance avec moyenne mobile")
                st.plotly_chart(fig_tendance, use_container_width=True)
                
                # Interprétation
                with st.expander("🔍 Interprétation de la tendance"):
                    # Calculer la pente de la tendance
                    if len(df_tendance) > 1:
                        x = np.arange(len(df_tendance))
                        y = df_tendance['moyenne_mobile'].values
                        slope = np.polyfit(x, y, 1)[0] if not np.isnan(y).any() else 0
                        
                        if slope > 0.1:
                            tendance = "hausse significative"
                        elif slope > 0:
                            tendance = "légère hausse"
                        elif slope < -0.1:
                            tendance = "baisse significative"
                        elif slope < 0:
                            tendance = "légère baisse"
                        else:
                            tendance = "stabilité"
                    else:
                        tendance = "indéterminée"
                    
                    st.markdown(f"""
                    **Interprétation de la tendance:**
                    
                    - 📈 **Direction**: {tendance} du nombre d'offres
                    - 📊 **Moyenne mobile**: Lissée sur 7 jours pour réduire le bruit
                    - 🔍 **Points aberrants**: Les points isolés représentent des jours exceptionnels
                    
                    **Analyse:**
                    La moyenne mobile permet de identifier la tendance sous-jacente en lissant les variations quotidiennes.
                    Une tendance à la hausse suggère un marché de l'emploi en expansion, tandis qu'une baisse
                    peut indiquer un ralentissement économique ou saisonnier.
                    """)
            else:
                st.info("📉 Pas assez de données pour afficher une tendance significative")
        
        with tab4:
            st.subheader("📋 Échantillon des données filtrées")
            st.caption("Aperçu des données brutes après application des filtres")
            st.dataframe(df_filtre.head(100))
            
            # Bouton de téléchargement
            csv = df_filtre.to_csv(index=False)
            st.download_button(
                label="📥 Télécharger les données filtrées (CSV)",
                data=csv,
                file_name=f"offres_emploi_filtre_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement du fichier: {str(e)}")
        st.info("Assurez-vous que votre fichier CSV contient au minimum une colonne 'date_publication' avec des dates valides.")

else:
    # Page d'accueil sans données
    st.info("👆 Veuillez télécharger un fichier CSV pour commencer l'analyse")
    
    st.markdown("""
    ### 📋 Format attendu du fichier CSV
    
    Votre fichier doit contenir au minimum ces colonnes :
    - `date_publication` : Date de publication de l'offre (format: YYYY-MM-DD)
    - `lien` : Lien vers l'offre (identifiant unique)
    
    Colonnes optionnelles pour des analyses plus riches :
    - `date_expiration` : Date d'expiration
    - `compagnie` : Nom de l'entreprise
    - `lieu` : Lieu de travail (peut contenir plusieurs valeurs séparées par des virgules)
    - `type_contrat` : Type de contrat (peut contenir plusieurs valeurs séparées par des virgules)
    - `titre` : Titre du poste
    
    ### 🎯 Fonctionnalités disponibles
    
    - **Analyses temporelles dynamiques** : Par jour, mois, année, trimestre
    - **Comparaisons entre périodes** : Évolution et tendances
    - **Filtres avancés** : Par lieu, type de contrat, période personnalisée
    - **Visualisations interactives** : Graphiques, heatmaps, moyennes mobiles
    - **Métriques en temps réel** : Nombre d'offres, entreprises, durée de validité
    - **Export de données** : Téléchargement des données filtrées
    
    ### 🔧 Améliorations récentes
    
    - Gestion des valeurs multiples dans les colonnes "lieu" et "type_contrat"
    - Descriptions détaillées pour chaque analyse
    - Interface utilisateur améliorée avec des informations contextuelles
    - Interprétations automatiques des graphiques
    """)

# Footer
st.markdown("---")
st.markdown("*Dashboard créé avec Streamlit - Analyse des offres d'emploi*")