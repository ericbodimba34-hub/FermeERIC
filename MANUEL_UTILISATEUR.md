# Guide Utilisateur — Application DFM
## Exploitation Avicole & Cunicole « La Ferme de Diégonefla »

Bienvenue dans le manuel d'utilisation officiel de l'application **DFM**. Ce document vous explique étape par étape comment utiliser chaque module au quotidien.

---

### 1. Prise en main et Tableau de bord
À l'ouverture de l'application, l'écran d'accueil présente la synthèse en temps réel de votre exploitation :
- **10 indicateurs clés :**
  1. **Poulets :** Effectif total vivant en élevage (chair, pondeuses, poussins).
  2. **Lapins :** Total des lapereaux en engraissement et des reproducteurs.
  3. **Œufs Disponibles :** Stock actuel d'œufs frais de table (en unités et plateaux de 30).
  4. **Lots Actifs :** Nombre total de bandes ou bâtiments actuellement peuplés.
  5. **Reproducteurs :** Nombre de mâles et lapines mères en activité cunicole.
  6. **Stock Aliments :** Quantité totale d'aliments et matières premières disponibles (en kg).
  7. **CA du Mois :** Chiffre d'affaires cumulé des ventes réalisées sur le mois en Franc CFA (FCFA).
  8. **Dépenses du Mois :** Somme des approvisionnements, salaires et charges enregistrés ce mois.
  9. **Bénéfice Net :** Résultat d'exploitation instantané (**CA du Mois moins Dépenses**).
  10. **Créances Clients :** Montant total des factures émises en attente de règlement.
- **Alertes automatiques :** Un bandeau d'alerte s'affiche en tête pour signaler les événements critiques :
  - Niveau de stock d'aliment inférieur au seuil de sécurité.
  - Mise bas imminente d'une lapine reproductrice (à J+30 de la saillie).
  - Éclosion programmée dans la couveuse (à J+21 de la mise en incubation).
  - Créance client en attente dépassant le seuil de vigilance.
  - Mortalité hebdomadaire supérieure à la normale.

---

### 2. Gestion des Volailles (Poulets)
1. **Création d'un nouveau lot :** Cliquez sur `+ Nouveau Lot Volaille`, renseignez la désignation, la souche (ex: *Cobb 500, Isa Brown, Goliath*), l'effectif initial de poussins et le bâtiment de destination.
2. **Pesée de contrôle :** Sur la ligne du lot concerné, cliquez sur `⚖ Pesée`. Indiquez le poids moyen constaté en grammes. Le système actualise immédiatement la moyenne du cheptel.
3. **Mortalités :** En cas de perte de sujets, cliquez sur `⚠ Perte`. Saisissez le nombre et la cause (ex: *tri initial, coup de chaleur, problème respiratoire*). L'effectif actuel du lot et les indicateurs du tableau de bord sont réduits en temps réel.

---

### 3. Gestion des Lapins (Cunicole)
Le module cunicole s'articule en 3 onglets :
1. **Reproducteurs Mâles & Femelles :** Répertoire des reproducteurs avec code tatouage, race (*Fauve de Bourgogne, Néo-Zélandais Blanc, Géant des Flandres, Papillon Français*), cage et statut (*actif, gestation, repos*).
2. **Saillies, Gestations & Portées :**
   - Cliquez sur `+ Enregistrer une Saillie`. Choisissez la femelle et le mâle. La date prévisionnelle de mise bas est calculée automatiquement à J+31.
   - À la naissance, cliquez sur `🍼 Mise Bas` pour consigner les lapereaux vivants et morts-nés.
   - Au moment du sevrage, cliquez sur `🌿 Sevrage` pour transférer les lapereaux sevrés dans un lot d'engraissement.
3. **Lots d'Engraissement :** Suivi des effectifs de lapereaux par cage ou batterie jusqu'à la vente.

---

