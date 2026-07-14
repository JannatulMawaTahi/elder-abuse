# Elder Abuse Detection & Legal Assistance — Implementation Flow

> **Project:** A Unified AI Framework for Elder Abuse Detection & Legal Assistance
> **Course:** CSE 499A — Undergraduate Thesis, North South University
> **Supervisor:** Dr. Sifat Momen, Professor, ECE
> **Team:** Lamia Islam Mim (2212085042), Jannatul Mawa Tahi (2212096042),
> Umme Sani Ananna (2221618042), Farihaa Khadija Ahmed (2221852042)

> **Last Updated: 2 June 2026 — REVISED after supervisor feedback**
> **Legend:** `✅ Done` | `🔄 In Progress` | `⬜ Pending` | `⏭️ Next`

---

## ⚠️ MAJOR REVISION — Supervisor Feedback (June 2026)

Sir asked for two changes, both accepted:

### 1. Interaction model → Guided Yes/No Questions (not long free speech)

```
আগে:  বৃদ্ধ লম্বা করে voice complaint দেবে → Whisper → AI
      ❌ বৃদ্ধ গুছিয়ে বলতে পারে না; Whisper বাংলা typo করে

এখন:  System বাংলায় TTS দিয়ে একটা একটা সহজ প্রশ্ন করে
      → screen এ বড় [হ্যাঁ] [না] button → user শুধু চাপে
      ✅ বৃদ্ধদের জন্য অনেক সহজ, কম ভুল, structured data
      ✅ Free voice input থাকবে OPTIONAL ("আরও কিছু বলতে চান?")
```

### 2. Add Admin Dashboard (researcher / NGO / authority)

Dataset analysis + public-comment sentiment analysis + model performance —
so that researchers and NGOs can understand elder-abuse patterns.

### What this changed

| Item | Status |
|------|--------|
| Guided Q&A + TTS | 🆕 NEW — core interaction |
| Admin Dashboard | 🆕 NEW |
| Free-form voice (Whisper) | 🔄 Kept as OPTIONAL ("আরও কিছু বলতে চান?") |
| Complaint PDF generator | ❌ DROPPED from scope (code kept as future work) |
| Everything else (dataset, EDA, legal KB, RAG engine) | ✅ Fully reused |

---

## 1. SYSTEM OVERVIEW

### 1.1 One React PWA — three routes (FINAL, approved)

```
┌────────────────────────────────────────────────────────────┐
│  /            🏠 HOME (web)                                 │
│               ✨ Lottie animation (hero)                    │
│               প্রকল্পের পরিচয় ও উদ্দেশ্য                     │
│               [ ▶ সাহায্য নিন ]   [ 📊 Dashboard ]          │
├────────────────────────────────────────────────────────────┤
│  /assess      📱 প্রশ্নোত্তর — mobile-first                  │
│               বড় button, 🔊 শুনুন, progress bar             │
│               → ফোনে app-এর মতো অভিজ্ঞতা                    │
├────────────────────────────────────────────────────────────┤
│  /dashboard   📊 ADMIN DASHBOARD (password-protected)       │
│               live analytics + dataset + sentiment + metrics│
└────────────────────────────────────────────────────────────┘
```

**Why a PWA, not a native app** — একই React codebase; ফোনে
"Add to Home Screen" করলে icon সহ full-screen app-এর মতো চলে।
Native (Flutter/React Native) হলে আলাদা stack + Play Store approval
লাগত → ২-মাসের thesis timeline-এ অসম্ভব। PWA-তে demo ফোনেই দেখানো যায়।

| Item | Decision |
|------|----------|
| App type | **Responsive React PWA** (installable on phone) |
| Home animation | **Lottie** (free, lightweight, smooth) |
| Dashboard access | **Simple password** (ethics + "access-controlled" in thesis) |
| Deploy | Vercel (frontend) + Render (backend) + Firebase (data) |

### 1.2 Who really uses it (honest design reality)

