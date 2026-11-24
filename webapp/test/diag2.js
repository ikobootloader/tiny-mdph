const path = require("path");
global.window = global;
global.MiniSearch = require(path.join(__dirname, "..", "..", "vendor", "minisearch", "dist", "umd", "index.js"));
require(path.join(__dirname, "..", "data", "model.js"));
require(path.join(__dirname, "..", "data", "fiches.js"));
require(path.join(__dirname, "..", "js", "classifier.js"));
require(path.join(__dirname, "..", "js", "app.js"));
const assistant = new MiniIAAssistant(window.MODEL, window.FICHES);
const qs = process.argv.slice(2);
for (const q of qs) {
  const r = assistant.repondre(q);
  const cls = assistant.classifier.classify(q);
  const hits = assistant.search.search(q);
  console.log(`Q: ${q}`);
  console.log(`  classifieur -> ${cls.className} (${cls.confidence.toFixed(2)})`);
  console.log(`  recherche   -> ${hits.length ? hits[0].id + ' (' + hits[0].score.toFixed(1) + ')' : '(aucun hit)'}`);
  console.log(`  resultat    -> ${r.type === 'fiche' ? 'FICHE: ' + r.fiche.id : 'ABSTENTION'}`);
  console.log();
}
