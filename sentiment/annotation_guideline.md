# Annotation Guideline — Elder-Abuse Sentiment Dataset

**Annotators:** 4 team members — A (Lamia), B, C, D — label **independently**, do NOT discuss.
Each fills their own `annotator_{A,B,C,D}.xlsx`; the first 450 rows are shared by all four (for
Fleiss' Kappa), the rest are unique to each person → the whole dataset gets a human label.
**Task:** For every comment, assign **two** labels — (A) Polarity and (B) Emotion.

> ⚠️ Label the **comment text only**. Do NOT use the video's `abuse_type` to decide the label —
> that column is the video topic, not the comment's feeling. Ignore it while annotating.

---

## A. Polarity (3 classes) — the overall emotional valence

| Label | Meaning | Examples |
|---|---|---|
| **Negative** | anger, grief, condemnation, blame, cursing — any negative feeling | "এই কুলাঙ্গার ছেলের জাহান্নামেও জায়গা হবে না"; "আহারে কত কষ্ট 😢" |
| **Positive** | prayer/blessing for the victim, offering help, gratitude, hope, praise | "আল্লাহ ওনাদের জান্নাত দিক"; "আমি ওনার দায়িত্ব নিতে চাই" |
| **Neutral** | factual statement, question, tagging someone, no clear feeling | "ভিডিওটা কোথাকার?"; "এটা কোন এলাকা?" |

---

## B. Emotion (5 classes) — pick the **dominant** one

| Label | When to use | Examples |
|---|---|---|
| **Anger/Condemnation** | rage at the abuser, cursing, demanding punishment/justice | "ধিক্কার জানাই"; "এদের ফাঁসি হওয়া উচিত"; "কুলাঙ্গার" |
| **Grief/Sympathy** | sadness, pity, empathy for the victim | "বুড়ো বয়সে এত কষ্ট, চোখে পানি চলে এলো 😢" |
| **Prayer/Religious** | invoking Allah/religion, dua, afterlife framing as the MAIN tone | "আল্লাহ ওনাদের ভালো রাখুক"; "কেয়ামতের দিন বিচার হবে" |
| **Victim-blaming** | blaming the parents / victim / their past upbringing or society | "মা-বাবাই ঠিকমতো মানুষ করেনি, তাই আজ এই দিন" |
| **Neutral-Other** | factual, question, tagging, off-topic — fits none above | "কোন হাসপাতাল এটা?"; "ভাই নাম্বার দেন" |

---

## Religious / "Allah" comments — decision tree (READ — this recurs a lot)

Religion is just the *language*; decide the emotion by **who the comment targets and why**.

1. **Dua / blessing FOR the victim** ("আল্লাহ ওনাদের ভালো রাখুক / জান্নাত দিক / সহায় হোন")
   → `Prayer/Religious`, polarity **Positive**
2. **Curse / punishment on the ABUSER in God's name** ("আল্লাহ গজব দিক / জাহান্নামে নিক / কখনো ক্ষমা করবে না")
   → this is anger expressed through religion → `Anger/Condemnation`, polarity **Negative**
3. **Pure faith statement, no target** ("আল্লাহ সব দেখছেন / কেয়ামতে বিচার হবে")
   → `Prayer/Religious`, polarity **Neutral** (Negative if the tone is clearly harsh)
4. **Religion mixed with grief** ("ইন্নালিল্লাহ… আল্লাহ মাফ করুক", crying tone)
   → if sadness dominates → `Grief/Sympathy`; if dua dominates → `Prayer/Religious` (pick the stronger).

| Comment | emotion | polarity |
|---|---|---|
| আল্লাহ ওনাদের ভালো রাখুক, জান্নাত দিক | Prayer/Religious | Positive |
| আল্লাহ এই কুলাঙ্গারদের গজব দিক, জাহান্নামে নিক | Anger/Condemnation | Negative |
| এদের আল্লাহ কখনো ক্ষমা করবে না | Anger/Condemnation | Negative |
| আল্লাহ সব দেখছেন, কেয়ামতে বিচার হবে | Prayer/Religious | Neutral |

---

## Victim-blaming vs Anger vs Neutral-Other — the hardest boundary (READ — recurs a lot)

`Victim-blaming` means the negative judgement targets the **elderly VICTIM** (or their past,
choices, parenting, upbringing) and frames their suffering as **deserved / their own fault**.
If the target is NOT the victim, it is NOT victim-blaming.

**Two questions, in order:**
1. **Who does it blame/attack?**
   - The victim / their past / their parenting → **Victim-blaming**
   - The abuser (the children) or a third party (e.g. the wives) → **Anger/Condemnation**
2. **Is there any blame at all, or just generic advice/observation?**
   - Generic advice with NO blame aimed at *this* victim → **Neutral-Other**
   - But advice that implies the victim failed ("if YOU had taught your kids deen, this wouldn't
     happen to YOU") → still **Victim-blaming**.

| Comment (gist) | Label | why |
|---|---|---|
| "এরা সমাজের বিষ" (these abusers are society's poison) | Anger/Condemnation | attacks the abuser |
| "৯০% নারীদের কারণে… ঘৃণা করি" (I hate the wives who cause this) | Anger/Condemnation | attacks a third party |
| "সবার ইসলামিক শিক্ষা ও হালাল ইনকাম দরকার" (everyone needs Islamic education) | Neutral-Other | generic advice, no target |
| "ধর্মের শিক্ষা ছাড়া সব শিক্ষাই মূল্যহীন" (all education without religion is worthless) | Neutral-Other | generic opinion |
| "হারামের টাকায় এ অবস্থা / কর্মফল" (haram money, this is the karma) | Victim-blaming | blames victim's past |
| "সন্তানকে দ্বীন শিক্ষা দেননি তাই আপনার এই অবস্থা" (you didn't teach your kids deen, so this is your state) | Victim-blaming | blames victim's parenting |

**Key tell for Victim-blaming:** a cause→effect that pins the suffering on the victim's own past —
"তাই / কারণ … এই অবস্থা", "কর্মফল", "নিজের দোষে", "হারামের টাকার ফল".

---

## Tie-break & edge rules (read carefully)

1. **Multiple emotions in one comment → pick the DOMINANT (strongest) one.**
2. **Religion + anger** ("আল্লাহ এদের বিচার করবেন") →
   - if the main thrust is **curse / demand for punishment** → `Anger/Condemnation`
   - if the main thrust is **faith / leaving it to God / dua** → `Prayer/Religious`
3. **Sarcasm / irony** → label by the *intended* meaning, not the literal words.
4. **Emoji matter:** 😢😭 → grief signal; 😡🤬 → anger signal. Use them as evidence.
5. **Code-switched (Banglish/English)** comments follow the same rules.
6. If you are genuinely unsure, put your best guess and write a short note in the `notes` column.

---

## How to fill the sheet

1. Open your own file: `annotator_A.xlsx` (Lamia), `_B` / `_C` / `_D` (Members 2–4). Use the
   **"Annotate"** sheet (the "Instructions" sheet is just the legend).
2. For each row, read the **Comment**, then choose **polarity** and **emotion** from the dropdowns.
3. Optional: add a `notes` remark for hard cases.
4. Do **not** delete/reorder rows and do **not** edit the `comment_id` column.
5. Save when done. All four files are matched by `comment_id`; the shared 450 rows give **Fleiss'
   Kappa** (`python sentiment/src/kappa4.py`), and every comment's final label is assembled into
   `human_labels.csv` (overlap = majority vote, unique = your label).

**Labels (exact spelling used in dropdowns):**
- polarity: `Negative` · `Neutral` · `Positive`
- emotion: `Anger/Condemnation` · `Grief/Sympathy` · `Prayer/Religious` · `Victim-blaming` · `Neutral-Other`