```
Operator (app চালায়):   সাক্ষর সাহায্যকারী — প্রতিবেশী / তরুণ আত্মীয় /
                        NGO কর্মী / UP সদস্য / সমাজকর্মী
Participant (উত্তর দেয়): বৃদ্ধ নিজে — প্রশ্ন শোনে, হ্যাঁ/না চাপে
Beneficiary:            বৃদ্ধ

→ একজন সম্পূর্ণ নিরক্ষর বৃদ্ধ একা smartphone চালাতে পারবে না।
  System তাকে OPERATOR বানায় না — PARTICIPANT বানায়
  (প্রশ্ন শোনে, উত্তর দেয়, ফলাফল শোনে)।
→ এটাই honest design; thesis এ এভাবেই লেখা হবে।
```

### 1.3 Elder App — user flow (FINAL, Lamia-approved)

```
০. স্বাগতম পর্দা
   "স্বাগতম। আমি আপনার সমস্যাটি বুঝতে কিছু সহজ প্রশ্ন করব।
    সব তথ্য গোপন রাখা হবে।"
   [ ▶ শুরু করুন ]   [ 🔊 শুনুন ]
        ↓
১. কে রিপোর্ট করছে?      [ আমি নিজে ] [ অন্যের পক্ষে ]
২. বয়স প্রায় ৬০+?        [ হ্যাঁ ] [ না ]
৩. ভুক্তভোগী            [ পুরুষ ] [ মহিলা ] [ বলতে চাই না ]
৪. এলাকা                 বিভাগ → জেলা  (দুই ধাপ, সহজ navigation)
        ↓
৫. ⭐ সমস্যা বেছে নিন (একাধিক বাছা যাবে — বড় icon button):
      👊 শারীরিক নির্যাতন
      🗣️ মানসিক নির্যাতন
      💰 আর্থিক নির্যাতন
      🍚 অবহেলা
      🏠 পরিত্যাগ
      ⚫ মৃত্যুর ঘটনা      (শুধু "অন্যের পক্ষে" হলে)
        ↓
৬. শুধু নির্বাচিত সমস্যার follow-up প্রশ্ন (প্রতিটির ১–২টি)
৭. নির্যাতনকারী কে?  → পরিবারের সদস্য? → সম্পর্ক বাছাই
৮. ঝুঁকি (২টি প্রশ্ন)
        ↓
৯. (Optional) "আরও কিছু বলতে চান?" → voice input (Whisper)
        ↓
১০. AI বিশ্লেষণ → ফলাফল পর্দা (🔊 পড়ে শোনাবে)
        ↓
১১. সম্মতি: "আপনি কি এই ঘটনার রিপোর্ট সংরক্ষণ করতে চান?"
      🟢 হ্যাঁ → Firestore-এ save + Dashboard আপডেট
      🔴 না   → ফলাফল দেখাবে, কিছুই সংরক্ষণ হবে না

প্রতিটি পর্দায়: 🔊 "শুনুন" button + graphical progress bar (██████░░░░ ৬০%)
মোট প্রশ্ন: ১টি সমস্যা → ~১০–১১ · ২টি সমস্যা → ~১২–১৩
```

### 1.3.1 Result page (FINAL)

```
✓ নির্যাতনের ধরন          — শারীরিক নির্যাতন + অবহেলা
✓ ঝুঁকির মাত্রা            — উচ্চ
✓ AI-এর সম্ভাব্যতা: ৮৭%    (Confidence — সহজ বাংলায়)
✓ লঙ্ঘিত আইন             — PMA 2013 §3, §4 · দণ্ডবিধি §323
✓ সম্ভাব্য কারণ 🆕        — পারিবারিক দ্বন্দ্ব / সম্পত্তি বিরোধ /
                            আর্থিক নির্ভরশীলতা
✓ AI-এর ব্যাখ্যা 🆕       — "আপনি বলেছেন গত ১২ মাসে মারধর হয়েছে
                            এবং হাসপাতালে যেতে হয়েছে — তাই ..."
   ⚠️ Disclaimer: "এই ফলাফলটি আপনার দেওয়া উত্তরের ভিত্তিতে AI বিশ্লেষণ
      করে তৈরি করা হয়েছে। এটি চূড়ান্ত আইনি সিদ্ধান্ত নয়।"
✓ করণীয়                  — থানায় FIR · UNO-তে অভিযোগ · NLASO
✓ জরুরি যোগাযোগ:
      [ ☎ ৯৯৯ ]  [ ☎ NLASO ১৬৪৩০ ]  [ ☎ বিশ্বস্ত ব্যক্তিকে ফোন করুন 🆕 ]
```

