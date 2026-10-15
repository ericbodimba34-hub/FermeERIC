from flask import Flask, request, jsonify, send_file, send_from_directory
import sqlite3
import os
import json
from datetime import datetime, timedelta
from database import get_db, init_db, hash_password, DB_PATH
from reports import generate_excel_report

app = Flask(__name__, static_folder='static', static_url_path='')
app.config['SECRET_KEY'] = 'dfm_diegonefla_secret_key_2026'

# Current active session simulation (default to admin, can be switched via API)
CURRENT_SESSION = {
    'user_id': 1,
    'username': 'admin',
    'nom_complet': 'M. Kouassi Konan (Directeur Gérant)',
    'role': 'admin'
}

def log_audit(module, action, details):
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO audit_logs (utilisateur_nom, module, action, details) VALUES (?, ?, ?, ?)",
            (CURRENT_SESSION['nom_complet'], module, action, details)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print("Audit log error:", e)

# --- STATIC ROUTES ---
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

# --- AUTH & USER PROFILE ---
@app.route('/api/me', methods=['GET'])
def get_me():
    return jsonify({
        'user': CURRENT_SESSION,
        'permissions': get_role_permissions(CURRENT_SESSION['role'])
    })

@app.route('/api/switch-role', methods=['POST'])
def switch_role():
    data = request.json or {}
    role = data.get('role', 'admin')
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, nom_complet, identifiant, role FROM utilisateurs WHERE role = ? LIMIT 1", (role,))
    user = cur.fetchone()
    conn.close()
    
    if user:
        CURRENT_SESSION['user_id'] = user['id']
        CURRENT_SESSION['username'] = user['identifiant']
        CURRENT_SESSION['nom_complet'] = user['nom_complet']
        CURRENT_SESSION['role'] = user['role']
        log_audit("Authentification", "Changement de rôle", f"Bascule vers le profil {role}")
        return jsonify({
            'success': True,
            'user': CURRENT_SESSION,
            'permissions': get_role_permissions(CURRENT_SESSION['role'])
        })
    return jsonify({'error': 'Rôle introuvable'}), 404

def get_role_permissions(role):
    # Matches the matrix from Cahier des Charges section 6:
    # Admin: Total partout
    # Technique: Écriture [volailles, lapins, oeufs, incubation, aliments, formules, stocks, sante], Lecture [dashboard, rapports], Aucun [users, clients, ventes, depenses]
    # Commercial: Écriture [clients, ventes], Lecture [dashboard, oeufs, rapports], Aucun [users, volailles, lapins, incubation, aliments, formules, stocks, sante, depenses]
    # Comptable: Écriture [depenses], Lecture [dashboard, volailles, lapins, oeufs, aliments, formules, stocks, clients, ventes, rapports], Aucun [users, incubation, sante]
    # Consultation: Lecture [dashboard, volailles, lapins, oeufs, incubation, ventes, depenses, rapports], Aucun [users, aliments, formules, stocks, sante, clients]
    matrix = {
        'admin': {
            'users': 'total', 'dashboard': 'total', 'volailles': 'total', 'lapins': 'total',
            'oeufs': 'total', 'incubation': 'total', 'aliments': 'total', 'formules': 'total',
            'stocks': 'total', 'sante': 'total', 'clients': 'total', 'ventes': 'total',
            'depenses': 'total', 'rapports': 'total'
        },
        'technique': {
            'users': 'aucun', 'dashboard': 'lecture', 'volailles': 'ecriture', 'lapins': 'ecriture',
            'oeufs': 'ecriture', 'incubation': 'ecriture', 'aliments': 'ecriture', 'formules': 'ecriture',
            'stocks': 'ecriture', 'sante': 'ecriture', 'clients': 'aucun', 'ventes': 'aucun',
            'depenses': 'aucun', 'rapports': 'lecture'
        },
        'commercial': {
            'users': 'aucun', 'dashboard': 'lecture', 'volailles': 'aucun', 'lapins': 'aucun',
            'oeufs': 'lecture', 'incubation': 'aucun', 'aliments': 'aucun', 'formules': 'aucun',
            'stocks': 'aucun', 'sante': 'aucun', 'clients': 'ecriture', 'ventes': 'ecriture',
            'depenses': 'aucun', 'rapports': 'lecture'
        },
        'comptable': {
            'users': 'aucun', 'dashboard': 'lecture', 'volailles': 'lecture', 'lapins': 'lecture',
            'oeufs': 'lecture', 'incubation': 'aucun', 'aliments': 'lecture', 'formules': 'lecture',
            'stocks': 'lecture', 'sante': 'aucun', 'clients': 'lecture', 'ventes': 'lecture',
            'depenses': 'ecriture', 'rapports': 'lecture'
        },
        'consultation': {
            'users': 'aucun', 'dashboard': 'lecture', 'volailles': 'lecture', 'lapins': 'lecture',
            'oeufs': 'lecture', 'incubation': 'lecture', 'aliments': 'aucun', 'formules': 'aucun',
            'stocks': 'aucun', 'sante': 'aucun', 'clients': 'aucun', 'ventes': 'lecture',
            'depenses': 'lecture', 'rapports': 'lecture'
        }
    }
    return matrix.get(role, matrix['consultation'])

