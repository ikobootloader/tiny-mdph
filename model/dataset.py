# -*- coding: utf-8 -*-
"""Charge le corpus factice (corpus/fiches.json, corpus/hors_champ.json) et
construit les exemples (texte, label) pour l'entraînement du classifieur.

Le jeu de test (corpus/jeu_test_factice.json) n'est volontairement PAS chargé
ici : il ne doit jamais servir à l'entraînement (voir plan de projet)."""
import json
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_DIR = os.path.join(ROOT, "corpus")

HORS_CHAMP_LABEL = "HORS_CHAMP"


def load_fiches():
    with open(os.path.join(CORPUS_DIR, "fiches.json"), encoding="utf-8") as f:
        return json.load(f)


def load_hors_champ():
    with open(os.path.join(CORPUS_DIR, "hors_champ.json"), encoding="utf-8") as f:
        return json.load(f)


def load_test_set():
    with open(os.path.join(CORPUS_DIR, "jeu_test_factice.json"), encoding="utf-8") as f:
        return json.load(f)


def build_examples(seed=0, val_per_class=1):
    """Retourne (classes, train, val) où `classes` liste les ids de fiche plus
    HORS_CHAMP (dans cet ordre, pour que l'export JS soit stable), et train/val
    sont des listes de (texte, index_de_classe).

    Une reformulation par fiche part en validation (réglage du seuil), le
    reste à l'entraînement. Pour HORS_CHAMP, un dixième des questions part en
    validation."""
    fiches = load_fiches()
    hors_champ = load_hors_champ()
    classes = [f["id"] for f in fiches] + [HORS_CHAMP_LABEL]
    index = {c: i for i, c in enumerate(classes)}

    rng = random.Random(seed)
    train, val = [], []

    for f in fiches:
        texts = [f["question"]] + list(f["reformulations"])
        rng.shuffle(texts)
        for t in texts[:val_per_class]:
            val.append((t, index[f["id"]]))
        for t in texts[val_per_class:]:
            train.append((t, index[f["id"]]))

    hc = list(hors_champ)
    rng.shuffle(hc)
    n_val = max(1, len(hc) // 10)
    for t in hc[:n_val]:
        val.append((t, index[HORS_CHAMP_LABEL]))
    for t in hc[n_val:]:
        train.append((t, index[HORS_CHAMP_LABEL]))

    rng.shuffle(train)
    return classes, train, val


if __name__ == "__main__":
    classes, train, val = build_examples()
    print(len(classes), "classes (dont HORS_CHAMP)")
    print(len(train), "exemples d'entraînement,", len(val), "exemples de validation")