### 1.4 Key architectural decision — maximum reuse

```
হ্যাঁ/না উত্তর → বাংলা text সারাংশ তৈরি
   ("সন্তান মারধর করে: হ্যাঁ | খাবার দেয় না: হ্যাঁ | ...")
        ↓
   সেই text → rag_engine (Gemini)  ← আগে বানানো, অপরিবর্তিত
        ↓
   abuse type + risk + আইন + করণীয়

সুবিধা:
✅ rag_engine, act_knowledge_base, keyword_classifier — সব ১০০% reuse
✅ একই classifier free-text ও Q&A দুইটাতেই চলে
✅ test_split.csv (real cases) এ মাপা metrics valid থাকে (dashboard এ)
```

---

## 1.5 QUESTION BANK (FINAL — approved by Lamia)

### Screening (all users)

| # | প্রশ্ন | উত্তর |
|---|--------|-------|
| Q1 | আপনি কি নিজে এই সমস্যার শিকার? | [আমি নিজে] [অন্যের পক্ষে] |
| Q2 | ভুক্তভোগীর বয়স কি **প্রায়** ৬০ বছর বা তার বেশি? | [হ্যাঁ] [না] |
| Q3 | ভুক্তভোগী | [পুরুষ] [মহিলা] [**বলতে চাই না**] |
| Q4 | এলাকা | বিভাগ → জেলা (দুই ধাপ) |

### Category selector (multi-select, big icon buttons)

| Icon | লেখা | key |
|------|------|-----|
| 👊 | শারীরিক নির্যাতন | physical |
| 🗣️ | মানসিক নির্যাতন | verbal |
| 💰 | আর্থিক নির্যাতন | financial |
| 🍚 | অবহেলা | neglect |
| 🏠 | পরিত্যাগ | abandonment |
| ⚫ | মৃত্যুর ঘটনা *(শুধু third-party)* | murder |

### Follow-ups (asked only for selected categories)

| # | প্রশ্ন | Category |
|---|--------|----------|
| P1 | **গত ১২ মাসে** কি আপনাকে মারধর, ধাক্কা, চড় বা লাথি দেওয়া হয়েছে? | physical |
| P2 | আঘাতের কারণে কি কখনো ডাক্তার বা হাসপাতালে যেতে হয়েছে? | physical (গুরুতর) |
| V1 | আপনাকে কি গালিগালাজ, অপমান, ভয় দেখানো বা হুমকি দেওয়া হয়? | verbal |
| V2 | আপনাকে কি একঘরে করে রাখা হয় বা "বোঝা" মনে করা হয়? | verbal |
| F1 | **আপনার অনুমতি ছাড়া** কি কেউ আপনার টাকা, পেনশন বা বয়স্ক ভাতা নিয়ে নেয়? | financial |
| F2 | **আপনার অনুমতি ছাড়া** কি জমি বা সম্পত্তি লিখে নেওয়া হয়েছে? | financial |
| N1 | পরিবার কি **ইচ্ছাকৃতভাবে** আপনাকে খাবার, **পানি** বা যত্ন থেকে বঞ্চিত করে? | neglect |
| N2 | অসুস্থ হলে পরিবার কি **ইচ্ছাকৃতভাবে** চিকিৎসা বা ওষুধ দেয় না? | neglect (চিকিৎসা) |
| A1 | আপনাকে কি বাড়ি থেকে বের করে দেওয়া হয়েছে? | abandonment |
| A2 | আপনাকে কি **দীর্ঘ সময় একা ফেলে রাখা হয়** বা পরিবার খোঁজ নেয় না? | abandonment |
| M1 | নির্যাতনের কারণে কি ভুক্তভোগী মারা গেছেন? *(third-party only)* | murder → ৯৯৯ + থানা |