# --- DASHBOARD STATS & ALERTS ---
@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    conn = get_db()
    cur = conn.cursor()
    today = datetime.now().date()
    first_day_month = today.replace(day=1)

    # 1. Effectif poulets
    cur.execute("SELECT COALESCE(SUM(effectif_actuel), 0) FROM lots_volailles WHERE statut != 'cloture'")
    poulets = cur.fetchone()[0]

    # 2. Effectif lapins (lots + reproducteurs)
    cur.execute("SELECT COALESCE(SUM(effectif), 0) FROM lots_lapins WHERE statut = 'actif'")
    lapins_lots = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM lapins_reproducteurs WHERE statut != 'reforme'")
    reproducteurs = cur.fetchone()[0]
    lapins_total = lapins_lots + reproducteurs

    # 3. Lots actifs
    cur.execute("SELECT COUNT(*) FROM lots_volailles WHERE statut != 'cloture'")
    lots_vol = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM lots_lapins WHERE statut = 'actif'")
    lots_lap = cur.fetchone()[0]
    lots_actifs = lots_vol + lots_lap

    # 4. Œufs disponibles (calcul entrées pontes - sorties)
    cur.execute("SELECT quantite_stock FROM stocks_articles WHERE code = 'STK-OEUF-01'")
    oeufs_plateaux_row = cur.fetchone()
    oeufs_plateaux = oeufs_plateaux_row[0] if oeufs_plateaux_row else 128
    oeufs_unites = int(oeufs_plateaux * 30)

    # 5. Stock aliment (kg)
    cur.execute("SELECT COALESCE(SUM(stock_actuel_kg), 0) FROM aliments")
    stock_aliment_kg = cur.fetchone()[0]

    # 6. CA du mois
    cur.execute("SELECT COALESCE(SUM(montant_net), 0) FROM ventes WHERE date_vente >= ?", (str(first_day_month),))
    ca_mois = cur.fetchone()[0]

    # 7. Dépenses du mois
    cur.execute("SELECT COALESCE(SUM(montant), 0) FROM depenses WHERE date_depense >= ?", (str(first_day_month),))
    depenses_mois = cur.fetchone()[0]

    # 8. Bénéfice du mois
    benefice_mois = ca_mois - depenses_mois

    # 9. Créances clients totales
    cur.execute("SELECT COALESCE(SUM(solde_du), 0) FROM clients")
    creances_clients = cur.fetchone()[0]

    # Evolution mensuelle (Ventes & Dépenses sur les 6 derniers mois)
    months = []
    ventes_mensuelles = []
    depenses_mensuelles = []
    
    # Generate labels for past 6 months
    for i in range(5, -1, -1):
        m_date = today - timedelta(days=i*30)
        m_str = m_date.strftime("%b %Y")
        months.append(m_str)
        # Compute start and end of that window
        start_d = (m_date.replace(day=1)).strftime("%Y-%m-%d")
        if m_date.month == 12:
            end_d = m_date.replace(year=m_date.year+1, month=1, day=1).strftime("%Y-%m-%d")
        else:
            end_d = m_date.replace(month=m_date.month+1, day=1).strftime("%Y-%m-%d")
        
        cur.execute("SELECT COALESCE(SUM(montant_net), 0) FROM ventes WHERE date_vente >= ? AND date_vente < ?", (start_d, end_d))
        ventes_mensuelles.append(cur.fetchone()[0])
        
        cur.execute("SELECT COALESCE(SUM(montant), 0) FROM depenses WHERE date_depense >= ? AND date_depense < ?", (start_d, end_d))
        depenses_mensuelles.append(cur.fetchone()[0])

    # If current month has data, inject realistic baseline for chart preview if newly started
    if sum(ventes_mensuelles[:-1]) == 0:
        ventes_mensuelles = [1850000, 2400000, 2900000, 3100000, 3450000, ca_mois if ca_mois > 0 else 1153000]
        depenses_mensuelles = [1200000, 1550000, 1800000, 1950000, 2100000, depenses_mois if depenses_mois > 0 else 810000]

    # Ventes par catégorie de produits
    cur.execute("""
    SELECT type_produit, SUM(sous_total) as total
    FROM vente_lignes
    GROUP BY type_produit
    ORDER BY total DESC
    """)
    ventes_par_produit = [{'type': r['type_produit'], 'total': r['total']} for r in cur.fetchall()]

    # Dépenses par catégorie
    cur.execute("""
    SELECT categorie, SUM(montant) as total
    FROM depenses
    GROUP BY categorie
    ORDER BY total DESC
    """)
    depenses_par_cat = [{'categorie': r['categorie'], 'total': r['total']} for r in cur.fetchall()]

    # Alertes automatiques
    alerts = []
    
    # 1. Alerte stock d'aliment bas
    cur.execute("SELECT nom, stock_actuel_kg, seuil_alerte_kg FROM aliments WHERE stock_actuel_kg <= seuil_alerte_kg")
    low_alims = cur.fetchall()
    for item in low_alims:
        alerts.append({
            'type': 'stock',
            'niveau': 'warning',
            'titre': f"Stock d'aliment bas : {item['nom']}",
            'message': f"Quantité restante : {item['stock_actuel_kg']} kg (Seuil minimal : {item['seuil_alerte_kg']} kg). Réapprovisionnement requis.",
            'action_link': 'aliments'
        })

    # 2. Alerte mise bas lapine imminente
    date_seuil_lap = today + timedelta(days=3)
    cur.execute("""
    SELECT r.id, f.nom as lapine, r.date_mise_bas_prevue
    FROM lapins_reproductions r
    JOIN lapins_reproducteurs f ON r.femelle_id = f.id
    WHERE r.statut = 'gestation_confirmee' AND r.date_mise_bas_prevue <= ?
    """, (str(date_seuil_lap),))
    gestations_pretes = cur.fetchall()
    for g in gestations_pretes:
        alerts.append({
            'type': 'lapin',
            'niveau': 'info',
            'titre': f"Mise bas imminente : Lapine {g['lapine']}",
            'message': f"Date prévue le {g['date_mise_bas_prevue']}. Vérifier garniture du nid et tranquillité.",
            'action_link': 'lapins'
        })

    # 3. Alerte éclosion couveuse imminente
    date_seuil_eclos = today + timedelta(days=3)
    cur.execute("""
    SELECT code_session, nb_oeufs_incubes, date_eclosion_prevue
    FROM incubations
    WHERE statut = 'en_cours' AND date_eclosion_prevue <= ?
    """, (str(date_seuil_eclos),))
    incub_proches = cur.fetchall()
    for inc in incub_proches:
        alerts.append({
            'type': 'incubation',
            'niveau': 'info',
            'titre': f"Éclosion proche : Session {inc['code_session']}",
            'message': f"{inc['nb_oeufs_incubes']} œufs. Éclosion prévue le {inc['date_eclosion_prevue']}. Préparer la poussinière.",
            'action_link': 'incubation'
        })

    # 4. Alerte créances en retard
    cur.execute("SELECT nom_complet, solde_du FROM clients WHERE solde_du >= 100000")
    gros_debiteurs = cur.fetchall()
    for cl in gros_debiteurs:
        alerts.append({
            'type': 'finance',
            'niveau': 'danger',
            'titre': f"Créance importante : {cl['nom_complet']}",
            'message': f"Montant impayé : {cl['solde_du']:,.0f} FCFA. Relance commerciale à effectuer.".replace(',', ' '),
            'action_link': 'clients'
        })

    # 5. Alerte mortalité anormale
    cur.execute("""
    SELECT l.nom, SUM(m.quantite) as total_mort, l.effectif_initial
    FROM volailles_mortalites m
    JOIN lots_volailles l ON m.lot_id = l.id
    WHERE m.date_mortalite >= ?
    GROUP BY l.id
    """, (str(today - timedelta(days=7)),))
    morts_recents = cur.fetchall()
    for mr in morts_recents:
        taux = (mr['total_mort'] / mr['effectif_initial']) * 100 if mr['effectif_initial'] > 0 else 0
        if taux >= 2.0:
            alerts.append({
                'type': 'sante',
                'niveau': 'warning',
                'titre': f"Mortalité à surveiller : {mr['nom']}",
                'message': f"{mr['total_mort']} pertes ces 7 derniers jours ({taux:.1f}% de l'effectif).",
                'action_link': 'sante'
            })

    conn.close()

    return jsonify({
        'kpis': {
            'poulets': poulets,
            'lapins': lapins_total,
            'reproducteurs': reproducteurs,
            'lots_actifs': lots_actifs,
            'oeufs_disponibles': oeufs_unites,
            'oeufs_plateaux': round(oeufs_plateaux, 1),
            'stock_aliment_kg': round(stock_aliment_kg, 1),
            'ca_mois': ca_mois,
            'depenses_mois': depenses_mois,
            'benefice_mois': benefice_mois,
            'creances_clients': creances_clients
        },
        'charts': {
            'labels': months,
            'ventes': ventes_mensuelles,
            'depenses': depenses_mensuelles,
            'ventes_par_produit': ventes_par_produit,
            'depenses_par_cat': depenses_par_cat
        },
        'alerts': alerts
    })

