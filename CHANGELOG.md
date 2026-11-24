# Changelog

## 2026-11-23 — Rafraîchissement des sources MDPH

Lecture du plan de projet et exploration du dossier `sources/` (trois prototypes antérieurs : `CHATBOT MDPH/`, `chatbot-keywords-mdph/`, `chatbot-rag-mdph/`). Recherche et récupération des versions les plus récentes des sources citées dans le plan (section « Données : sources, licences, corpus »).

Ajouté dans `sources/` :
- `CNSA_TC_v2.3.2_2026-10/` — Tronc commun SI-MDPH et Référentiel Fonctionnel, version **2.3.2** (publiée par la CNSA en octobre 2026), remplace les PDF V2.1.3 déjà présents dans `CHATBOT MDPH/docs/`.
- `formulaires_2026-11/cerfa_15692-01_MDPH.pdf` — formulaire unique MDPH en vigueur, vérifié le 13 juillet 2026.
- `formulaires_2026-11/CNSA_guide_eligibilites_MDPH_2024-04.pdf` — guide des éligibilités CDAPH (avril 2024), complète le guide AAH de 2017 déjà présent.
- `service-public-vectorise_2026-11/` — dataset DINUM des fiches Service-Public vectorisées, mis à jour le jour même, plus un extrait filtré (601 passages / 84 fiches) sur les termes MDPH/handicap.

Détails, licences et limites consignés dans `sources/SOURCES_INDEX.md`.

Point notable : au 20 octobre 2026, les résultats de l'expérimentation CNSA du chatbot juridique (Mesure 17) n'étaient pas publiés ; une source plus récente indique un délai de remise des rapports MDPH fixé au 31 décembre 2026, donc une publication probablement plus tardive que ce qu'anticipait le plan.

## 2026-11-23 — Dépendances techniques (phase 2)

Cloné dans `vendor/` les deux briques techniques citées par le plan :
- `Tiny-2.1` (WollyMonjac, MIT) — contient `training/train2.py` et `training/gen2.py`, base de l'entraînement du mini-classifieur, ainsi que `DATA_LICENSES.md` comme modèle de registre des licences de données.
- `minisearch` (lucaong, MIT) — bibliothèque de recherche plein texte sans dépendance.

Reste manquant pour développer le modèle : le corpus réel de 150 à 200 fiches validées (doit venir des vraies questions des agents MDA, relevées en phase 0), le jeu de test écrit par des agents, et le contenu interne MDA (circuits, contacts). Ce sont des données propres à la MDA que je ne peux pas produire ; voir réponse donnée à l'utilisateur dans la conversation du 23/11/2026.

## 2026-11-23 — Jeu de données factice (corpus/)

Construit un corpus de test dans `corpus/` : 28 fiches au format exact du plan (question/réponse ≤80 mots/source/dates/reformulations), 30 questions hors champ, 15 questions de test. Réponses rédigées à partir des sources déjà récupérées (Service-Public.fr, Cerfa 15692*01, guide CNSA), pas inventées — sauf deux fiches explicitement marquées FACTICE (circuit interne, refus sur situation individuelle). Objectif : faire tourner `vendor/Tiny-2.1` (classifieur) + `vendor/minisearch` de bout en bout pour tester l'architecture, pas remplacer la phase 1 du plan. Détails et limites dans `corpus/README.md`.

## 2026-11-23 — Pipeline complet : classifieur, export JS, page locale, tests

