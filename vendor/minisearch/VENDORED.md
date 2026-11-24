# minisearch (vendorisé)

Fichiers de `minisearch@7.2.0` (https://github.com/lucaong/minisearch), licence MIT
(voir `LICENSE.txt`). Seuls les fichiers du bundle UMD nécessaires à l'exécution
dans le navigateur sont conservés (`dist/umd/`) — pas les sources TypeScript, les
tests ni les exemples du dépôt d'origine.

`dist/umd/package.json` force `"type": "commonjs"` pour que Node.js (utilisé par
les tests dans `webapp/test/`) traite `index.js` comme un module CommonJS, car
le `package.json` du dépôt minisearch déclare `"type": "module"` au niveau racine.
