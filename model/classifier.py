# -*- coding: utf-8 -*-
"""Mini-classifieur char-level, construit sur les briques de vendor/Tiny-2.1
(train2.py) : mêmes blocs transformer (attention causale + MLP, RMSNorm),
mais une tête de classification à la place de la sortie générative, comme
demandé par le plan de projet ("partir de train2.py [...] remplacer la sortie
générative par une tête de classification")."""
import os
import sys
import unicodedata
import torch
import torch.nn as nn

VENDOR_TRAINING = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "vendor", "Tiny-2.1", "training",
)
sys.path.insert(0, VENDOR_TRAINING)
import train2 as tiny  # noqa: E402  (Block, Norm, Cfg, encode, VOCAB, CTX)

PAD = 0  # encode() never produces 0, donc 0 sert de padding


def normalize_text(s):
    """Minuscules, accents normalisés (retirés), comme demandé par le plan de
    projet pour la robustesse aux sigles et aux fautes de frappe. tiny.encode
    ne gère que l'ASCII imprimable (32..126) : les accents doivent partir
    avant, sous peine d'index hors de la table d'embedding."""
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return "".join(c if 32 <= ord(c) <= 126 or c == "\n" else " " for c in s)


def encode_padded(texts, max_ctx=tiny.CTX):
    ids = [tiny.encode(normalize_text(t))[: max_ctx - 1] for t in texts]
    T = max(1, max(len(s) for s in ids))
    x = torch.zeros(len(ids), T, dtype=torch.long)
    lengths = torch.zeros(len(ids), dtype=torch.long)
    for i, s in enumerate(ids):
        x[i, : len(s)] = torch.tensor(s, dtype=torch.long)
        lengths[i] = max(len(s) - 1, 0)  # index du dernier token réel
    return x, lengths


class Classifier(nn.Module):
    """Mêmes briques que tiny.Model (emb, pos, blocks, norme finale), plus une
    tête linéaire D -> nb_classes appliquée sur le dernier token de la
    question (l'attention causale lui a déjà fait voir toute la question)."""

    def __init__(self, cfg, n_classes):
        super().__init__()
        self.c = cfg
        self.emb = nn.Embedding(tiny.VOCAB, cfg.D)
        self.pos = nn.Embedding(tiny.CTX, cfg.D)
        self.blocks = nn.ModuleList([tiny.Block(cfg) for _ in range(cfg.L)])
        self.nf = tiny.Norm(cfg.D)
        self.head = nn.Linear(cfg.D, n_classes, bias=True)
        nn.init.normal_(self.emb.weight, std=0.05)
        nn.init.normal_(self.pos.weight, std=0.05)
        for b in self.blocks:
            for m in (b.q, b.k, b.v, b.o, b.f1, b.f2):
                nn.init.normal_(m.weight, std=0.5 / (m.in_features ** 0.5))
        nn.init.zeros_(self.head.bias)
        nn.init.normal_(self.head.weight, std=0.02)

    def forward(self, idx, lengths):
        x = self.emb(idx) + self.pos(torch.arange(idx.shape[1]))
        for b in self.blocks:
            x = b(x)
        x = self.nf(x)
        pooled = x[torch.arange(x.shape[0]), lengths]
        return self.head(pooled)
