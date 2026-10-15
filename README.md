# Logiciel DFM — La Ferme de Diégonefla
### Application de gestion intégrée d'exploitation avicole et cunicole
**Version :** 1.0 — Production  
**Devise d'exploitation :** Franc CFA (FCFA)  
**Date :** 16 septembre 2026  
**Localisation :** Diégonefla, Région du Gôh, Côte d'Ivoire  

---

## 1. Présentation Générale
L'application **DFM** a été conçue pour centraliser, fiabiliser et optimiser l'ensemble des opérations techniques, logistiques, commerciales et financières de **La Ferme de Diégonefla**.

Elle couvre rigoureusement les **14 modules** spécifiés dans le Cahier des Charges fonctionnel et technique (Version 1.0) :
1. **Authentification & Gestion des utilisateurs** (avec respect strict de la matrice des droits de la section 6)
2. **Tableau de bord (Dashboard)** (10 indicateurs clés, graphiques d'évolution mensuelle, alertes automatiques en temps réel)
3. **Gestion des volailles (Poulets)** (Lots, souches Cobb 500, Goliath, Isa Brown, pesées, mortalités, effectifs)
4. **Gestion des lapins (Cunicole)** (Lots engraissement, reproducteurs individuels Zeus/Bella..., suivi des saillies J+31, mises bas, sevrages)
5. **Gestion des œufs** (Collectes journalières, classification par calibre gros/moyen/petit, casses, stocks en plateaux de 30 et unités)
6. **Incubation** (Mises en couveuse automatique, mirage J7/J14, éclosions et rattachement automatique à un nouveau lot de volailles)
7. **Gestion des aliments** (Catalogue, alertes automatiques de seuil minimal en kg, suivi des réceptions et distributions journalières)
8. **Formules alimentaires** (Composition des rations fermières, calcul instantané du coût de revient au kg et par sac de 50 kg, outil de fabrication/mélange)
9. **Gestion des stocks** (Inventaire consolidé aliments, œufs, produits vétérinaires, emballages, valorisation globale du stock en FCFA)
10. **Suivi sanitaire & Prophylaxie** (Registre des actes vétérinaires, délais d'attente, calendrier prophylactique officiel volailles et lapins)
11. **Gestion des clients** (Fiches clients avec coordonnées, historique d'achats, suivi et encaissement des créances avec relance)
12. **Gestion des ventes & Facturation** (Vente comptoir et facturation client, déduction automatique des stocks, reçu/facture imprimable et exportable)
13. **Gestion des dépenses & Achats** (Charges d'exploitation par poste, calcul automatique du compte de résultat net : CA - Dépenses = Bénéfice)
14. **Rapports & Paramètres** (Export Excel .xlsx automatique avec openpyxl, version imprimable A4, sauvegarde JSON intégrale, réinitialisation démo)

---

## 2. Architecture Technique

### 2.1 Socle Logiciel
- **Backend :** Python 3 avec Flask, REST API modulaire et sécurisée
- **Base de données :** SQLite relationnelle avec clés étrangères (`dfm_ferme.db`)
- **Frontend :** Single-Page Application (SPA) responsive, stylisée aux couleurs d'exploitation (vert émeraude, ardoise, blanc), conçue sans dépendances externes CDN pour une autonomie totale même en connexion restreinte ou hors-ligne
- **Génération de Rapports :** Moteur `openpyxl` pour des classeurs Microsoft Excel réels (`.xlsx`) stylisés et calculés
- **Visualisations & Graphiques :** Rendu Canvas HTML5 natif (sans librairie externe) pour une rapidité absolue et zéro latence

### 2.2 Matrice des Rôles et Droits d'Accès (Section 6)
L'application implémente la matrice définie au cahier des charges :
| Module | Administrateur | Responsable Technique | Responsable Commercial | Comptable | Consultation |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Utilisateurs** | Total | Aucun | Aucun | Aucun | Aucun |
| **Tableau de bord** | Total | Lecture | Lecture | Lecture | Lecture |
| **Volailles** | Total | Écriture | Aucun | Lecture | Lecture |
| **Lapins** | Total | Écriture | Aucun | Lecture | Lecture |
| **Œufs** | Total | Écriture | Lecture | Lecture | Lecture |
| **Incubation** | Total | Écriture | Aucun | Aucun | Lecture |
| **Aliments** | Total | Écriture | Aucun | Lecture | Aucun |
| **Formules** | Total | Écriture | Aucun | Lecture | Aucun |
| **Stocks** | Total | Écriture | Aucun | Lecture | Aucun |
| **Santé** | Total | Écriture | Aucun | Aucun | Aucun |
| **Clients** | Total | Aucun | Écriture | Lecture | Aucun |
| **Ventes** | Total | Aucun | Écriture | Lecture | Lecture |
| **Dépenses / Achats** | Total | Aucun | Aucun | Écriture | Lecture |
| **Rapports / Paramètres** | Total | Lecture | Lecture | Lecture | Lecture |

*Note de test :* Un sélecteur interactif rapide de rôle est disponible dans l'en-tête pour permettre à tout évaluateur de tester instantanément l'adaptation dynamique de l'interface et des droits !

---

## 3. Structure des Fichiers

```text
/home/user/dfm-app/
├── app.py                # Serveur Flask et API REST des 14 modules
├── database.py           # Définition des 26 tables SQLite et jeu de données réaliste
├── reports.py            # Générateur de rapports Excel professionnels (.xlsx)
├── static/
│   ├── index.html        # Interface utilisateur complète (SPA)
│   ├── styles.css        # Feuille de styles moderne, responsive et prête pour impression
│   └── app.js            # Logique frontend, routage, Canvas charts, modals et calculs
├── data/
│   ├── dfm_ferme.db      # Base de données SQLite opérationnelle
│   └── Rapport_DFM_...xlsx # Exports de rapports générés
├── README.md             # Documentation technique
└── MANUEL_UTILISATEUR.md # Guide d'utilisation détaillé
```

---

## 4. Démarrage et Déploiement

### 4.1 Lancement local
```bash
cd /home/user/dfm-app
python3 app.py
```
Le serveur démarre immédiatement sur le port `5000` (`http://0.0.0.0:5000`).

### 4.2 Réinitialisation des données de test
À tout moment, vous pouvez régénérer l'ensemble du cheptel et des écritures de test pour La Ferme de Diégonefla :
```bash
python3 /home/user/dfm-app/database.py
```
ou directement depuis le logiciel via le menu **Rapports & Paramètres > Réinitialiser avec les Données de Test**.

---

## 5. Comptes de Démonstration Préconfigurés

| Identifiant | Mot de passe | Nom complet | Rôle & Permissions |
| :--- | :--- | :--- | :--- |
| `admin` | `admin123` | M. Kouassi Konan | **Administrateur** (Accès total sur les 14 modules) |
| `technique` | `tech123` | Mme Awa Traoré | **Responsable Technique** (Cheptel, santé, aliments, incubation) |
| `commercial` | `comm123` | M. Jean-Marc Brou | **Responsable Commercial** (Clients, factures, encaissements) |
| `comptable` | `compta123` | Mme Estelle Bamba | **Gestionnaire Financier** (Dépenses, charges, trésorerie) |
| `direction` | `dir123` | Délégué Direction | **Consultation** (Lecture seule et indicateurs synthétiques) |
