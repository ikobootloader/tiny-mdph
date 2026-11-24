// Vérifie que l'inférence JS (classifier.js) donne les mêmes résultats que
// PyTorch (model/train.py), comme l'exige le plan de projet avant tout usage
// ("vérifier que la version JavaScript donne les mêmes prédictions que
// PyTorch sur tout le jeu de test"). Usage : node webapp/test/parity_check.js
const path = require("path");
global.window = global; // pour que classifier.js attache MiniClassifier ici

require(path.join(__dirname, "..", "data", "model.js"));
require(path.join(__dirname, "..", "js", "classifier.js"));

const fs = require("fs");
const expected = JSON.parse(fs.readFileSync(process.argv[2], "utf-8"));
// expected: [{question, className, confidence}, ...] produit par un script Python de contrôle

const clf = new MiniClassifier(window.MODEL);
let ok = 0;
for (const row of expected) {
  const r = clf.classify(row.question);
  const match = r.className === row.className && Math.abs(r.confidence - row.confidence) < 0.01;
  if (!match) {
    console.log("MISMATCH:", row.question, "attendu", row.className, row.confidence.toFixed(3),
      "obtenu", r.className, r.confidence.toFixed(3));
  } else ok++;
}
console.log(`${ok}/${expected.length} prédictions JS identiques à PyTorch (tolérance 0.01 sur la confiance)`);
if (ok !== expected.length) process.exit(1);