### Abuser (Trust Blind Spot — dataset: 41.8% family)

| # | প্রশ্ন | উত্তর |
|---|--------|-------|
| AB1 | নির্যাতনকারী কি পরিবারের সদস্য? | [হ্যাঁ] [না] |
| AB2a | *(AB1=হ্যাঁ)* সম্পর্ক | [ছেলে][মেয়ে][পুত্রবধূ][জামাই][নাতি-নাতনি][ভাই-বোন][অন্য আত্মীয়] |
| AB2b | *(AB1=না)* কে | [প্রতিবেশী][অপরিচিত][অন্য] |

### Risk

| # | প্রশ্ন | প্রভাব |
|---|--------|--------|
| R1 | নির্যাতন কি এখনো চলছে? | চলমান → risk ↑ |
| R2 | আপনার কি **এখনই নিরাপদ জায়গায় যাওয়ার প্রয়োজন আছে?** | হ্যাঁ → জরুরি SOS ৯৯৯ |

---

## 1.6 ADMIN DASHBOARD (FINAL)

### Section 1 — Live assessment analytics 🆕 (Firestore, real-time)
```
✓ Abuse Type — Pie chart
✓ Monthly Trend — line
✓ Gender Ratio
✓ District Map
✓ Family vs Non-family Abuser  (Trust Blind Spot live)
✓ Risk Level Distribution
```
> শুধুমাত্র সেই assessment যেগুলোতে ব্যবহারকারী **সংরক্ষণে সম্মতি দিয়েছেন**।
> কোনো নাম/পরিচয় নয় — শুধু anonymized: abuse type, risk, district, gender,
> abuser relation, timestamp.

### Section 2 — Elder Abuse Dataset (199 cases) — ✅ 11 charts exist
### Section 3 — Public Comment Sentiment (2,301) — ✅ 23 figures exist
### Section 4 — Model Performance
```
✅ Sentiment: Linear SVM macro-F1 0.683 vs BanglaBERT 0.611 (McNemar p=0.026)
🆕 Elder-abuse classifier: accuracy / precision / recall / F1 (test_split.csv)
```

---

## 2. ABUSE CATEGORIES (6 — unchanged)

| Category | বাংলা | Severity | আইন |
|----------|-------|----------|-----|
| Physical | শারীরিক নির্যাতন | 4 | PMA §3; দণ্ডবিধি §323, §324 |
| Verbal / Emotional | মৌখিক / মানসিক নির্যাতন | 1 | দণ্ডবিধি §506 |
| Financial | আর্থিক নির্যাতন | 2 | দণ্ডবিধি §406, §420 |
| Neglect | অবহেলা | 2 | PMA §4 |
| Abandonment | পরিত্যাগ | 3 | PMA §3, §4 |
| Murder | হত্যা | 5 | দণ্ডবিধি §302, §304 |

> Murder — বৃদ্ধ নিজে রিপোর্ট করবে না; third-party (প্রতিবেশী) reporting flow-এ
> প্রযোজ্য, এবং dataset/dashboard-এ থাকে।

---

## 3. DATA ASSETS (all ✅ complete)

### 3.1 Elder Abuse Dataset — `data/`
```
✅ 199 real cases (Primary field-work + News + TV interviews)
✅ Cleaned + normalized (20 columns), train/test split (159/40)
✅ 11 EDA charts (abuse type, abuser relation, top locations, gender,
   severity, age, year trend, heatmap, Trust Blind Spot, source, severity×gender)
✅ Trust Blind Spot: 41.8% abusers are family members
```

