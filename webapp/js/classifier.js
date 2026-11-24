// Mini-classifieur char-level, inférence pure JS, sans dépendance.
// Relit window.MODEL (webapp/data/model.js, généré par model/export_js.py)
// et reproduit exactement le calcul de model/classifier.py (Classifier.forward).
(function (global) {
  "use strict";

  function dequantize(t) {
    // t = {shape:[R,C], scales:[R], int8:[[...]]}
    const [R, Cc] = t.shape;
    const out = new Array(R);
    for (let r = 0; r < R; r++) {
      const row = new Float32Array(Cc);
      const s = t.scales[r];
      const qrow = t.int8[r];
      for (let c = 0; c < Cc; c++) row[c] = qrow[c] * s;
      out[r] = row;
    }
    return out; // out[row][col], c'est à dire la matrice W telle quelle (out_features x in_features)
  }

  function normalizeText(s) {
    // Minuscules, accents retirés, comme model/classifier.py normalize_text().
    s = s.toLowerCase().normalize("NFKD").replace(/[̀-ͯ]/g, "");
    let r = "";
    for (const ch of s) {
      const code = ch.codePointAt(0);
      r += (code >= 32 && code <= 126) || ch === "\n" ? ch : " ";
    }
    return r;
  }

  function encode(s) {
    const ids = [];
    for (const ch of s) ids.push(ch === "\n" ? 1 : ch.codePointAt(0) - 30);
    return ids;
  }

  // y[out] = sum_in x[in] * W[out][in]   (+ bias[out] si fourni)
  function linear(x, W, bias) {
    const outDim = W.length, inDim = W[0].length;
    const y = new Float32Array(outDim);
    for (let o = 0; o < outDim; o++) {
      let acc = bias ? bias[o] : 0;
      const row = W[o];
      for (let i = 0; i < inDim; i++) acc += x[i] * row[i];
      y[o] = acc;
    }
    return y;
  }

  function rmsNorm(x, gain) {
    let ms = 0;
    for (let i = 0; i < x.length; i++) ms += x[i] * x[i];
    ms = ms / x.length;
    const inv = 1 / Math.sqrt(ms + 1e-5);
    const y = new Float32Array(x.length);
    for (let i = 0; i < x.length; i++) y[i] = x[i] * inv * gain[i];
    return y;
  }

  function softmax(logits) {
    const m = Math.max(...logits);
    const exps = logits.map((v) => Math.exp(v - m));
    const sum = exps.reduce((a, b) => a + b, 0);
    return exps.map((v) => v / sum);
  }

  class Classifier {
    constructor(model) {
      this.m = model;
      this.D = model.cfg.D;
      this.H = model.cfg.H;
      this.emb = dequantize(model.emb); // [VOCAB][D]
      this.pos = dequantize(model.pos); // [CTX][D]
      this.blocks = model.blocks.map((b) => ({
        n1: b.n1,
        n2: b.n2,
        q: dequantize(b.q),
        k: dequantize(b.k),
        v: dequantize(b.v),
        o: dequantize(b.o),
        f1: dequantize(b.f1),
        f2: dequantize(b.f2),
      }));
      this.nf = model.nf;
      this.headW = dequantize(model.head_w);
      this.headB = model.head_b;
    }

    // Attention causale multi-têtes sur toute la séquence (T x D) -> (T x D)
    attention(seq, blk) {
      const T = seq.length, D = this.D, H = this.H, hd = D / H;
      const Q = seq.map((x) => linear(x, blk.q));
      const K = seq.map((x) => linear(x, blk.k));
      const V = seq.map((x) => linear(x, blk.v));
      const out = seq.map(() => new Float32Array(D));
      for (let h = 0; h < H; h++) {
        const off = h * hd;
        for (let t = 0; t < T; t++) {
          const scores = new Float32Array(t + 1);
          let maxS = -Infinity;
          for (let u = 0; u <= t; u++) {
            let dot = 0;
            for (let d = 0; d < hd; d++) dot += Q[t][off + d] * K[u][off + d];
            dot /= Math.sqrt(hd);
            scores[u] = dot;
            if (dot > maxS) maxS = dot;
          }
          let sum = 0;
          for (let u = 0; u <= t; u++) { scores[u] = Math.exp(scores[u] - maxS); sum += scores[u]; }
          for (let d = 0; d < hd; d++) {
            let acc = 0;
            for (let u = 0; u <= t; u++) acc += (scores[u] / sum) * V[u][off + d];
            out[t][off + d] = acc;
          }
        }
      }
      return out.map((x) => linear(x, blk.o));
    }

    block(seq, blk) {
      const normed1 = seq.map((x) => rmsNorm(x, blk.n1));
      const attnOut = this.attention(normed1, blk);
      const afterAttn = seq.map((x, i) => x.map((v, d) => v + attnOut[i][d]));
      const normed2 = afterAttn.map((x) => rmsNorm(x, blk.n2));
      const mlpOut = normed2.map((x) => {
        const h = linear(x, blk.f1).map((v) => Math.max(0, v)); // ReLU
        return linear(h, blk.f2);
      });
      return afterAttn.map((x, i) => x.map((v, d) => v + mlpOut[i][d]));
    }

    // Retourne {classIndex, confidence, probs} pour une question donnée.
    classify(question) {
      const ids = encode(normalizeText(question)).slice(0, this.m.ctx - 1);
      let seq = ids.map((id, t) => {
        const e = this.emb[id], p = this.pos[t];
        const x = new Float32Array(this.D);
        for (let d = 0; d < this.D; d++) x[d] = e[d] + p[d];
        return x;
      });
      for (const blk of this.blocks) seq = this.block(seq, blk);
      const last = rmsNorm(seq[seq.length - 1], this.nf);
      const logits = linear(last, this.headW, this.headB);
      const probs = softmax(Array.from(logits));
      let best = 0;
      for (let i = 1; i < probs.length; i++) if (probs[i] > probs[best]) best = i;
      return { className: this.m.classes[best], confidence: probs[best], probs };
    }
  }

  global.MiniClassifier = Classifier;
  global.MiniClassifierUtils = { normalizeText, encode };
})(typeof window !== "undefined" ? window : globalThis);
