// =========================================================================
// APPLICATION DFM — LA FERME DE DIÉGONEFLA
// Client-side Application Controller
// =========================================================================

const app = {
    currentView: 'dashboard',
    userRole: 'admin',
    permissions: {},
    allClients: [],
    allLotsVolailles: [],
    allLotsLapins: [],
    allAliments: [],
    
    // Initialisation
    init() {
        this.setupNavigation();
        this.setupEventListeners();
        this.setDefaultDates();
        this.checkAuth();
        this.showView('dashboard');
    },

    // Formatters
    formatFCFA(val) {
        if (val === null || val === undefined) return '0 FCFA';
        return Number(val).toLocaleString('fr-FR') + ' FCFA';
    },

    formatNumber(val) {
        if (val === null || val === undefined) return '0';
        return Number(val).toLocaleString('fr-FR');
    },

    toast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `<span>${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span> <span>${message}</span>`;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    },

    // Navigation setup
    setupNavigation() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const view = item.getAttribute('data-view');
                if (view) {
                    this.showView(view);
                    // Close mobile sidebar if open
                    document.getElementById('sidebar').classList.remove('open');
                }
            });
        });

        // Mobile toggle
        const mobBtn = document.getElementById('mobile-menu-btn');
        if (mobBtn) {
            mobBtn.addEventListener('click', () => {
                document.getElementById('sidebar').classList.toggle('open');
            });
        }

        // Role switcher
        const roleSel = document.getElementById('role-select');
        if (roleSel) {
            roleSel.addEventListener('change', (e) => {
                this.switchRole(e.target.value);
            });
        }

        // Quick actions in header
        document.getElementById('btn-quick-sale')?.addEventListener('click', () => {
            this.openModal('modal-nouvelle-vente');
        });
        document.getElementById('btn-quick-excel')?.addEventListener('click', () => {
            window.location.href = '/api/rapports/excel';
        });
    },

    setupEventListeners() {
        // Close modal on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'));
            }
        });
    },

    setDefaultDates() {
        const todayStr = new Date().toISOString().split('T')[0];
        const dateInputs = [
            'vente-date', 'lot-volaille-date-entree', 'pesee-date', 'mortalite-date',
            'ponte-date', 'incub-date-mise', 'depense-date', 'reglement-date'
        ];
        dateInputs.forEach(id => {
            const el = document.getElementById(id);
            if (el) el.value = todayStr;
        });
    },

    // Auth & Permissions Matrix (Cahier des charges section 6)
    async checkAuth() {
        try {
            const res = await fetch('/api/me');
            const data = await res.json();
            this.userRole = data.user.role;
            this.permissions = data.permissions;
            
            const roleSel = document.getElementById('role-select');
            if (roleSel) roleSel.value = this.userRole;
            
            this.applyPermissionsUI();
        } catch (e) {
            console.error('Erreur auth:', e);
        }
    },

    async switchRole(role) {
        try {
            const res = await fetch('/api/switch-role', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ role })
            });
            const data = await res.json();
            if (data.success) {
                this.userRole = data.user.role;
                this.permissions = data.permissions;
                this.applyPermissionsUI();
                this.toast(`Profil basculé sur : ${data.user.nom_complet}`, 'info');
                
                // If current view is no longer accessible, redirect to dashboard
                const currentPerm = this.permissions[this.currentView];
                if (currentPerm === 'aucun') {
                    this.showView('dashboard');
                } else {
                    this.loadViewData(this.currentView);
                }
            }
        } catch (e) {
            this.toast('Erreur lors du changement de profil', 'error');
        }
    },

    applyPermissionsUI() {
        // Enforce sidebar items accessibility
        document.querySelectorAll('.nav-item').forEach(item => {
            const mod = item.getAttribute('data-module');
            if (!mod) return;
            const perm = this.permissions[mod];
            if (perm === 'aucun') {
                item.classList.add('restricted');
                item.setAttribute('title', 'Accès non autorisé pour ce profil (Matrice Section 6)');
            } else {
                item.classList.remove('restricted');
                item.removeAttribute('title');
            }
        });

        // Toggle write buttons based on permission
        const currentPerm = this.permissions[this.currentView] || 'total';
        const isReadOnly = (currentPerm === 'lecture');
        
        document.querySelectorAll('.btn-ecriture').forEach(btn => {
            btn.style.display = isReadOnly ? 'none' : '';
        });
        
        // Hide quick new sale button in header if no sales access
        const quickSaleBtn = document.getElementById('btn-quick-sale');
        if (quickSaleBtn) {
            quickSaleBtn.style.display = (this.permissions['ventes'] === 'ecriture' || this.permissions['ventes'] === 'total') ? '' : 'none';
        }
    },

    // View Switching Router
    showView(viewName) {
        // Check permission
        if (this.permissions[viewName] === 'aucun') {
            this.toast("Accès restreint pour votre rôle selon la matrice du cahier des charges.", 'error');
            return;
        }

        this.currentView = viewName;

        // Update nav active state
        document.querySelectorAll('.nav-item').forEach(item => {
            if (item.getAttribute('data-view') === viewName) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // Hide all views, show current
        document.querySelectorAll('.app-view').forEach(view => {
            view.classList.remove('active');
            view.style.display = 'none';
        });

        const activeSec = document.getElementById(`view-${viewName}`);
        if (activeSec) {
            activeSec.classList.add('active');
            activeSec.style.display = 'block';
        }

        // Update header texts
        const titles = {
            'dashboard': ['Tableau de bord', "Vue d'ensemble en temps réel des activités de la ferme"],
            'volailles': ['Élevage Volailles (Poulets)', 'Suivi des lots, croissance, mortalité et cheptel de poulets'],
            'lapins': ['Élevage Cunicole (Lapins)', 'Suivi des reproducteurs, saillies, naissances et engraissement'],
            'oeufs': ['Gestion des Œufs', "Production journalière, classification par calibre et gestion des stocks"],
            'incubation': ['Incubation & Couveuses', "Mises en couveuse, mirage et éclosions avec rattachement aux lots"],
            'aliments': ['Gestion des Aliments', "Stock disponible en kilogrammes, alertes de seuil et distributions"],
            'formules': ['Formules Alimentaires', "Composition des rations locales et calcul automatique du coût de revient"],
            'stocks': ['Stocks Consolidés', "Inventaire centralisé, mouvements et valorisation totale du stock"],
            'sante': ['Suivi Sanitaire & Prophylaxie', "Actes vétérinaires, calendrier prophylactique et alertes de mortalité"],
            'clients': ['Gestion des Clients', "Fiches clients, historique des achats et suivi des créances"],
            'ventes': ['Gestion des Ventes & Factures', "Enregistrement des ventes, facturation et suivi des encaissements"],
            'depenses': ['Dépenses & Achats', "Suivi des charges, approvisionnements et calcul du résultat net"],
            'utilisateurs': ['Utilisateurs & Sécurité', "Gestion des accès et journal de traçabilité des opérations"],
            'rapports': ['Rapports & Paramètres', "Exports Excel / PDF et paramétrage de l'exploitation"]
        };

        const [t, d] = titles[viewName] || ['Gestion Ferme DFM', 'La Ferme de Diégonefla'];
        document.getElementById('current-view-title').innerText = t;
        document.getElementById('current-view-desc').innerText = d;

        this.applyPermissionsUI();
        this.loadViewData(viewName);
    },

    loadViewData(viewName) {
        switch (viewName) {
            case 'dashboard': this.loadDashboard(); break;
            case 'volailles': this.loadVolailles(); break;
            case 'lapins': this.loadLapins(); break;
            case 'oeufs': this.loadOeufs(); break;
            case 'incubation': this.loadIncubation(); break;
            case 'aliments': this.loadAliments(); break;
            case 'formules': this.loadFormules(); break;
            case 'stocks': this.loadStocks(); break;
            case 'sante': this.loadSante(); break;
            case 'clients': this.loadClients(); break;
            case 'ventes': this.loadVentes(); break;
            case 'depenses': this.loadDepenses(); break;
            case 'utilisateurs': this.loadUtilisateurs(); break;
            case 'rapports': this.loadParametres(); break;
        }
    },

    // =========================================================================
    // MODULE 2: TABLEAU DE BORD (DASHBOARD)
    // =========================================================================
    async loadDashboard() {
        try {
            const res = await fetch('/api/dashboard/stats');
            const data = await res.json();
            
            // 10 KPIs exacts
            document.getElementById('kpi-poulets').innerText = this.formatNumber(data.kpis.poulets);
            document.getElementById('kpi-lapins').innerText = this.formatNumber(data.kpis.lapins);
            document.getElementById('kpi-oeufs').innerText = this.formatNumber(data.kpis.oeufs_disponibles);
            document.getElementById('kpi-oeufs-plateaux').innerText = `${data.kpis.oeufs_plateaux} plateaux de 30`;
            document.getElementById('kpi-lots').innerText = data.kpis.lots_actifs;
            document.getElementById('kpi-reproducteurs').innerText = data.kpis.reproducteurs;
            document.getElementById('kpi-aliment').innerText = `${this.formatNumber(data.kpis.stock_aliment_kg)} kg`;
            document.getElementById('kpi-ca').innerText = this.formatFCFA(data.kpis.ca_mois);
            document.getElementById('kpi-depenses').innerText = this.formatFCFA(data.kpis.depenses_mois);
            document.getElementById('kpi-benefice').innerText = this.formatFCFA(data.kpis.benefice_mois);
            document.getElementById('kpi-creances').innerText = this.formatFCFA(data.kpis.creances_clients);

            // Badges in sidebar
            const bP = document.getElementById('badge-poulets');
            if (bP) bP.innerText = data.kpis.poulets;
            const bL = document.getElementById('badge-lapins');
            if (bL) bL.innerText = data.kpis.lapins;
            const bO = document.getElementById('badge-oeufs');
            if (bO) bO.innerText = `${data.kpis.oeufs_plateaux} pl`;

            // Automatic alerts
            this.renderAlerts(data.alerts);

            // Canvas charts
            this.renderEvolutionChart(data.charts.labels, data.charts.ventes, data.charts.depenses);
            this.renderProductBreakdownChart(data.charts.ventes_par_produit);

            // Recent sales
            this.loadRecentSales();

        } catch (e) {
            console.error('Erreur chargement dashboard:', e);
        }
    },

    renderAlerts(alerts) {
        const container = document.getElementById('alerts-container');
        if (!container) return;
        container.innerHTML = '';
        
        if (!alerts || alerts.length === 0) return;
        
        alerts.forEach(al => {
            const banner = document.createElement('div');
            banner.className = `alert-banner ${al.niveau}`;
            banner.innerHTML = `
                <div class="alert-text-group">
                    <span style="font-size: 1.1rem;">⚠️</span>
                    <div>
                        <strong>${al.titre}</strong> — <span>${al.message}</span>
                    </div>
                </div>
                <button class="alert-action-btn" onclick="app.showView('${al.action_link}')">Consulter →</button>
            `;
            container.appendChild(banner);
        });
    },

    renderEvolutionChart(labels, ventes, depenses) {
        const canvas = document.getElementById('canvas-evolution');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const dpr = window.devicePixelRatio || 1;
        
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);
        
        const width = rect.width;
        const height = rect.height;
        ctx.clearRect(0, 0, width, height);

        const padLeft = 70;
        const padBottom = 30;
        const padTop = 30;
        const padRight = 20;
        const chartW = width - padLeft - padRight;
        const chartH = height - padTop - padBottom;

        const maxVal = Math.max(...ventes, ...depenses, 1000000) * 1.15;

        // Draw horizontal grid lines
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 1;
        ctx.fillStyle = '#64748b';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'right';

        const gridSteps = 4;
        for (let i = 0; i <= gridSteps; i++) {
            const y = padTop + chartH - (i / gridSteps) * chartH;
            const val = (i / gridSteps) * maxVal;
            ctx.beginPath();
            ctx.moveTo(padLeft, y);
            ctx.lineTo(width - padRight, y);
            ctx.stroke();
            ctx.fillText(Math.round(val / 1000) + 'k F', padLeft - 8, y + 3);
        }

        // Draw Bars for Dépenses
        const n = labels.length;
        const barWidth = (chartW / n) * 0.3;
        const groupW = chartW / n;

        labels.forEach((label, i) => {
            const groupX = padLeft + i * groupW + groupW / 2;
            
            // X label
            ctx.fillStyle = '#475569';
            ctx.font = '11px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(label, groupX, height - 8);

            // Bar Dépenses (Rouge/Orange clair)
            const depH = (depenses[i] / maxVal) * chartH;
            ctx.fillStyle = '#f87171';
            ctx.beginPath();
            ctx.roundRect(groupX - barWidth - 2, padTop + chartH - depH, barWidth, depH, [4, 4, 0, 0]);
            ctx.fill();

            // Bar Ventes (Vert)
            const vH = (ventes[i] / maxVal) * chartH;
            ctx.fillStyle = '#22c55e';
            ctx.beginPath();
            ctx.roundRect(groupX + 2, padTop + chartH - vH, barWidth, vH, [4, 4, 0, 0]);
            ctx.fill();
        });

        // Legend at top
        ctx.textAlign = 'left';
        // Green
        ctx.fillStyle = '#22c55e';
        ctx.fillRect(padLeft + 10, 8, 12, 12);
        ctx.fillStyle = '#1e293b';
        ctx.font = '11px sans-serif';
        ctx.fillText('Ventes (CA)', padLeft + 28, 18);

        // Red
        ctx.fillStyle = '#f87171';
        ctx.fillRect(padLeft + 120, 8, 12, 12);
        ctx.fillStyle = '#1e293b';
        ctx.fillText('Dépenses', padLeft + 138, 18);
    },

    renderProductBreakdownChart(items) {
        const canvas = document.getElementById('canvas-produits');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const dpr = window.devicePixelRatio || 1;
        
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);
        
        const width = rect.width;
        const height = rect.height;
        ctx.clearRect(0, 0, width, height);

        if (!items || items.length === 0) {
            ctx.fillStyle = '#64748b';
            ctx.font = '12px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('Aucune vente enregistrée', width / 2, height / 2);
            return;
        }

        const total = items.reduce((s, x) => s + x.total, 0);
        const colors = ['#15803d', '#0284c7', '#d97706', '#9333ea', '#e11d48', '#64748b'];
        
        const cx = width / 2 - 40;
        const cy = height / 2;
        const radius = Math.min(cx, cy) - 20;
        let startAngle = -Math.PI / 2;

        items.slice(0, 5).forEach((item, idx) => {
            const sliceAngle = (item.total / total) * 2 * Math.PI;
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.arc(cx, cy, radius, startAngle, startAngle + sliceAngle);
            ctx.closePath();
            ctx.fillStyle = colors[idx % colors.length];
            ctx.fill();

            // Legend item
            const ly = 30 + idx * 24;
            ctx.fillRect(width - 110, ly, 10, 10);
            ctx.fillStyle = '#334155';
            ctx.font = '10px sans-serif';
            ctx.textAlign = 'left';
            const pct = Math.round((item.total / total) * 100);
            const labelClean = (item.type || 'Autre').replace('_', ' ').toUpperCase();
            ctx.fillText(`${labelClean} (${pct}%)`, width - 94, ly + 9);

            startAngle += sliceAngle;
        });

        // Inner circle for Donut effect
        ctx.beginPath();
        ctx.arc(cx, cy, radius * 0.55, 0, 2 * Math.PI);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
    },

    async loadRecentSales() {
        const res = await fetch('/api/ventes');
        const sales = await res.json();
        const tbody = document.querySelector('#dashboard-recent-sales tbody');
        if (!tbody) return;
        tbody.innerHTML = '';
        
        sales.slice(0, 5).forEach(s => {
            const tr = document.createElement('tr');
            const badgeClass = s.statut_paiement === 'paye' ? 'badge-success' : (s.statut_paiement === 'acompte' ? 'badge-warning' : 'badge-danger');
            tr.innerHTML = `
                <td><strong>${s.numero_facture}</strong></td>
                <td>${s.date_vente}</td>
                <td>${s.client_nom}</td>
                <td><strong>${this.formatFCFA(s.montant_net)}</strong></td>
                <td>${this.formatFCFA(s.montant_regle)}</td>
                <td style="color: ${s.montant_restant > 0 ? 'var(--danger)' : 'var(--text-muted)'}">${this.formatFCFA(s.montant_restant)}</td>
                <td><span class="badge ${badgeClass}">${s.statut_paiement}</span></td>
            `;
            tbody.appendChild(tr);
        });
    },

    // =========================================================================
    // MODULE 3: VOLAILLES (POULETS)
    // =========================================================================
    async loadVolailles() {
        const res = await fetch('/api/volailles/lots');
        const lots = await res.json();
        this.allLotsVolailles = lots;
        const tbody = document.querySelector('#table-volailles tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        lots.forEach(lot => {
            const tr = document.createElement('tr');
            const statutBadge = lot.statut === 'en_ponte' ? 'badge-warning' : (lot.statut === 'en_finition' ? 'badge-info' : 'badge-success');
            tr.innerHTML = `
                <td><strong>${lot.code}</strong></td>
                <td>
                    <div style="font-weight: 600;">${lot.nom}</div>
                    <div style="color: var(--text-muted); font-size: 0.78rem;">Souche : ${lot.souche}</div>
                </td>
                <td><span class="badge badge-neutral">${lot.type_production}</span></td>
                <td>${lot.date_entree}</td>
                <td>${this.formatNumber(lot.effectif_initial)}</td>
                <td><strong style="color: var(--primary);">${this.formatNumber(lot.effectif_actuel)}</strong></td>
                <td>${lot.poids_moyen_g ? `${lot.poids_moyen_g} g` : '—'}</td>
                <td>${lot.batiment || '—'}</td>
                <td><span class="badge ${statutBadge}">${lot.statut.replace('_', ' ')}</span></td>
                <td>
                    <button class="btn btn-sm btn-secondary btn-ecriture" onclick="app.openPeseeModal(${lot.id}, '${lot.nom}')">⚖ Pesée</button>
                    <button class="btn btn-sm btn-secondary btn-ecriture" style="color: var(--danger);" onclick="app.openMortaliteModal(${lot.id}, '${lot.nom}')">⚠ Perte</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        this.applyPermissionsUI();
    },

    openPeseeModal(lotId, lotNom) {
        document.getElementById('pesee-lot-id').value = lotId;
        document.getElementById('pesee-lot-nom').value = lotNom;
        this.openModal('modal-pesee-volaille');
    },

    openMortaliteModal(lotId, lotNom) {
        document.getElementById('mortalite-lot-id').value = lotId;
        document.getElementById('mortalite-lot-nom').value = lotNom;
        this.openModal('modal-mortalite-volaille');
    },

    async submitNouveauLotVolaille() {
        const form = document.getElementById('form-nouveau-lot-volaille');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        const res = await fetch('/api/volailles/lots', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            this.toast('Nouveau lot de volailles créé avec succès !');
            this.closeModal('modal-nouveau-lot-volaille');
            form.reset();
            this.loadVolailles();
        } else {
            this.toast('Erreur lors de la création du lot', 'error');
        }
    },

    async submitPesee() {
        const lotId = document.getElementById('pesee-lot-id').value;
        const poids = document.getElementById('pesee-poids').value;
        const dateP = document.getElementById('pesee-date').value;
        const notes = document.getElementById('pesee-notes').value;

        const res = await fetch(`/api/volailles/lots/${lotId}/pesee`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ poids_moyen_g: poids, date_pesee: dateP, notes })
        });
        if (res.ok) {
            this.toast('Pesée enregistrée !');
            this.closeModal('modal-pesee-volaille');
            this.loadVolailles();
        }
    },

    async submitMortalite() {
        const lotId = document.getElementById('mortalite-lot-id').value;
        const qte = document.getElementById('mortalite-qte').value;
        const dateM = document.getElementById('mortalite-date').value;
        const cause = document.getElementById('mortalite-cause').value;

        const res = await fetch(`/api/volailles/lots/${lotId}/mortalite`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quantite: qte, date_mortalite: dateM, cause })
        });
        if (res.ok) {
            this.toast('Mortalité enregistrée et effectif mis à jour.');
            this.closeModal('modal-mortalite-volaille');
            this.loadVolailles();
        }
    },

    // =========================================================================
    // MODULE 4: LAPINS (CUNICOLE)
    // =========================================================================
    switchRabbitTab(tab) {
        document.getElementById('tab-lapins-reproducteurs').style.display = (tab === 'reproducteurs') ? 'block' : 'none';
        document.getElementById('tab-lapins-reproductions').style.display = (tab === 'reproductions') ? 'block' : 'none';
        document.getElementById('tab-lapins-lots').style.display = (tab === 'lots') ? 'block' : 'none';

        document.querySelectorAll('#view-lapins .tab-btn').forEach(btn => btn.classList.remove('active'));
        event.target.classList.add('active');
        this.loadLapins();
    },

    async loadLapins() {
        // 1. Reproducteurs
        const resRep = await fetch('/api/lapins/reproducteurs');
        const repros = await resRep.json();
        const tbodyRep = document.querySelector('#table-reproducteurs tbody');
        if (tbodyRep) {
            tbodyRep.innerHTML = '';
            repros.forEach(r => {
                const tr = document.createElement('tr');
                const badgeClass = r.sexe === 'male' ? 'badge-info' : 'badge-warning';
                const stClass = r.statut === 'gestation' ? 'badge-danger' : 'badge-success';
                tr.innerHTML = `
                    <td><strong>${r.code_tatouage}</strong></td>
                    <td><strong>${r.nom}</strong></td>
                    <td>${r.race}</td>
                    <td><span class="badge ${badgeClass}">${r.sexe.toUpperCase()}</span></td>
                    <td>${r.cage_numero || '—'}</td>
                    <td>${r.date_entree}</td>
                    <td>${r.portees_total}</td>
                    <td><span class="badge ${stClass}">${r.statut}</span></td>
                    <td style="color: var(--text-muted); font-size: 0.78rem;">${r.notes || ''}</td>
                `;
                tbodyRep.appendChild(tr);
            });
        }

        // 2. Reproductions & Saillies
        const resRepro = await fetch('/api/lapins/reproductions');
        const reproductions = await resRepro.json();
        const tbodyS = document.querySelector('#table-reproductions tbody');
        if (tbodyS) {
            tbodyS.innerHTML = '';
            reproductions.forEach(s => {
                const tr = document.createElement('tr');
                let actionBtn = '';
                if (s.statut === 'gestation_confirmee' || s.statut === 'saillie') {
                    actionBtn = `<button class="btn btn-sm btn-primary btn-ecriture" onclick="app.actionMiseBas(${s.id})">🍼 Mise Bas</button>`;
                } else if (s.statut === 'mise_bas_effectuee') {
                    actionBtn = `<button class="btn btn-sm btn-secondary btn-ecriture" onclick="app.actionSevrage(${s.id})">🌿 Sevrage</button>`;
                }

                tr.innerHTML = `
                    <td><strong>${s.femelle_nom}</strong> (${s.femelle_code})</td>
                    <td>${s.male_nom || '—'}</td>
                    <td>${s.date_saillie}</td>
                    <td style="font-weight: 600; color: #b45309;">${s.date_mise_bas_prevue}</td>
                    <td>${s.nes_vivants || '—'}</td>
                    <td>${s.morts_nes || 0}</td>
                    <td>${s.nb_sevres || '—'}</td>
                    <td><span class="badge badge-neutral">${s.statut.replace('_', ' ')}</span></td>
                    <td>${actionBtn}</td>
                `;
                tbodyS.appendChild(tr);
            });
        }

        // 3. Lots lapins engraissement
        const resLots = await fetch('/api/lapins/lots');
        const lotsL = await resLots.json();
        this.allLotsLapins = lotsL;
        const tbodyL = document.querySelector('#table-lots-lapins tbody');
        if (tbodyL) {
            tbodyL.innerHTML = '';
            lotsL.forEach(l => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${l.code}</strong></td>
                    <td>${l.designation}</td>
                    <td>${l.race}</td>
                    <td><span class="badge badge-info">${l.type_lot}</span></td>
                    <td><strong style="color: var(--primary);">${l.effectif}</strong></td>
                    <td>${l.emplacement || '—'}</td>
                    <td><span class="badge badge-success">${l.statut}</span></td>
                `;
                tbodyL.appendChild(tr);
            });
        }
        this.applyPermissionsUI();
    },

    async actionMiseBas(repId) {
        const nbr = prompt("Nombre de lapereaux nés vivants :", "7");
        if (nbr === null) return;
        const morts = prompt("Nombre de lapereaux morts-nés :", "0") || 0;

        const res = await fetch(`/api/lapins/reproductions/${repId}/mise-bas`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nes_vivants: nbr, morts_nes: morts })
        });
        if (res.ok) {
            this.toast(`Mise bas enregistrée (${nbr} vivants) !`);
            this.loadLapins();
        }
    },

    async actionSevrage(repId) {
        const nbr = prompt("Nombre de lapereaux sevrés avec succès :", "7");
        if (nbr === null) return;

        const res = await fetch(`/api/lapins/reproductions/${repId}/sevrage`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nb_sevres: nbr, lot_destination_id: 1 })
        });
        if (res.ok) {
            this.toast(`Sevrage réussi et lapereaux intégrés à l'engraissement !`);
            this.loadLapins();
        }
    },

    // =========================================================================
    // MODULE 5: ŒUFS
    // =========================================================================
    async loadOeufs() {
        const res = await fetch('/api/oeufs/stock');
        const dataStock = await res.json();
        document.getElementById('oeufs-view-total').innerText = this.formatNumber(dataStock.unites);
        document.getElementById('oeufs-view-plateaux').innerText = `${dataStock.plateaux} plateaux de 30`;
        document.getElementById('oeufs-view-valeur').innerText = this.formatFCFA(dataStock.plateaux * 2200);

        const resP = await fetch('/api/oeufs/pontes');
        const pontes = await resP.json();
        const tbody = document.querySelector('#table-pontes tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        pontes.forEach(p => {
            const tr = document.createElement('tr');
            const pl = Math.round((p.quantite_total / 30) * 10) / 10;
            tr.innerHTML = `
                <td><strong>${p.date_ponte}</strong></td>
                <td>${p.lot_nom}</td>
                <td><strong style="color: var(--primary);">${this.formatNumber(p.quantite_total)}</strong></td>
                <td>${pl} pl.</td>
                <td>${p.gros_calibre}</td>
                <td>${p.moyen_calibre}</td>
                <td>${p.petit_calibre}</td>
                <td style="color: var(--danger);">${p.casses}</td>
                <td style="color: var(--text-muted); font-size: 0.78rem;">${p.notes || ''}</td>
            `;
            tbody.appendChild(tr);
        });

        // Populate select lot pondeuses
        const sel = document.getElementById('ponte-lot-select');
        if (sel) {
            sel.innerHTML = '';
            this.allLotsVolailles.filter(l => l.type_production === 'ponte' || l.statut === 'en_ponte').forEach(l => {
                const opt = document.createElement('option');
                opt.value = l.id;
                opt.text = `${l.nom} (${l.effectif_actuel} pondeuses)`;
                sel.appendChild(opt);
            });
            if (sel.options.length === 0) {
                const opt = document.createElement('option');
                opt.value = 2;
                opt.text = "Pondeuses Isa Brown — Bâtiment 2 (782 pondeuses)";
                sel.appendChild(opt);
            }
        }
    },

    calcEggBreakdown() {
        const total = parseInt(document.getElementById('ponte-total').value) || 0;
        document.getElementById('ponte-gros').value = Math.round(total * 0.55);
        document.getElementById('ponte-moyen').value = Math.round(total * 0.35);
        document.getElementById('ponte-petit').value = total - Math.round(total * 0.55) - Math.round(total * 0.35);
        document.getElementById('ponte-casses').value = Math.round(total * 0.015);
    },

    async submitPonte() {
        const total = document.getElementById('ponte-total').value;
        const lotId = document.getElementById('ponte-lot-select').value;
        const dateP = document.getElementById('ponte-date').value;
        const gros = document.getElementById('ponte-gros').value;
        const moyen = document.getElementById('ponte-moyen').value;
        const petit = document.getElementById('ponte-petit').value;
        const casses = document.getElementById('ponte-casses').value;

        const res = await fetch('/api/oeufs/pontes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                lot_id: lotId,
                date_ponte: dateP,
                quantite_total: total,
                gros_calibre: gros,
                moyen_calibre: moyen,
                petit_calibre: petit,
                casses: casses
            })
        });
        if (res.ok) {
            this.toast('Ramassage d’œufs enregistré et stock augmenté !');
            this.closeModal('modal-nouvelle-ponte');
            this.loadOeufs();
        }
    },

    // =========================================================================
    // MODULE 6: INCUBATION
    // =========================================================================
    async loadIncubation() {
        const res = await fetch('/api/incubations');
        const incubs = await res.json();
        const tbody = document.querySelector('#table-incubations tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        incubs.forEach(inc => {
            const tr = document.createElement('tr');
            const stBadge = inc.statut === 'en_cours' ? 'badge-warning' : 'badge-success';
            let actionBtn = '';
            if (inc.statut === 'en_cours') {
                actionBtn = `<button class="btn btn-sm btn-primary btn-ecriture" onclick="app.openClotureEclosion(${inc.id}, '${inc.code_session}', ${inc.nb_oeufs_incubes})">🐣 Clôturer Éclosion</button>`;
            } else {
                actionBtn = `<span style="color: var(--success); font-weight: 600;">Lot #${inc.lot_cree_id || 'OK'}</span>`;
            }

            tr.innerHTML = `
                <td><strong>${inc.code_session}</strong></td>
                <td>${inc.date_mise}</td>
                <td><strong>${this.formatNumber(inc.nb_oeufs_incubes)}</strong></td>
                <td>${inc.incubateur_nom || 'Couveuse'}</td>
                <td style="color: #b45309; font-weight: 600;">${inc.date_eclosion_prevue}</td>
                <td>${inc.oeufs_clairs || 0}</td>
                <td>${inc.poussins_vigoureux || '—'}</td>
                <td><strong>${inc.taux_eclosion ? `${inc.taux_eclosion}%` : '—'}</strong></td>
                <td><span class="badge ${stBadge}">${inc.statut.replace('_', ' ')}</span></td>
                <td>${actionBtn}</td>
            `;
            tbody.appendChild(tr);
        });

        // Lot source select
        const sel = document.getElementById('incub-lot-source');
        if (sel) {
            sel.innerHTML = '<option value="">-- Pondeuses Internes --</option>';
            this.allLotsVolailles.forEach(l => {
                const opt = document.createElement('option');
                opt.value = l.id;
                opt.text = l.nom;
                sel.appendChild(opt);
            });
        }
    },

    openClotureEclosion(id, code, nbOeufs) {
        document.getElementById('eclosion-incub-id').value = id;
        document.getElementById('eclosion-code-session').value = code;
        const estim = Math.round(nbOeufs * 0.85);
        document.getElementById('eclosion-nb-total').value = estim;
        document.getElementById('eclosion-nb-vigoureux').value = estim;
        this.openModal('modal-cloture-eclosion');
    },

    async submitIncubation() {
        const form = document.getElementById('form-nouvelle-incubation');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        const res = await fetch('/api/incubations', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            this.toast('Session d’incubation enregistrée et œufs déduits du stock.');
            this.closeModal('modal-nouvelle-incubation');
            this.loadIncubation();
        }
    },

    async submitClotureEclosion() {
        const id = document.getElementById('eclosion-incub-id').value;
        const eclos = document.getElementById('eclosion-nb-total').value;
        const vig = document.getElementById('eclosion-nb-vigoureux').value;
        const creerLot = document.getElementById('eclosion-creer-lot').checked;

        const res = await fetch(`/api/incubations/${id}/eclosion`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ poussins_eclos: eclos, poussins_vigoureux: vig, creer_lot: creerLot })
        });
        const d = await res.json();
        if (res.ok) {
            this.toast(`Éclosion validée (Taux : ${d.taux_eclosion}%) ! Nouveau lot créé.`);
            this.closeModal('modal-cloture-eclosion');
            this.loadIncubation();
        }
    },

    // =========================================================================
    // MODULE 7: ALIMENTS
    // =========================================================================
    async loadAliments() {
        const res = await fetch('/api/aliments');
        const aliments = await res.json();
        this.allAliments = aliments;
        const tbody = document.querySelector('#table-aliments tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        aliments.forEach(a => {
            const tr = document.createElement('tr');
            const isLow = a.stock_actuel_kg <= a.seuil_alerte_kg;
            const stBadge = isLow ? 'badge-danger' : 'badge-success';
            tr.innerHTML = `
                <td><strong>${a.code}</strong></td>
                <td><strong>${a.nom}</strong></td>
                <td><span class="badge badge-neutral">${a.categorie}</span></td>
                <td><strong style="color: ${isLow ? 'var(--danger)' : 'var(--primary)'}; font-size: 1rem;">${this.formatNumber(a.stock_actuel_kg)} kg</strong></td>
                <td>${this.formatNumber(a.seuil_alerte_kg)} kg</td>
                <td>${this.formatFCFA(a.prix_unitaire_kg)} / kg</td>
                <td>${a.emplacement || '—'}</td>
                <td><span class="badge ${stBadge}">${isLow ? '⚠️ Seuil Bas' : 'Normal'}</span></td>
            `;
            tbody.appendChild(tr);
        });
    },

    // =========================================================================
    // MODULE 8: FORMULES ALIMENTAIRES (RATIONS & SIMULATION)
    // =========================================================================
    async loadFormules() {
        const res = await fetch('/api/formules');
        const formules = await res.json();
        const container = document.getElementById('formules-container');
        if (!container) return;
        container.innerHTML = '';

        formules.forEach(f => {
            const card = document.createElement('div');
            card.className = 'section-card';
            card.style.marginBottom = '0';
            
            let ingRows = '';
            (f.ingredients || []).forEach(ing => {
                ingRows += `
                    <div style="display: flex; justify-content: space-between; font-size: 0.8rem; padding: 3px 0; border-bottom: 1px dashed var(--border);">
                        <span>${ing.nom_ingredient}</span>
                        <span><strong>${ing.proportion_pct}%</strong> (${ing.prix_kg} F/kg)</span>
                    </div>
                `;
            });

            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                    <h4 style="font-size: 1rem; color: var(--text-main); font-weight: 700;">${f.nom}</h4>
                    <span class="badge badge-info">${f.phase}</span>
                </div>
                <p style="font-size: 0.78rem; color: var(--text-muted); margin-bottom: 0.75rem;">${f.description || ''}</p>
                <div style="margin-bottom: 0.75rem;">
                    ${ingRows}
                </div>
                <div style="background: #f8fafc; padding: 0.6rem; border-radius: 6px; display: flex; justify-content: space-between; margin-bottom: 0.75rem;">
                    <div>Coût / kg : <strong style="color: var(--primary);">${f.cout_revient_kg} FCFA</strong></div>
                    <div>Sac 50kg : <strong style="color: var(--primary);">${this.formatFCFA(f.cout_sac_50kg)}</strong></div>
                </div>
                <button class="btn btn-sm btn-primary btn-ecriture" style="width: 100%;" onclick="app.simulerFabrication(${f.id}, '${f.nom}')">
                    ⚙ Fabriquer une tournée (Mélange)
                </button>
            `;
            container.appendChild(card);
        });
        this.applyPermissionsUI();
    },

    async simulerFabrication(fId, nom) {
        const qte = prompt(`Quantité de ration à fabriquer pour '${nom}' (en kg) :`, "200");
        if (!qte) return;

        const res = await fetch(`/api/formules/${fId}/fabriquer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quantite_kg: parseFloat(qte) })
        });
        const d = await res.json();
        if (res.ok) {
            let resume = `Fabrication réussie de ${d.quantite_fabriquee} kg !\nCoût total : ${this.formatFCFA(d.cout_total)}\n\nMatières consommées :\n`;
            d.ingredients_consommes.forEach(i => {
                resume += `• ${i.nom} : ${i.quantite_kg} kg\n`;
            });
            alert(resume);
            this.toast('Ration fabriquée et intégrée au stock d’aliments !');
        }
    },

    // =========================================================================
    // MODULE 9: STOCKS CONSOLIDÉS
    // =========================================================================
    async loadStocks() {
        const res = await fetch('/api/stocks');
        const data = await res.json();
        
        document.getElementById('stock-valeur-totale').innerText = this.formatFCFA(data.valeur_totale);
        document.getElementById('stock-nb-articles').innerText = data.articles.length;

        const tbody = document.querySelector('#table-stocks tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        data.articles.forEach(art => {
            const tr = document.createElement('tr');
            const isAlert = art.quantite_stock <= art.seuil_alerte;
            tr.innerHTML = `
                <td><strong>${art.code}</strong></td>
                <td>${art.designation}</td>
                <td><span class="badge badge-neutral">${art.categorie}</span></td>
                <td><strong style="color: ${isAlert ? 'var(--danger)' : 'var(--text-main)'};">${this.formatNumber(art.quantite_stock)}</strong></td>
                <td>${art.unite}</td>
                <td>${this.formatNumber(art.seuil_alerte)}</td>
                <td>${this.formatFCFA(art.prix_unitaire)}</td>
                <td><strong>${this.formatFCFA(art.valeur_stock)}</strong></td>
                <td>${art.emplacement || '—'}</td>
                <td><span class="badge ${isAlert ? 'badge-danger' : 'badge-success'}">${isAlert ? 'Alerte Seuil' : 'Disponible'}</span></td>
            `;
            tbody.appendChild(tr);
        });
    },

    // =========================================================================
    // MODULE 10: SANTÉ & PROPHYLAXIE
    // =========================================================================
    switchSanteTab(tab) {
        document.getElementById('tab-sante-interventions').style.display = (tab === 'interventions') ? 'block' : 'none';
        document.getElementById('tab-sante-prophylaxie').style.display = (tab === 'prophylaxie') ? 'block' : 'none';

        document.querySelectorAll('#view-sante .tab-btn').forEach(btn => btn.classList.remove('active'));
        event.target.classList.add('active');
        this.loadSante();
    },

    async loadSante() {
        // Interventions
        const resI = await fetch('/api/sante/interventions');
        const inters = await resI.json();
        const tbodyI = document.querySelector('#table-sante tbody');
        if (tbodyI) {
            tbodyI.innerHTML = '';
            inters.forEach(it => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${it.date_intervention}</strong></td>
                    <td><span class="badge badge-neutral">${it.espece}</span></td>
                    <td><strong>${it.lot_nom || 'Tout le cheptel'}</strong></td>
                    <td><span class="badge badge-info">${it.type_intervention}</span></td>
                    <td><strong>${it.nom_produit}</strong></td>
                    <td>${it.posologie || '—'}</td>
                    <td>${it.delai_attente_jours ? `${it.delai_attente_jours} jours` : '0'}</td>
                    <td>${it.intervenant || '—'}</td>
                    <td style="color: var(--text-muted); font-size: 0.78rem;">${it.notes || ''}</td>
                `;
                tbodyI.appendChild(tr);
            });
        }

        // Prophylaxie
        const resP = await fetch('/api/sante/prophylaxie');
        const proph = await resP.json();
        const tbodyP = document.querySelector('#table-prophylaxie tbody');
        if (tbodyP) {
            tbodyP.innerHTML = '';
            proph.forEach(p => {
                const tr = document.createElement('tr');
                const isFait = p.statut === 'fait';
                tr.innerHTML = `
                    <td><span class="badge badge-neutral">${p.espece.replace('_', ' ')}</span></td>
                    <td><strong>${p.age_recommande}</strong></td>
                    <td>${p.libelle}</td>
                    <td><strong>${p.vaccin_produit}</strong></td>
                    <td>${p.mode_administration || '—'}</td>
                    <td><span class="badge ${isFait ? 'badge-success' : 'badge-warning'}">${isFait ? '✓ Réalisé' : 'À planifier'}</span></td>
                    <td>
                        <button class="btn btn-sm ${isFait ? 'btn-secondary' : 'btn-primary'} btn-ecriture" onclick="app.toggleProphylaxie(${p.id})">
                            ${isFait ? 'Marquer Non Fait' : 'Marquer Réalisé'}
                        </button>
                    </td>
                `;
                tbodyP.appendChild(tr);
            });
        }
        this.applyPermissionsUI();
    },

    async toggleProphylaxie(id) {
        const res = await fetch(`/api/sante/prophylaxie/${id}/toggle`, { method: 'PUT' });
        if (res.ok) {
            this.toast('Statut prophylaxie mis à jour');
            this.loadSante();
        }
    },

    // =========================================================================
    // MODULE 11: CLIENTS & CRÉANCES
    // =========================================================================
    async loadClients() {
        const res = await fetch('/api/clients');
        const clients = await res.json();
        this.allClients = clients;

        const tbody = document.querySelector('#table-clients tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        clients.forEach(c => {
            const tr = document.createElement('tr');
            const hasCreance = c.solde_du > 0;
            tr.innerHTML = `
                <td><strong>${c.code}</strong></td>
                <td><strong>${c.nom_complet}</strong></td>
                <td><span class="badge badge-neutral">${c.type_client}</span></td>
                <td>${c.telephone || '—'}</td>
                <td>${c.ville || 'Diégonefla'}</td>
                <td><strong style="color: ${hasCreance ? 'var(--danger)' : 'var(--success)'};">${this.formatFCFA(c.solde_du)}</strong></td>
                <td>${this.formatFCFA(c.limite_credit)}</td>
                <td><span class="badge ${c.statut === 'actif' ? 'badge-success' : 'badge-danger'}">${c.statut}</span></td>
                <td>
                    ${hasCreance ? `<button class="btn btn-sm btn-primary btn-ecriture" onclick="app.openReglementCreance(${c.id}, '${c.nom_complet.replace(/'/g, "\\'")}', ${c.solde_du})">💰 Encaisser</button>` : ''}
                </td>
            `;
            tbody.appendChild(tr);
        });
        this.applyPermissionsUI();
    },

    openReglementCreance(id, nom, solde) {
        document.getElementById('reglement-client-id').value = id;
        document.getElementById('reglement-client-nom').value = nom;
        document.getElementById('reglement-solde-du').value = this.formatFCFA(solde);
        document.getElementById('reglement-montant').value = solde;
        this.openModal('modal-reglement-creance');
    },

    async submitReglementCreance() {
        const id = document.getElementById('reglement-client-id').value;
        const montant = document.getElementById('reglement-montant').value;
        const dateR = document.getElementById('reglement-date').value;
        const mode = document.getElementById('reglement-mode').value;

        const res = await fetch(`/api/clients/${id}/reglement`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ montant: parseFloat(montant), date_reglement: dateR, mode_paiement: mode })
        });
        if (res.ok) {
            this.toast('Encaissement enregistré ! Créance client mise à jour.');
            this.closeModal('modal-reglement-creance');
            this.loadClients();
        }
    },

    async submitNouveauClient() {
        const form = document.getElementById('form-nouveau-client');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        const res = await fetch('/api/clients', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            this.toast('Nouveau client ajouté !');
            this.closeModal('modal-nouveau-client');
            form.reset();
            this.loadClients();
        }
    },

    // =========================================================================
    // MODULE 12: VENTES & FACTURATION
    // =========================================================================
    async loadVentes() {
        const res = await fetch('/api/ventes');
        const ventes = await res.json();
        const tbody = document.querySelector('#table-ventes tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        ventes.forEach(v => {
            const tr = document.createElement('tr');
            const stBadge = v.statut_paiement === 'paye' ? 'badge-success' : (v.statut_paiement === 'acompte' ? 'badge-warning' : 'badge-danger');
            tr.innerHTML = `
                <td><strong>${v.numero_facture}</strong></td>
                <td>${v.date_vente}</td>
                <td><strong>${v.client_nom}</strong></td>
                <td><strong>${this.formatFCFA(v.montant_net)}</strong></td>
                <td>${this.formatFCFA(v.montant_regle)}</td>
                <td style="color: ${v.montant_restant > 0 ? 'var(--danger)' : 'var(--text-muted)'}; font-weight: 600;">${this.formatFCFA(v.montant_restant)}</td>
                <td><span class="badge badge-neutral">${v.mode_paiement.toUpperCase()}</span></td>
                <td><span class="badge ${stBadge}">${v.statut_paiement}</span></td>
                <td>
                    <button class="btn btn-sm btn-secondary" onclick="app.viewFacture(${v.id})">🖨 Voir Facture</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        // Setup clients in sales modal select
        this.populateVenteClientsSelect();
        // Setup initial product row in sale modal
        const container = document.getElementById('vente-lignes-container');
        if (container && container.children.length === 0) {
            this.addVenteLine();
        }
    },

    populateVenteClientsSelect() {
        const sel = document.getElementById('vente-client-select');
        if (!sel) return;
        sel.innerHTML = '<option value="">-- Client Comptoir (Passage) --</option>';
        this.allClients.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.id;
            opt.text = `${c.nom_complet} (${c.ville}) — Solde dû : ${this.formatFCFA(c.solde_du)}`;
            sel.appendChild(opt);
        });
    },

    onVenteClientChange() {
        const sel = document.getElementById('vente-client-select');
        const nomInput = document.getElementById('vente-client-nom');
        if (sel.value) {
            const cl = this.allClients.find(c => c.id == sel.value);
            if (cl) nomInput.value = cl.nom_complet;
        } else {
            nomInput.value = "Client Comptoir";
        }
    },

    addVenteLine() {
        const container = document.getElementById('vente-lignes-container');
        const div = document.createElement('div');
        div.className = 'form-row vente-line-row';
        div.style.marginBottom = '0.5rem';
        div.innerHTML = `
            <div style="flex: 2;">
                <select class="form-control line-product-select" onchange="app.onProductSelectChange(this)">
                    <option value="poulet_vif" data-unit="unite" data-price="4500">Poulet de chair vif (pièce)</option>
                    <option value="poulet_pac" data-unit="kg" data-price="3100">Poulet prêt à cuire PAC (kg)</option>
                    <option value="oeufs_plateau" data-unit="plateau" data-price="2200">Plateau de 30 œufs frais</option>
                    <option value="lapin_vif" data-unit="unite" data-price="6000">Lapin de chair vivant (pièce)</option>
                    <option value="lapin_decoupe" data-unit="kg" data-price="6000">Lapin découpé / PAC (kg)</option>
                    <option value="poussin" data-unit="unite" data-price="700">Poussins d'un jour</option>
                    <option value="autre" data-unit="unite" data-price="1000">Autre produit ferme</option>
                </select>
            </div>
            <div style="flex: 1;">
                <input type="number" class="form-control line-qte" placeholder="Qté" value="1" min="1" oninput="app.calcVenteTotals()">
            </div>
            <div style="flex: 1.2;">
                <input type="number" class="form-control line-price" placeholder="Prix Unitaire" value="4500" oninput="app.calcVenteTotals()">
            </div>
            <div style="flex: 1.2; display: flex; align-items: center; justify-content: space-between;">
                <span class="line-subtotal" style="font-weight: 700; font-size: 0.85rem;">4 500 F</span>
                <button type="button" class="btn btn-sm btn-secondary" onclick="this.closest('.vente-line-row').remove(); app.calcVenteTotals();" style="color: var(--danger); border: none;">✕</button>
            </div>
        `;
        container.appendChild(div);
        this.calcVenteTotals();
    },

    onProductSelectChange(selectEl) {
        const row = selectEl.closest('.vente-line-row');
        const opt = selectEl.selectedOptions[0];
        const price = opt.getAttribute('data-price') || 0;
        row.querySelector('.line-price').value = price;
        this.calcVenteTotals();
    },

    calcVenteTotals() {
        let brut = 0;
        document.querySelectorAll('.vente-line-row').forEach(row => {
            const qte = parseFloat(row.querySelector('.line-qte').value) || 0;
            const pu = parseFloat(row.querySelector('.line-price').value) || 0;
            const sub = qte * pu;
            brut += sub;
            row.querySelector('.line-subtotal').innerText = sub.toLocaleString('fr-FR') + ' F';
        });

        const remise = parseFloat(document.getElementById('vente-remise').value) || 0;
        const net = Math.max(0, brut - remise);
        
        let regleEl = document.getElementById('vente-regle');
        if (regleEl.value === "" || parseFloat(regleEl.value) === 0) {
            regleEl.value = net; // Par défaut, payé au comptant
        }
        const regle = parseFloat(regleEl.value) || 0;
        const restant = Math.max(0, net - regle);

        document.getElementById('vente-total-brut').innerText = this.formatFCFA(brut);
        document.getElementById('vente-total-net').innerText = this.formatFCFA(net);
        document.getElementById('vente-total-restant').innerText = this.formatFCFA(restant);
    },

    async submitNouvelleVente() {
        const lignes = [];
        document.querySelectorAll('.vente-line-row').forEach(row => {
            const sel = row.querySelector('.line-product-select');
            const opt = sel.selectedOptions[0];
            const qte = parseFloat(row.querySelector('.line-qte').value) || 0;
            const pu = parseFloat(row.querySelector('.line-price').value) || 0;
            if (qte > 0) {
                lignes.push({
                    type_produit: sel.value,
                    designation: opt.text,
                    quantite: qte,
                    unite: opt.getAttribute('data-unit') || 'unite',
                    prix_unitaire: pu,
                    lot_source_id: (sel.value.startsWith('poulet') ? 1 : (sel.value.startsWith('lapin') ? 1 : null))
                });
            }
        });

        if (lignes.length === 0) {
            this.toast('Veuillez ajouter au moins un produit à la vente.', 'error');
            return;
        }

        const data = {
            client_id: document.getElementById('vente-client-select').value || null,
            client_nom: document.getElementById('vente-client-nom').value,
            date_vente: document.getElementById('vente-date').value,
            remise: parseFloat(document.getElementById('vente-remise').value) || 0,
            montant_regle: parseFloat(document.getElementById('vente-regle').value) || 0,
            mode_paiement: document.getElementById('vente-mode-paiement').value,
            lignes: lignes
        };

        const res = await fetch('/api/ventes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const resp = await res.json();
        if (res.ok) {
            this.toast(`Vente enregistrée avec succès (Facture ${resp.numero_facture}) !`);
            this.closeModal('modal-nouvelle-vente');
            this.loadVentes();
            this.viewFacture(resp.id);
        } else {
            this.toast(resp.error || 'Erreur lors de la vente', 'error');
        }
    },

    async viewFacture(venteId) {
        const res = await fetch(`/api/ventes/${venteId}`);
        const v = await res.json();
        const area = document.getElementById('facture-printable-area');

        let rowsHtml = '';
        (v.lignes || []).forEach(l => {
            rowsHtml += `
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #e2e8f0;">${l.designation}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: center;">${l.quantite} ${l.unite}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: right;">${this.formatFCFA(l.prix_unitaire)}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: bold;">${this.formatFCFA(l.sous_total)}</td>
                </tr>
            `;
        });

        area.innerHTML = `
            <div style="font-family: inherit; color: #0f172a; padding: 1rem;">
                <!-- Header Facture -->
                <div style="display: flex; justify-content: space-between; align-items: start; border-bottom: 2px solid #15803d; padding-bottom: 1rem; margin-bottom: 1.5rem;">
                    <div>
                        <h2 style="color: #15803d; margin: 0; font-size: 1.5rem;">LA FERME DE DIÉGONEFLA</h2>
                        <p style="font-size: 0.85rem; color: #64748b; margin-top: 4px;">
                            Élevage Avicole & Cunicole | Production d'Œufs & Poussins<br>
                            Route de Gagnoa, Diégonefla, Côte d'Ivoire<br>
                            Tél : +225 07 58 12 34 56 / +225 05 44 98 76 10
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <span style="background: #15803d; color: white; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 0.85rem;">FACTURE CLIENT</span>
                        <h3 style="margin: 8px 0 0 0; font-size: 1.1rem;">${v.numero_facture}</h3>
                        <p style="font-size: 0.85rem; color: #64748b; margin: 2px 0 0 0;">Date : <strong>${v.date_vente}</strong></p>
                    </div>
                </div>

                <!-- Client Info -->
                <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 1rem; border-radius: 6px; margin-bottom: 1.5rem;">
                    <div style="font-size: 0.75rem; text-transform: uppercase; color: #64748b; font-weight: bold;">Facturé à :</div>
                    <div style="font-size: 1.1rem; font-weight: bold; color: #0f172a;">${v.client_nom}</div>
                    <div style="font-size: 0.85rem; color: #475569;">
                        ${v.client_telephone ? `Tél : ${v.client_telephone} | ` : ''} 
                        ${v.client_ville ? `Localisation : ${v.client_ville}` : ''}
                    </div>
                </div>

                <!-- Lignes Table -->
                <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-bottom: 1.5rem;">
                    <thead>
                        <tr style="background: #15803d; color: white;">
                            <th style="padding: 8px; text-align: left;">Désignation Produit</th>
                            <th style="padding: 8px; text-align: center;">Quantité</th>
                            <th style="padding: 8px; text-align: right;">Prix Unitaire</th>
                            <th style="padding: 8px; text-align: right;">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rowsHtml}
                    </tbody>
                </table>

                <!-- Totaux -->
                <div style="display: flex; justify-content: flex-end; margin-bottom: 2rem;">
                    <div style="width: 280px; font-size: 0.9rem;">
                        <div style="display: flex; justify-content: space-between; padding: 4px 0;">
                            <span>Sous-total Brut :</span>
                            <span>${this.formatFCFA(v.montant_brut)}</span>
                        </div>
                        ${v.remise > 0 ? `
                        <div style="display: flex; justify-content: space-between; padding: 4px 0; color: #dc2626;">
                            <span>Remise :</span>
                            <span>- ${this.formatFCFA(v.remise)}</span>
                        </div>` : ''}
                        <div style="display: flex; justify-content: space-between; padding: 6px 0; border-top: 2px solid #e2e8f0; font-size: 1.1rem; font-weight: bold; color: #15803d;">
                            <span>Net à Payer :</span>
                            <span>${this.formatFCFA(v.montant_net)}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 4px 0; color: #16a34a;">
                            <span>Montant Versé :</span>
                            <span>${this.formatFCFA(v.montant_regle)}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; padding: 4px 0; font-weight: bold; color: ${v.montant_restant > 0 ? '#dc2626' : '#16a34a'};">
                            <span>Solde Restant Dû :</span>
                            <span>${this.formatFCFA(v.montant_restant)}</span>
                        </div>
                    </div>
                </div>

                <!-- Signatures Block -->
                <div style="display: flex; justify-content: space-between; padding-top: 2rem; border-top: 1px dashed #cbd5e1; font-size: 0.85rem; color: #64748b;">
                    <div style="text-align: center; width: 200px;">
                        Visa Client<br><br><br>
                        ___________________
                    </div>
                    <div style="text-align: center; width: 200px;">
                        Pour La Ferme de Diégonefla<br>
                        <em>La Direction</em><br><br>
                        [Cachet & Signature]
                    </div>
                </div>
            </div>
        `;
        this.openModal('modal-facture-viewer');
    },

    // =========================================================================
    // MODULE 13: DÉPENSES & ACHATS
    // =========================================================================
    async loadDepenses() {
        const res = await fetch('/api/depenses');
        const depenses = await res.json();
        const tbody = document.querySelector('#table-depenses tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        depenses.forEach(d => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${d.reference}</strong></td>
                <td>${d.date_depense}</td>
                <td><span class="badge badge-neutral">${d.categorie.toUpperCase()}</span></td>
                <td><strong>${d.libelle}</strong></td>
                <td>${d.fournisseur || '—'}</td>
                <td><strong style="color: var(--danger);">${this.formatFCFA(d.montant)}</strong></td>
                <td><span class="badge badge-info">${d.mode_paiement.toUpperCase()}</span></td>
                <td>${d.num_piece || '—'}</td>
                <td>
                    <button class="btn btn-sm btn-secondary btn-ecriture" style="color: var(--danger); border: none;" onclick="app.deleteDepense(${d.id})">✕ Suppr.</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        this.applyPermissionsUI();
    },

    async submitNouvelleDepense() {
        const form = document.getElementById('form-nouvelle-depense');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        const res = await fetch('/api/depenses', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            this.toast('Dépense enregistrée avec succès !');
            this.closeModal('modal-nouvelle-depense');
            form.reset();
            this.loadDepenses();
        }
    },

    async deleteDepense(id) {
        if (!confirm("Voulez-vous vraiment supprimer cette écriture de dépense ?")) return;
        const res = await fetch(`/api/depenses/${id}`, { method: 'DELETE' });
        if (res.ok) {
            this.toast('Dépense supprimée.');
            this.loadDepenses();
        }
    },

    // =========================================================================
    // MODULE 1: UTILISATEURS & AUDIT
    // =========================================================================
    async loadUtilisateurs() {
        const resU = await fetch('/api/utilisateurs');
        const users = await resU.json();
        const tbodyU = document.querySelector('#table-utilisateurs tbody');
        if (tbodyU) {
            tbodyU.innerHTML = '';
            users.forEach(u => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${u.id}</td>
                    <td><strong>${u.nom_complet}</strong></td>
                    <td><code>${u.identifiant}</code></td>
                    <td><span class="badge badge-primary">${u.role.toUpperCase()}</span></td>
                    <td>${u.email || '—'}</td>
                    <td>${u.telephone || '—'}</td>
                    <td><span class="badge badge-success">${u.statut}</span></td>
                    <td>
                        <button class="btn btn-sm btn-secondary" onclick="app.switchRole('${u.role}')">Tester Rôle</button>
                    </td>
                `;
                tbodyU.appendChild(tr);
            });
        }

        // Audit logs
        const resA = await fetch('/api/audit');
        const logs = await resA.json();
        const tbodyA = document.querySelector('#table-audit tbody');
        if (tbodyA) {
            tbodyA.innerHTML = '';
            logs.forEach(l => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="white-space: nowrap; font-size: 0.78rem;">${l.date_action}</td>
                    <td><strong>${l.utilisateur_nom}</strong></td>
                    <td><span class="badge badge-neutral">${l.module}</span></td>
                    <td><strong>${l.action}</strong></td>
                    <td style="color: var(--text-muted); font-size: 0.8rem;">${l.details}</td>
                `;
                tbodyA.appendChild(tr);
            });
        }
    },

    // =========================================================================
    // MODULE 14: PARAMÈTRES & RESTAURATION
    // =========================================================================
    async loadParametres() {
        const res = await fetch('/api/parametres');
        const params = await res.json();
        const form = document.getElementById('form-parametres');
        if (!form) return;
        for (const [k, v] of Object.entries(params)) {
            const input = form.elements[k];
            if (input) input.value = v;
        }
    },

    async saveParametres() {
        const form = document.getElementById('form-parametres');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        const res = await fetch('/api/parametres', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            this.toast('Paramètres généraux sauvegardés avec succès !');
        }
    },

    async resetDemoData() {
        if (!confirm("Voulez-vous réinitialiser toutes les données de test de La Ferme de Diégonefla ?")) return;
        const res = await fetch('/api/reset-demo', { method: 'POST' });
        if (res.ok) {
            this.toast('Données de démo réinitialisées avec succès !');
            this.showView('dashboard');
        }
    },

    async submitNouvelAliment() {
        const form = document.getElementById('form-nouvel-aliment');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        const res = await fetch('/api/aliments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            this.toast('Aliment ajouté au catalogue !');
            this.closeModal('modal-nouvel-aliment');
            form.reset();
            this.loadAliments();
        }
    },

    async submitMouvementAliment() {
        const alimId = document.getElementById('mvt-aliment-select').value;
        const typeMvt = document.getElementById('mvt-aliment-type').value;
        const qte = document.getElementById('mvt-aliment-qte').value;
        const lot = document.getElementById('mvt-aliment-lot').value;
        const res = await fetch('/api/aliments/mouvement', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                aliment_id: alimId,
                type_mouvement: typeMvt,
                quantite_kg: parseFloat(qte),
                lot_destine: lot
            })
        });
        if (res.ok) {
            this.toast('Mouvement d’aliment validé !');
            this.closeModal('modal-mouvement-aliment');
            this.loadAliments();
        }
    },

    async submitNouvelArticle() {
        const form = document.getElementById('form-nouvel-article');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        const res = await fetch('/api/stocks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            this.toast('Article ajouté au stock !');
            this.closeModal('modal-nouvel-article');
            form.reset();
            this.loadStocks();
        }
    },

    async submitNouveauReproducteur() {
        const form = document.getElementById('form-nouveau-reproducteur');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        const res = await fetch('/api/lapins/reproducteurs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            this.toast('Reproducteur cunicole enregistré !');
            this.closeModal('modal-nouveau-reproducteur');
            form.reset();
            this.loadLapins();
        }
    },

    async submitNouvelleSaillie() {
        const fId = document.getElementById('saillie-femelle-select').value;
        const mId = document.getElementById('saillie-male-select').value;
        const dt = document.getElementById('saillie-date').value;
        const res = await fetch('/api/lapins/reproductions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ femelle_id: fId, male_id: mId, date_saillie: dt })
        });
        if (res.ok) {
            this.toast('Saillie enregistrée ! Échéance mise bas calculée à J+31.');
            this.closeModal('modal-nouvelle-saillie');
            this.loadLapins();
        }
    },

    async submitNouvelleInterventionSante() {
        const form = document.getElementById('form-intervention-sante');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        const res = await fetch('/api/sante/interventions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            this.toast('Acte sanitaire consigné au registre !');
            this.closeModal('modal-nouvelle-intervention-sante');
            form.reset();
            this.loadSante();
        }
    },

    async submitNouvelUtilisateur() {
        const form = document.getElementById('form-nouvel-utilisateur');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        const res = await fetch('/api/utilisateurs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const resp = await res.json();
        if (res.ok) {
            this.toast('Compte utilisateur créé avec succès !');
            this.closeModal('modal-nouvel-utilisateur');
            form.reset();
            this.loadUtilisateurs();
        } else {
            this.toast(resp.error || 'Erreur lors de la création', 'error');
        }
    },

    // Modal Helper
    async openModal(modalId) {
        const m = document.getElementById(modalId);
        if (!m) return;

        // Dynamic select population hooks
        if (modalId === 'modal-mouvement-aliment') {
            const sel = document.getElementById('mvt-aliment-select');
            if (sel) {
                sel.innerHTML = '';
                this.allAliments.forEach(a => {
                    const opt = document.createElement('option');
                    opt.value = a.id;
                    opt.text = `${a.nom} (Stock : ${a.stock_actuel_kg} kg)`;
                    sel.appendChild(opt);
                });
            }
        } else if (modalId === 'modal-nouvelle-saillie') {
            const res = await fetch('/api/lapins/reproducteurs');
            const repros = await res.json();
            const fSel = document.getElementById('saillie-femelle-select');
            const mSel = document.getElementById('saillie-male-select');
            if (fSel && mSel) {
                fSel.innerHTML = '';
                mSel.innerHTML = '';
                repros.filter(r => r.sexe === 'femelle').forEach(f => {
                    const opt = document.createElement('option');
                    opt.value = f.id;
                    opt.text = `${f.nom} (${f.code_tatouage}) - ${f.race}`;
                    fSel.appendChild(opt);
                });
                repros.filter(r => r.sexe === 'male').forEach(m => {
                    const opt = document.createElement('option');
                    opt.value = m.id;
                    opt.text = `${m.nom} (${m.code_tatouage}) - ${m.race}`;
                    mSel.appendChild(opt);
                });
            }
            const sDate = document.getElementById('saillie-date');
            if (sDate) sDate.value = new Date().toISOString().split('T')[0];
        } else if (modalId === 'modal-nouvelle-intervention-sante') {
            const sDate = document.getElementById('sante-date');
            if (sDate) sDate.value = new Date().toISOString().split('T')[0];
        }

        m.classList.add('active');
    },

    closeModal(modalId) {
        const m = document.getElementById(modalId);
        if (m) m.classList.remove('active');
    }
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});
