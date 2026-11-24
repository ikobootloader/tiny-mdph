// Évalue le système complet (recherche + classifieur + arbitrage) tel qu'il
// tourne réellement dans la page HTML, sur le jeu de test factice. Reprend
// les mesures du plan de projet (section "Évaluation et critères
// d'acceptation"), à l'échelle jouet de ce corpus factice.
// Usage : node webapp/test/evaluate_e2e.js
const path = require("path");
const fs = require("fs");

global.window = global;
global.MiniSearch = require(path.join(__dirname, "..", "..", "vendor", "minisearch", "dist", "umd", "index.js"));
require(path.join(__dirname, "..", "data", "model.js"));
require(path.join(__dirname, "..", "data", "fiches.js"));
require(path.join(__dirname, "..", "js", "classifier.js"));
require(path.join(__dirname, "..", "js", "app.js"));

const assistant = new MiniIAAssistant(window.MODEL, window.FICHES);

const testSet = JSON.parse(fs.readFileSync(
  path.join(__dirname, "..", "..", "corpus", "jeu_test_factice.json"), "utf-8"));

let bonneFicheDirecte = 0, mauvaiseFicheSure = 0, nbDirecte = 0;
let abstentionHorsChamp = 0, nbHorsChamp = 0;
let bonneDansLes3 = 0, nbAbstentionSurChamp = 0;

for (const row of testSet) {
  const r = assistant.repondre(row.question);
  const estHorsChamp = row.id_attendu === "HORS_CHAMP";

  if (estHorsChamp) {
    nbHorsChamp++;
    if (r.type === "abstention") abstentionHorsChamp++;
    else console.log(`  [hors champ affiché comme sûr] "${row.question}" -> ${r.fiche.id}`);
  } else if (r.type === "fiche") {
    nbDirecte++;
    if (r.fiche.id === row.id_attendu) bonneFicheDirecte++;
    else { mauvaiseFicheSure++; console.log(`  [mauvaise fiche sûre] "${row.question}" -> ${r.fiche.id} (attendu ${row.id_attendu})`); }
  } else {
    nbAbstentionSurChamp++;
    if (r.proches.some((f) => f.id === row.id_attendu)) bonneDansLes3++;
    else console.log(`  [absent du top 3] "${row.question}" -> [${r.proches.map((f) => f.id).join(", ")}] (attendu ${row.id_attendu})`);
  }
}

console.log("\n--- Résultats sur le jeu de test factice (" + testSet.length + " questions) ---");
console.log(`Fiche affichée directement : ${nbDirecte}/${testSet.length}`);
console.log(`  dont correcte : ${bonneFicheDirecte}/${nbDirecte || 1} = ${(100 * bonneFicheDirecte / (nbDirecte || 1)).toFixed(0)}%  (seuil plan : >=85%)`);
console.log(`  dont incorrecte (mauvaise fiche affichée comme sûre) : ${mauvaiseFicheSure}  (seuil plan : <=2% du total)`);
console.log(`Abstention correcte sur hors champ : ${abstentionHorsChamp}/${nbHorsChamp} = ${(100 * abstentionHorsChamp / (nbHorsChamp || 1)).toFixed(0)}%  (seuil plan : >=95%)`);
console.log(`Bonne fiche dans le top 3 quand abstention (hors cas hors-champ) : ${bonneDansLes3}/${nbAbstentionSurChamp || 1} = ${(100 * bonneDansLes3 / (nbAbstentionSurChamp || 1)).toFixed(0)}%  (seuil plan : >=90%)`);
