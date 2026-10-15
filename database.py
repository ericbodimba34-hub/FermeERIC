import sqlite3
import os
import hashlib
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'dfm_ferme.db')

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db(force_reseed=False):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db_exists = os.path.exists(DB_PATH)
    
    if force_reseed and db_exists:
        os.remove(DB_PATH)
        db_exists = False

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Create tables
    cur.executescript('''
    CREATE TABLE IF NOT EXISTS parametres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cle TEXT UNIQUE NOT NULL,
        valeur TEXT NOT NULL,
        description TEXT
    );

    CREATE TABLE IF NOT EXISTS utilisateurs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom_complet TEXT NOT NULL,
        identifiant TEXT UNIQUE NOT NULL,
        mot_de_passe TEXT NOT NULL,
        role TEXT NOT NULL, -- 'admin', 'technique', 'commercial', 'comptable', 'consultation'
        email TEXT,
        telephone TEXT,
        statut TEXT DEFAULT 'actif', -- 'actif', 'inactif'
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS lots_volailles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        nom TEXT NOT NULL,
        souche TEXT NOT NULL, -- 'Cobb 500 (Chair)', 'Isa Brown (Pondeuse)', 'Goliath (Fermier)', etc.
        type_production TEXT NOT NULL, -- 'chair', 'ponte', 'mixte'
        date_entree DATE NOT NULL,
        effectif_initial INTEGER NOT NULL,
        effectif_actuel INTEGER NOT NULL,
        batiment TEXT,
        statut TEXT DEFAULT 'en_elevage', -- 'en_elevage', 'en_ponte', 'en_finition', 'vendu', 'cloture'
        poids_moyen_g REAL DEFAULT 0,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS volailles_pesees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lot_id INTEGER NOT NULL REFERENCES lots_volailles(id) ON DELETE CASCADE,
        date_pesee DATE NOT NULL,
        age_jours INTEGER,
        poids_moyen_g REAL NOT NULL,
        echantillon_nb INTEGER DEFAULT 10,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS volailles_mortalites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lot_id INTEGER NOT NULL REFERENCES lots_volailles(id) ON DELETE CASCADE,
        date_mortalite DATE NOT NULL,
        quantite INTEGER NOT NULL,
        cause TEXT,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS lots_lapins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        designation TEXT NOT NULL,
        race TEXT NOT NULL,
        type_lot TEXT NOT NULL, -- 'engraissement', 'maternite', 'sevrage'
        effectif INTEGER NOT NULL,
        emplacement TEXT,
        statut TEXT DEFAULT 'actif',
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS lapins_reproducteurs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code_tatouage TEXT UNIQUE NOT NULL,
        nom TEXT NOT NULL,
        race TEXT NOT NULL,
        sexe TEXT NOT NULL, -- 'male', 'femelle'
        date_naissance DATE,
        date_entree DATE NOT NULL,
        cage_numero TEXT,
        statut TEXT DEFAULT 'actif', -- 'actif', 'gestation', 'repos', 'reforme'
        portees_total INTEGER DEFAULT 0,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS lapins_reproductions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        male_id INTEGER REFERENCES lapins_reproducteurs(id) ON DELETE SET NULL,
        femelle_id INTEGER NOT NULL REFERENCES lapins_reproducteurs(id) ON DELETE CASCADE,
        date_saillie DATE NOT NULL,
        date_mise_bas_prevue DATE NOT NULL,
        date_mise_bas_reelle DATE,
        nes_vivants INTEGER DEFAULT 0,
        morts_nes INTEGER DEFAULT 0,
        date_sevrage DATE,
        nb_sevres INTEGER DEFAULT 0,
        statut TEXT DEFAULT 'saillie', -- 'saillie', 'gestation_confirmee', 'mise_bas_effectuee', 'sevree', 'echec'
        lot_destination_id INTEGER REFERENCES lots_lapins(id) ON DELETE SET NULL,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS lapins_mortalites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lot_id INTEGER REFERENCES lots_lapins(id) ON DELETE SET NULL,
        reproducteur_id INTEGER REFERENCES lapins_reproducteurs(id) ON DELETE SET NULL,
        date_mortalite DATE NOT NULL,
        quantite INTEGER NOT NULL,
        cause TEXT,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS oeufs_pontes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lot_id INTEGER NOT NULL REFERENCES lots_volailles(id) ON DELETE CASCADE,
        date_ponte DATE NOT NULL,
        quantite_total INTEGER NOT NULL,
        gros_calibre INTEGER DEFAULT 0,
        moyen_calibre INTEGER DEFAULT 0,
        petit_calibre INTEGER DEFAULT 0,
        casses INTEGER DEFAULT 0,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS oeufs_mouvements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_mouvement DATE NOT NULL,
        type_mouvement TEXT NOT NULL, -- 'entree_ponte', 'sortie_vente', 'sortie_incubation', 'perte_casse'
        quantite INTEGER NOT NULL,
        reference TEXT,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS incubations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code_session TEXT UNIQUE NOT NULL,
        date_mise DATE NOT NULL,
        nb_oeufs_incubes INTEGER NOT NULL,
        lot_source_id INTEGER REFERENCES lots_volailles(id) ON DELETE SET NULL,
        incubateur_nom TEXT,
        date_mirage DATE,
        oeufs_clairs INTEGER DEFAULT 0,
        date_eclosion_prevue DATE NOT NULL,
        date_eclosion_reelle DATE,
        poussins_eclos INTEGER DEFAULT 0,
        poussins_vigoureux INTEGER DEFAULT 0,
        taux_eclosion REAL DEFAULT 0,
        statut TEXT DEFAULT 'en_cours', -- 'en_cours', 'termine', 'annule'
        lot_cree_id INTEGER REFERENCES lots_volailles(id) ON DELETE SET NULL,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS aliments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        nom TEXT NOT NULL,
        categorie TEXT NOT NULL, -- 'volaille', 'lapin', 'matiere_premiere'
        stock_actuel_kg REAL NOT NULL DEFAULT 0,
        seuil_alerte_kg REAL NOT NULL DEFAULT 100,
        prix_unitaire_kg REAL NOT NULL DEFAULT 0,
        conditionnement_sac_kg REAL DEFAULT 50,
        emplacement TEXT,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS aliments_mouvements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aliment_id INTEGER NOT NULL REFERENCES aliments(id) ON DELETE CASCADE,
        date_mouvement DATE NOT NULL,
        type_mouvement TEXT NOT NULL, -- 'entree_achat', 'entree_fabrication', 'sortie_distribution', 'ajustement'
        quantite_kg REAL NOT NULL,
        espece_destinee TEXT, -- 'volaille', 'lapin', 'stock'
        lot_destine TEXT,
        cout_total REAL DEFAULT 0,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS formules_alimentaires (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        espece TEXT NOT NULL, -- 'volaille_chair', 'volaille_ponte', 'lapin_croissance', 'lapin_maternite'
        phase TEXT, -- 'demarrage', 'croissance', 'finition', 'ponte'
        description TEXT,
        cout_revient_kg REAL DEFAULT 0,
        cout_sac_50kg REAL DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS formule_ingredients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        formule_id INTEGER NOT NULL REFERENCES formules_alimentaires(id) ON DELETE CASCADE,
        nom_ingredient TEXT NOT NULL,
        proportion_pct REAL NOT NULL, -- pourcentage du mélange
        prix_kg REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS stocks_articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        designation TEXT NOT NULL,
        categorie TEXT NOT NULL, -- 'aliment', 'oeuf', 'sante', 'materiel', 'emballage'
        unite TEXT NOT NULL, -- 'kg', 'unite', 'plateau', 'flacon', 'sac'
        quantite_stock REAL NOT NULL DEFAULT 0,
        seuil_alerte REAL NOT NULL DEFAULT 10,
        prix_unitaire REAL NOT NULL DEFAULT 0,
        emplacement TEXT,
        statut TEXT DEFAULT 'disponible'
    );

    CREATE TABLE IF NOT EXISTS stocks_mouvements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id INTEGER NOT NULL REFERENCES stocks_articles(id) ON DELETE CASCADE,
        date_mouvement DATE NOT NULL,
        type_mouvement TEXT NOT NULL, -- 'entree', 'sortie', 'inventaire'
        quantite REAL NOT NULL,
        cout_unitaire REAL DEFAULT 0,
        motif TEXT,
        utilisateur_nom TEXT,
        reference TEXT
    );

    CREATE TABLE IF NOT EXISTS sante_interventions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_intervention DATE NOT NULL,
        espece TEXT NOT NULL, -- 'volaille', 'lapin'
        lot_type TEXT,
        lot_id INTEGER,
        lot_nom TEXT,
        type_intervention TEXT NOT NULL, -- 'vaccination', 'traitement', 'vermifuge', 'vitamines', 'desinfection'
        nom_produit TEXT NOT NULL,
        posologie TEXT,
        cause_pathologie TEXT,
        delai_attente_jours INTEGER DEFAULT 0,
        intervenant TEXT,
        notes TEXT
    );

    CREATE TABLE IF NOT EXISTS sante_programme_prophylaxie (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        espece TEXT NOT NULL, -- 'volaille_chair', 'volaille_ponte', 'lapin'
        age_recommande TEXT NOT NULL, -- ex: 'J1', 'J7', 'J14', 'Semaine 8'
        libelle TEXT NOT NULL,
        vaccin_produit TEXT NOT NULL,
        mode_administration TEXT,
        statut TEXT DEFAULT 'a_prevoir' -- 'a_prevoir', 'fait', 'en_retard'
    );

    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        nom_complet TEXT NOT NULL,
        type_client TEXT NOT NULL, -- 'revendeur', 'restaurant', 'particulier', 'marche', 'grossiste'
        telephone TEXT,
        email TEXT,
        adresse TEXT,
        ville TEXT DEFAULT 'Diégonefla',
        solde_du REAL DEFAULT 0,
        limite_credit REAL DEFAULT 500000,
        statut TEXT DEFAULT 'actif',
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS ventes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_facture TEXT UNIQUE NOT NULL,
        client_id INTEGER REFERENCES clients(id) ON DELETE SET NULL,
        client_nom TEXT NOT NULL,
        date_vente DATE NOT NULL,
        montant_brut REAL NOT NULL,
        remise REAL DEFAULT 0,
        montant_net REAL NOT NULL,
        montant_regle REAL NOT NULL,
        montant_restant REAL NOT NULL,
        mode_paiement TEXT NOT NULL, -- 'especes', 'mobile_money', 'virement', 'cheque'
        statut_paiement TEXT NOT NULL, -- 'paye', 'acompte', 'impaye'
        date_echeance DATE,
        notes TEXT,
        created_by TEXT DEFAULT 'Commercial',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS vente_lignes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vente_id INTEGER NOT NULL REFERENCES ventes(id) ON DELETE CASCADE,
        designation TEXT NOT NULL,
        type_produit TEXT NOT NULL, -- 'poulet_vif', 'poulet_pac', 'lapin_vif', 'lapin_decoupe', 'oeufs_plateau', 'oeufs_unite', 'poussin', 'lapereau', 'autre'
        quantite REAL NOT NULL,
        unite TEXT NOT NULL,
        prix_unitaire REAL NOT NULL,
        sous_total REAL NOT NULL,
        lot_source_id INTEGER
    );

    CREATE TABLE IF NOT EXISTS reglements_clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vente_id INTEGER REFERENCES ventes(id) ON DELETE CASCADE,
        client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
        date_reglement DATE NOT NULL,
        montant REAL NOT NULL,
        mode_paiement TEXT NOT NULL,
        reference TEXT,
        encaisse_par TEXT
    );

    CREATE TABLE IF NOT EXISTS depenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reference TEXT UNIQUE NOT NULL,
        date_depense DATE NOT NULL,
        categorie TEXT NOT NULL, -- 'aliments', 'sante', 'equipement', 'energie', 'salaires', 'transport', 'entretien', 'divers'
        libelle TEXT NOT NULL,
        fournisseur TEXT,
        montant REAL NOT NULL,
        mode_paiement TEXT NOT NULL, -- 'especes', 'mobile_money', 'virement', 'cheque'
        num_piece TEXT,
        notes TEXT,
        created_by TEXT DEFAULT 'Comptable',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_action DATETIME DEFAULT CURRENT_TIMESTAMP,
        utilisateur_nom TEXT NOT NULL,
        module TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT
    );
    ''')
    conn.commit()

    # Check if we should seed default data
    cur.execute("SELECT COUNT(*) FROM utilisateurs")
    count_users = cur.fetchone()[0]
    
    if count_users == 0:
        seed_data(conn)

    conn.close()