### 3.2 Public Comment Sentiment Corpus — `sentiment/` ✅ COMPLETE
```
✅ 2,454 raw → 2,301 cleaned comments (YouTube / Facebook)
✅ Splits: train 1609 / val 345 / test 345 (locked, sha256-verified)
✅ 4 human annotators + Kappa agreement; LLM-assisted labels
✅ Labels: polarity (Neg/Neu/Pos), emotion (5), abuse-type,
   victim-blaming, prayer, religious framing, language
✅ Models: Linear SVM macro-F1 = 0.683  |  BanglaBERT macro-F1 = 0.611
   McNemar p = 0.026 (SVM significantly better on this small corpus)
✅ 23 figures (wordcloud, confusion matrices, t-SNE, etc.)
✅ Statistical findings:
   - Victim-blaming × Neglect/Abandonment: Fisher's exact OR = 4.87, p < 0.001
   - Religious framing in 22.1% of comments
   - Language robustness: SVM holds on Banglish; BanglaBERT breaks down
```

### 3.3 Legal Knowledge Base — `backend/phase1_outputs/`
```
✅ act_knowledge_base.json — 16 sections (9 PMA 2013 + 7 দণ্ডবিধি)
   (penalty corrected via bdlaws: ১,০০,০০০ টাকা / ৩ মাস)
✅ keyword_dictionary.json — 231 keywords (Bangla + English + mixed)
```

---

## 4. TECHNOLOGY STACK

| Component | Tool | Cost |
|-----------|------|------|
| Question TTS (বাংলা কণ্ঠ) | **edge-tts** (bn-BD voices) | Free, no API key |
| AI legal analysis | Google Gemini 2.5 Flash | Free tier |
| Optional voice input | Groq Whisper API | Free tier |
| Backend | FastAPI + uvicorn | Free |
| Frontend | React + Vite + Tailwind | Free |
| Dashboard charts | Existing PNGs + Recharts | Free |
| Sentiment models | Linear SVM / BanglaBERT (trained) | Free |
| Deploy | Vercel (frontend) + Render (backend) | Free |

**Monthly cost: $0.00**

---

## 5. WHAT'S DONE vs WHAT'S NEW

### ✅ COMPLETE (reused as-is)

| Module | Purpose in new plan |
|--------|---------------------|
| `data/` + 11 EDA charts | Dashboard Section 1 |
| `sentiment/` (full study) | Dashboard Section 2 + 3 |
| `backend/app/rag_engine.py` | Analyzes Q&A summary → abuse type, risk, law, advice |
| `backend/app/keyword_classifier.py` | Fast first-pass category + severity |
| `backend/phase1_outputs/*.json` | Legal KB + keywords |
| `backend/app/whisper_service.py` | OPTIONAL free-voice input |
| `backend/app/preprocessor.py` | Audio → WAV (for optional voice) |
| `backend/app/main.py` | FastAPI base + CORS |
| `backend/app/entity_extractor.py` | Reporter type (self/third-party) |

### 🆕 NEW (to build)

| Module | What |
|--------|------|
| `question_bank.json` | ~15–18 Bangla yes/no questions (6 categories) |
| `question_engine.py` | Question flow + answer scoring → text summary |
| `tts_service.py` | edge-tts: Bangla text → audio (questions + results) |
| API endpoints | `/questions`, `/analyze-answers`, `/tts` |
| React Elder App | Big হ্যাঁ/না buttons, TTS playback, result screen |
| React Admin Dashboard | `/dashboard` route — 3 sections |
| `evaluate_classifier.py` | Elder-abuse classifier metrics (acc/P/R/F1) |

### ❌ DROPPED

```
pdf_generator.py — code থাকবে (future work), scope-এ নেই
map/geolocation  — সময় থাকলে optional
```

---

## 6. IMPLEMENTATION STEPS

