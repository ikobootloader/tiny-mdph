# -*- coding: utf-8 -*-
"""Rejoue le modèle entraîné (out/classifier.pt) sur le jeu de test factice et
écrit les prédictions PyTorch dans out/parity_reference.json, pour que
webapp/test/parity_check.js vérifie que la version JavaScript calcule
exactement la même chose."""
import json
import os

import torch
import torch.nn.functional as F

import classifier as C
import dataset as D
import train2 as tiny  # noqa: F401

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")

ck = torch.load(os.path.join(OUT_DIR, "classifier.pt"), map_location="cpu")
cfg = tiny.Cfg(**ck["cfg"])
model = C.Classifier(cfg, len(ck["classes"]))
model.load_state_dict(ck["sd"])
model.eval()

# Le fichier exporté en JS (model/export_js.py) est quantifié en 8 bits : pour
# comparer "les mêmes prédictions que PyTorch", il faut comparer au modèle
# quantifié, pas au modèle flottant d'origine (sinon l'écart mesuré est celui
# de la quantification, pas un bug éventuel de l'implémentation JS).
with torch.no_grad():
    for n, p in model.named_parameters():
        if p.dim() == 2:
            s = (p.abs().amax(1, keepdim=True) / 127.0).clamp_min(1e-8)
            p.copy_(torch.clamp(torch.round(p / s), -127, 127) * s)

test = D.load_test_set()
texts = [t["question"] for t in test]
x, lengths = C.encode_padded(texts)
with torch.no_grad():
    probs = F.softmax(model(x, lengths), dim=-1)
conf, idx = probs.max(-1)

rows = [{"question": q, "className": ck["classes"][i], "confidence": c.item()}
        for q, i, c in zip(texts, idx.tolist(), conf)]
path = os.path.join(OUT_DIR, "parity_reference.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)
print(f"écrit {path} ({len(rows)} questions)")
