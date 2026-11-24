const path = require("path");
global.window = global;
global.MiniSearch = require(path.join(__dirname, "..", "..", "vendor", "minisearch", "dist", "umd", "index.js"));
require(path.join(__dirname, "..", "data", "model.js"));
require(path.join(__dirname, "..", "data", "fiches.js"));
require(path.join(__dirname, "..", "js", "classifier.js"));
require(path.join(__dirname, "..", "js", "app.js"));

const assistant = new MiniIAAssistant(window.MODEL, window.FICHES);

const q = process.argv[2] || "il va faire beau ce week-end ?";
const cls = assistant.classifier.classify(q);
console.log("=== classifieur ===");
console.log("classe predite:", cls.className, "confiance:", cls.confidence.toFixed(3));
const ranked = cls.probs.map((p, i) => ({ p, name: window.MODEL.classes[i] })).sort((a, b) => b.p - a.p).slice(0, 8);
for (const r of ranked) console.log("  ", r.name, r.p.toFixed(3));

console.log("\n=== minisearch ===");
const hits = assistant.search.search(q);
console.log("nb hits:", hits.length);
for (const h of hits.slice(0, 8)) console.log("  ", h.id, h.score.toFixed(3), JSON.stringify(h.terms));

console.log("\n=== seuil ===", assistant.threshold);