```
── COMPLETED ────────────────────────────────────────────────────
✅ Dataset + EDA (199 cases, 11 charts)
✅ keyword_dictionary.json + act_knowledge_base.json
✅ Backend: FastAPI, preprocessor, whisper_service, keyword_classifier
✅ rag_engine.py (Gemini legal triage) + entity_extractor.py
✅ Sentiment study (2301 comments, SVM/BERT, 23 figures) — sentiment/

── PHASE A: Guided Q&A + TTS (backend) ──────────────────────────
✅ A1. Question bank FINALISED (see §1.5) — Lamia approved
✅ A2. question_bank.json — 6 categories, 5 intro, 11 follow-ups, 6 closing,
       consent, result spec, 8 divisions / 64 districts
✅ A3. question_engine.py — branch/skip logic, progress bar, Bangla summary,
       rule-based severity/risk/confidence, anonymized dashboard record
       (risk 5 "জরুরি" reserved for real emergencies only)
✅ A4. tts_service.py — edge-tts bn-BD-NabanitaNeural (female), normal speed
       (slowed-down rate sounded broken — tested & rejected by Lamia);
       disk cache (28 ms on hit), prewarm() for all 24 spoken texts
✅ A5. rag_engine extension — analyze_assessment(): AI explanation (quotes the
       elder's OWN answers), সম্ভাব্য কারণ, ≤4 short করণীয়, disclaimer.
       applicable_sections lists ONLY violated laws — procedural sections
       (§5 complaint procedure, §7 penalty, §8 emergency aid) are excluded.
✅ A6. storage.py — anonymized save, ONLY on consent (ConsentRequiredError
       otherwise). sanitize() whitelists 10 analytics fields; name/phone/
       free-text are dropped. Dual backend: Firestore if backend/firebase-key.json
       exists, else local JSON (dev). dashboard_stats() → 6 live charts.
✅ A7. main.py endpoints (v0.2.0) — STATELESS: the client holds `answers` and
       sends it every call, so no server-side session can be lost on restart.
         POST /flow/next        answers → next screen + progress (branch logic
                                lives here; the frontend knows no rules)
         GET  /flow/categories  murder shown only for third_party
         GET  /flow/divisions   8 divisions
         GET  /flow/districts   districts of one division (404 if unknown)
         POST /analyze          rule engine decides type/risk/confidence;
                                Gemini adds the Bangla prose on top. If Gemini
                                fails → still returns the deterministic result
                                (degraded: true) instead of erroring.
         GET  /tts              Bangla text → mp3, disk-cached (~5 ms on hit)
         POST /save-report      saves ONLY if consent=true; the record is rebuilt
                                server-side from answers, never trusted from the
                                client, then sanitize()d
         POST /dashboard/login  + GET /dashboard/stats (X-Admin-Password header)
         POST /transcribe       optional free voice ("আরও কিছু বলতে চান?")
       Two bugs found & fixed while testing:
         • welcome screen had no `field`, so the client would store its answer
           under the id while the engine looked for `started` → infinite loop on
           screen 1. Every screen now declares its own `field`.
         • result screen showed raw ids ("pma_sec3"). Ids from either Gemini or
           the rule-engine fallback now map to titles via _readable_sections().
✅ A8. Tests — 65 new (195 total, all green, ~100 s). Gemini / Firestore /
       edge-tts are mocked, so the suite is offline, fast and burns no quota.
         tests/test_question_engine.py (29) — branch logic, the no-infinite-loop
           invariant, risk ceiling, confidence bounds, anonymisation
         tests/test_storage.py         (13) — consent, whitelist fails closed,
           dashboard aggregation, corrupt-file tolerance
         tests/test_flow_api.py        (23) — the API contract the React app
           depends on, incl. the full client walk, Gemini-down degradation, and
           "a client cannot smuggle identity into the database"
       Two test bugs of my own, both instructive:
         • asserted every screen carries `field`, but the real contract is
           `field || id`; rewrote it as the invariant that actually matters —
           answering a screen must always advance the flow
         • asserted escalates_severity raises `severity`; it raises `risk`, and
           on physical (severity 4, already at the non-emergency ceiling) the
           bump is swallowed by the cap. Retested on financial (severity 2).

╔════════════════════════════════════════════════════════════════╗
║  PHASE A COMPLETE — backend works end to end.                  ║
║  answers → next screen → risk + violated law + Bangla          ║
║  explanation → spoken aloud → saved only on consent →          ║
║  dashboard. Next: Phase B, the React PWA.                      ║
╚════════════════════════════════════════════════════════════════╝

── PHASE B: React PWA (frontend) ────────────────────────────────
⬜ B1. React + Vite + Tailwind + PWA setup (installable)
⬜ B2. `/` Home — Lottie animation, intro, [সাহায্য নিন] [Dashboard]
⬜ B3. `/assess` Welcome screen (স্বাগতম + ▶ শুরু করুন + 🔊)
⬜ B4. Question screens — big buttons, 🔊 শুনুন, graphical progress bar
⬜ B5. Category multi-select screen (6 big icon buttons)
⬜ B6. Division → District selector (two-step)
⬜ B7. Result screen — type, risk, সম্ভাব্যতা, laws, সম্ভাব্য কারণ,
       AI explanation + disclaimer, actions, ☎ ৯৯৯ / ১৬৪৩০ / বিশ্বস্ত ব্যক্তি
⬜ B8. Consent screen — "রিপোর্ট সংরক্ষণ করতে চান?" [হ্যাঁ][না]
⬜ B9. Optional voice input ("আরও কিছু বলতে চান?")

── PHASE C: Admin Dashboard ─────────────────────────────────────
⬜ C1. /dashboard route + layout + simple password protection
⬜ C2. Section 1 🆕 — Live analytics (Firestore): abuse pie, monthly trend,
       gender ratio, district map, family vs non-family, risk distribution
⬜ C3. Section 2 — Elder abuse dataset (11 existing charts)
⬜ C4. Section 3 — Comment sentiment (23 existing figures)
⬜ C5. Section 4 — Model performance (sentiment + elder-abuse classifier)

── PHASE D: Evaluation, Deploy, Thesis ──────────────────────────
⬜ D1. evaluate_classifier.py — accuracy / precision / recall / F1 on test_split
⬜ D2. End-to-end test + bug fix
⬜ D3. Deploy (Vercel + Render + Firebase)
⬜ D4. Thesis + demo video + presentation
```

