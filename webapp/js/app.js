// Arbitrage recherche plein texte (MiniSearch) + mini-classifieur, comme
// décrit dans le plan de projet : si les deux avis désignent la même fiche
// avec un score suffisant, elle s'affiche ; sinon, abstention + 3 fiches
// proches. Aucune donnée n'est envoyée nulle part : tout tourne en local.
(function (global) {
  "use strict";

  const HORS_CHAMP = "HORS_CHAMP";

  // MiniSearch ne filtre aucun mot vide par défaut (processTerm ne fait que
  // minusculiser). Sans cette liste, une question comme "il va faire beau ce
  // week-end ?" matche sur "il"/"ce"/"en" et remonte une fiche au hasard avec
  // un score élevé simplement parce qu'elle contient ces mots de liaison.
  //
  // Attention : les mots interrogatifs (quoi, comment, pourquoi, quand, où,
  // qui, que) ne sont PAS des mots vides ici — ce sont souvent le seul signal
  // qui distingue "qu'est-ce que la PCH" (définition) de "comment demander la
  // PCH" (démarches) une fois le nom de la prestation filtré. Les retirer a
  // provoqué une régression (toute question PCH retombait sur la même fiche
  // au hasard) : ne pas les remettre dans cette liste.
  const STOPWORDS_FR = new Set((
    "le la les l un une des de du d au aux ce cet cette ces il elle ils elles " +
    "je tu nous vous on est sont être avoir a ont pas ne " +
    "pour par sur sous dans avec sans et ou mais donc or ni car en y se sa son " +
    "ses leur leurs mon ma mes ton ta tes notre nos votre vos si plus moins " +
    "faire fait va vais vont été ça cela"
  ).split(" "));

  function processTerm(term) {
    const t = term.toLowerCase();
    return STOPWORDS_FR.has(t) ? null : t;
  }

  function buildSearchIndex(fiches) {
    const idx = new MiniSearch({
      fields: ["question", "reformulations", "reponse"],
      storeFields: ["id"],
      processTerm,
      searchOptions: { prefix: true, fuzzy: 0.2, boost: { question: 2, reformulations: 2 } },
    });
    idx.addAll(fiches.map((f) => ({
      id: f.id,
      question: f.question,
      reformulations: f.reformulations.join(" "),
      reponse: f.reponse,
    })));
    return idx;
  }

  class Assistant {
    constructor(model, fiches) {
      this.classifier = new MiniClassifier(model);
      this.threshold = model.threshold;
      this.fiches = fiches;
      this.byId = Object.fromEntries(fiches.map((f) => [f.id, f]));
      this.search = buildSearchIndex(fiches);
    }

    // Renvoie soit {type:"fiche", fiche, confidence}, soit
    // {type:"abstention", proches:[fiche,fiche,fiche]}.
    repondre(question) {
      const q = (question || "").trim();
      const cls = this.classifier.classify(q);
      const searchHits = this.search.search(q);
      const topSearchId = searchHits.length ? searchHits[0].id : null;

      const accord = cls.className !== HORS_CHAMP &&
        cls.className === topSearchId &&
        cls.confidence >= this.threshold;

      if (accord) {
        return { type: "fiche", fiche: this.byId[cls.className], confidence: cls.confidence };
      }

      const proches = [];
      const seen = new Set();
      for (const hit of searchHits) {
        if (!seen.has(hit.id) && this.byId[hit.id]) { proches.push(this.byId[hit.id]); seen.add(hit.id); }
        if (proches.length >= 3) break;
      }
      if (proches.length < 3) {
        // Complète avec les classes les mieux notées par le classifieur, au cas
        // où la recherche plein texte n'a rien trouvé du tout.
        const ranked = cls.probs
          .map((p, i) => ({ p, name: this.classifier.m.classes[i] }))
          .filter((r) => r.name !== HORS_CHAMP && this.byId[r.name] && !seen.has(r.name))
          .sort((a, b) => b.p - a.p);
        for (const r of ranked) {
          proches.push(this.byId[r.name]);
          seen.add(r.name);
          if (proches.length >= 3) break;
        }
      }
      return { type: "abstention", proches };
    }
  }

  global.MiniIAAssistant = Assistant;
})(typeof window !== "undefined" ? window : globalThis);
