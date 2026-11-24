# -*- coding: utf-8 -*-
"""Quantifie le classifieur entraîné (model/out/classifier.pt) en entiers 8
bits (une échelle par ligne, comme Tiny 2.1) et l'écrit dans un fichier .js
autonome (webapp/data/model.js), chargé par <script> dans la page locale —
une page ouverte en file:// ne peut pas faire de fetch().
Écrit aussi webapp/data/fiches.js à partir de corpus/fiches.json."""
import json
import os

import numpy as np
import torch

import classifier as C
import train2 as tiny  # noqa: F401

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
WEBAPP_DATA = os.path.join(ROOT, "webapp", "data")
os.makedirs(WEBAPP_DATA, exist_ok=True)


def quantize_row_major(w):
    """w: tensor 2D -> (scales par ligne [R], int8 [R,C])."""
    arr = w.detach().numpy().astype(np.float32)
    scales = np.maximum(np.abs(arr).max(axis=1) / 127.0, 1e-8)
    q = np.clip(np.round(arr / scales[:, None]), -127, 127).astype(np.int8)
    return scales.tolist(), q.tolist()


def quantized_tensor(name, w):
    scales, q = quantize_row_major(w)
    return {"shape": list(w.shape), "scales": scales, "int8": q}


def export_model():
    ck = torch.load(os.path.join(OUT_DIR, "classifier.pt"), map_location="cpu")
    cfg = tiny.Cfg(**ck["cfg"])
    model = C.Classifier(cfg, len(ck["classes"]))
    model.load_state_dict(ck["sd"])
    model.eval()
    sd = model.state_dict()

    blocks = []
    for i in range(cfg.L):
        p = f"blocks.{i}."
        blocks.append({
            "n1": sd[p + "n1.g"].tolist(),
            "n2": sd[p + "n2.g"].tolist(),
            "q": quantized_tensor("q", sd[p + "q.weight"]),
            "k": quantized_tensor("k", sd[p + "k.weight"]),
            "v": quantized_tensor("v", sd[p + "v.weight"]),
            "o": quantized_tensor("o", sd[p + "o.weight"]),
            "f1": quantized_tensor("f1", sd[p + "f1.weight"]),
            "f2": quantized_tensor("f2", sd[p + "f2.weight"]),
        })

    out = {
        "format": "mini-ia-mdph-classifier-v1",
        "cfg": {"D": cfg.D, "L": cfg.L, "H": cfg.H, "HID": cfg.HID},
        "vocab": tiny.VOCAB,
        "ctx": tiny.CTX,
        "classes": ck["classes"],
        "threshold": ck["threshold"],
        "emb": quantized_tensor("emb", sd["emb.weight"]),
        "pos": quantized_tensor("pos", sd["pos.weight"]),
        "blocks": blocks,
        "nf": sd["nf.g"].tolist(),
        "head_w": quantized_tensor("head_w", sd["head.weight"]),
        "head_b": sd["head.bias"].tolist(),
    }

    path = os.path.join(WEBAPP_DATA, "model.js")
    with open(path, "w", encoding="utf-8") as f:
        f.write("// Généré par model/export_js.py — ne pas éditer à la main.\n")
        f.write("window.MODEL = ")
        json.dump(out, f, separators=(",", ":"))
        f.write(";\n")
    size_kb = os.path.getsize(path) / 1024
    print(f"écrit {path} ({size_kb:.0f} Ko)")


def export_fiches():
    with open(os.path.join(ROOT, "corpus", "fiches.json"), encoding="utf-8") as f:
        fiches = json.load(f)
    path = os.path.join(WEBAPP_DATA, "fiches.js")
    with open(path, "w", encoding="utf-8") as f:
        f.write("// Généré par model/export_js.py à partir de corpus/fiches.json.\n")
        f.write("window.FICHES = ")
        json.dump(fiches, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    print(f"écrit {path} ({len(fiches)} fiches)")


if __name__ == "__main__":
    export_model()
    export_fiches()
