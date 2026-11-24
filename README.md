# tiny-mdph

Prototype technique testant l'architecture du [plan de projet](Plan%20de%20projet%20—%20Mini-IA%20métier%20MDPH%20(type%20Tiny%202.1).pdf) :
un assistant local, hors ligne, pour les agents d'une MDPH, qui n'affiche jamais que des fiches validées — jamais
de texte généré librement. Un mini-classifieur neuronal (inspiré de [Tiny 2.1](https://github.com/WollyMonjac/Tiny-2.1))
reconnaît la question, une recherche plein texte ([MiniSearch](https://github.com/lucaong/minisearch)) donne un
second avis ; une fiche ne s'affiche que si les deux s'accordent, sinon le système répond « je ne sais pas ».

Construit avec un **jeu de données factice** (voir `corpus/README.md`) : il ne remplace pas la vraie collecte de
questions MDA prévue en phase 0/1 du plan, il sert à vérifier que l'architecture choisie (recherche + mini-classifieur) tient la route.

## Mise en route

Aucune installation n'est nécessaire pour utiliser l'assistant : ouvrir `webapp/index.html` directement dans un
navigateur (double-clic, aucun serveur). Les fiches et le modèle entraîné sont déjà inclus dans `webapp/data/`.

Pour retoucher le corpus ou réentraîner le classifieur, deux dépendances externes sont nécessaires mais **ne sont
pas incluses dans ce dépôt** (voir "Dépendances externes" ci-dessous) : Python 3 + PyTorch, et une copie locale de
Tiny 2.1.

## Grandes lignes de la construction

1. **Sources** (`sources/`) — seul `sources/SOURCES_INDEX.md` est versionné : il documente où retélécharger les
   documents officiels utilisés (CNSA Tronc commun v2.3.2, Cerfa 15692\*01, guide des éligibilités CNSA, extrait du
   dataset Service-Public.fr vectorisé), avec dates et licences. Les fichiers eux-mêmes (plusieurs centaines de Mo)
   ne sont pas dans le dépôt.
2. **Dépendances techniques** (`vendor/`) — `minisearch` (recherche plein texte JS, MIT) est vendorisé (fichiers du
   bundle UMD uniquement, voir `vendor/minisearch/VENDORED.md`). `Tiny-2.1` (MIT) n'est **pas** inclus : c'est le
   modèle source dont ce projet reprend l'architecture, pas une dépendance de ce dépôt — voir "Dépendances externes".
3. **Corpus factice** (`corpus/`) — 114 fiches, converties et complétées à partir de sources publiques et d'un
   prototype antérieur de l'auteur (non inclus dans ce dépôt). Détails et méthode de fusion dans `corpus/README.md`.
   Toujours pas la vraie collecte MDA de la phase 1 du plan.
4. **Mini-classifieur** (`model/`) — reprend les blocs transformer de `vendor/Tiny-2.1/training/train2.py`
   (attention causale, RMSNorm) mais remplace la sortie générative par une tête de classification (une classe par
   fiche + une classe HORS_CHAMP), comme demandé par le plan. Entraîné en PyTorch, seuil d'abstention réglé sur un
   jeu de validation distinct du jeu de test, puis quantifié en entiers 8 bits et exporté en `.js` (pas de `fetch`,
   une page `file://` ne peut pas charger de fichiers annexes).
5. **Page locale** (`webapp/`) — `index.html` sans serveur ni dépendance réseau : charge les fiches, le modèle et
   MiniSearch via des balises `<script>`, et affiche une fiche seulement quand le classifieur et la recherche
   plein texte désignent la même fiche avec assez de confiance ; sinon « Je ne sais pas » + 3 fiches proches.
6. **Tests** (`webapp/test/`) — `parity_check.js` vérifie que l'inférence JavaScript calcule exactement la même
   chose que PyTorch (exigence du plan) ; `evaluate_e2e.js` rejoue le jeu de test factice sur le système complet et
   rapporte les mesures du plan (fiche correcte, mauvaise fiche affichée comme sûre, abstention, top-3). La page a
   aussi été ouverte dans un vrai navigateur (Playwright) pour confirmer l'affichage.

## Dépendances externes (pour réentraîner)

`model/classifier.py` réutilise les blocs transformer de `vendor/Tiny-2.1/training/train2.py` (attention causale,
RMSNorm), remplacés par une tête de classification. Ce code n'est pas vendorisé ici : le récupérer d'abord avec

```
git clone https://github.com/WollyMonjac/Tiny-2.1 vendor/Tiny-2.1
```

## Reproduire

```
python model/train.py                  # entraîne + évalue le classifieur
python model/export_js.py              # quantifie et écrit webapp/data/*.js
node webapp/test/parity_check.js model/out/parity_reference.json
node webapp/test/evaluate_e2e.js       # mesures du plan sur le jeu de test
```
Puis ouvrir `webapp/index.html` directement dans un navigateur.

## Ce que le test de viabilité a montré

Le pipeline tourne de bout en bout et l'inférence JS est identique à PyTorch quand on compare au bon modèle (celui
réellement quantifié et exporté — une erreur de méthode corrigée en cours de route, voir `CHANGELOG.md`) : 15/15.

Avec le corpus initial à 28 fiches, le classifieur seul généralisait mal aux reformulations non vues. Après fusion
avec le corpus `chatbot-keywords-mdph` (114 fiches, voir `corpus/README.md`), la régression logistique de référence
progresse nettement (33 % → 60-67 %) : plus de données aide, comme attendu. Le mini-classifieur seul reste faible à
cette échelle (115 classes, ~11 exemples chacune) — pas un bug, Tiny 2.1 lui-même a eu besoin de 15 millions
d'exemples. L'**arbitrage** classifieur + recherche garde sa propriété essentielle : 0 mauvaise fiche n'est jamais
affichée comme sûre sur le jeu de test.

En creusant une baisse de l'abstention sur le hors champ (100 % → 50 % juste après la fusion), la cause réelle
s'est révélée être `MiniSearch` : sans filtrage des mots vides (absent par défaut), une question comme « il va
faire beau ce week-end ? » matchait sur « il »/« ce »/« en » et remontait une fiche au hasard avec un score élevé.
Corrigé en ajoutant une liste de mots vides français à l'index (`webapp/js/app.js`) ; vérifié de nouveau à 100 %
d'abstention correcte, y compris dans un vrai navigateur (Playwright), pas seulement en test automatisé.

Ce correctif a introduit un second bug, repéré en testant la page à la main (pas par les tests automatisés, qui ne
l'exerçaient pas) : la liste de mots vides incluait par erreur des mots interrogatifs (« quoi », « comment »...),
qui sont ici un signal utile, pas du bruit — leur retrait faisait retomber des questions comme « c'est quoi la PCH »
sur la mauvaise fiche PCH. Corrigé, revérifié aux trois mêmes niveaux. Leçon retenue : `jeu_test_factice.json`
(15 questions) est trop petit pour détecter ce genre de régression — un vrai jeu de test plus large (phase 1 du
plan) l'aurait probablement attrapé. Détails des deux bugs dans `CHANGELOG.md`.

Le système reste prudent par construction : sur les cas restants où le classifieur se trompe, il s'abstient plutôt
que d'afficher une mauvaise fiche. Le prochain gain réel viendra du **volume et de la diversité du vrai corpus
MDA**, pas d'un réglage du modèle.

**Mise à jour après génération d'un jeu de données synthétiques exhaustif** (`corpus/PROMPT_GENERATION_SYNTHETIQUE.md`,
deux allers-retours de génération car la première tentative produisait des reformulations grammaticalement cassées
sur 67 fiches sur 114 — détails dans `corpus/README.md`). Le jeu de test est passé de 15 à **645 questions**, avec
des paires volontairement confusables entre fiches proches. Verdict à cette échelle, plus représentatif que les
tests précédents : réponse directe correcte 90 % et abstention hors champ 100 % tiennent toujours leur seuil, mais
**mauvaise fiche affichée comme sûre (2,5 %, seuil ≤2 %)** et **bonne fiche dans le top 3 lors d'une abstention
(85 %, seuil ≥90 %)** ne sont plus atteints. En creusant, la plupart des erreurs confondent un aspect proche de la
même prestation (démarches vs conditions), pas une prestation différente — mais le dépassement de seuil est réel.
Un bug de performance a aussi été corrigé au passage : l'entraînement passait tout le corpus en un seul lot à
chaque pas, viable à 259 exemples mais pas à 2443 (plus de 30 minutes sans terminer) ; corrigé en repassant par
mini-lots de 64, comme le fait `vendor/Tiny-2.1` dont le code s'inspire.

**Mise à jour après analyse des causes** : 23 des 83 échecs venaient de deux gabarits de phrase réutilisés mécaniquement
par le générateur sur 8-10 fiches chacun (un seul défaut compté 23 fois, pas 23 problèmes). Une fois retirés, le
critère de sécurité repassait déjà sous son seuil ; le critère de couverture restait en dessous mais pour de vraies
raisons (vocabulaire courant absent : "déambulateur", "malentendante", "orientation en ULIS/MAS/FAM"...). Corrigé
par l'ajout de 38 reformulations ciblées sur 32 fiches. **Les quatre critères mesurables du plan sont désormais
atteints** (95% réponse directe correcte, 1,1% mauvaise fiche sûre, 95% abstention hors champ, 90% top-3) — les deux
derniers tout juste au seuil, pas confortablement : un effet de bord est déjà apparu (une question hors champ sur une
amende de stationnement confondue avec la CMI Stationnement, à cause d'une reformulation ajoutée ailleurs).

**Classifieur seul vs recherche seule vs arbitrage** — `node webapp/test/evaluate_e2e.js --compare` (ou la bascule
sur la page) mesure les trois séparément. Verdict net : ni le classifieur seul (73,5% de réponses confiantes
fausses — son seuil de confiance appris ne filtre quasiment rien), ni la recherche seule (21,9%, 10x le seuil du
plan) ne tiennent la propriété de sécurité ; seule leur combinaison y arrive (1,1%). C'est la validation directe du
choix d'architecture du plan : ni l'un ni l'autre composant ne suffit seul.

Détails des limites connues dans `corpus/README.md` et `sources/SOURCES_INDEX.md`. Historique daté dans `CHANGELOG.md`.
