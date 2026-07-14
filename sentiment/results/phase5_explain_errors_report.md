# Phase 5 — Explainability & Error Analysis (batch 2)

## A. What words drive each polarity (Linear-SVM coefficients, word n-grams)

**Negative** — `ai` · `বিচার` · `এমন` · `শিক্ষিত` · `অবস্থা` · `o` · `মহিলা` · `সে` · `দেশে` · `না` · `হায়রে` · `ছেলে`

**Neutral** — `করা উচিত` · `মা বাবা` · `ভাবে` · `দাও` · `করতে হবে` · `baber` · `হতে পারে` · `সাহায্য করবেন` · `চিনি` · `নাকি` · `ara` · `২`

**Positive** — `ভিডিও` · `আল্লাহ সবাইকে` · `আমার বাবা` · `good` · `ধন্যবাদ` · `সহায়` · `ভালো` · `k` · `সুন্দর` · `babai` · `দান করো` · `ওনাকে`

> These are the most positively-weighted word features per class — a faithful, transparent view of what the classifier keys on (no black box).

## B. Error analysis (held-out test)

- Test accuracy: SVM **0.788**, BanglaBERT **0.728**.
- Both models wrong on **43** / 345 · SVM-only-wrong 30 · BERT-only-wrong 51.

### Dominant confusions

| Model | most common true→pred errors |
|---|---|
| SVM | Neutral→Negative (36), Negative→Neutral (22), Positive→Negative (7), Positive→Neutral (5) |
| BanglaBERT | Neutral→Negative (43), Negative→Neutral (31), Positive→Negative (7), Neutral→Positive (6) |

### Error rate by group (lower = better)

| Group | SVM | BanglaBERT |
|---|---|---|
| Bangla script | 0.191 | 0.226 |
| Latin/code-mixed | 0.316 | 0.509 |
| has emoji | 0.224 | 0.429 |
| no emoji | 0.209 | 0.247 |

> Confirms the batch-1 finding: BanglaBERT's error rate spikes on Latin/code-mixed text.

### Hardest cases (both models wrong)

| id | true | SVM | BERT | comment |
|---|---|---|---|---|
| C00064 | Neutral | Negative | Negative | Ai Milton shomdder keo koto bitorko korselo.jara Valo kaj Kore tader o char nai |
| C00163 | Neutral | Negative | Negative | উনাকে বৃদ্ধা আশ্রমে তো দিতে পারে, সাংবাদিক  ভাইরা চাইলে পারবে |
| C00206 | Positive | Neutral | Negative | নাদিরা বেগম কি বেঁচে আছেন?  She seems very lonely and you don't  even mentioned about her children. I hope she find peac |
| C00277 | Neutral | Negative | Negative | ৩১ বছর আগে তো উনি বুড়া ছিলেন না |
| C00282 | Neutral | Negative | Negative | আপনি কলেজে শিক্ষক আপনার সন্তানদের মানুষ করতে যে পরিমাণ পরিশ্রম হয়েছে আপনার। তাহলে আপনাকে মানুষের মতো মানুষ করতে আপনার প |
| C00316 | Neutral | Negative | Negative | এমন দুর্দশা থেকে মুক্ত করতেই কুরআনের আগমন। আপনারা আধুনিক হতে হতে আমেরিকাকে ছাড়িয়ে যেতে পারেন, তবে শান্তি জিনিসটা কুরআন |
| C00369 | Neutral | Positive | Negative | Briddasromtir payment ki rokom ,ki dhoroner sujog shubidha achey ? Address din pls.Ami ctg thekey dekchi.amr boyosh 70 b |
| C00414 | Positive | Negative | Negative | Perfect bou hote parbo kina jni na kintu sosur sasuri k kokhonoi biddhasrom a pathabo na😢 |
| C00489 | Positive | Neutral | Negative | বৃদ্ধা  আশ্রম এ  অনেক  বৃদ্ধা  মহিলা পুরুষ  আছে   ভালো  থাকবেন  ইনশাল্লাহ আমিন |
| C00522 | Neutral | Negative | Negative | মায়ের চোখের পানি কখনো বৃথা যায়  না |
| C00636 | Positive | Negative | Neutral | মেয়েদের কথা শুনে মনটা ভরে গেলে, |
| C00735 | Neutral | Negative | Negative | Bastobota boro kothin... Ekhon young generation basto career niye ... Onnoke deyar somoy koi? Tai aj jodi amar bari thek |

> Many hard cases are sarcasm, mixed sentiment, or Neutral-vs-Negative boundary calls — the intrinsically ambiguous middle.