def seed_data(conn):
    cur = conn.cursor()
    today = datetime.now().date()

    # 1. Paramètres
    params = [
        ('ferme_nom', 'La Ferme de Diégonefla', 'Dénomination officielle de la ferme'),
        ('ferme_activites', 'Élevage avicole, cunicole, production d’œufs et incubation', 'Activités principales'),
        ('ferme_adresse', 'Quartier Résidentiel, Route de Gagnoa, Diégonefla, Côte d’Ivoire', 'Adresse géographique'),
        ('ferme_telephone', '+225 07 58 12 34 56 / +225 05 44 98 76 10', 'Contacts téléphoniques'),
        ('ferme_email', 'contact@ferme-diegonefla.ci', 'Adresse email'),
        ('devise', 'FCFA', 'Monnaie d’exploitation'),
        ('seuil_stock_aliment_kg', '200', 'Seuil d’alerte global stock aliment (kg)'),
        ('seuil_mortalite_pct', '3.0', 'Taux de mortalité critique d’alerte (%)'),
        ('delai_alerte_creance_jours', '15', 'Délai d’alerte créances impayées (jours)'),
        ('version_app', '1.0 — Production', 'Version du logiciel DFM')
    ]
    cur.executemany("INSERT INTO parametres (cle, valeur, description) VALUES (?, ?, ?)", params)

    # 2. Utilisateurs (conforme Section 2.1 & 6)
    users = [
        ('M. Kouassi Konan (Directeur Gérant)', 'admin', hash_password('admin123'), 'admin', 'direction@ferme-diegonefla.ci', '+225 07 01 02 03 04'),
        ('Mme Awa Traoré (Resp. Technique & Élevage)', 'technique', hash_password('tech123'), 'technique', 'technique@ferme-diegonefla.ci', '+225 07 05 06 07 08'),
        ('M. Jean-Marc Brou (Resp. Commercial)', 'commercial', hash_password('comm123'), 'commercial', 'commercial@ferme-diegonefla.ci', '+225 05 09 10 11 12'),
        ('Mme Estelle Bamba (Gestionnaire Financier)', 'comptable', hash_password('compta123'), 'comptable', 'finance@ferme-diegonefla.ci', '+225 01 13 14 15 16'),
        ('M. Le Délégué / Partenaire (Consultation)', 'direction', hash_password('dir123'), 'consultation', 'audit@ferme-diegonefla.ci', '+225 07 17 18 19 20'),
    ]
    cur.executemany("INSERT INTO utilisateurs (nom_complet, identifiant, mot_de_passe, role, email, telephone) VALUES (?, ?, ?, ?, ?, ?)", users)

    # 3. Lots Volailles
    date_lot1 = today - timedelta(days=38)
    date_lot2 = today - timedelta(days=180)
    date_lot3 = today - timedelta(days=16)
    date_lot4 = today - timedelta(days=5)

    volailles = [
        ('LOT-VOL-01', 'Poulets de chair Cobb 500 — Bâtiment 1', 'Cobb 500 (Chair)', 'chair', str(date_lot1), 1200, 1145, 'Bâtiment 1 Nord', 'en_finition', 2180, 'Excellente croissance, sortie prévue la semaine prochaine.'),
        ('LOT-VOL-02', 'Pondeuses Isa Brown — Bâtiment 2', 'Isa Brown (Pondeuse)', 'ponte', str(date_lot2), 800, 782, 'Bâtiment 2 Sud', 'en_ponte', 1850, 'Pic de ponte atteint, taux journalier ~89%.'),
        ('LOT-VOL-03', 'Poulets Goliath Fermiers — Enclos C', 'Goliath (Fermier)', 'chair', str(date_lot3), 500, 492, 'Enclos Plein Air C', 'en_elevage', 460, 'Issus de l’incubation interne INCUB-2026-02.'),
        ('LOT-VOL-04', 'Poussins Cobb 500 — Poussinière D', 'Cobb 500 (Chair)', 'chair', str(date_lot4), 1500, 1485, 'Poussinière Chauffée D', 'en_elevage', 125, 'Démarrage en cours, chauffage radiant opérationnel.')
    ]
    cur.executemany("INSERT INTO lots_volailles (code, nom, souche, type_production, date_entree, effectif_initial, effectif_actuel, batiment, statut, poids_moyen_g, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", volailles)

    # Pesées volailles
    pesees = [
        (1, str(today - timedelta(days=31)), 7, 185, 20, 'Pesée J7 conforme aux normes Cobb'),
        (1, str(today - timedelta(days=24)), 14, 460, 25, 'Pesée J14 très bonne homogénéité'),
        (1, str(today - timedelta(days=17)), 21, 920, 25, 'Pesée J21'),
        (1, str(today - timedelta(days=10)), 28, 1480, 30, 'Pesée J28'),
        (1, str(today - timedelta(days=3)), 35, 2050, 30, 'Pesée J35 - Début aliment finition'),
        (3, str(today - timedelta(days=9)), 7, 150, 15, 'Pesée J7 Goliath'),
        (3, str(today - timedelta(days=2)), 14, 410, 15, 'Pesée J14 Goliath vigoureux')
    ]
    cur.executemany("INSERT INTO volailles_pesees (lot_id, date_pesee, age_jours, poids_moyen_g, echantillon_nb, notes) VALUES (?, ?, ?, ?, ?, ?)", pesees)

    # Mortalités volailles
    mortalites_v = [
        (1, str(today - timedelta(days=35)), 12, 'Faiblesse première semaine', 'Tri initial poussins'),
        (1, str(today - timedelta(days=20)), 8, 'Asphyxie localisée', 'Ventilation corrigée'),
        (1, str(today - timedelta(days=5)), 5, 'Mort subite cardiaque', 'Sujets lourds'),
        (2, str(today - timedelta(days=15)), 4, 'Prolapsus', 'Surveillance pondeuses'),
        (3, str(today - timedelta(days=10)), 8, 'Piétinement', 'Régulation litière'),
        (4, str(today - timedelta(days=2)), 15, 'Déshydratation transport', 'Traitement antistress effectué')
    ]
    cur.executemany("INSERT INTO volailles_mortalites (lot_id, date_mortalite, quantite, cause, notes) VALUES (?, ?, ?, ?, ?)", mortalites_v)

    # 4. Lapins Reproducteurs & Lots
    reproducteurs = [
        ('REP-M-01', 'Zeus', 'Fauve de Bourgogne', 'male', str(today - timedelta(days=450)), str(today - timedelta(days=400)), 'Cage M-01', 'actif', 18, 'Mâle reproducteur dominant, excellente descendance'),
        ('REP-M-02', 'Titan', 'Néo-Zélandais Blanc', 'male', str(today - timedelta(days=380)), str(today - timedelta(days=330)), 'Cage M-02', 'actif', 14, 'Très calme, bon gabarit'),
        ('REP-M-03', 'César', 'Papillon Français', 'male', str(today - timedelta(days=320)), str(today - timedelta(days=280)), 'Cage M-03', 'actif', 9, 'Croisement vigoureux'),
        ('REP-F-01', 'Bella', 'Néo-Zélandaise Blanche', 'femelle', str(today - timedelta(days=400)), str(today - timedelta(days=360)), 'Cage F-01', 'gestation', 8, 'Saillie le 22 du mois dernier, mise bas prévue très bientôt !'),
        ('REP-F-02', 'Flora', 'Fauve de Bourgogne', 'femelle', str(today - timedelta(days=370)), str(today - timedelta(days=340)), 'Cage F-02', 'gestation', 7, 'Gestation confirmée par palpation'),
        ('REP-F-03', 'Luna', 'Géant des Flandres', 'femelle', str(today - timedelta(days=350)), str(today - timedelta(days=310)), 'Cage F-03', 'repos', 6, 'En repos post-sevrage'),
        ('REP-F-04', 'Perle', 'Néo-Zélandaise Blanche', 'femelle', str(today - timedelta(days=310)), str(today - timedelta(days=270)), 'Cage F-04', 'actif', 5, 'Portée récente sevrée avec 8 lapereaux'),
        ('REP-F-05', 'Reine', 'Fauve de Bourgogne', 'femelle', str(today - timedelta(days=290)), str(today - timedelta(days=250)), 'Cage F-05', 'repos', 4, 'Bonne laitière')
    ]
    cur.executemany("INSERT INTO lapins_reproducteurs (code_tatouage, nom, race, sexe, date_naissance, date_entree, cage_numero, statut, portees_total, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", reproducteurs)

    # Lots lapins engraissement / sevrage
    lots_lap = [
        ('LOT-LAP-01', 'Bande Engraissement Lapereaux A', 'Fauve de Bourgogne x Néo-Z', 'engraissement', 48, 'Batterie Engraissement 1', 'actif', 'Poids moyen 1,8 kg, prêts pour vente dans 2 semaines'),
        ('LOT-LAP-02', 'Bande Sevrage B', 'Néo-Zélandais Blanc', 'sevrage', 36, 'Batterie Sevrage 2', 'actif', 'Sevrés il y a 10 jours, bonne adaptation aux granulés'),
        ('LOT-LAP-03', 'Bande Engraissement Lapins C', 'Géant x Papillon', 'engraissement', 42, 'Batterie Engraissement 3', 'actif', 'Croissance rapide')
    ]
    cur.executemany("INSERT INTO lots_lapins (code, designation, race, type_lot, effectif, emplacement, statut, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", lots_lap)

    # Saillies & Gestations lapins
    reproductions = [
        (1, 4, str(today - timedelta(days=28)), str(today + timedelta(days=2)), None, 0, 0, None, 0, 'gestation_confirmee', None, 'Mise bas imminente ! Boîte à nid garnie de paille et poils.'),
        (2, 5, str(today - timedelta(days=20)), str(today + timedelta(days=10)), None, 0, 0, None, 0, 'gestation_confirmee', None, 'Palpation positive à J14'),
        (1, 7, str(today - timedelta(days=65)), str(today - timedelta(days=35)), str(today - timedelta(days=34)), 9, 1, str(today - timedelta(days=4)), 8, 'sevree', 2, 'Portée de 8 lapereaux sevrés avec succès transférés au lot LOT-LAP-02'),
        (3, 6, str(today - timedelta(days=5)), str(today + timedelta(days=25)), None, 0, 0, None, 0, 'saillie', None, 'Saillie effectuée, contrôle palpation prévu à J12')
    ]
    cur.executemany("INSERT INTO lapins_reproductions (male_id, femelle_id, date_saillie, date_mise_bas_prevue, date_mise_bas_reelle, nes_vivants, morts_nes, date_sevrage, nb_sevres, statut, lot_destination_id, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", reproductions)

    # 5. Gestion des Œufs (historique des 7 derniers jours)
    oeufs_data = []
    for d in range(7, 0, -1):
        dt = today - timedelta(days=d)
        qte = 690 + (d * 8) % 40
        gros = int(qte * 0.55)
        moyen = int(qte * 0.35)
        petit = qte - gros - moyen
        casse = 8 + (d % 4)
        oeufs_data.append((2, str(dt), qte, gros, moyen, petit, casse, f'Collecte quotidienne du matin et de l’après-midi — Bâtiment 2'))
    cur.executemany("INSERT INTO oeufs_pontes (lot_id, date_ponte, quantite_total, gros_calibre, moyen_calibre, petit_calibre, casses, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", oeufs_data)

    # Mouvements d'œufs
    mvt_oeufs = [
        (str(today - timedelta(days=6)), 'entree_ponte', 710, 'PONTE-B2', 'Collecte journalière'),
        (str(today - timedelta(days=5)), 'sortie_vente', 600, 'FAC-2026-003', 'Vente 20 plateaux Superette Oumé'),
        (str(today - timedelta(days=4)), 'sortie_incubation', 300, 'INCUB-2026-03', 'Mise en incubateur'),
        (str(today - timedelta(days=3)), 'sortie_vente', 900, 'FAC-2026-001', 'Vente 30 plateaux Coopérative Gouro'),
        (str(today - timedelta(days=2)), 'entree_ponte', 724, 'PONTE-B2', 'Collecte journalière'),
        (str(today - timedelta(days=1)), 'entree_ponte', 705, 'PONTE-B2', 'Collecte journalière')
    ]
    cur.executemany("INSERT INTO oeufs_mouvements (date_mouvement, type_mouvement, quantite, reference, notes) VALUES (?, ?, ?, ?, ?)", mvt_oeufs)

    # 6. Incubation
    incubations = [
        ('INCUB-2026-03', str(today - timedelta(days=18)), 850, 2, 'Couveuse Automatique Victoria 1000', str(today - timedelta(days=11)), 62, str(today + timedelta(days=3)), None, 0, 0, 0, 'en_cours', None, 'Mirage à J7 concluant (62 œufs clairs écartés). Éclosion prévue dans 3 jours !'),
        ('INCUB-2026-02', str(today - timedelta(days=37)), 550, 2, 'Couveuse Automatique Victoria 1000', str(today - timedelta(days=30)), 38, str(today - timedelta(days=16)), str(today - timedelta(days=16)), 462, 455, 84.0, 'termine', 3, 'Très bon taux d’éclosion de 84%. Poussins transférés dans le lot LOT-VOL-03 Goliath.')
    ]
    cur.executemany("INSERT INTO incubations (code_session, date_mise, nb_oeufs_incubes, lot_source_id, incubateur_nom, date_mirage, oeufs_clairs, date_eclosion_prevue, date_eclosion_reelle, poussins_eclos, poussins_vigoureux, taux_eclosion, statut, lot_cree_id, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", incubations)

    # 7. Aliments
    aliments = [
        ('ALIM-V-DEM', 'Aliment Démarrage Volailles (Miettes)', 'volaille', 850, 300, 320, 50, 'Magasin Aliment A1', 'Riche en protéines 21% pour poussins J1-J21'),
        ('ALIM-V-CROIS', 'Aliment Croissance Poulet de Chair', 'volaille', 1450, 400, 290, 50, 'Magasin Aliment A2', 'Protéines 19%, énergie métabolisable 3100 kcal'),
        ('ALIM-V-FIN', 'Aliment Finition Poulet de Chair', 'volaille', 780, 300, 275, 50, 'Magasin Aliment A3', 'Aliment densifié pour engraissement final'),
        ('ALIM-V-PONT', 'Aliment Pondeuse Haute Ponte', 'volaille', 160, 300, 280, 50, 'Magasin Aliment B1', 'Enrichi en calcium pour coquille d’œuf solide — ALERTE SEUIL BAS'),
        ('ALIM-L-CROIS', 'Granulés Lapins Croissance & Finition', 'lapin', 520, 200, 260, 50, 'Hangar Cunicole C1', 'Aliment complet riche en fibres et luzerne'),
        ('ALIM-L-MAT', 'Granulés Lapine Reproductrice & Allaitante', 'lapin', 80, 150, 285, 50, 'Hangar Cunicole C2', 'Haute valeur nutritionnelle — ALERTE SEUIL BAS'),
        ('MP-MAIS', 'Maïs Grain Jaune Concassé', 'matiere_premiere', 2800, 500, 180, 50, 'Silo Grains', 'Base énergétique pour fabrication locale de ration'),
        ('MP-SOJA', 'Tourteau de Soja 48%', 'matiere_premiere', 950, 300, 390, 50, 'Magasin Matières Premières', 'Source protéique végétale essentielle'),
        ('MP-SON', 'Son de Blé Fin', 'matiere_premiere', 620, 200, 110, 50, 'Magasin Matières Premières', 'Apport de fibres pour volailles et lapins')
    ]
    cur.executemany("INSERT INTO aliments (code, nom, categorie, stock_actuel_kg, seuil_alerte_kg, prix_unitaire_kg, conditionnement_sac_kg, emplacement, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", aliments)

    # Mouvements d'aliments
    mvts_alim = [
        (1, str(today - timedelta(days=1)), 'sortie_distribution', 75, 'volaille', 'LOT-VOL-04', 24000, 'Ration journalière poussinière'),
        (2, str(today - timedelta(days=1)), 'sortie_distribution', 120, 'volaille', 'LOT-VOL-01', 34800, 'Distribution bâtiment 1'),
        (4, str(today - timedelta(days=1)), 'sortie_distribution', 95, 'volaille', 'LOT-VOL-02', 26600, 'Distribution pondeuses'),
        (5, str(today - timedelta(days=1)), 'sortie_distribution', 35, 'lapin', 'LOT-LAP-01 & 02', 9100, 'Distribution granulés lapins'),
        (7, str(today - timedelta(days=4)), 'entree_achat', 2000, 'stock', 'Silo Grains', 360000, 'Livraison coopérative céréalière Gagnoa')
    ]
    cur.executemany("INSERT INTO aliments_mouvements (aliment_id, date_mouvement, type_mouvement, quantite_kg, espece_destinee, lot_destine, cout_total, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", mvts_alim)

    # 8. Formules Alimentaires
    cur.execute("""
    INSERT INTO formules_alimentaires (nom, espece, phase, description, cout_revient_kg, cout_sac_50kg)
    VALUES ('Formule Finition Poulet Chair Fermier', 'volaille_chair', 'finition', 'Formulation fermière locale optimisée pour engraissement rapide Cobb et Goliath', 248.5, 12425)
    """)
    f1_id = cur.lastrowid
    f1_ing = [
        (f1_id, 'Maïs grain concassé', 55.0, 180),
        (f1_id, 'Tourteau de soja', 22.0, 390),
        (f1_id, 'Son de blé', 12.0, 110),
        (f1_id, 'Farine de poisson séché', 6.0, 450),
        (f1_id, 'Prémix CMV 1%', 2.5, 950),
        (f1_id, 'Huile de palme raffinée', 1.5, 650),
        (f1_id, 'Sel de cuisine iodé', 0.5, 100),
        (f1_id, 'Coquilles d’huîtres broyées', 0.5, 150)
    ]
    cur.executemany("INSERT INTO formule_ingredients (formule_id, nom_ingredient, proportion_pct, prix_kg) VALUES (?, ?, ?, ?)", f1_ing)

    cur.execute("""
    INSERT INTO formules_alimentaires (nom, espece, phase, description, cout_revient_kg, cout_sac_50kg)
    VALUES ('Formule Pondeuse Pleine Ponte', 'volaille_ponte', 'ponte', 'Ration riche en calcium et acides aminés pour maximiser le taux de ponte et la qualité de la coquille', 262.0, 13100)
    """)
    f2_id = cur.lastrowid
    f2_ing = [
        (f2_id, 'Maïs grain concassé', 50.0, 180),
        (f2_id, 'Tourteau de soja', 20.0, 390),
        (f2_id, 'Coquilles d’huîtres broyées', 9.0, 150),
        (f2_id, 'Son de blé', 13.0, 110),
        (f2_id, 'Farine de poisson séché', 4.0, 450),
        (f2_id, 'Prémix Pondeuse CMV', 3.0, 1100),
        (f2_id, 'Sel de cuisine', 0.5, 100),
        (f2_id, 'Huile végétale', 0.5, 650)
    ]
    cur.executemany("INSERT INTO formule_ingredients (formule_id, nom_ingredient, proportion_pct, prix_kg) VALUES (?, ?, ?, ?)", f2_ing)

    cur.execute("""
    INSERT INTO formules_alimentaires (nom, espece, phase, description, cout_revient_kg, cout_sac_50kg)
    VALUES ('Granulés Cunicoles Croissance', 'lapin_croissance', 'croissance', 'Aliment complet équilibré pour lapereaux post-sevrage avec taux élevé de cellulose brute', 222.0, 11100)
    """)
    f3_id = cur.lastrowid
    f3_ing = [
        (f3_id, 'Son de blé', 35.0, 110),
        (f3_id, 'Farine de fourrage / luzerne locale', 25.0, 160),
        (f3_id, 'Tourteau de soja', 18.0, 390),
        (f3_id, 'Maïs broyé', 14.0, 180),
        (f3_id, 'Prémix Lapin Cunicole', 5.0, 850),
        (f3_id, 'Sel marin et minéraux', 2.0, 120),
        (f3_id, 'Mélasse liante', 1.0, 300)
    ]
    cur.executemany("INSERT INTO formule_ingredients (formule_id, nom_ingredient, proportion_pct, prix_kg) VALUES (?, ?, ?, ?)", f3_ing)

    # 9. Stocks Articles Consolidés
    articles_stock = [
        ('STK-ALIM-01', 'Aliment Démarrage Volailles', 'aliment', 'kg', 850, 300, 320, 'Magasin A1', 'disponible'),
        ('STK-ALIM-02', 'Aliment Croissance Volailles', 'aliment', 'kg', 1450, 400, 290, 'Magasin A2', 'disponible'),
        ('STK-ALIM-03', 'Aliment Finition Volailles', 'aliment', 'kg', 780, 300, 275, 'Magasin A3', 'disponible'),
        ('STK-ALIM-04', 'Aliment Pondeuse Ponte', 'aliment', 'kg', 160, 300, 280, 'Magasin B1', 'alerte_stock'),
        ('STK-ALIM-05', 'Granulés Lapins Croissance', 'aliment', 'kg', 520, 200, 260, 'Hangar Cunicole', 'disponible'),
        ('STK-ALIM-06', 'Granulés Lapine Maternité', 'aliment', 'kg', 80, 150, 285, 'Hangar Cunicole', 'alerte_stock'),
        ('STK-OEUF-01', 'Œufs frais de table (Plateaux 30)', 'oeuf', 'plateau', 128, 40, 2200, 'Local Calibrage', 'disponible'),
        ('STK-MED-01', 'Oxytétracycline 20% injectable', 'sante', 'flacon', 8, 3, 4500, 'Pharmacie Vétérinaire', 'disponible'),
        ('STK-MED-02', 'Vitaperos Complexe Antistress (1L)', 'sante', 'flacon', 5, 2, 8500, 'Pharmacie Vétérinaire', 'disponible'),
        ('STK-MED-03', 'Vaccin HB1 / Clone 30 (1000 doses)', 'sante', 'flacon', 3, 2, 7500, 'Frigo Vétérinaire', 'disponible'),
        ('STK-MED-04', 'Lévamisole Vermifuge Poudre (100g)', 'sante', 'sachet', 12, 5, 2500, 'Pharmacie Vétérinaire', 'disponible'),
        ('STK-MAT-01', 'Alvéoles en carton pour 30 œufs', 'emballage', 'unite', 450, 100, 120, 'Magasin Emballages', 'disponible'),
        ('STK-MAT-02', 'Sacs d’aliment vides 50 kg', 'emballage', 'unite', 180, 50, 200, 'Magasin Emballages', 'disponible')
    ]
    cur.executemany("INSERT INTO stocks_articles (code, designation, categorie, unite, quantite_stock, seuil_alerte, prix_unitaire, emplacement, statut) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", articles_stock)

    # 10. Suivi Sanitaire (Santé & Prophylaxie)
    prophylaxie = [
        ('volaille_chair', 'J1 (Couvoir)', 'Vaccination Marek + Newcastle HB1', 'Vaccin bivalent HB1/Marek', 'Nébulisation / Injection sous-cutanée', 'fait'),
        ('volaille_chair', 'J7', 'Vaccination Gumboro (Souche intermédiaire)', 'Gumboro IBD Clone', 'Eau de boisson avec lait écrémé', 'fait'),
        ('volaille_chair', 'J14', 'Vaccination Newcastle Clon 30 + Traitement Antistress', 'Newcastle Clone 30 + Vitaperos', 'Goutte oculaire ou eau', 'fait'),
        ('volaille_chair', 'J21', 'Rappel Gumboro', 'Gumboro IBD Rappel', 'Eau de boisson', 'a_prevoir'),
        ('volaille_chair', 'J28', 'Déparasitage interne (Vermifuge)', 'Lévamisole / Pipérazine', 'Eau de boisson', 'a_prevoir'),
        ('volaille_ponte', 'Semaine 6', 'Vaccination Variole Aviaire (Transfixion alaire)', 'Diftosec / Poulvac', 'Transfixion de l’aile', 'fait'),
        ('volaille_ponte', 'Semaine 10', 'Traitement Coriza et Bronchite infectieuse', 'Bacterin Aviaire', 'Injection intramusculaire', 'fait'),
        ('volaille_ponte', 'Semaine 16', 'Rappel combiné Newcastle + EDS (Syndrome de chute de ponte)', 'ND+EDS Inactivé', 'Injection pectorale', 'fait'),
        ('lapin', 'J35 (Post-sevrage)', 'Prévention Coccidiose intestinale et hépatique', 'Sulfadiazine + Triméthoprime', 'Eau de boisson 5 jours', 'fait'),
        ('lapin', 'J50', 'Vaccination VHD (Maladie Hémorragique Virale)', 'Cunivak VHD', 'Injection sous-cutanée', 'a_prevoir'),
        ('lapin', 'Tous les 3 mois', 'Déparasitage général reproducteurs mâles et femelles', 'Ivermectine 1%', 'Injection sous-cutanée 0.2ml', 'a_prevoir')
    ]
    cur.executemany("INSERT INTO sante_programme_prophylaxie (espece, age_recommande, libelle, vaccin_produit, mode_administration, statut) VALUES (?, ?, ?, ?, ?, ?)", prophylaxie)

    interventions_sante = [
        (str(today - timedelta(days=24)), 'volaille', 'chair', 1, 'Poulets de chair Cobb 500 — Bâtiment 1', 'vaccination', 'Newcastle Clone 30', '1 dose par sujet dans eau', 'Prophylaxie planifiée J14', 0, 'Dr. Yao (Vétérinaire conseil)', 'Excellente prise vaccinale, aucun effet indésirable'),
        (str(today - timedelta(days=18)), 'volaille', 'chair', 1, 'Poulets de chair Cobb 500 — Bâtiment 1', 'vitamines', 'Vitaperos Complexe', '1 ml par litre d’eau pendant 3 jours', 'Prévention coup de chaleur', 0, 'Awa Traoré', 'Distribution aux heures fraîches'),
        (str(today - timedelta(days=12)), 'volaille', 'ponte', 2, 'Pondeuses Isa Brown — Bâtiment 2', 'vermifuge', 'Lévamisole 10%', '2g par litre d’eau sur 24h', 'Vermifugation périodique de ponte', 3, 'Dr. Yao', 'Délai d’attente respecté'),
        (str(today - timedelta(days=8)), 'lapin', 'engraissement', 1, 'Bande Engraissement Lapereaux A', 'traitement', 'Anticoccidien Sulfadiméthoxine', '5 ml / 10L d’eau pendant 4 jours', 'Symptômes de diarrhée bénigne sur 2 sujets', 5, 'Awa Traoré', 'Guérison rapide constatée'),
        (str(today - timedelta(days=3)), 'volaille', 'chair', 4, 'Poussins Cobb 500 — Poussinière D', 'vitamines', 'Polivit Végétal Démarrage', '1 sachet / 100L', 'Arrivée poussins antistress transport', 0, 'Awa Traoré', 'Bonne vivacité')
    ]
    cur.executemany("INSERT INTO sante_interventions (date_intervention, espece, lot_type, lot_id, lot_nom, type_intervention, nom_produit, posologie, cause_pathologie, delai_attente_jours, intervenant, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", interventions_sante)

    # 11. Clients & Créances
    clients = [
        ('CLI-001', 'Hôtel-Restaurant Le Fromager', 'restaurant', '+225 07 48 90 12 34', 'fromager.gagnoa@gmail.com', 'Boulevard Principal', 'Gagnoa', 185000, 500000, 'actif', 'Gros client régulier, livraison chaque jeudi. Créance en cours à relancer.'),
        ('CLI-002', 'Restaurant La Paillote Gourmande', 'restaurant', '+225 05 12 34 56 78', 'paillote.diego@ci.net', 'Près de la Gare Routière', 'Diégonefla', 60000, 200000, 'actif', 'Commandes hebdomadaires de poulets et lapins braisés.'),
        ('CLI-003', 'Coopérative Revendeurs Marché Gouro', 'grossiste', '+225 01 23 45 67 89', 'coop.gouro@ci.net', 'Grand Marché Central', 'Diégonefla', 0, 1000000, 'actif', 'Paie comptant par virement Wave, achète 30 à 50 plateaux d’œufs par semaine.'),
        ('CLI-004', 'Superette Express Oumé', 'revendeur', '+225 07 77 88 99 00', 'superette.oume@yahoo.fr', 'Face Station Shell', 'Oumé', 95000, 300000, 'actif', 'Vente d’œufs et de poulets prêts à cuire emballés.'),
        ('CLI-005', 'M. Kouamé Jean-Baptiste', 'particulier', '+225 05 66 55 44 33', 'kouame.jb@gmail.com', 'Quartier Commerce', 'Diégonefla', 0, 100000, 'actif', 'Particulier fidèle, achats pour cérémonies et week-ends.'),
        ('CLI-006', 'Mme Viviane N’Guessan (Rôtisserie Divine)', 'restaurant', '+225 07 22 33 44 55', 'rotisserie.viviane@ci.net', 'Marché de Nuit', 'Diégonefla', 40000, 250000, 'actif', 'Achat de poulets de chair vifs par lots de 25.')
    ]
    cur.executemany("INSERT INTO clients (code, nom_complet, type_client, telephone, email, adresse, ville, solde_du, limite_credit, statut, notes) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", clients)

    # 12. Ventes & Factures
    ventes = [
        ('FAC-2026-001', 3, 'Coopérative Revendeurs Marché Gouro', str(today - timedelta(days=12)), 220000, 0, 220000, 220000, 0, 'mobile_money', 'paye', str(today - timedelta(days=12)), 'Règlement total Wave immédiat', 'Jean-Marc Brou'),
        ('FAC-2026-002', 1, 'Hôtel-Restaurant Le Fromager', str(today - timedelta(days=9)), 425000, 10000, 415000, 230000, 185000, 'virement', 'acompte', str(today + timedelta(days=5)), 'Acompte de 230 000 FCFA versé, solde de 185 000 FCFA dû au 21 du mois', 'Jean-Marc Brou'),
        ('FAC-2026-003', 4, 'Superette Express Oumé', str(today - timedelta(days=7)), 165000, 5000, 160000, 65000, 95000, 'mobile_money', 'acompte', str(today + timedelta(days=7)), 'Livraison 20 plateaux d’œufs et 20 poulets PAC', 'Jean-Marc Brou'),
        ('FAC-2026-004', 5, 'M. Kouamé Jean-Baptiste', str(today - timedelta(days=5)), 78000, 0, 78000, 78000, 0, 'especes', 'paye', str(today - timedelta(days=5)), 'Achat comptant 15 poulets fermiers pour baptême', 'Jean-Marc Brou'),
        ('FAC-2026-005', 2, 'Restaurant La Paillote Gourmande', str(today - timedelta(days=3)), 160000, 0, 160000, 100000, 60000, 'especes', 'acompte', str(today + timedelta(days=4)), '25 poulets de chair + 8 lapins de chair', 'Jean-Marc Brou'),
        ('FAC-2026-006', 6, 'Mme Viviane N’Guessan (Rôtisserie Divine)', str(today - timedelta(days=1)), 115000, 0, 115000, 75000, 40000, 'mobile_money', 'acompte', str(today + timedelta(days=6)), '30 poulets de chair vifs', 'Jean-Marc Brou'),
        ('FAC-2026-007', 1, 'Hôtel-Restaurant Le Fromager', str(today - timedelta(days=1)), 980000, 30000, 950000, 950000, 0, 'virement', 'paye', str(today - timedelta(days=1)), 'Gros réassort : 300 poulets PAC et 50 plateaux d’œufs. Réglé par virement', 'Jean-Marc Brou'),
        ('FAC-2026-008', 3, 'Coopérative Revendeurs Marché Gouro', str(today), 440000, 0, 440000, 440000, 0, 'mobile_money', 'paye', str(today), '200 plateaux d’œufs de table plein ponte. Réglé Wave', 'Jean-Marc Brou')
    ]
    cur.executemany("INSERT INTO ventes (numero_facture, client_id, client_nom, date_vente, montant_brut, remise, montant_net, montant_regle, montant_restant, mode_paiement, statut_paiement, date_echeance, notes, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", ventes)

    # Lignes de factures
    lignes_v = [
        # Facture 1
        (1, 'Œufs frais de table (Plateau de 30)', 'oeufs_plateau', 100, 'plateau', 2200, 220000, 2),
        # Facture 2
        (2, 'Poulets de chair prêts à cuire (PAC)', 'poulet_pac', 110, 'kg', 3100, 341000, 1),
        (2, 'Lapins prêts à cuire', 'lapin_decoupe', 14, 'kg', 6000, 84000, None),
        # Facture 3
        (3, 'Œufs frais de table (Plateau de 30)', 'oeufs_plateau', 30, 'plateau', 2300, 69000, 2),
        (3, 'Poulets prêts à cuire emballés', 'poulet_pac', 32, 'kg', 3000, 96000, 1),
        # Facture 4
        (4, 'Poulets Goliath Fermiers Vifs', 'poulet_vif', 15, 'unite', 5200, 78000, 3),
        # Facture 5
        (5, 'Poulets de chair vifs (2.1 kg)', 'poulet_vif', 25, 'unite', 4400, 110000, 1),
        (5, 'Lapins de chair vivants (2 kg)', 'lapin_vif', 8, 'unite', 6250, 50000, 1),
        # Facture 6
        (6, 'Poulets de chair vifs (2.0 kg)', 'poulet_vif', 25, 'unite', 4600, 115000, 1),
        # Facture 7
        (7, 'Poulets de chair prêts à cuire (PAC)', 'poulet_pac', 280, 'kg', 3100, 868000, 1),
        (7, 'Œufs frais de table (Plateau de 30)', 'oeufs_plateau', 50, 'plateau', 2240, 112000, 2),
        # Facture 8
        (8, 'Œufs frais de table (Plateau de 30)', 'oeufs_plateau', 200, 'plateau', 2200, 440000, 2)
    ]
    cur.executemany("INSERT INTO vente_lignes (vente_id, designation, type_produit, quantite, unite, prix_unitaire, sous_total, lot_source_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", lignes_v)

    # Règlements clients
    reglements = [
        (1, 3, str(today - timedelta(days=12)), 220000, 'mobile_money', 'TRANS-WAVE-8910', 'Jean-Marc Brou'),
        (2, 1, str(today - timedelta(days=9)), 230000, 'virement', 'VIR-SGBCI-4421', 'Estelle Bamba'),
        (3, 4, str(today - timedelta(days=7)), 65000, 'mobile_money', 'TRANS-OM-3329', 'Jean-Marc Brou'),
        (4, 5, str(today - timedelta(days=5)), 78000, 'especes', 'RECU-ESP-004', 'Jean-Marc Brou'),
        (5, 2, str(today - timedelta(days=3)), 100000, 'especes', 'RECU-ESP-005', 'Jean-Marc Brou'),
        (6, 6, str(today - timedelta(days=1)), 75000, 'mobile_money', 'TRANS-WAVE-9921', 'Jean-Marc Brou'),
        (7, 1, str(today - timedelta(days=1)), 950000, 'virement', 'VIR-SGBCI-4490', 'Estelle Bamba'),
        (8, 3, str(today), 440000, 'mobile_money', 'TRANS-WAVE-9955', 'Jean-Marc Brou')
    ]
    cur.executemany("INSERT INTO reglements_clients (vente_id, client_id, date_reglement, montant, mode_paiement, reference, encaisse_par) VALUES (?, ?, ?, ?, ?, ?, ?)", reglements)

    # 13. Dépenses & Achats
    depenses = [
        ('DEP-2026-001', str(today - timedelta(days=14)), 'aliments', 'Achat 2 tonnes maïs jaune concassé', 'Coopérative Céréalière de Gagnoa', 360000, 'virement', 'FA-COOP-882', 'Approvisionnement stock ration', 'Estelle Bamba'),
        ('DEP-2026-002', str(today - timedelta(days=12)), 'aliments', 'Achat tourteau de soja 48% (800 kg)', 'Ivoire Aliments Abidjan', 312000, 'mobile_money', 'FA-IA-1044', 'Matière première riche en protéines', 'Estelle Bamba'),
        ('DEP-2026-003', str(today - timedelta(days=10)), 'sante', 'Médicaments vétérinaires et vaccins Newcastle/Gumboro', 'Pharmacie Vétérinaire du Gôh', 85000, 'especes', 'TIK-PV-552', 'Renouvellement pharmacie d’élevage', 'Awa Traoré'),
        ('DEP-2026-004', str(today - timedelta(days=8)), 'salaires', 'Acompte quinzaine 3 ouvriers d’élevage', 'Personnel Ferme Diégonefla', 240000, 'mobile_money', 'PAIE-QUINZ-01', 'Avance sur salaires du mois', 'Estelle Bamba'),
        ('DEP-2026-005', str(today - timedelta(days=6)), 'energie', 'Carburant groupe électrogène & livraison', 'Station TotalEnergies Diégonefla', 75000, 'especes', 'FAC-TOT-992', '100 litres gasoil pour secours électrique', 'Estelle Bamba'),
        ('DEP-2026-006', str(today - timedelta(days=4)), 'equipement', 'Abreuvoirs automatiques lapins & pipettes volailles', 'AgriMat Ivoire', 48000, 'mobile_money', 'FAC-AM-221', 'Remplacement matériel défectueux', 'Awa Traoré'),
        ('DEP-2026-007', str(today - timedelta(days=2)), 'entretien', 'Désinfectant crésyl, chaux vive pour bâtiments', 'Quincaillerie Centrale', 32000, 'especes', 'FAC-QC-712', 'Vide sanitaire Bâtiment 1', 'Awa Traoré')
    ]
    cur.executemany("INSERT INTO depenses (reference, date_depense, categorie, libelle, fournisseur, montant, mode_paiement, num_piece, notes, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", depenses)

    # 14. Logs d'audit
    audit = [
        (str(today - timedelta(days=1)), 'Awa Traoré', 'Aliments', 'Distribution', 'Distribution de 120 kg aliment croissance au Lot LOT-VOL-01'),
        (str(today - timedelta(days=1)), 'Jean-Marc Brou', 'Ventes', 'Création', 'Émission facture FAC-2026-006 (115 000 FCFA) pour Mme Viviane N’Guessan'),
        (str(today - timedelta(days=2)), 'Awa Traoré', 'Volailles', 'Pesée', 'Pesée de contrôle Lot LOT-VOL-03 Goliath (Poids moyen: 410g)'),
        (str(today - timedelta(days=3)), 'Estelle Bamba', 'Dépenses', 'Création', 'Enregistrement dépense équipement (48 000 FCFA)'),
        (str(today - timedelta(days=4)), 'Kouassi Konan', 'Incubation', 'Suivi', 'Contrôle température et hygrométrie Couveuse Victoria (INCUB-2026-03)')
    ]
    cur.executemany("INSERT INTO audit_logs (date_action, utilisateur_nom, module, action, details) VALUES (?, ?, ?, ?, ?)", audit)

    conn.commit()

if __name__ == '__main__':
    init_db(force_reseed=True)
    print("Database initialized and seeded successfully.")