### Lamia's review changes now folded in (v2 → FINAL)

| # | Change | Where |
|---|--------|-------|
| 1 | Welcome screen (স্বাগতম) | §1.3, B2 |
| 2 | Gender: + "বলতে চাই না" | §1.5 Q3 |
| 3 | District: বিভাগ → জেলা (two-step) | §1.5 Q4, B5 |
| 4 | Formal category names (শারীরিক নির্যাতন …) | §1.5 selector |
| 5 | "AI-এর সম্ভাব্যতা: ৮৭%" (not "Confidence 87%") | §1.3.1 |
| 6 | ☎ বিশ্বস্ত ব্যক্তিকে ফোন করুন | §1.3.1, B6 |
| 7 | সম্ভাব্য কারণ section | §1.3.1, A5 |
| 8 | 6 dashboard charts | §1.6, C2 |
| 9 | AI disclaimer ("চূড়ান্ত আইনি সিদ্ধান্ত নয়") | §1.3.1, A5 |
| 10 | Graphical progress bar (██████░░░░ ৬০%) | §1.3, B3 |
| ⭐ | Consent before saving ("সংরক্ষণ করতে চান?") | §1.3, A6, B7 |

---

## 7. TIMELINE (~3–3.5 weeks remaining)

| Phase | Work | Days |
|-------|------|------|
| A — Q&A + TTS backend | question bank, engine, TTS, API, tests | 3–4 |
| B — Elder App frontend | React, buttons, TTS, result screen | 4–5 |
| C — Admin Dashboard | 3 sections (charts already exist) | 3–4 |
| D — Eval + Deploy + Thesis | metrics, test, deploy, write-up | 5–7 |
| **Total** | | **~3–3.5 weeks** ✅ |

> Sentiment study being already complete removed the single biggest time risk.

---

## 8. RESEARCH CONTRIBUTIONS (thesis novelty)

