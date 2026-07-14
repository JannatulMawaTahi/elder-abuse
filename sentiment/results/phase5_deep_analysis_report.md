# Phase 5 — Deep Analysis (batch 1)

Three analyses beyond the descriptive EDA. (Emotion labels are the current LLM labels; the victim-blaming audit / human Kappa are still in progress, so emotion splits are indicative.)

## 1. Language-wise model robustness (held-out test)

| Language | n | Linear SVM acc | BanglaBERT acc |
|---|---|---|---|
| Bangla | 288 | 0.809 | 0.774 |
| Banglish (Latin) | 52 | 0.673 | 0.462 |
| Code-mixed | 5 | 0.800 | 0.800 |

> Shows whether the models hold up on Banglish/Latin & code-mixed comments, not just pure Bangla — a key robustness question for a code-switched corpus.

## 2. Embedding structure — do the labels have unsupervised support?

- BanglaBERT sentence embeddings, KMeans vs human labels (Adjusted Rand Index):
  - cluster ↔ **emotion** (k=5): **ARI = 0.051**
  - cluster ↔ **polarity** (k=3): **ARI = 0.059**
- t-SNE projection coloured by emotion: `figures/20_embedding_tsne_emotion.png`.
> ARI > 0 means the human categories line up with natural structure in the embedding space (partial validation of the label scheme); low ARI means the classes overlap heavily in meaning — expected for fine-grained emotion on short social text.

## 3. Religious framing

- **22.1%** of all comments use religious language.
- Religion is the *vehicle* of both condemnation and blessing — see the polarity split and the emotion mix within religious comments: `figures/21_religious_framing.png`.

Figures: `18_lang_distribution.png`, `19_lang_model_accuracy.png`, `20_embedding_tsne_emotion.png`, `21_religious_framing.png`.