### 4. Gestion des Œufs
1. **Ramassage quotidien :** Cliquez sur `+ Enregistrer Ramassage`. Renseignez le lot de pondeuses et le nombre total d'œufs ramassés. L'application calcule automatiquement la répartition par calibre (*Gros, Moyen, Petit*) et déduit les œufs cassés.
2. **Mouvements & Ventes :** Toute vente ou mise en couveuse déduit directement les œufs du stock disponible.

---

### 5. Incubation (Couveuses)
1. **Lancement d'une incubation :** Cliquez sur `+ Lancer une Incubation`. Indiquez le nombre d'œufs et la couveuse. Le calendrier calcule le premier mirage à J+7 et l'éclosion prévisionnelle à J+21.
2. **Clôture de l'éclosion :** Cliquez sur `🐣 Clôturer Éclosion`. Saisissez le nombre de poussins éclos et vigoureux. L'application calcule le taux d'éclosion (%) et propose de **créer automatiquement un nouveau lot de volailles** dans votre cheptel !

---

### 6. Gestion des Aliments & Formules
1. **Suivi des stocks :** Chaque aliment dispose d'une jauge avec stock actuel et seuil d'alerte en kg.
2. **Distribution quotidienne :** Cliquez sur `Distribution / Mouvement` pour consigner la ration donnée à un lot de volailles ou de lapins.
3. **Formules alimentaires :** Visualisez les recettes de rations fermières (*Finition Poulet, Pondeuse Haute Ponte, Granulés Lapin*).
   - Le système calcule en temps réel le **coût de revient au kg** et par **sac de 50 kg**.
   - Vous pouvez cliquer sur `⚙ Fabriquer une tournée` : le logiciel calcule la quantité exacte de chaque ingrédient (*maïs, soja, son de blé, poisson, CMV*) et ajoute le mélange fini au stock d'aliments.

---

### 7. Ventes & Facturation
1. **Émission d'une vente :** Cliquez sur `+ Nouvelle Vente` ou sur le bouton vert en haut à droite.
   - Sélectionnez un client ou laissez *Client Comptoir*.
   - Choisissez les produits vendus (*Poulets vifs, Poulets prêts à cuire au kg, Plateaux d'œufs, Lapins vifs, Poussins...*).
   - Indiquez la quantité et le prix unitaire en FCFA.
   - Indiquez le montant perçu. Si le montant réglé est inférieur au net à payer, le solde restant est automatiquement ajouté à la **créance du client** !
   - Le stock correspondant (œufs ou sujets) est instantanément déduit.
2. **Facture / Reçu imprimable :** Cliquez sur `🖨 Voir Facture` pour générer une facture officielle complète avec logo, coordonnées de la ferme, détail des lignes, montants et zone de signatures.

---

### 8. Dépenses & Approvisionnements
1. **Enregistrement :** Cliquez sur `+ Enregistrer une Dépense`. Choisissez la catégorie (*Aliments, Santé, Salaires, Énergie, Équipement, Entretien, Divers*), le fournisseur, le montant en FCFA et le mode de règlement.
2. **Calcul de la rentabilité :** Les charges sont immédiatement soustraites du chiffre d'affaires pour afficher le bénéfice net de la ferme.

---

### 9. Clients & Créances
1. **Suivi des soldes :** Visualisez la liste des clients et leur dette actuelle.
2. **Encaissement :** Lorsqu'un client règle une dette, cliquez sur `💰 Encaisser`. Saisissez la somme reçue. Le solde du client et les alertes financières sont immédiatement mis à jour.

---

### 10. Rapports, Exports & Sauvegardes
1. **Export Excel (.xlsx) :** Cliquez sur `Export Excel` pour télécharger une feuille de calcul complète comprenant les bilans financiers, les ventes, les dépenses, l'état du cheptel et des stocks.
2. **Sauvegarde complète :** Dans le menu *Rapports & Paramètres*, cliquez sur `Exporter la Sauvegarde Complète (JSON)` pour conserver une copie de sécurité hors-ligne de vos données.
3. **Paramètres de l'exploitation :** Ajustez les coordonnées de la ferme, les numéros de téléphone et les seuils d'alertes personnalisés.
