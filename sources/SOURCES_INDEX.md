# Index des sources — mise à jour du 23/11/2026

Ce dossier `sources/` contient deux types de contenu :

- des **prototypes antérieurs** (`CHATBOT MDPH/`, `chatbot-keywords-mdph/`, `chatbot-rag-mdph/`), conservés tels quels ;
- des **sources documentaires officielles**, dont une partie vient d'être rafraîchie (ce document).

Conformément au plan de projet, ces sources alimentent la phase 1 (constitution du corpus de fiches). Elles ne remplacent pas le travail du comité métier : ce sont des matières premières à trier, pas des fiches validées.

## Sources récupérées le 23/11/2026

| Dossier | Contenu | Version / date trouvée | Licence | Remplace |
|---|---|---|---|---|
| `CNSA_TC_v2.3.2_2026-10/` | Tronc commun SI-MDPH : glossaire, modèles de courrier, motivations harmonisées, nomenclatures structurantes, tronc commun (5 PDF) + paquet "Référentiel Fonctionnel" (dictionnaire de données, spécifications de courriers, nomenclatures d'évaluation) | **V2.3.2**, publié par la CNSA en **octobre 2026** | CNSA — réutilisation à usage professionnel MDPH, statut à confirmer en phase 0 (comme noté dans le plan) | Les PDF V2.1.3 dans `CHATBOT MDPH/docs/` (obsolètes de 2 versions) |
| `formulaires_2026-11/cerfa_15692-01_MDPH.pdf` | Formulaire unique de demande/renouvellement MDPH (AAH, PCH, AEEH, CMI, ESAT, hébergement...) | **Cerfa 15692\*01**, fiche vérifiée le **13 juillet 2026** sur service-public.gouv.fr | Formulaire administratif public, libre diffusion | Confirme que le Cerfa 13788 dans le `LIRE_MOI.txt` du prototype `CHATBOT MDPH` est obsolète — ce numéro n'est plus accepté |
| `formulaires_2026-11/CNSA_guide_eligibilites_MDPH_2024-04.pdf` | Guide des éligibilités pour les décisions prises en CDAPH (toutes prestations, pas seulement l'AAH) | Publié par la CNSA, **avril 2024** | CNSA | Complète (ne remplace pas) le `guide_pratique_aah.pdf` de 2017 présent dans `CHATBOT MDPH/docs/`, qui ne couvre que l'AAH et date de 9 ans |
| `service-public-vectorise_2026-11/service_public_part_0.parquet` | Intégralité des fiches Service-Public.fr Particuliers, découpées et vectorisées (embeddings bge-m3) | Dataset **mis à jour le jour même (23/11/2026)**, hébergé par la DINUM sur Hugging Face (`AgentPublic/service-public`) | Licence Ouverte / Etalab 2.0 | Remplace la référence du plan à une « mise à jour trimestrielle » : la version réelle est mise à jour en continu |
| `service-public-vectorise_2026-11/corpus_handicap_mdph_extrait.jsonl` et `.csv` | Extraction filtrée du fichier ci-dessus : 601 passages / 84 fiches contenant un terme MDPH (handicap, AAH, PCH, RQTH, AEEH, CDAPH, CMI, ESAT, AESH...), sans les vecteurs d'embedding (fichier lisible) | Dérivé le 23/11/2026 | Idem | Point de départ concret pour la phase 1 (repérer les fiches à transformer en fiches validées) |

Le fichier `.parquet` complet pèse ~198 Mo (toutes thématiques confondues, pas seulement handicap) ; l'extrait `corpus_handicap_mdph_extrait.*` est la partie directement utile et pèse ~1,7 Mo.

## Compléments au tableau « Existant vérifié » du plan de projet

Ces points étaient signalés « à vérifier » ou incertains dans le plan du 22/11/2026 ; voici ce que la recherche du 23/11/2026 a permis de préciser.

- **Mesure 17 de la CNSA (chatbot juridique)** : au 20 octobre 2026, les résultats n'étaient toujours pas publiés malgré l'annonce d'une disponibilité mi-octobre (confirmé par ActuIA). Une recherche plus récente indique que **les MDPH participantes doivent transmettre leur rapport d'expérimentation à la CNSA jusqu'au 31 décembre 2026** — la publication des résultats est donc probablement plus tardive que prévu dans le plan. À reconfirmer directement auprès de la CNSA en phase 0, comme déjà prévu.
- **Code de l'action sociale et des familles (Légifrance)** : les textes de Légifrance sont diffusés sous Licence Ouverte/Etalab 2.0 (cadre CRPA), comme les fiches Service-Public. Le point « à vérifier » du plan peut donc être levé : la réutilisation est libre, sous réserve de la mention de source et de date habituelle.
- **CERFA de la demande MDPH** : confirmé toujours en vigueur sous le numéro **15692\*01** (le 13788 cité dans un ancien prototype local est obsolète). Un formulaire simplifié est expérimenté depuis mars 2026 dans 5 départements pilotes, mais n'est pas encore généralisé.

## Non fait / limites

- Je n'ai pas trouvé de documents CNSA « Orientations métier » (EA-MISPE/PCPE, PAG, Recours, révision tiers) en version plus récente que le V2.1.3 déjà présent localement — ils ne figurent pas dans le paquet V2.3.2 téléchargé. Possible qu'ils n'aient pas été republiés séparément ou qu'ils soient fusionnés dans le document "Tronc commun" principal.
- Le contenu propre à la MDA (portail, procédures internes) reste hors de portée : seul le comité métier de la MDA peut le fournir.
- Fiabilité : plusieurs informations ci-dessus proviennent de résumés de recherche web (non lus en intégralité) ou de sites tiers non officiels (comparateurs, blogs) quand la source officielle était inaccessible — acceptable pour cette phase de test de viabilité, mais à revérifier avant tout usage en production, conformément à la règle n°1 du plan (aucune réponse affichée sans fiche validée).