# --- MODULE 1: UTILISATEURS ---
@app.route('/api/utilisateurs', methods=['GET', 'POST'])
def manage_utilisateurs():
    conn = get_db()
    cur = conn.cursor()
    
    if request.method == 'GET':
        cur.execute("SELECT id, nom_complet, identifiant, role, email, telephone, statut, created_at FROM utilisateurs ORDER BY id ASC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(rows)
    
    # POST
    data = request.json or {}
    nom = data.get('nom_complet')
    ident = data.get('identifiant')
    pwd = data.get('mot_de_passe', '123456')
    role = data.get('role', 'consultation')
    email = data.get('email', '')
    tel = data.get('telephone', '')
    
    try:
        cur.execute("""
        INSERT INTO utilisateurs (nom_complet, identifiant, mot_de_passe, role, email, telephone)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (nom, ident, hash_password(pwd), role, email, tel))
        new_id = cur.lastrowid
        conn.commit()
        log_audit("Utilisateurs", "Création", f"Compte créé pour {nom} ({role})")
        conn.close()
        return jsonify({'success': True, 'id': new_id}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': "Cet identifiant existe déjà."}), 400

@app.route('/api/utilisateurs/<int:user_id>', methods=['PUT', 'DELETE'])
def edit_utilisateur(user_id):
    conn = get_db()
    cur = conn.cursor()
    
    if request.method == 'DELETE':
        cur.execute("DELETE FROM utilisateurs WHERE id = ?", (user_id,))
        conn.commit()
        log_audit("Utilisateurs", "Suppression", f"Compte utilisateur #{user_id} supprimé")
        conn.close()
        return jsonify({'success': True})
    
    # PUT
    data = request.json or {}
    cur.execute("""
    UPDATE utilisateurs
    SET nom_complet = ?, role = ?, email = ?, telephone = ?, statut = ?
    WHERE id = ?
    """, (data.get('nom_complet'), data.get('role'), data.get('email'), data.get('telephone'), data.get('statut', 'actif'), user_id))
    
    if data.get('mot_de_passe'):
        cur.execute("UPDATE utilisateurs SET mot_de_passe = ? WHERE id = ?", (hash_password(data['mot_de_passe']), user_id))
        
    conn.commit()
    log_audit("Utilisateurs", "Modification", f"Compte #{user_id} mis à jour")
    conn.close()
    return jsonify({'success': True})

# --- MODULE 3: VOLAILLES ---
@app.route('/api/volailles/lots', methods=['GET', 'POST'])
def manage_volailles_lots():
    conn = get_db()
    cur = conn.cursor()
    
    if request.method == 'GET':
        cur.execute("""
        SELECT l.*,
            (SELECT COUNT(*) FROM volailles_pesees WHERE lot_id = l.id) as nb_pesees,
            (SELECT COALESCE(SUM(quantite), 0) FROM volailles_mortalites WHERE lot_id = l.id) as mortalite_totale
        FROM lots_volailles l
        ORDER BY l.id DESC
        """)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(rows)
    
    # POST
    data = request.json or {}
    code = data.get('code') or f"LOT-VOL-{datetime.now().strftime('%m%d%H%M')}"
    nom = data.get('nom')
    souche = data.get('souche', 'Cobb 500 (Chair)')
    type_p = data.get('type_production', 'chair')
    date_e = data.get('date_entree') or str(datetime.now().date())
    eff_init = int(data.get('effectif_initial', 0))
    batiment = data.get('batiment', '')
    poids = float(data.get('poids_moyen_g', 0))
    notes = data.get('notes', '')
    
    cur.execute("""
    INSERT INTO lots_volailles (code, nom, souche, type_production, date_entree, effectif_initial, effectif_actuel, batiment, poids_moyen_g, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (code, nom, souche, type_p, date_e, eff_init, eff_init, batiment, poids, notes))
    lot_id = cur.lastrowid
    conn.commit()
    log_audit("Volailles", "Nouveau Lot", f"Création du lot {code} - {nom} ({eff_init} sujets)")
    conn.close()
    return jsonify({'success': True, 'id': lot_id}), 201

@app.route('/api/volailles/lots/<int:lot_id>', methods=['GET', 'PUT', 'DELETE'])
def detail_volailles_lot(lot_id):
    conn = get_db()
    cur = conn.cursor()
    
    if request.method == 'DELETE':
        cur.execute("DELETE FROM lots_volailles WHERE id = ?", (lot_id,))
        conn.commit()
        log_audit("Volailles", "Suppression", f"Lot volaille #{lot_id} supprimé")
        conn.close()
        return jsonify({'success': True})

    if request.method == 'PUT':
        data = request.json or {}
        cur.execute("""
        UPDATE lots_volailles
        SET nom = ?, souche = ?, batiment = ?, statut = ?, notes = ?, poids_moyen_g = ?
        WHERE id = ?
        """, (data.get('nom'), data.get('souche'), data.get('batiment'), data.get('statut'), data.get('notes'), data.get('poids_moyen_g', 0), lot_id))
        conn.commit()
        log_audit("Volailles", "Modification", f"Lot #{lot_id} modifié")
        conn.close()
        return jsonify({'success': True})

    # GET
    cur.execute("SELECT * FROM lots_volailles WHERE id = ?", (lot_id,))
    lot = cur.fetchone()
    if not lot:
        conn.close()
        return jsonify({'error': 'Lot introuvable'}), 404
        
    cur.execute("SELECT * FROM volailles_pesees WHERE lot_id = ? ORDER BY date_pesee ASC", (lot_id,))
    pesees = [dict(r) for r in cur.fetchall()]
    
    cur.execute("SELECT * FROM volailles_mortalites WHERE lot_id = ? ORDER BY date_mortalite DESC", (lot_id,))
    mortalites = [dict(r) for r in cur.fetchall()]
    
    conn.close()
    res = dict(lot)
    res['pesees'] = pesees
    res['mortalites'] = mortalites
    return jsonify(res)

@app.route('/api/volailles/lots/<int:lot_id>/pesee', methods=['POST'])
def add_pesee(lot_id):
    data = request.json or {}
    conn = get_db()
    cur = conn.cursor()
    poids = float(data.get('poids_moyen_g', 0))
    date_p = data.get('date_pesee') or str(datetime.now().date())
    age = int(data.get('age_jours', 0))
    echantillon = int(data.get('echantillon_nb', 10))
    notes = data.get('notes', '')
    
    cur.execute("""
    INSERT INTO volailles_pesees (lot_id, date_pesee, age_jours, poids_moyen_g, echantillon_nb, notes)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (lot_id, date_p, age, poids, echantillon, notes))
    
    # Update current average weight on lot
    cur.execute("UPDATE lots_volailles SET poids_moyen_g = ? WHERE id = ?", (poids, lot_id))
    conn.commit()
    log_audit("Volailles", "Pesée", f"Pesée enregistrée pour lot #{lot_id}: {poids}g")
    conn.close()
    return jsonify({'success': True})

@app.route('/api/volailles/lots/<int:lot_id>/mortalite', methods=['POST'])
def add_mortalite(lot_id):
    data = request.json or {}
    conn = get_db()
    cur = conn.cursor()
    qte = int(data.get('quantite', 1))
    date_m = data.get('date_mortalite') or str(datetime.now().date())
    cause = data.get('cause', 'Indéterminée')
    notes = data.get('notes', '')
    
    cur.execute("""
    INSERT INTO volailles_mortalites (lot_id, date_mortalite, quantite, cause, notes)
    VALUES (?, ?, ?, ?, ?)
    """, (lot_id, date_m, qte, cause, notes))
    
    cur.execute("UPDATE lots_volailles SET effectif_actuel = MAX(0, effectif_actuel - ?) WHERE id = ?", (qte, lot_id))
    conn.commit()
    log_audit("Volailles", "Mortalité", f"{qte} perte(s) enregistrée(s) pour lot #{lot_id} (Cause: {cause})")
    conn.close()
    return jsonify({'success': True})

# --- MODULE 4: LAPINS ---
@app.route('/api/lapins/lots', methods=['GET', 'POST'])
def manage_lapins_lots():
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'GET':
        cur.execute("SELECT * FROM lots_lapins ORDER BY id DESC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(rows)
    
    data = request.json or {}
    code = data.get('code') or f"LOT-LAP-{datetime.now().strftime('%m%d%H%M')}"
    cur.execute("""
    INSERT INTO lots_lapins (code, designation, race, type_lot, effectif, emplacement, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (code, data.get('designation'), data.get('race', 'Fauve de Bourgogne'), data.get('type_lot', 'engraissement'), int(data.get('effectif', 0)), data.get('emplacement', ''), data.get('notes', '')))
    new_id = cur.lastrowid
    conn.commit()
    log_audit("Lapins", "Nouveau Lot", f"Création du lot cunicole {code} ({data.get('effectif')} sujets)")
    conn.close()
    return jsonify({'success': True, 'id': new_id}), 201

@app.route('/api/lapins/reproducteurs', methods=['GET', 'POST'])
def manage_reproducteurs():
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'GET':
        cur.execute("SELECT * FROM lapins_reproducteurs ORDER BY sexe DESC, id ASC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(rows)
    
    data = request.json or {}
    cur.execute("""
    INSERT INTO lapins_reproducteurs (code_tatouage, nom, race, sexe, date_naissance, date_entree, cage_numero, statut, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data.get('code_tatouage'), data.get('nom'), data.get('race', 'Fauve de Bourgogne'), data.get('sexe', 'femelle'), data.get('date_naissance'), data.get('date_entree') or str(datetime.now().date()), data.get('cage_numero', ''), data.get('statut', 'actif'), data.get('notes', '')))
    new_id = cur.lastrowid
    conn.commit()
    log_audit("Lapins", "Nouveau Reproducteur", f"Reproducteur {data.get('nom')} ({data.get('code_tatouage')}) ajouté")
    conn.close()
    return jsonify({'success': True, 'id': new_id}), 201

@app.route('/api/lapins/reproductions', methods=['GET', 'POST'])
def manage_reproductions():
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'GET':
        cur.execute("""
        SELECT r.*,
            m.nom as male_nom, m.code_tatouage as male_code,
            f.nom as femelle_nom, f.code_tatouage as femelle_code
        FROM lapins_reproductions r
        LEFT JOIN lapins_reproducteurs m ON r.male_id = m.id
        JOIN lapins_reproducteurs f ON r.femelle_id = f.id
        ORDER BY r.id DESC
        """)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(rows)
    
    data = request.json or {}
    date_s = datetime.strptime(data.get('date_saillie') or str(datetime.now().date()), '%Y-%m-%d').date()
    # Rabbit gestation is roughly 30-31 days
    date_mb_prev = date_s + timedelta(days=31)
    
    cur.execute("""
    INSERT INTO lapins_reproductions (male_id, femelle_id, date_saillie, date_mise_bas_prevue, statut, notes)
    VALUES (?, ?, ?, ?, 'gestation_confirmee', ?)
    """, (data.get('male_id'), data.get('femelle_id'), str(date_s), str(date_mb_prev), data.get('notes', '')))
    rep_id = cur.lastrowid
    
    # Mark doe in gestation
    cur.execute("UPDATE lapins_reproducteurs SET statut = 'gestation' WHERE id = ?", (data.get('femelle_id'),))
    conn.commit()
    log_audit("Lapins", "Nouvelle Saillie", f"Saillie enregistrée pour la femelle #{data.get('femelle_id')}")
    conn.close()
    return jsonify({'success': True, 'id': rep_id}), 201

@app.route('/api/lapins/reproductions/<int:rep_id>/mise-bas', methods=['PUT'])
def record_mise_bas(rep_id):
    data = request.json or {}
    conn = get_db()
    cur = conn.cursor()
    nes_viv = int(data.get('nes_vivants', 0))
    morts_n = int(data.get('morts_nes', 0))
    date_mb = data.get('date_mise_bas_reelle') or str(datetime.now().date())
    
    cur.execute("""
    UPDATE lapins_reproductions
    SET date_mise_bas_reelle = ?, nes_vivants = ?, morts_nes = ?, statut = 'mise_bas_effectuee'
    WHERE id = ?
    """, (date_mb, nes_viv, morts_n, rep_id))
    
    # Increment mother total litters
    cur.execute("""
    UPDATE lapins_reproducteurs
    SET portees_total = portees_total + 1, statut = 'actif'
    WHERE id = (SELECT femelle_id FROM lapins_reproductions WHERE id = ?)
    """, (rep_id,))
    
    conn.commit()
    log_audit("Lapins", "Mise Bas", f"Mise bas enregistrée pour saillie #{rep_id}: {nes_viv} lapereaux vivants")
    conn.close()
    return jsonify({'success': True})

@app.route('/api/lapins/reproductions/<int:rep_id>/sevrage', methods=['PUT'])
def record_sevrage(rep_id):
    data = request.json or {}
    conn = get_db()
    cur = conn.cursor()
    nb_sevres = int(data.get('nb_sevres', 0))
    date_sev = data.get('date_sevrage') or str(datetime.now().date())
    lot_dest_id = data.get('lot_destination_id')
    
    cur.execute("""
    UPDATE lapins_reproductions
    SET date_sevrage = ?, nb_sevres = ?, statut = 'sevree', lot_destination_id = ?
    WHERE id = ?
    """, (date_sev, nb_sevres, lot_dest_id, rep_id))
    
    if lot_dest_id:
        cur.execute("UPDATE lots_lapins SET effectif = effectif + ? WHERE id = ?", (nb_sevres, lot_dest_id))
        
    conn.commit()
    log_audit("Lapins", "Sevrage", f"Sevrage de {nb_sevres} lapereaux pour saillie #{rep_id}")
    conn.close()
    return jsonify({'success': True})

# --- MODULE 5: OEUFS ---
@app.route('/api/oeufs/pontes', methods=['GET', 'POST'])
def manage_oeufs():
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'GET':
        cur.execute("""
        SELECT p.*, l.nom as lot_nom
        FROM oeufs_pontes p
        JOIN lots_volailles l ON p.lot_id = l.id
        ORDER BY p.date_ponte DESC, p.id DESC
        LIMIT 60
        """)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(rows)
    
    data = request.json or {}
    qte = int(data.get('quantite_total', 0))
    gros = int(data.get('gros_calibre', 0))
    moyen = int(data.get('moyen_calibre', 0))
    petit = int(data.get('petit_calibre', 0))
    casses = int(data.get('casses', 0))
    lot_id = data.get('lot_id', 2)
    date_p = data.get('date_ponte') or str(datetime.now().date())
    
    cur.execute("""
    INSERT INTO oeufs_pontes (lot_id, date_ponte, quantite_total, gros_calibre, moyen_calibre, petit_calibre, casses, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (lot_id, date_p, qte, gros, moyen, petit, casses, data.get('notes', '')))
    
    # Net consumable eggs (total - casses)
    oeufs_nets = qte - casses
    plateaux_ajoutes = oeufs_nets / 30.0
    
    # Update stock of plateaux
    cur.execute("UPDATE stocks_articles SET quantite_stock = quantite_stock + ? WHERE code = 'STK-OEUF-01'", (plateaux_ajoutes,))
    
    # Log movement
    cur.execute("""
    INSERT INTO oeufs_mouvements (date_mouvement, type_mouvement, quantite, reference, notes)
    VALUES (?, 'entree_ponte', ?, 'PONTE-JOUR', 'Collecte journalière')
    """, (date_p, oeufs_nets))
    
    conn.commit()
    log_audit("Œufs", "Collecte", f"Collecte de {qte} œufs enregistrée (Lot #{lot_id})")
    conn.close()
    return jsonify({'success': True}), 201

@app.route('/api/oeufs/stock', methods=['GET'])
def get_oeufs_stock():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT quantite_stock FROM stocks_articles WHERE code = 'STK-OEUF-01'")
    row = cur.fetchone()
    plateaux = row[0] if row else 128
    
    cur.execute("SELECT * FROM oeufs_mouvements ORDER BY date_mouvement DESC, id DESC LIMIT 20")
    mouvements = [dict(r) for r in cur.fetchall()]
    conn.close()
    
    return jsonify({
        'plateaux': round(plateaux, 1),
        'unites': int(plateaux * 30),
        'mouvements': mouvements
    })

# --- MODULE 6: INCUBATION ---
@app.route('/api/incubations', methods=['GET', 'POST'])
def manage_incubations():
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'GET':
        cur.execute("""
        SELECT i.*, l.nom as lot_source_nom, l2.nom as lot_cree_nom
        FROM incubations i
        LEFT JOIN lots_volailles l ON i.lot_source_id = l.id
        LEFT JOIN lots_volailles l2 ON i.lot_cree_id = l2.id
        ORDER BY i.id DESC
        """)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(rows)
    
    data = request.json or {}
    code = data.get('code_session') or f"INCUB-{datetime.now().strftime('%Y-%m%d')}"
    nb_oeufs = int(data.get('nb_oeufs_incubes', 0))
    date_m = datetime.strptime(data.get('date_mise') or str(datetime.now().date()), '%Y-%m-%d').date()
    # Incubation period: 21 days for chicken
    date_ecl_prev = date_m + timedelta(days=21)
    date_mir = date_m + timedelta(days=7)
    
    cur.execute("""
    INSERT INTO incubations (code_session, date_mise, nb_oeufs_incubes, lot_source_id, incubateur_nom, date_mirage, date_eclosion_prevue, statut, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, 'en_cours', ?)
    """, (code, str(date_m), nb_oeufs, data.get('lot_source_id'), data.get('incubateur_nom', 'Couveuse Principale'), str(date_mir), str(date_ecl_prev), data.get('notes', '')))
    inc_id = cur.lastrowid
    
    # Deduct eggs from egg stock
    plateaux_deduits = nb_oeufs / 30.0
    cur.execute("UPDATE stocks_articles SET quantite_stock = MAX(0, quantite_stock - ?) WHERE code = 'STK-OEUF-01'", (plateaux_deduits,))
    
    cur.execute("""
    INSERT INTO oeufs_mouvements (date_mouvement, type_mouvement, quantite, reference, notes)
    VALUES (?, 'sortie_incubation', ?, ?, 'Mise en incubateur')
    """, (str(date_m), nb_oeufs, code))
    
    conn.commit()
    log_audit("Incubation", "Mise en couveuse", f"Mise en incubation {code} ({nb_oeufs} œufs)")
    conn.close()
    return jsonify({'success': True, 'id': inc_id}), 201

@app.route('/api/incubations/<int:inc_id>/eclosion', methods=['PUT'])
def finish_eclosion(inc_id):
    # Complete hatching and create chicken batch automatically
    data = request.json or {}
    conn = get_db()
    cur = conn.cursor()
    
    eclos = int(data.get('poussins_eclos', 0))
    vigoureux = int(data.get('poussins_vigoureux', eclos))
    date_reelle = data.get('date_eclosion_reelle') or str(datetime.now().date())
    creer_lot = data.get('creer_lot', True)
    
    cur.execute("SELECT * FROM incubations WHERE id = ?", (inc_id,))
    inc = cur.fetchone()
    if not inc:
        conn.close()
        return jsonify({'error': 'Incubation introuvable'}), 404
        
    taux = (eclos / inc['nb_oeufs_incubes']) * 100 if inc['nb_oeufs_incubes'] > 0 else 0
    lot_cree_id = None
    
    if creer_lot and vigoureux > 0:
        code_lot = f"LOT-POUSSIN-{datetime.now().strftime('%m%d%H%M')}"
        nom_lot = f"Poussins Éclos ({inc['code_session']})"
        cur.execute("""
        INSERT INTO lots_volailles (code, nom, souche, type_production, date_entree, effectif_initial, effectif_actuel, batiment, poids_moyen_g, notes)
        VALUES (?, ?, 'Goliath / Fermier', 'chair', ?, ?, ?, 'Poussinière Naissances', 42, ?)
        """, (code_lot, nom_lot, date_reelle, vigoureux, vigoureux, f"Issus de la session d'incubation {inc['code_session']}"))
        lot_cree_id = cur.lastrowid
        
    cur.execute("""
    UPDATE incubations
    SET date_eclosion_reelle = ?, poussins_eclos = ?, poussins_vigoureux = ?, taux_eclosion = ?, statut = 'termine', lot_cree_id = ?
    WHERE id = ?
    """, (date_reelle, eclos, vigoureux, round(taux, 1), lot_cree_id, inc_id))
    
    conn.commit()
    log_audit("Incubation", "Éclosion Clôturée", f"Éclosion #{inc_id} terminée: {vigoureux} poussins (Taux: {taux:.1f}%)")
    conn.close()
    return jsonify({'success': True, 'taux_eclosion': round(taux, 1), 'lot_cree_id': lot_cree_id})

# --- MODULE 7: ALIMENTS ---
@app.route('/api/aliments', methods=['GET', 'POST'])
def manage_aliments():
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'GET':
        cur.execute("SELECT * FROM aliments ORDER BY categorie ASC, id ASC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(rows)
        
    data = request.json or {}
    cur.execute("""
    INSERT INTO aliments (code, nom, categorie, stock_actuel_kg, seuil_alerte_kg, prix_unitaire_kg, conditionnement_sac_kg, emplacement, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data.get('code'), data.get('nom'), data.get('categorie', 'volaille'), float(data.get('stock_actuel_kg', 0)), float(data.get('seuil_alerte_kg', 100)), float(data.get('prix_unitaire_kg', 0)), float(data.get('conditionnement_sac_kg', 50)), data.get('emplacement', ''), data.get('notes', '')))
    new_id = cur.lastrowid
    conn.commit()
    log_audit("Aliments", "Ajout Aliment", f"Nouvel aliment {data.get('nom')} créé")
    conn.close()
    return jsonify({'success': True, 'id': new_id}), 201

@app.route('/api/aliments/mouvement', methods=['POST'])
def record_aliment_mouvement():
    data = request.json or {}
    conn = get_db()
    cur = conn.cursor()
    
    alim_id = data.get('aliment_id')
    type_mvt = data.get('type_mouvement') # 'entree_achat', 'sortie_distribution'
    qte = float(data.get('quantite_kg', 0))
    date_m = data.get('date_mouvement') or str(datetime.now().date())
    espece = data.get('espece_destinee', 'volaille')
    lot_dest = data.get('lot_destine', '')
    cout = float(data.get('cout_total', 0))
    notes = data.get('notes', '')
    
    cur.execute("""
    INSERT INTO aliments_mouvements (aliment_id, date_mouvement, type_mouvement, quantite_kg, espece_destinee, lot_destine, cout_total, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (alim_id, date_m, type_mvt, qte, espece, lot_dest, cout, notes))
    
    if type_mvt.startswith('entree'):
        cur.execute("UPDATE aliments SET stock_actuel_kg = stock_actuel_kg + ? WHERE id = ?", (qte, alim_id))
    else:
        cur.execute("UPDATE aliments SET stock_actuel_kg = MAX(0, stock_actuel_kg - ?) WHERE id = ?", (qte, alim_id))
        
    conn.commit()
    log_audit("Aliments", "Mouvement", f"Mouvement {type_mvt} ({qte} kg) pour aliment #{alim_id}")
    conn.close()
    return jsonify({'success': True})

# --- MODULE 8: FORMULES ALIMENTAIRES ---
@app.route('/api/formules', methods=['GET', 'POST'])
def manage_formules():
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'GET':
        cur.execute("SELECT * FROM formules_alimentaires ORDER BY id ASC")
        formules = [dict(r) for r in cur.fetchall()]
        for f in formules:
            cur.execute("SELECT * FROM formule_ingredients WHERE formule_id = ?", (f['id'],))
            f['ingredients'] = [dict(i) for i in cur.fetchall()]
        conn.close()
        return jsonify(formules)
        
    data = request.json or {}
    ingredients = data.get('ingredients', [])
    
    # Calculate cost per kg
    cout_kg = sum((float(i.get('proportion_pct', 0)) / 100.0) * float(i.get('prix_kg', 0)) for i in ingredients)
    cout_sac = cout_kg * 50
    
    cur.execute("""
    INSERT INTO formules_alimentaires (nom, espece, phase, description, cout_revient_kg, cout_sac_50kg)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (data.get('nom'), data.get('espece', 'volaille_chair'), data.get('phase', 'croissance'), data.get('description', ''), round(cout_kg, 2), round(cout_sac, 2)))
    f_id = cur.lastrowid
    
    for ing in ingredients:
        cur.execute("""
        INSERT INTO formule_ingredients (formule_id, nom_ingredient, proportion_pct, prix_kg)
        VALUES (?, ?, ?, ?)
        """, (f_id, ing.get('nom_ingredient'), float(ing.get('proportion_pct', 0)), float(ing.get('prix_kg', 0))))
        
    conn.commit()
    log_audit("Formules", "Création Recette", f"Nouvelle formule créée: {data.get('nom')} (Coût: {cout_kg:.1f} FCFA/kg)")
    conn.close()
    return jsonify({'success': True, 'id': f_id}), 201

@app.route('/api/formules/<int:f_id>/fabriquer', methods=['POST'])
def fabriquer_ration(f_id):
    # Mixing/producing a batch of feed from raw materials
    data = request.json or {}
    qte_a_fabriquer_kg = float(data.get('quantite_kg', 100))
    nom_aliment_stock = data.get('nom_aliment_stock', 'Aliment Fabriqué Maison')
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM formules_alimentaires WHERE id = ?", (f_id,))
    formule = cur.fetchone()
    if not formule:
        conn.close()
        return jsonify({'error': 'Formule introuvable'}), 404
        
    cur.execute("SELECT * FROM formule_ingredients WHERE formule_id = ?", (f_id,))
    ingredients = cur.fetchall()
    
    ingredients_utilises = []
    for ing in ingredients:
        qte_ing = (ing['proportion_pct'] / 100.0) * qte_a_fabriquer_kg
        ingredients_utilises.append({
            'nom': ing['nom_ingredient'],
            'quantite_kg': round(qte_ing, 2),
            'cout_partiel': round(qte_ing * ing['prix_kg'], 2)
        })
        
    # Add to stock
    code_alim = f"ALIM-FAB-{f_id}"
    cur.execute("SELECT id FROM aliments WHERE code = ?", (code_alim,))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE aliments SET stock_actuel_kg = stock_actuel_kg + ? WHERE id = ?", (qte_a_fabriquer_kg, row['id']))
        target_alim_id = row['id']
    else:
        cur.execute("""
        INSERT INTO aliments (code, nom, categorie, stock_actuel_kg, seuil_alerte_kg, prix_unitaire_kg)
        VALUES (?, ?, 'mixte', ?, 100, ?)
        """, (code_alim, f"{formule['nom']} (Fabrication Interne)", qte_a_fabriquer_kg, formule['cout_revient_kg']))
        target_alim_id = cur.lastrowid
        
    # Log movement
    cur.execute("""
    INSERT INTO aliments_mouvements (aliment_id, date_mouvement, type_mouvement, quantite_kg, espece_destinee, cout_total, notes)
    VALUES (?, ?, 'entree_fabrication', ?, 'stock', ?, ?)
    """, (target_alim_id, str(datetime.now().date()), qte_a_fabriquer_kg, qte_a_fabriquer_kg * formule['cout_revient_kg'], f"Fabrication ration {formule['nom']}"))
    
    conn.commit()
    log_audit("Formules", "Fabrication", f"Fabrication de {qte_a_fabriquer_kg} kg de '{formule['nom']}'")
    conn.close()
    
    return jsonify({
        'success': True,
        'quantite_fabriquee': qte_a_fabriquer_kg,
        'cout_total': round(qte_a_fabriquer_kg * formule['cout_revient_kg'], 2),
        'ingredients_consommes': ingredients_utilises
    })

# --- MODULE 9: STOCKS CONSOLIDÉS ---
@app.route('/api/stocks', methods=['GET', 'POST'])
def manage_stocks():
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'GET':
        cur.execute("""
        SELECT *, (quantite_stock * prix_unitaire) as valeur_stock
        FROM stocks_articles
        ORDER BY categorie ASC, id ASC
        """)
        rows = [dict(r) for r in cur.fetchall()]
        
        cur.execute("SELECT COALESCE(SUM(quantite_stock * prix_unitaire), 0) FROM stocks_articles")
        valeur_totale = cur.fetchone()[0]
        
        cur.execute("SELECT * FROM stocks_mouvements ORDER BY date_mouvement DESC, id DESC LIMIT 25")
        mouvements = [dict(r) for r in cur.fetchall()]
        
        conn.close()
        return jsonify({
            'articles': rows,
            'valeur_totale': valeur_totale,
            'mouvements': mouvements
        })
        
    data = request.json or {}
    cur.execute("""
    INSERT INTO stocks_articles (code, designation, categorie, unite, quantite_stock, seuil_alerte, prix_unitaire, emplacement)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (data.get('code'), data.get('designation'), data.get('categorie', 'aliment'), data.get('unite', 'kg'), float(data.get('quantite_stock', 0)), float(data.get('seuil_alerte', 10)), float(data.get('prix_unitaire', 0)), data.get('emplacement', '')))
    new_id = cur.lastrowid
    conn.commit()
    log_audit("Stocks", "Nouvel Article", f"Article {data.get('designation')} ajouté au catalogue stock")
    conn.close()
    return jsonify({'success': True, 'id': new_id}), 201

@app.route('/api/stocks/mouvement', methods=['POST'])
def stock_mouvement():
    data = request.json or {}
    conn = get_db()
    cur = conn.cursor()
    
    article_id = data.get('article_id')
    type_mvt = data.get('type_mouvement') # 'entree', 'sortie', 'inventaire'
    qte = float(data.get('quantite', 0))
    motif = data.get('motif', '')
    
    cur.execute("SELECT * FROM stocks_articles WHERE id = ?", (article_id,))
    art = cur.fetchone()
    if not art:
        conn.close()
        return jsonify({'error': 'Article introuvable'}), 404
        
    if type_mvt == 'entree':
        cur.execute("UPDATE stocks_articles SET quantite_stock = quantite_stock + ? WHERE id = ?", (qte, article_id))
    elif type_mvt == 'sortie':
        cur.execute("UPDATE stocks_articles SET quantite_stock = MAX(0, quantite_stock - ?) WHERE id = ?", (qte, article_id))
    elif type_mvt == 'inventaire':
        cur.execute("UPDATE stocks_articles SET quantite_stock = ? WHERE id = ?", (qte, article_id))
        
    cur.execute("""
    INSERT INTO stocks_mouvements (article_id, date_mouvement, type_mouvement, quantite, cout_unitaire, motif, utilisateur_nom)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (article_id, str(datetime.now().date()), type_mvt, qte, art['prix_unitaire'], motif, CURRENT_SESSION['nom_complet']))
    
    conn.commit()
    log_audit("Stocks", "Mouvement", f"Mouvement {type_mvt} ({qte}) sur {art['designation']}")
    conn.close()
    return jsonify({'success': True})

# --- MODULE 10: SUIVI SANITAIRE (SANTÉ) ---
@app.route('/api/sante/interventions', methods=['GET', 'POST'])
def manage_sante_interventions():
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'GET':
        cur.execute("SELECT * FROM sante_interventions ORDER BY date_intervention DESC, id DESC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(rows)
        
    data = request.json or {}
    cur.execute("""
    INSERT INTO sante_interventions (date_intervention, espece, lot_type, lot_id, lot_nom, type_intervention, nom_produit, posologie, cause_pathologie, delai_attente_jours, intervenant, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data.get('date_intervention') or str(datetime.now().date()), data.get('espece', 'volaille'), data.get('lot_type', ''), data.get('lot_id'), data.get('lot_nom', ''), data.get('type_intervention', 'vaccination'), data.get('nom_produit', ''), data.get('posologie', ''), data.get('cause_pathologie', ''), int(data.get('delai_attente_jours', 0)), data.get('intervenant', CURRENT_SESSION['nom_complet']), data.get('notes', '')))
    new_id = cur.lastrowid
    conn.commit()
    log_audit("Santé", "Intervention", f"Acte sanitaire enregistré : {data.get('type_intervention')} ({data.get('nom_produit')})")
    conn.close()
    return jsonify({'success': True, 'id': new_id}), 201

@app.route('/api/sante/prophylaxie', methods=['GET', 'POST'])
def manage_prophylaxie():
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'GET':
        cur.execute("SELECT * FROM sante_programme_prophylaxie ORDER BY espece ASC, id ASC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(rows)
        
    data = request.json or {}
    cur.execute("""
    INSERT INTO sante_programme_prophylaxie (espece, age_recommande, libelle, vaccin_produit, mode_administration, statut)
    VALUES (?, ?, ?, ?, ?, 'a_prevoir')
    """, (data.get('espece', 'volaille_chair'), data.get('age_recommande'), data.get('libelle'), data.get('vaccin_produit'), data.get('mode_administration', '')))
    new_id = cur.lastrowid
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'id': new_id}), 201

@app.route('/api/sante/prophylaxie/<int:prop_id>/toggle', methods=['PUT'])
def toggle_prophylaxie(prop_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT statut FROM sante_programme_prophylaxie WHERE id = ?", (prop_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return jsonify({'error': 'Introuvable'}), 404
        
    new_statut = 'fait' if row['statut'] != 'fait' else 'a_prevoir'
    cur.execute("UPDATE sante_programme_prophylaxie SET statut = ? WHERE id = ?", (new_statut, prop_id))
    conn.commit()
    log_audit("Santé", "Prophylaxie", f"Statut prophylaxie #{prop_id} passé à '{new_statut}'")
    conn.close()
    return jsonify({'success': True, 'statut': new_statut})

# --- MODULE 11: CLIENTS ---
@app.route('/api/clients', methods=['GET', 'POST'])
def manage_clients():
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'GET':
        cur.execute("SELECT * FROM clients ORDER BY solde_du DESC, nom_complet ASC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(rows)
        
    data = request.json or {}
    code = data.get('code') or f"CLI-{datetime.now().strftime('%m%d%H%M')}"
    cur.execute("""
    INSERT INTO clients (code, nom_complet, type_client, telephone, email, adresse, ville, limite_credit, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (code, data.get('nom_complet'), data.get('type_client', 'particulier'), data.get('telephone', ''), data.get('email', ''), data.get('adresse', ''), data.get('ville', 'Diégonefla'), float(data.get('limite_credit', 500000)), data.get('notes', '')))
    new_id = cur.lastrowid
    conn.commit()
    log_audit("Clients", "Nouveau Client", f"Client {data.get('nom_complet')} enregistré")
    conn.close()
    return jsonify({'success': True, 'id': new_id}), 201

@app.route('/api/clients/<int:cli_id>', methods=['GET', 'PUT', 'DELETE'])
def detail_client(cli_id):
    conn = get_db()
    cur = conn.cursor()
    
    if request.method == 'DELETE':
        cur.execute("DELETE FROM clients WHERE id = ?", (cli_id,))
        conn.commit()
        log_audit("Clients", "Suppression", f"Fiche client #{cli_id} supprimée")
        conn.close()
        return jsonify({'success': True})

    if request.method == 'PUT':
        data = request.json or {}
        cur.execute("""
        UPDATE clients
        SET nom_complet = ?, type_client = ?, telephone = ?, email = ?, adresse = ?, ville = ?, limite_credit = ?, statut = ?, notes = ?
        WHERE id = ?
        """, (data.get('nom_complet'), data.get('type_client'), data.get('telephone'), data.get('email'), data.get('adresse'), data.get('ville'), float(data.get('limite_credit', 500000)), data.get('statut', 'actif'), data.get('notes', ''), cli_id))
        conn.commit()
        log_audit("Clients", "Modification", f"Fiche client #{cli_id} modifiée")
        conn.close()
        return jsonify({'success': True})

    # GET
    cur.execute("SELECT * FROM clients WHERE id = ?", (cli_id,))
    client = cur.fetchone()
    if not client:
        conn.close()
        return jsonify({'error': 'Client introuvable'}), 404
        
    cur.execute("SELECT * FROM ventes WHERE client_id = ? ORDER BY date_vente DESC", (cli_id,))
    ventes = [dict(v) for v in cur.fetchall()]
    
    cur.execute("SELECT * FROM reglements_clients WHERE client_id = ? ORDER BY date_reglement DESC", (cli_id,))
    reglements = [dict(r) for r in cur.fetchall()]
    
    conn.close()
    res = dict(client)
    res['ventes'] = ventes
    res['reglements'] = reglements
    return jsonify(res)

@app.route('/api/clients/<int:cli_id>/reglement', methods=['POST'])
def add_client_reglement(cli_id):
    data = request.json or {}
    montant = float(data.get('montant', 0))
    mode = data.get('mode_paiement', 'especes')
    ref = data.get('reference', 'ENCAISS-DIRECT')
    date_reg = data.get('date_reglement') or str(datetime.now().date())
    vente_id = data.get('vente_id')
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
    INSERT INTO reglements_clients (vente_id, client_id, date_reglement, montant, mode_paiement, reference, encaisse_par)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (vente_id, cli_id, date_reg, montant, mode, ref, CURRENT_SESSION['nom_complet']))
    
    # Deduct from client solde_du
    cur.execute("UPDATE clients SET solde_du = MAX(0, solde_du - ?) WHERE id = ?", (montant, cli_id))
    
    # If linked to specific sale, update sale regle & restant
    if vente_id:
        cur.execute("UPDATE ventes SET montant_regle = montant_regle + ?, montant_restant = MAX(0, montant_restant - ?) WHERE id = ?", (montant, montant, vente_id))
        cur.execute("SELECT montant_restant FROM ventes WHERE id = ?", (vente_id,))
        rest = cur.fetchone()[0]
        st = 'paye' if rest == 0 else 'acompte'
        cur.execute("UPDATE ventes SET statut_paiement = ? WHERE id = ?", (st, vente_id))
        
    conn.commit()
    log_audit("Finances", "Encaissement", f"Encaissement de {montant:,.0f} FCFA pour le client #{cli_id}".replace(',', ' '))
    conn.close()
    return jsonify({'success': True})

# --- MODULE 12: VENTES ---
@app.route('/api/ventes', methods=['GET', 'POST'])
def manage_ventes():
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'GET':
        cur.execute("""
        SELECT v.*, c.telephone as client_telephone
        FROM ventes v
        LEFT JOIN clients c ON v.client_id = c.id
        ORDER BY v.date_vente DESC, v.id DESC
        """)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(rows)
        
    data = request.json or {}
    lignes = data.get('lignes', [])
    if not lignes:
        conn.close()
        return jsonify({'error': 'Veuillez ajouter au moins une ligne de produit.'}), 400
        
    num_fac = data.get('numero_facture') or f"FAC-{datetime.now().strftime('%Y-%m%d%H%M')}"
    client_id = data.get('client_id')
    client_nom = data.get('client_nom', 'Client Comptoir')
    date_v = data.get('date_vente') or str(datetime.now().date())
    remise = float(data.get('remise', 0))
    mode_p = data.get('mode_paiement', 'especes')
    regle = float(data.get('montant_regle', 0))
    echeance = data.get('date_echeance')
    notes = data.get('notes', '')
    
    brut = sum(float(l.get('quantite', 1)) * float(l.get('prix_unitaire', 0)) for l in lignes)
    net = max(0, brut - remise)
    restant = max(0, net - regle)
    
    statut_p = 'paye' if restant == 0 else ('acompte' if regle > 0 else 'impaye')
    
    cur.execute("""
    INSERT INTO ventes (numero_facture, client_id, client_nom, date_vente, montant_brut, remise, montant_net, montant_regle, montant_restant, mode_paiement, statut_paiement, date_echeance, notes, created_by)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (num_fac, client_id, client_nom, date_v, brut, remise, net, regle, restant, mode_p, statut_p, echeance, notes, CURRENT_SESSION['nom_complet']))
    vente_id = cur.lastrowid
    
    for l in lignes:
        qte = float(l.get('quantite', 1))
        pu = float(l.get('prix_unitaire', 0))
        st = qte * pu
        cur.execute("""
        INSERT INTO vente_lignes (vente_id, designation, type_produit, quantite, unite, prix_unitaire, sous_total, lot_source_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (vente_id, l.get('designation'), l.get('type_produit', 'autre'), qte, l.get('unite', 'unite'), pu, st, l.get('lot_source_id')))
        
        # Deduct from corresponding lots or egg stock
        tp = l.get('type_produit')
        if tp == 'oeufs_plateau':
            cur.execute("UPDATE stocks_articles SET quantite_stock = MAX(0, quantite_stock - ?) WHERE code = 'STK-OEUF-01'", (qte,))
            cur.execute("INSERT INTO oeufs_mouvements (date_mouvement, type_mouvement, quantite, reference, notes) VALUES (?, 'sortie_vente', ?, ?, 'Vente client')", (date_v, int(qte*30), num_fac))
        elif tp in ('poulet_vif', 'poulet_pac') and l.get('lot_source_id'):
            cur.execute("UPDATE lots_volailles SET effectif_actuel = MAX(0, effectif_actuel - ?) WHERE id = ?", (int(qte), l.get('lot_source_id')))
        elif tp in ('lapin_vif', 'lapin_decoupe') and l.get('lot_source_id'):
            cur.execute("UPDATE lots_lapins SET effectif = MAX(0, effectif - ?) WHERE id = ?", (int(qte), l.get('lot_source_id')))

    # If sale not fully paid, increase client solde_du
    if client_id and restant > 0:
        cur.execute("UPDATE clients SET solde_du = solde_du + ? WHERE id = ?", (restant, client_id))
        
    # Log payment if regle > 0
    if regle > 0 and client_id:
        cur.execute("""
        INSERT INTO reglements_clients (vente_id, client_id, date_reglement, montant, mode_paiement, reference, encaisse_par)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (vente_id, client_id, date_v, regle, mode_p, f"ACPT-{num_fac}", CURRENT_SESSION['nom_complet']))

    conn.commit()
    log_audit("Ventes", "Nouvelle Vente", f"Facture {num_fac} ({net:,.0f} FCFA) émise pour {client_nom}".replace(',', ' '))
    conn.close()
    return jsonify({'success': True, 'id': vente_id, 'numero_facture': num_fac}), 201

@app.route('/api/ventes/<int:vente_id>', methods=['GET'])
def get_vente_details(vente_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    SELECT v.*, c.telephone as client_telephone, c.adresse as client_adresse, c.ville as client_ville
    FROM ventes v
    LEFT JOIN clients c ON v.client_id = c.id
    WHERE v.id = ?
    """, (vente_id,))
    vente = cur.fetchone()
    if not vente:
        conn.close()
        return jsonify({'error': 'Vente introuvable'}), 404
        
    cur.execute("SELECT * FROM vente_lignes WHERE vente_id = ?", (vente_id,))
    lignes = [dict(r) for r in cur.fetchall()]
    
    cur.execute("SELECT * FROM reglements_clients WHERE vente_id = ?", (vente_id,))
    reglements = [dict(r) for r in cur.fetchall()]
    
    conn.close()
    res = dict(vente)
    res['lignes'] = lignes
    res['reglements'] = reglements
    return jsonify(res)

# --- MODULE 13: DÉPENSES & ACHATS ---
@app.route('/api/depenses', methods=['GET', 'POST'])
def manage_depenses():
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'GET':
        cur.execute("SELECT * FROM depenses ORDER BY date_depense DESC, id DESC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return jsonify(rows)
        
    data = request.json or {}
    ref = data.get('reference') or f"DEP-{datetime.now().strftime('%Y-%m%d%H%M')}"
    date_d = data.get('date_depense') or str(datetime.now().date())
    cat = data.get('categorie', 'divers')
    libelle = data.get('libelle', '')
    fournisseur = data.get('fournisseur', '')
    montant = float(data.get('montant', 0))
    mode_p = data.get('mode_paiement', 'especes')
    num_p = data.get('num_piece', '')
    notes = data.get('notes', '')
    
    cur.execute("""
    INSERT INTO depenses (reference, date_depense, categorie, libelle, fournisseur, montant, mode_paiement, num_piece, notes, created_by)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ref, date_d, cat, libelle, fournisseur, montant, mode_p, num_p, notes, CURRENT_SESSION['nom_complet']))
    new_id = cur.lastrowid
    conn.commit()
    log_audit("Dépenses", "Nouvelle Dépense", f"Dépense {ref} ({montant:,.0f} FCFA) - {libelle}".replace(',', ' '))
    conn.close()
    return jsonify({'success': True, 'id': new_id}), 201

@app.route('/api/depenses/<int:dep_id>', methods=['DELETE'])
def delete_depense(dep_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM depenses WHERE id = ?", (dep_id,))
    conn.commit()
    log_audit("Dépenses", "Suppression", f"Dépense #{dep_id} supprimée")
    conn.close()
    return jsonify({'success': True})

# --- MODULE 14: RAPPORTS & PARAMÈTRES ---
@app.route('/api/parametres', methods=['GET', 'POST'])
def manage_parametres():
    conn = get_db()
    cur = conn.cursor()
    if request.method == 'GET':
        cur.execute("SELECT cle, valeur, description FROM parametres")
        params = {r['cle']: r['valeur'] for r in cur.fetchall()}
        conn.close()
        return jsonify(params)
        
    data = request.json or {}
    for k, v in data.items():
        cur.execute("INSERT INTO parametres (cle, valeur) VALUES (?, ?) ON CONFLICT(cle) DO UPDATE SET valeur = excluded.valeur", (k, str(v)))
    conn.commit()
    log_audit("Paramètres", "Mise à jour", "Paramètres généraux de l'exploitation modifiés")
    conn.close()
    return jsonify({'success': True})

@app.route('/api/rapports/excel', methods=['GET'])
def download_excel_report():
    out_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(out_dir, exist_ok=True)
    filename = f"Rapport_DFM_Diegonefla_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    out_path = os.path.join(out_dir, filename)
    generate_excel_report(DB_PATH, out_path)
    log_audit("Rapports", "Export Excel", f"Génération du fichier {filename}")
    return send_file(out_path, as_attachment=True, download_name=filename)

@app.route('/api/backup', methods=['GET'])
def backup_database():
    conn = get_db()
    cur = conn.cursor()
    
    # Export all tables as JSON dump
    tables = [
        'parametres', 'utilisateurs', 'lots_volailles', 'volailles_pesees', 'volailles_mortalites',
        'lots_lapins', 'lapins_reproducteurs', 'lapins_reproductions', 'lapins_mortalites',
        'oeufs_pontes', 'oeufs_mouvements', 'incubations', 'aliments', 'aliments_mouvements',
        'formules_alimentaires', 'formule_ingredients', 'stocks_articles', 'stocks_mouvements',
        'sante_interventions', 'sante_programme_prophylaxie', 'clients', 'ventes', 'vente_lignes',
        'reglements_clients', 'depenses', 'audit_logs'
    ]
    dump = {'version': '1.0', 'exported_at': datetime.now().isoformat(), 'tables': {}}
    for tbl in tables:
        cur.execute(f"SELECT * FROM {tbl}")
        dump['tables'][tbl] = [dict(r) for r in cur.fetchall()]
        
    conn.close()
    log_audit("Système", "Sauvegarde", "Sauvegarde complète JSON de la ferme téléchargée")
    return jsonify(dump)

@app.route('/api/reset-demo', methods=['POST'])
def reset_demo():
    init_db(force_reseed=True)
    log_audit("Système", "Réinitialisation Démo", "Base de données réinitialisée avec le jeu de test Diégonefla")
    return jsonify({'success': True, 'message': 'Données de test réinitialisées avec succès.'})

@app.route('/api/audit', methods=['GET'])
def get_audit_logs():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM audit_logs ORDER BY date_action DESC LIMIT 60")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(rows)

if __name__ == '__main__':
    init_db()
    # Bind to 0.0.0.0 as required by system prompt
    app.run(host='0.0.0.0', port=5000, debug=False)
