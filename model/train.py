# -*- coding: utf-8 -*-
"""Entraîne le mini-classifieur sur le corpus factice, compare avec la
régression logistique de référence (n-grammes de caractères), règle le seuil
d'abstention sur le jeu de validation, puis évalue sur le jeu de test factice
(jamais vu à l'entraînement). Usage : python train.py
"""
import json
import os
import random

import numpy as np
import torch
import torch.nn.functional as F

import classifier as C
import dataset as D
import train2 as tiny  # noqa: F401 (déjà sur sys.path via classifier.py)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT_DIR, exist_ok=True)


def train_model(classes, train_examples, val_examples, epochs=40, bs=64, seed=0):
    """Entraîne par mini-lots (comme vendor/Tiny-2.1/training/train2.py, pas en
    un seul lot géant) : avec le corpus élargi (~2500 exemples après la fusion
    synthétique), un lot complet à chaque pas rendait chaque pas O(B·T²) sur
    tout le jeu d'entraînement — correct à 259 exemples, mais rédhibitoire à
    2500 (le premier essai a dépassé 30 minutes sans terminer un seul passage
    de journalisation). Les mini-lots rendent le coût par pas indépendant de
    la taille du corpus. Arrêt précoce : on garde l'état dont la validation
    est la meilleure, pas celui de fin d'entraînement."""
    torch.manual_seed(seed)
    rng = random.Random(seed)
    cfg = tiny.Cfg(D=64, L=2, H=4, HID=128)
    model = C.Classifier(cfg, len(classes))
    opt = torch.optim.AdamW(model.parameters(), lr=3e-3, weight_decay=0.05)

    val_texts = [t for t, _ in val_examples]
    val_labels = torch.tensor([y for _, y in val_examples], dtype=torch.long)
    vx, vlen = C.encode_padded(val_texts)

    steps_per_epoch = max(1, len(train_examples) // bs)
    total_steps = epochs * steps_per_epoch
    indices = list(range(len(train_examples)))
    step = 0
    best_acc, best_state = -1.0, None
    while step < total_steps:
        rng.shuffle(indices)
        for i in range(0, len(indices) - bs + 1, bs):
            batch = [train_examples[j] for j in indices[i:i + bs]]
            texts = [t for t, _ in batch]
            labels = torch.tensor([y for _, y in batch], dtype=torch.long)
            x, lengths = C.encode_padded(texts)

            model.train()
            opt.zero_grad(set_to_none=True)
            logits = model(x, lengths)
            loss = F.cross_entropy(logits, labels)
            loss.backward()
            opt.step()
            step += 1

            if step % steps_per_epoch == 0:
                model.eval()
                with torch.no_grad():
                    train_acc = (logits.argmax(-1) == labels).float().mean().item()
                    val_acc = (model(vx, vlen).argmax(-1) == val_labels).float().mean().item()
                if val_acc > best_acc:
                    best_acc = val_acc
                    best_state = {k: v.clone() for k, v in model.state_dict().items()}
                epoch_no = step // steps_per_epoch
                if epoch_no % 4 == 0:
                    print(f"  epoque {epoch_no:3d}/{epochs}  step {step:5d}  loss {loss.item():.3f}  "
                          f"train_acc(lot) {train_acc:.1%}  val_acc {val_acc:.1%}  (best {best_acc:.1%})",
                          flush=True)
            if step >= total_steps:
                break

    model.load_state_dict(best_state)
    print(f"  meilleur état retenu : val_acc {best_acc:.1%}")
    return model, cfg


@torch.no_grad()
def predict(model, classes, texts):
    model.eval()
    x, lengths = C.encode_padded(texts)
    probs = F.softmax(model(x, lengths), dim=-1)
    conf, idx = probs.max(-1)
    return [(classes[i], c.item()) for i, c in zip(idx.tolist(), conf)]


def tune_threshold(model, classes, val_examples):
    """Choisit le seuil de confiance qui minimise les erreurs sur la
    validation : abstention si confiance < seuil, sinon classe prédite."""
    texts = [t for t, _ in val_examples]
    gold = [y for _, y in val_examples]
    preds = predict(model, classes, texts)
    hc = classes.index(D.HORS_CHAMP_LABEL)

    best_t, best_score = 0.0, -1
    for t in [i / 100 for i in range(0, 100, 2)]:
        correct = 0
        for (pred_cls, conf), y in zip(preds, gold):
            pred_idx = classes.index(pred_cls) if conf >= t else hc
            correct += int(pred_idx == y)
        score = correct / len(gold)
        if score > best_score:
            best_t, best_score = t, score
    return best_t, best_score


def logistic_regression_baseline(train_examples, val_examples, classes):
    """Modèle de référence du plan : régression logistique sur des n-grammes
    de caractères. Sert à vérifier que le mini-classifieur apporte un gain."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression

    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), lowercase=True)
    Xtr = vec.fit_transform([t for t, _ in train_examples])
    ytr = [y for _, y in train_examples]
    clf = LogisticRegression(max_iter=2000)
    clf.fit(Xtr, ytr)

    Xv = vec.transform([t for t, _ in val_examples])
    yv = [y for _, y in val_examples]
    acc = clf.score(Xv, yv)
    return clf, vec, acc


def evaluate_test_set(model, classes, threshold, lr_clf=None, lr_vec=None):
    test = D.load_test_set()
    texts = [t["question"] for t in test]
    gold = [t["id_attendu"] for t in test]
    preds = predict(model, classes, texts)
    hc = D.HORS_CHAMP_LABEL

    rows = []
    n_ok = 0
    for (pred_cls, conf), g, q in zip(preds, gold, texts):
        final = pred_cls if conf >= threshold else hc
        ok = final == g
        n_ok += ok
        rows.append((q, g, final, round(conf, 2), ok))
    print(f"\nClassifieur (seuil {threshold:.2f}) sur le jeu de test factice "
          f"({len(test)} questions) : {n_ok}/{len(test)} = {n_ok / len(test):.1%}")
    for q, g, final, conf, ok in rows:
        mark = "OK " if ok else "X  "
        print(f"  {mark}{q!r:60s} attendu={g:22s} prédit={final:22s} conf={conf}")

    if lr_clf is not None:
        Xt = lr_vec.transform(texts)
        lr_preds = lr_clf.predict(Xt)
        lr_classes = [classes[i] for i in lr_preds]
        lr_ok = sum(p == g for p, g in zip(lr_classes, gold))
        print(f"\nRégression logistique (référence, sans abstention) : "
              f"{lr_ok}/{len(test)} = {lr_ok / len(test):.1%}")

    return rows


def main():
    classes, train_examples, val_examples = D.build_examples(seed=0)
    print(f"{len(classes)} classes, {len(train_examples)} exemples d'entraînement, "
          f"{len(val_examples)} de validation\n")

    print("Entraînement du mini-classifieur (2 couches, largeur 64)...")
    model, cfg = train_model(classes, train_examples, val_examples)

    threshold, val_score = tune_threshold(model, classes, val_examples)
    print(f"\nSeuil de confiance retenu : {threshold:.2f} "
          f"(score sur validation : {val_score:.1%})")

    print("\nEntraînement de la régression logistique de référence...")
    lr_clf, lr_vec, lr_val_acc = logistic_regression_baseline(train_examples, val_examples, classes)
    print(f"  Régression logistique, score sur validation : {lr_val_acc:.1%}")

    evaluate_test_set(model, classes, threshold, lr_clf, lr_vec)

    torch.save({"cfg": vars(cfg), "sd": model.state_dict(), "classes": classes,
                "threshold": threshold}, os.path.join(OUT_DIR, "classifier.pt"))
    print(f"\nModèle sauvegardé dans {OUT_DIR}/classifier.pt")


if __name__ == "__main__":
    main()