```
1. First Bangla elder-abuse corpus (199 primary field-collected cases)
   + Trust Blind Spot finding (41.8% family abusers)

2. Public-comment sentiment/emotion corpus (2,301 annotated comments)
   + Victim-blaming concentrated in Neglect/Abandonment (OR = 4.87)
   + Religious framing in 22.1% of discourse
   + SVM > BanglaBERT on small imbalanced Bangla corpus (McNemar p = 0.026)
   + Language robustness: BanglaBERT fails on Banglish, SVM holds

3. ASR-robustness finding: Whisper Bangla typos ("মারধর"→"মার্ধুর") break
   keyword & embedding matching, but LLM (Gemini) recovers meaning.
   Embedding comparison: MiniLM 2/5, e5-base 4/5, Gemini-direct correct.
   → motivated the guided Q&A design (avoids ASR noise entirely)

4. Accessible design for low-literacy elders: voice-out questions +
   yes/no buttons; elder as PARTICIPANT (helper as operator) — honest,
   evidence-based accessibility model

5. Abuse → Bangladeshi-law taxonomy (PMA 2013 + দণ্ডবিধি, severity 1–5)
```

---

## 9. KEY DESIGN DECISIONS

| Decision | Why |
|----------|-----|
| Guided yes/no Q&A (not free speech) | Elders can't compose long complaints; avoids Whisper Bangla errors |
| TTS (edge-tts, bn-BD) | Illiterate elders must HEAR questions & results |
| Q&A answers → text summary → rag_engine | 100% reuse of the Gemini legal engine + KB |
| Keyword + Gemini hybrid | Keyword = fast/offline first pass; Gemini = typo-robust reasoning |
| Gemini-direct (not vector RAG) | Bangla embeddings failed on ASR typos (tested); KB is small |
| Whisper kept as OPTIONAL | Preserves work; lets elders add detail; supports ASR research |
| PDF dropped | Supervisor scope; code retained as future work |
| Dashboard in same React app (`/dashboard`) | Simpler deploy, one codebase |

---

## 10. LEGAL FRAMEWORK

**পিতা-মাতার ভরণ-পোষণ আইন, ২০১৩** — §3 ভরণপোষণ · §4 অবহেলা/পরিত্যাগ নিষিদ্ধ ·
§5 UNO-তে অভিযোগ · §6 UNO-এর ক্ষমতা · §7 শাস্তি (১,০০,০০০ টাকা / ৩ মাস) · §8 জরুরি সহায়তা

**দণ্ডবিধি ১৮৬০** — §302 হত্যা · §323/§324 আঘাত · §406 বিশ্বাসভঙ্গ ·
§420 প্রতারণা · §506 ভয় দেখানো

**জরুরি নম্বর** — ৯৯৯ (জাতীয় জরুরি) · ১৬৪৩০ (NLASO বিনামূল্যে আইনি সহায়তা) ·
১০৯২১ (মহিলা হেল্পলাইন)

---

## 11. CURRENT STATUS

| Phase | Status |
|-------|--------|
| Dataset + EDA | ✅ Complete |
| Legal KB + keywords | ✅ Complete |
| Backend core (FastAPI, Whisper, classifier) | ✅ Complete |
| RAG engine (Gemini legal triage) | ✅ Complete |
| Sentiment study (2301 comments) | ✅ Complete |
| **A1 — Question bank finalised** | ✅ **Approved by Lamia** |
| **A2 — question_bank.json** | ⏭️ **NEXT** |
| A3–A8 — engine, TTS, storage, API | ⬜ Pending |
| B — Elder App frontend | ⬜ Pending |
| C — Admin Dashboard | ⬜ Pending |
| D — Eval + Deploy + Thesis | ⬜ Pending |

> **Next action:** A2 — encode the approved question bank as `question_bank.json`
> (questions + branch/skip logic + category mapping).
>
> **Rule:** প্রতিটি step শেষে Lamia confirm করবে → তারপর পরের step।
> কোনো step Lamia-কে না বলে শুরু হবে না।