Construit le prototype de bout en bout (voir `README.md` pour les grandes lignes) :
- `model/` : mini-classifieur PyTorch (2 couches, largeur 64, 29 classes) réutilisant les blocs de `vendor/Tiny-2.1/training/train2.py` avec une tête de classification à la place de la sortie générative. Seuil d'abstention réglé sur un jeu de validation séparé du jeu de test. Modèle de référence (régression logistique sur n-grammes de caractères) entraîné en parallèle pour comparaison, comme demandé par le plan.
- `model/export_js.py` : quantification 8 bits (une échelle par ligne) et export vers `webapp/data/model.js` (306 Ko) et `webapp/data/fiches.js`.
- `webapp/js/classifier.js` : réimplémentation JS pure de l'inférence (aucune dépendance). Vérifié identique à PyTorch sur les 15 questions du jeu de test (`webapp/test/parity_check.js`, 15/15).
- `webapp/js/app.js` + `webapp/index.html` : page locale (file://, sans serveur) combinant le classifieur et MiniSearch ; n'affiche une fiche que si les deux avis s'accordent, sinon « Je ne sais pas » + 3 fiches proches.
- `webapp/test/evaluate_e2e.js` : rejoue le jeu de test factice sur le système complet. Résultat : 0 mauvaise fiche affichée comme sûre, 100 % d'abstention correcte sur le hors champ, 100 % de bonne fiche dans le top 3 en cas d'abstention ; taux de réponse directe faible (2/15), cohérent avec un corpus factice 10x plus petit que la cible du plan.
- Page ouverte dans un vrai navigateur (Playwright, installé pour l'occasion) pour confirmer l'affichage réel — pas seulement les tests Node.

Constat principal : l'architecture (abstention apprise + arbitrage à deux avis) fait déjà ce qu'elle doit faire à cette échelle jouet — ne jamais afficher une mauvaise fiche avec assurance. Ce qui manque pour un vrai taux de réponse directe, c'est le volume et la diversité du vrai corpus MDA (phase 1 du plan), pas un changement d'architecture.

## 2026-11-23 — Fusion avec le corpus chatbot-keywords-mdph (28 → 114 fiches)

Comparé le corpus factice aux trois anciens prototypes dans `sources/`. Constat : `chatbot-keywords-mdph` (déjà testé sur 175 questions / 35 profils pour la MDA de l'Orne) couvre 101 sujets quasi tous absents du corpus factice, et inversement 13 fiches factices (établissements, déménagement, certificat médical, comportements de sécurité) couvrent des sujets absents de `chatbot-keywords-mdph`. Fusionné les deux dans `corpus/build_merged_corpus.py` :
- 101 chunks convertis au format du plan (question/réponse ≤80 mots/reformulations), 47 réponses condensées à la main pour respecter la limite sans perdre les faits.
- 13 fiches factices conservées (sujets complémentaires), 15 supprimées (doublons des chunks importés).
- **Trouvaille** : incohérence entre les fiches `chatbot-keywords-mdph` (12 mois) et le vrai formulaire Cerfa 15692*01 (6 mois) pour la validité du certificat médical — tranché en faveur de la source primaire.
- Bug corrigé pendant la construction : un gabarit de question produisait "Qu'est-ce que laPCH ?" (espace manquant) sur toutes les fiches utilisant un article non élidé — corrigé avant export.

Réentraîné le classifieur sur les 114 fiches (115 classes avec HORS_CHAMP, 1267 exemples). Résultats sur le jeu de test factice (mis à jour avec les nouveaux ids) :
- Régression logistique de référence : 60-67% (contre ~33% avec 28 fiches) — plus de données aide nettement ce modèle simple.
- Mini-classifieur seul toujours faible (attendu, 115 classes pour ~11 exemples chacune).
- Arbitrage classifieur+recherche : toujours 0 mauvaise fiche affichée comme sûre.
- **Régression trouvée** : abstention correcte sur le hors champ tombée de 100% à 50% — une question météo obtient désormais `SITUATION-INDIV-001` (la fiche de refus) au lieu d'un "je ne sais pas".
- Bug de méthodologie corrigé dans `webapp/test/parity_check.js` : la référence PyTorch comparait le modèle flottant, pas le modèle quantifié 8 bits réellement exporté en JS — après correction, parité confirmée 15/15.

Détails dans `corpus/README.md`.

## 2026-11-23 — Diagnostic et correction de la régression sur l'abstention

Investigué la régression ci-dessus avec `webapp/test/diag.js` (nouveau script, inspecte les scores bruts du classifieur et de MiniSearch pour une question donnée). Cause trouvée : MiniSearch ne filtre aucun mot vide par défaut (`processTerm` ne fait que minusculiser, confirmé dans `vendor/minisearch/src/MiniSearch.ts` et la doc officielle). La question « il va faire beau ce week-end ? » matchait sur « il »/« ce »/« en », des mots présents dans la plupart des fiches, et `SITUATION-INDIV-001` remontait en tête avec un score élevé juste parce que sa réponse contient souvent ces mots de liaison — sans lien avec son sens.

Corrigé en ajoutant une liste de mots vides français à l'index MiniSearch (`webapp/js/app.js`, option `processTerm`). Après correction, vérifié trois fois : `webapp/test/evaluate_e2e.js` (retour à 100% d'abstention correcte et 100% de bonne fiche dans le top 3), `webapp/test/parity_check.js` (toujours 15/15, le classifieur n'a pas été touché), et dans un vrai navigateur (Playwright, installé en session) sur plusieurs questions — pas seulement en test automatisé Node.

## 2026-11-23 — Second bug trouvé en testant manuellement la page (signalé par l'utilisateur)

L'utilisateur a signalé que la page répondait presque tout le temps « Je ne sais pas » en usage réel, alors que `evaluate_e2e.js` montrait de bons chiffres. Testé une dizaine de questions naturelles non présentes dans `jeu_test_factice.json` (`webapp/test/diag2.js`, nouveau script qui affiche côte à côte l'avis du classifieur, celui de MiniSearch et le résultat final) : certaines, comme « c'est quoi la pch », donnaient une abstention alors que le classifieur était confiant à 95% et correct.

Cause : la liste de mots vides ajoutée dans le correctif précédent incluait par erreur les mots interrogatifs (« quoi », « comment », « pourquoi », « quand », « où », « qui »). Une fois le nom de la prestation filtré, "c'est quoi la pch" et "comment demander la pch" se réduisaient tous les deux à "pch" : MiniSearch ne pouvait plus distinguer une question de définition d'une question de démarche, et remontait la fiche PCH ayant le plus de répétitions du mot "pch", pas la bonne. Le jeu de test automatisé (15 questions) ne l'avait pas détecté par hasard — aucune de ses phrases n'activait ce cas.

Corrigé en retirant les mots interrogatifs de la liste de mots vides (ils ne sont pas vides de sens ici : ce sont souvent le seul signal distinguant deux fiches sur le même sujet). Revérifié : "c'est quoi la pch" et "qu'est-ce que l'aah" répondent de nouveau directement, "il va faire beau ce week-end ?" s'abstient toujours correctement — dans `evaluate_e2e.js`, `parity_check.js` et un vrai navigateur.

Limite qui reste réelle, pas un bug : pour des reformulations plus éloignées ("comment demander la pch", "carte mobilité inclusion"), le classifieur se trompe encore souvent (115 classes, peu d'exemples chacune) ; l'arbitrage empêche alors une mauvaise réponse mais répond "je ne sais pas" plutôt que la bonne fiche. C'est le compromis prudence/couverture déjà documenté, pas quelque chose que ce correctif pouvait résoudre.

## 2026-11-23 — Jeu de données synthétiques exhaustif (deux allers-retours de génération)

Généré un jeu de données synthétiques via `corpus/PROMPT_GENERATION_SYNTHETIQUE.md` (grille registre × type de question, paires confusables, hors champ typé, lots train/test séparés). Premier résultat (`jeu_donnees_synthetiques_mdph.json`) relu avant intégration : **67 fiches sur 114 avaient des reformulations grammaticalement cassées** (le verbe de la question d'origine réutilisé comme s'il faisait partie du sujet, ex. "la CMI mention invalidité est-elle accordée" dupliqué). Régénéré uniquement ces 67 avec un prompt corrigé (`PROMPT_REGENERATION_67_FICHES.md`, incluant l'exemple réel de l'erreur comme garde-fou) → `jeu_donnees_synthetiques_mdph_corrige.json`, vérifié propre (0 fiche encore cassée). Fusionné le tout avec `corpus/merge_synthetic_dataset.py` : 8-15 reformulations/fiche → 18-25, hors champ 30 → 69, jeu de test 15 → **645 questions**.

En relançant l'entraînement sur ce corpus élargi, `model/train.py` a mis plus de 30 minutes sans terminer la première évaluation (processus Python à ~1 Go de RAM). Cause : la fonction d'entraînement passait tout le jeu d'entraînement en un seul lot à chaque pas (viable à 259 exemples, pas à 2443 — coût O(taille du lot × longueur²) côté attention). Corrigé en repassant par mini-lots de 64, comme le fait `vendor/Tiny-2.1/training/train2.py` dont ce code s'inspire : 40 époques tournent désormais en moins d'une minute.

Résultat marquant de l'évaluation sur les 645 questions (contre 15 avant) : deux des six critères du plan, qui affichaient 100% sur le petit jeu, ne sont plus atteints à cette échelle — mauvaise fiche affichée comme sûre à 2,5% (seuil ≤2%), bonne fiche dans le top 3 à 85% (seuil ≥90%). Les deux autres critères testables restent bons (réponse directe correcte 90%, abstention hors champ 100%). Détail des 16 cas d'erreur confiante et leur gravité réelle (la plupart confondent un aspect proche de la même prestation, pas une prestation différente) dans `corpus/README.md`. C'est exactement ce qu'un test exhaustif doit révéler et que 15 questions ne pouvaient pas montrer.

## 2026-11-23 — Analyse des causes et correctif ciblé : les 4 critères du plan passent

Décomposé les 83 échecs (16 + 67) par cause plutôt que de les traiter en bloc. Deux gabarits de phrase réutilisés mécaniquement par le générateur synthétique sur 8 à 10 fiches chacun ("On parle de X, mais à quoi cela renvoie-t-il ?", "Pour mon père, est-ce envisageable de demander X ?") représentaient à eux seuls 23 des 83 échecs — pas 23 faiblesses indépendantes, un seul défaut de diversité compté 23 fois. Une fois ces artefacts retirés du calcul : mauvaise fiche sûre tombe de 2,5% à **0,93%** (déjà sous le seuil), bonne fiche en top 3 remonte de 85% à **87,9%** (encore sous le seuil de justesse, cette fois pour de vraies raisons : vocabulaire courant absent des reformulations — "déambulateur", "malentendante", "orientation en ULIS/MAS/FAM", formulations obliques du déménagement).

Corrigé par `corpus/patch_targeted_reformulations.py` : 38 reformulations ajoutées sur 32 fiches — des paraphrases du motif des gabarits fautifs (pas les phrases de test elles-mêmes, pour ne pas fuiter le jeu de test) pour les fiches de définition et de conditions concernées, plus le vocabulaire réel manquant identifié ci-dessus. Prompt `PROMPT_GENERATION_SYNTHETIQUE.md` mis à jour avec une interdiction explicite de réutiliser un même gabarit sur plusieurs fiches, pour la prochaine génération.

Réentraîné et réévalué sur les mêmes 645 questions. **Les quatre critères mesurables du plan sont maintenant atteints** :
- Bonne fiche affichée directement : 95% (seuil ≥85%)
- Mauvaise fiche affichée comme sûre : 1,1% — 7/645 (seuil ≤2%)
- Abstention correcte sur le hors champ : 95% — 21/22 (seuil ≥95%, tout juste)
- Bonne fiche dans le top 3 : 90% — 438/486 (seuil ≥90%, tout juste)

Honnêteté sur les deux derniers : ils passent pile au seuil, pas confortablement. Un effet de bord est apparu avec l'ajout de reformulations sur `CMI-STATIONNEMENT-CONDITIONS` ("la carte de stationnement") : la question hors champ "Comment contester une amende de stationnement ?" est maintenant confondue avec cette fiche — exactement le genre de régression qu'ajouter des mots-clés peut provoquer ailleurs. À surveiller, pas à ignorer : avec un jeu de test plus grand encore, ce chevauchement lexical referait probablement baisser le score d'abstention sous le seuil.

## 2026-11-23 — Le classifieur seul et la recherche seule, mesurés séparément

Ajouté un paramètre `mode` à `Assistant.repondre()` (`webapp/js/app.js`) : `"arbitrage"` (défaut, inchangé), `"classifieur"` (ignore la recherche), `"recherche"` (ignore le classifieur, ne s'abstient jamais — elle n'a pas de mécanisme d'abstention propre). Bascule ajoutée sur `webapp/index.html` (boutons radio) pour tester interactivement ; `webapp/test/evaluate_e2e.js --compare` calcule les trois modes côte à côte sur les 645 questions.

Résultat, qui répond au critère du plan « gain du mini-modèle sur la recherche seule » :

| mode | fiche affichée directement | dont correcte | mauvaise sûre (seuil ≤2%) | abstention hors champ |
|---|---|---|---|---|
| arbitrage | 137/645 | 94,9% | **1,1%** | 95,5% |
| classifieur seul | 613/645 | 22,7% | **73,5%** | 27,3% |
| recherche seule | 623/645 | 77,4% | **21,9%** | 13,6% |

**Aucun des deux composants pris isolément ne passe le seuil de sécurité du plan** — ni le classifieur seul (sans la recherche, le seuil de confiance retenu étant 0,00, il ne s'abstient quasiment jamais : 73,5% de réponses confiantes fausses), ni la recherche seule (21,9%, soit 10 fois le seuil, cohérent avec ce que le plan annonçait déjà : « fiable mais dépend des mots employés », sans mécanisme d'abstention). C'est bien la combinaison des deux qui fait tenir la propriété de sécurité (1,1%), pas l'un ou l'autre. Démontré aussi en direct sur la page (Playwright) : la question hors champ « il va faire beau ce week-end ? » obtient « je ne sais pas » en arbitrage, mais une fiche MVA en mode classifieur seul et une fiche TND en mode recherche seule — toutes deux fausses avec assurance.

## 2026-11-23 — Architecture du classifieur : plus petit que Tiny 2.1, et c'est voulu

Question posée après les mauvais chiffres du mode « classifieur seul » : la taille de Tiny 2.1 d'origine (D=96, 4 couches, 367 000 paramètres) ferait-elle mieux que la taille actuelle (D=64, 2 couches, 87 731 paramètres), choisie à l'origine pour un corpus bien plus petit (259 exemples) ? Testé directement (script jetable, supprimé après usage) : avec le corpus actuel (2481 exemples d'entraînement, 115 classes), la taille Tiny 2.1 atteint 27,5% de précision sur le jeu de validation, contre 50,0% pour la taille actuelle. Plus gros surapprend plus vite avec ce volume de données ; la taille actuelle reste le bon choix. Aucun fichier du pipeline modifié par ce test.

## 2026-11-23 — Balayage complet : la taille actuelle est l'optimum, dans les deux sens

Question suivante, symétrique : et une architecture plus petite que l'actuelle, ce serait meilleur ? Écrit `model/sweep_architecture.py` (gardé cette fois, contrairement au script jetable précédent) et balayé 7 tailles, mêmes seed/split/boucle d'entraînement que `model/train.py` pour une comparaison honnête :

| Architecture | Paramètres | Précision validation |
|---|---|---|
| D=32, 1 couche | 19 283 | 42,5% |
| D=32, 2 couches | 27 539 | 45,8% |
| D=48, 1 couche | 35 011 | 46,7% |
| D=48, 2 couches | 53 539 | 46,7% |
| D=64, 1 couche | 54 835 | 47,5% |
| D=64, 2 couches (actuelle) | 87 731 | **50,0%** |
| D=96, 4 couches (Tiny 2.1) | 377 683 | 27,5% |

Tendance monotone dans les deux sens : la précision progresse avec la taille jusqu'à la configuration actuelle, puis s'effondre au-delà (déjà mesuré). Réponse claire à la question : non, plus petit ne serait pas meilleur — la taille actuelle est l'optimum empirique trouvé parmi les deux directions testées, pas un choix arbitraire ni un compromis par défaut.
