# Elder Abuse Detection & Legal Assistance — Complete Implementation Guide

> **Project Title:** A Unified AI Framework for Elder Abuse Detection & Legal Assistance
> **Course:** CSE 499A — Undergraduate Thesis, North South University
> **Semester:** Spring 2026 (Feb 2026 – Aug 2026)
> **Supervisor:** Dr. Sifat Momen, Professor, ECE
> **Team:**
> - Lamia Islam Mim (2212085042) — lamia.mim@northsouth.edu
> - Jannatul Mawa Tahi (2212096042)
> - Umme Sani Ananna (2221618042)
> - Farihaa Khadija Ahmed (2221852042) — farihaa.ahmed@northsouth.edu

---

## 1. PROJECT CONCEPT (সম্পূর্ণ ধারণা)

### 1.1 What is This System?

একটি AI-চালিত **বাংলাদেশী বৃদ্ধ নির্যাতন শনাক্তকরণ ও আইনি সহায়তা সিস্টেম**, যা:

1. **Voice Input নেয়** — গ্রামীণ বয়স্ক মানুষ বাংলায় কথা বলে তাদের সমস্যা জানায়
2. **নির্যাতন শনাক্ত করে** — AI বুঝতে পারে কোন ধরনের নির্যাতন হয়েছে
3. **আইনি পরামর্শ দেয়** — Parents' Maintenance Act 2013 ও Bangladesh Penal Code অনুযায়ী
4. **Legal Document তৈরি করে** — PDF আকারে complaint draft বানিয়ে দেয়
5. **নিকটতম সাহায্যকেন্দ্র দেখায়** — Map-এ ৪৯৫টি UNO অফিস ও হাসপাতাল

### 1.2 Why This System? (6টি Critical Problem Gap)

| # | সমস্যা | কেন সমস্যা |
|---|--------|------------|
| 1 | **Literacy Barrier** | গ্রামের ৫০%+ বয়স্ক মানুষ text-based system ব্যবহার করতে পারেন না |
| 2 | **Legal Knowledge Gap** | ৬০%+ বয়স্ক মানুষ Parents' Maintenance Act 2013 সম্পর্কে জানেন না |
| 3 | **Trust Blind Spot** | ৪১.৮% নির্যাতনকারী নিজের সন্তান — তাই রিপোর্ট করতে ভয় পান |
| 4 | **No Auto Triage** | কোন নির্যাতন কোন আইনে পড়ে তা automatically classify করার সিস্টেম নেই |
| 5 | **Dialect Barrier** | Sylhet, Chittagong, Noakhali dialect NLP models বোঝে না |
| 6 | **Geographic Gap** | কোথায় complaint করতে যাবেন তা জানেন না |

### 1.3 Who is the User?

- **Primary:** বাংলাদেশের গ্রামীণ বয়স্ক মানুষ (৬০+ বছর)
- **Secondary:** তাদের প্রতিবেশী, স্বেচ্ছাসেবী, এবং UNO অফিসের কর্মকর্তারা

---

## 2. DATASET OVERVIEW

### 2.1 Dataset Summary

| বৈশিষ্ট্য | তথ্য |
|---------|------|
| মোট Records | ১৯৯টি |
| মোট Columns | ১২টি (raw) → ১৯টি (cleaned, Phase 1 এ যোগ হবে) |
| ভাষা | বাংলা + ইংরেজি (bilingual) |
| Date Range | ২০১০ – ২০২৬ |
| Data Source Types | Secondary (News), Secondary (Interview), Primary (Interview) |

### 2.2 Data Sources

| Type | Source | উদাহরণ |
|------|--------|---------|
| Secondary (News) | jugantor.com, prothomalo.com, jagonews24.com, bd-pratidin.com, thedailystar.net, bangla.bdnews24.com, ittefaq.com.bd, banglatribune.com | অনলাইন সংবাদপত্র scraping |
| Secondary (Interview) | Shomoy TV, ATN News, Channel I, Bhorer Kagoj Live, Rtv News, DBC News, Kaler Kantho, Kalbela News, Channel24, NEWS24 | YouTube থেকে interview |
| Primary (Interview) | Field Work — Narayanganj, Comilla, Dhaka, Pabna, Lakshmipur, Chittagong, Madaripur, Noakhali, Faridpur, Mymensingh, Kushtia, Rajshahi, Sylhet, Satkhira, Gaibandha, Bandarban, Tangail, Chandpur, Meherpur | সরাসরি Field Interview (March–April 2026) |

### 2.3 Raw Dataset Columns (12টি)

```
Data Type | Date | Source | Location | Abuse Relation | Abuse Category |
Gender | Name | Age | Scenerio(Bangla) | Scenerio(English) | URL / Source type
```

### 2.4 Abuse Categories (Raw → Normalized)

Phase 1 এ normalize করতে হবে:

| Raw Category | Normalized Category | Severity (1-5) | Legal Section |
|-------------|-------------------|----------------|---------------|
| Physical, Physcial, Physical Abuse | **Physical Abuse** | 4 | PMA §3; BPC §323 |
| Abandonment | **Abandonment** | 3 | PMA §3 & §4 |
| Neglect, Neglect  | **Neglect** | 2 | PMA §4 |
| Financial Exploitation | **Financial Exploitation** | 2 | PMA §3; BPC §420/§406 |
| Murder | **Murder** | 5 | BPC §302/§304 |
| verbally, Verbally | **Verbal Abuse** | 1 | PMA §3; BPC §506 |
| Financial Exploitation and physical | **Mixed - Financial & Physical** | 4 | PMA §3; BPC §323/§420 |
| Neglect and Abandonment | **Mixed - Neglect & Abandonment** | 3 | PMA §4 |
| Financial Exploitation and Abandonment | **Mixed - Financial & Abandonment** | 3 | PMA §3 & §4 |
| Abandonment and physical | **Mixed - Physical & Abandonment** | 4 | PMA §3 & §4; BPC §323 |
| Physical and neglect | **Mixed - Physical & Neglect** | 3 | PMA §3 & §4 |
| Financial Exploitation and neglect | **Mixed - Financial & Neglect** | 2 | PMA §3 & §4 |
| Financial Exploitation and Murder | **Mixed - Financial & Murder** | 5 | BPC §302/§420 |

### 2.5 Key Findings from Dataset

- **সবচেয়ে বেশি নির্যাতনকারী:** Son (ছেলে) — ২১.৫%, Children (সন্তানরা) — ৪১.৮% (Trust Blind Spot)
- **সবচেয়ে বেশি ক্যাটাগরি:** Abandonment — ২৪.১%, Physical — ~২০%
- **Peak Vulnerability Age:** ৭০ বছর
- **Primary Victims:** Female বেশি (বিশেষত বিধবা মহিলারা)
- **Geographic Spread:** ঢাকা, চট্টগ্রাম, সিলেট, রাজশাহী, বরিশাল, খুলনা সহ সারা বাংলাদেশ

---

## 3. COMPLETE TECHNOLOGY STACK

### 3.1 Backend

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API Framework | **FastAPI** | REST API server |
| Speech-to-Text | **OpenAI Whisper Large-v3** | Bangla audio → text transcription |
| Audio Processing | **librosa + pydub + ffmpeg** | Noise gate, normalization, format conversion |
| AI/LLM | **GPT-4o-mini** (via OpenAI API) | Entity extraction, legal reasoning |
| RAG Framework | **LangChain** | Retrieval-Augmented Generation pipeline |
| Vector Database | **ChromaDB** or **FAISS** | Vectorized legal knowledge base |
| Embeddings | **OpenAI text-embedding-3-small** | Text → vector conversion |
| PDF Generation | **ReportLab** or **fpdf2** | Legal draft PDF creation |
| Server | **uvicorn** | ASGI server |

### 3.2 Frontend

| Layer | Technology | Purpose |
|-------|-----------|---------|
| UI Framework | **React (Vite)** | Mobile-responsive web app |
| Map | **Leaflet.js** | UNO & hospital navigation |
| Geospatial | **Haversine Formula** | Distance calculation to nearest UNO |
| Styling | **Tailwind CSS** | Senior-friendly UI design |

### 3.3 Data & Storage

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Cloud DB | **Firebase Firestore** | Offline-first case storage |
| File Storage | **Firebase Storage** | Audio files, PDFs |
| Security | **AES-256** | Encrypted sensitive data |
| Environment | **.env** | API keys (OpenAI, Firebase) |

### 3.4 Data Engineering

| Tool | Purpose |
|------|---------|
| **pandas** | Dataset cleaning, EDA |
| **numpy** | Numerical operations |
| **matplotlib / seaborn** | Data visualization |
| **scikit-learn** | Train/test split, evaluation metrics |
| **newspaper3k** | News scraping |

---

## 4. SYSTEM ARCHITECTURE (End-to-End Flow)

```
[User speaks in Bangla]
         │
         ▼
[React Frontend — Voice Recorder]
         │  (WebM/Opus audio upload)
         ▼
[FastAPI Backend — /transcribe endpoint]
         │
         ├──► [AudioPreprocessor]
         │        • Format → 16kHz mono WAV
         │        • Noise Gate (2% peak RMS)
         │        • Peak Normalization (-3.0 dBFS)
         │
         ├──► [WhisperService — Large-v3]
         │        • Bangla transcription
         │        • Dialect prompts (Sylhet/Chittagong/Noakhali/Standard)
         │        • Returns: text, confidence, segments, duration
         │
         ├──► [KeywordClassifier — Phase 2 / Rule-based]
         │        • Fast keyword matching
         │        • Abuse category + severity + legal section
         │
         ├──► [RAG Legal Triage Engine — Phase 3]
         │        • LangChain + ChromaDB
         │        • GPT-4o-mini with PMA 2013 context
         │        • Entity extraction (Name, Age, Location, Abuser)
         │        • Civil vs Criminal classification
         │        • Section-wise legal breakdown
         │
         ├──► [PDF Generator — Phase 3]
         │        • Formal complaint draft
         │        • Section-wise legal citations
         │        • Ready-to-file format
         │
         └──► [Geospatial Layer — Phase 4]
                  • User GPS coordinates
                  • Haversine distance to 495 UNOs
                  • Leaflet.js map rendering
                  • Nearest hospital + UNO office
         │
         ▼
[React Frontend — Results Display]
         • Transcript shown
         • Abuse category + severity badge
         • Legal advice (Bangla)
         • PDF download button
         • Map with nearest UNO
```

---

## 5. FOLDER STRUCTURE (Complete Target Structure)

```
elder-abuse-ai/
│
├── docs/                              ← Documentation
│   └── implementation-flow.md        ← এই ফাইল
│
├── data/                              ← Phase 1: Dataset & Knowledge Base
│   ├── Elder_abuse_Dataset.csv        ← Raw dataset (199 records, 12 columns)
│   ├── elder_abuse_cleaned.csv        ← Cleaned dataset (199 records, 19 columns)
│   ├── keyword_dictionary.json        ← Bangla+English abuse keyword dict
│   ├── act_knowledge_base.json        ← Parents' Maintenance Act 2013 full text
│   ├── train_split.csv                ← Train set (156 rows, 80%)
│   └── test_split.csv                 ← Test set (43 rows, 20%)
│
├── notebooks/
│   └── phase1_eda.py                  ← Phase 1 EDA & data engineering script
│
├── backend/                           ← Phase 2+3: FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    ← FastAPI entry point
│   │   ├── whisper_service.py         ← Whisper speech-to-text
│   │   ├── preprocessor.py            ← Audio preprocessing
│   │   ├── keyword_classifier.py      ← Rule-based keyword classifier
│   │   ├── rag_engine.py              ← Phase 3: LangChain + GPT-4o-mini RAG
│   │   ├── entity_extractor.py        ← Phase 3: GPT-4o-mini entity extraction
│   │   └── pdf_generator.py           ← Phase 3: Legal draft PDF generation
│   ├── vector_store/                  ← Phase 3: ChromaDB vector database
│   │   └── (auto-generated by ChromaDB)
│   ├── phase1_outputs/
│   │   └── keyword_dictionary.json    ← Phase 1 keyword dict (backend copy)
│   └── tests/
│       ├── test_whisper.py
│       ├── test_rag.py
│       └── test_pdf.py
│
├── frontend/                          ← Phase 4: React Frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── VoiceRecorder.jsx      ← Audio recording component
│   │   │   ├── TranscriptDisplay.jsx  ← Show transcript
│   │   │   ├── LegalAdvice.jsx        ← Legal triage results
│   │   │   ├── MapView.jsx            ← Leaflet.js UNO map
│   │   │   └── PDFDownload.jsx        ← PDF download button
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   └── Report.jsx
│   │   └── App.jsx
│   ├── public/
│   └── package.json
│
├── geospatial/                        ← Phase 4: UNO Location Data
│   └── uno_locations.json             ← 495 UNO GPS coordinates
│
├── venv/                              ← Python virtual environment (gitignored)
├── .env                               ← API keys (gitignored)
├── .gitignore
├── phase2_requirements.txt            ← Python dependencies
└── README.md
```

---

## 6. PHASE-BY-PHASE IMPLEMENTATION FLOW

---

### ✅ PHASE 1 — Data Engineering & EDA
**Timeline:** February – March 2026 (COMPLETED previously, needs to be re-done)
**Goal:** Dataset clean করা, keyword dictionary তৈরি, EDA চালানো

#### 6.1.1 What to Build

**File:** `notebooks/phase1_eda.py`

**Step 1: Load & Clean Dataset**
```python
# Input: data/Elder_abuse_Dataset.csv (199 rows, 12 columns)
# Output: data/elder_abuse_cleaned.csv (199 rows, 19 columns)

# 5টি নতুন column যোগ করতে হবে:
# 1. Abuse Category Normalized   — raw category → standard category
# 2. Abuse Relation Normalized   — raw relation → standard relation
# 3. Age Numeric                 — string age → integer
# 4. Date Parsed                 — string date → datetime
# 5. Year                        — datetime → year (integer)
# 6. Trust Blind Spot            — 1 if family member abuser, else 0
# 7. Severity Score              — 1-5 based on abuse category
```

**Step 2: Category Normalization**
```python
# Normalization Map:
category_map = {
    "Physical": "Physical Abuse",
    "Physcial": "Physical Abuse",           # typo fix
    "Physical Abuse": "Physical Abuse",
    "Neglect": "Neglect",
    "Neglect ": "Neglect",                  # trailing space fix
    "Abandonment": "Abandonment",
    "Financial Exploitation": "Financial Exploitation",
    "Murder": "Murder",
    "verbally": "Verbal Abuse",
    "Verbally ": "Verbal Abuse",
    "Financial Exploitation and physical": "Mixed - Financial & Physical",
    "Neglect and Abandonment": "Mixed - Neglect & Abandonment",
    "Financial Exploitation and Abandonment": "Mixed - Financial & Abandonment",
    "Abandonment and physical": "Mixed - Physical & Abandonment",
    "Physical and neglect": "Mixed - Physical & Neglect",
    "Financial Exploitation and neglect": "Mixed - Financial & Neglect",
    "Financial Exploitation and Murder": "Mixed - Financial & Murder",
    "Financial Exploitation, physical and abandonment": "Mixed - Financial & Physical & Abandonment",
}
```

**Step 3: Severity Score (1–5)**
```python
severity_map = {
    "Murder": 5,
    "Mixed - Financial & Murder": 5,
    "Physical Abuse": 4,
    "Mixed - Financial & Physical": 4,
    "Mixed - Physical & Abandonment": 4,
    "Mixed - Financial & Physical & Abandonment": 4,
    "Abandonment": 3,
    "Mixed - Physical & Neglect": 3,
    "Mixed - Neglect & Abandonment": 3,
    "Mixed - Financial & Abandonment": 3,
    "Financial Exploitation": 2,
    "Neglect": 2,
    "Mixed - Financial & Neglect": 2,
    "Verbal Abuse": 1,
}
```

**Step 4: Trust Blind Spot Flag**
```python
# Family members = Trust Blind Spot = 1
family_relations = [
    "Son", "Daughter", "Children", "Son and daughter-in-law",
    "Daughter-in-law", "Grand son", "Grandson", "Nephew and his wife",
    "Wife and Children", "Son, daughter-in-law and grand son",
    "Younger Brother", "Husband and daughter-in-law", "Family"
]
# যদি Abuse Relation এই list এ থাকে → Trust Blind Spot = 1
```

**Step 5: Stratified Train/Test Split**
```python
# 80/20 split, stratified by normalized category, seed=42
# Output: data/train_split.csv (156 rows)
# Output: data/test_split.csv (43 rows)
```

**Step 6: Keyword Dictionary তৈরি**
```json
// Output: data/keyword_dictionary.json
// Structure:
{
  "Physical Abuse": {
    "bangla": ["নির্যাতন", "মারধর", "মারপিট", "আঘাত", "পেটানো", "চড়", "লাথি"],
    "english": ["beat", "hit", "slap", "torture", "assault", "physical abuse"],
    "severity": 4,
    "legal_section": "Section 3 — PMA 2013; BPC §323"
  },
  // ... অন্যান্য categories
}
```

**Step 7: Legal Knowledge Base তৈরি**
```json
// Output: data/act_knowledge_base.json
// Parents' Maintenance Act 2013 এর 12টি section সম্পূর্ণ text
// BPC relevant sections (§302, §323, §406, §420, §506)
```

**Step 8: EDA Visualizations**
- Abuse category distribution
- Perpetrator relation distribution
- Geographic heatmap (Location-wise)
- Age distribution of victims
- Year-wise trend
- Trust Blind Spot analysis
- Severity distribution

#### 6.1.2 Phase 1 Deliverables
- [ ] `data/elder_abuse_cleaned.csv` (199 rows, 19 columns)
- [ ] `data/keyword_dictionary.json`
- [ ] `data/act_knowledge_base.json`
- [ ] `data/train_split.csv` (156 rows)
- [ ] `data/test_split.csv` (43 rows)
- [ ] `notebooks/phase1_eda.py`

#### 6.1.3 Phase 1 Success Criteria
- ১০০% category normalization accuracy
- ০ null values in critical columns (Category, Location, Relation)
- keyword_dictionary covers all 7 abuse types (Bangla + English)
- act_knowledge_base covers all 12 legal sections

---

### ✅ PHASE 2 — Speech Processing Backend
**Timeline:** March – April 2026 (COMPLETED previously, needs to be re-done)
**Goal:** FastAPI backend তৈরি, Whisper দিয়ে Bangla speech-to-text, audio preprocessing

#### 6.2.1 What to Build

**Backend Dependencies (`phase2_requirements.txt`):**
```
fastapi==0.115.0
uvicorn[standard]==0.30.0
python-multipart==0.0.9
openai-whisper==20231117
librosa==0.10.2
soundfile==0.12.1
pydub==0.25.1
numpy==1.26.4
scipy==1.13.0
pytest==8.2.2
httpx==0.27.0
```

**File 1: `backend/app/main.py`**
```python
# FastAPI app with 4 endpoints:
# POST /transcribe         — Audio file → transcript + classification
# POST /transcribe/text    — Direct text → classification (testing)
# GET  /health             — Service health check
# GET  /models             — Available Whisper models list

# Startup: Initialize WhisperService, AudioPreprocessor, KeywordClassifier
# CORS: localhost:5173 (Vite), localhost:3000 (CRA)
```

**Processing Pipeline (`/transcribe` endpoint):**
```
Audio Upload
    │
    ▼
AudioPreprocessor.process()
    ├── Format → 16kHz mono WAV (pydub + ffmpeg)
    ├── Noise Gate (threshold = 2% of peak RMS)
    └── Peak Normalization (-3.0 dBFS)
    │
    ▼
WhisperService.transcribe()
    ├── Language: "bn" (Bangla)
    ├── Dialect hints → initial_prompt
    ├── beam_size=5, temperature=0.0
    └── Returns: text, confidence, segments, duration
    │
    ▼
KeywordClassifier.classify()
    ├── Keyword matching (Bangla + English)
    ├── Abuse category detection
    ├── Severity score
    ├── Legal section reference
    └── Entity extraction (basic regex)
    │
    ▼
JSON Response
```

**File 2: `backend/app/whisper_service.py`**
```python
class WhisperService:
    # Lazy loading — first request এ model load হয়
    # model_size: "large-v3" (recommended), "medium" (low RAM)
    # Dialect prompts for Sylhet, Chittagong, Noakhali, Standard Bangla
    # compute_wer() method for evaluation
```

**File 3: `backend/app/preprocessor.py`**
```python
class AudioPreprocessor:
    # Supported formats: webm, ogg, mp3, m4a, flac, wav
    # Target: 16kHz, mono, PCM_16 WAV
    # Noise gate threshold: 2% of peak RMS
    # Peak target: -3.0 dBFS
```

**File 4: `backend/app/keyword_classifier.py`**
```python
class KeywordClassifier:
    # Loads from: backend/phase1_outputs/keyword_dictionary.json
    # classify(text) → category, severity, legal_section, matched_terms
    # _extract_entities(text) → victim_name, victim_age, location, abuser_relation
    # _civil_or_criminal(category, severity) → "Civil" or "Criminal"
    # _recommend_action(category, severity) → Bangla action string
```

**API Response Structure:**
```json
{
  "success": true,
  "transcript": {
    "text": "আমার ছেলে আমাকে বাড়ি থেকে বের করে দিয়েছে...",
    "language": "bn",
    "confidence": 0.87,
    "segments": [...],
    "duration_s": 12.4
  },
  "audio_stats": {
    "original_duration_s": 12.4,
    "sample_rate": 16000,
    "noise_gate_threshold": 0.002
  },
  "classification": {
    "category": "Abandonment",
    "matched_terms": ["বের করে", "পরিত্যাগ"],
    "legal_section": "Section 3 & 4 — PMA 2013",
    "severity": 3,
    "civil_or_criminal": "Civil",
    "recommended_action": "Section 5, PMA 2013 অনুযায়ী UNO অফিসে ভরণপোষণ অভিযোগ দাখিল করুন।",
    "entities": {
      "victim_name": null,
      "victim_age": null,
      "location": null,
      "abuser_relation": "Son"
    }
  },
  "processing_time_s": 3.21,
  "model": "large-v3"
}
```

**Run Command:**
```bash
cd elder-abuse-ai/backend
uvicorn app.main:app --reload --port 8000
```

#### 6.2.2 Phase 2 Deliverables
- [ ] `backend/app/__init__.py`
- [ ] `backend/app/main.py`
- [ ] `backend/app/whisper_service.py`
- [ ] `backend/app/preprocessor.py`
- [ ] `backend/app/keyword_classifier.py`
- [ ] `backend/phase1_outputs/keyword_dictionary.json` (Phase 1 থেকে copy)
- [ ] `phase2_requirements.txt`
- [ ] `.gitignore`
- [ ] `.env` (OPENAI_API_KEY)

#### 6.2.3 Phase 2 Success Criteria
- WER < 15% for regional Bangla dialects
- 90%+ success in noisy audio conditions
- API response time < 5 seconds

---

### 🔲 PHASE 3 — AI Core: RAG Legal Triage Engine
**Timeline:** April – June 2026 (NEXT PHASE)
**Goal:** GPT-4o-mini + LangChain + ChromaDB দিয়ে intelligent legal triage এবং PDF generation

#### 6.3.1 What to Build

**New Dependencies to add:**
```
langchain==0.1.x
langchain-openai==0.0.x
langchain-community==0.0.x
chromadb==0.4.x
openai==1.x.x
reportlab==4.x.x   # or fpdf2
tiktoken
```

**File 5: `backend/app/rag_engine.py`**

```python
# RAG Pipeline Architecture:
# 1. Vector Database Setup (one-time)
#    - act_knowledge_base.json → chunks → embeddings → ChromaDB
#    - text-embedding-3-small model
#
# 2. Query Processing (per request)
#    - User query (transcript) → embedding
#    - ChromaDB similarity search → top-k relevant legal sections
#    - LangChain chain: retrieved context + query → GPT-4o-mini
#    - System prompt: "তুমি শুধু Parents' Maintenance Act 2013 এবং BPC অনুযায়ী উত্তর দেবে"
#
# 3. Output Structure:
#    - abuse_type: string
#    - applicable_sections: list of section IDs
#    - section_summaries: dict {section_id: summary_in_bangla}
#    - recommended_action: string (Bangla)
#    - civil_or_criminal: string
#    - urgency_level: 1-5

class RAGLegalEngine:
    def __init__(self, knowledge_base_path, vector_store_path):
        # Initialize ChromaDB
        # Load embeddings model
        # Build vector store (if not exists)
        pass
    
    def build_vector_store(self):
        # act_knowledge_base.json → text chunks
        # Chunk strategy: section-level (প্রতিটি section আলাদা chunk)
        # Embed each chunk → store in ChromaDB
        pass
    
    def query(self, transcript: str, keyword_classification: dict) -> dict:
        # Hybrid approach:
        # 1. keyword_classification থেকে initial category নাও
        # 2. RAG দিয়ে detailed legal reasoning করো
        # 3. GPT-4o-mini prompt: transcript + retrieved sections → structured output
        pass
    
    def _build_prompt(self, transcript, retrieved_sections, kw_category):
        system_prompt = """
        তুমি একজন বাংলাদেশী আইনি সহায়তা AI।
        তোমাকে শুধুমাত্র Parents' Maintenance Act 2013 এবং Bangladesh Penal Code
        অনুযায়ী উত্তর দিতে হবে। কোনো অনুমান করবে না।
        শুধুমাত্র নিচের retrieved legal sections এর উপর ভিত্তি করে উত্তর দাও।
        """
        # Retrieved sections context inject করো
        # Structured JSON output চাও
        pass
```

**RAG Vector Database Setup:**
```python
# act_knowledge_base.json structure:
{
  "preamble": {"text": "...", "section": "Preamble"},
  "sec2": {"text": "...", "section": "Section 2 — Definitions"},
  "sec3": {"text": "...", "section": "Section 3 — Maintenance Obligation"},
  "sec4": {"text": "...", "section": "Section 4 — Medical Neglect & Abandonment"},
  "sec5": {"text": "...", "section": "Section 5 — Complaint Procedure (UNO)"},
  "sec6": {"text": "...", "section": "Section 6 — UNO Powers"},
  "sec7": {"text": "...", "section": "Section 7 — Punishment (1 month jail / 5000 BDT)"},
  "sec8": {"text": "...", "section": "Section 8 — Emergency Assistance"},
  "bpc_323": {"text": "...", "section": "BPC §323 — Voluntarily Causing Hurt"},
  "bpc_302": {"text": "...", "section": "BPC §302 — Murder Punishment"},
  "bpc_420": {"text": "...", "section": "BPC §420 — Cheating & Property Fraud"},
  "bpc_406": {"text": "...", "section": "BPC §406 — Breach of Trust"}
}
```

**File 6: `backend/app/entity_extractor.py`**
```python
# GPT-4o-mini দিয়ে entity extraction (Phase 2 এর regex-based কে replace করবে)

class EntityExtractor:
    def extract(self, transcript: str) -> dict:
        # GPT-4o-mini prompt:
        # transcript থেকে extract করো:
        # - victim_name: str | null
        # - victim_age: int | null  
        # - location: str | null  (Bangladesh district/thana)
        # - abuser_relation: str | null
        # - incident_date: str | null
        # - incident_type: list[str]
        # - property_involved: bool
        pass
```

**File 7: `backend/app/pdf_generator.py`**
```python
# ReportLab দিয়ে formal legal complaint PDF তৈরি

class PDFGenerator:
    def generate(self, transcript, entities, rag_result) -> bytes:
        # PDF Structure:
        # ১. Header: বাংলাদেশ সরকার লোগো + "অভিযোগপত্র"
        # ২. অভিযোগকারীর তথ্য (victim info)
        # ৩. অভিযুক্তের তথ্য (abuser info)
        # ৪. ঘটনার বিবরণ (transcript + structured summary)
        # ৫. প্রযোজ্য আইনি ধারা (legal sections)
        # ৬. দাবি ও প্রার্থনা (demands)
        # ৭. স্বাক্ষর স্থান
        # ৮. QR Code (case reference)
        pass
```

**Updated main.py — Phase 3 additions:**
```python
# POST /transcribe endpoint এ নতুন pipeline:
# Step 1: Audio preprocessing (same as Phase 2)
# Step 2: Whisper transcription (same as Phase 2)
# Step 3: Keyword classification (same as Phase 2)
# Step 4: RAG legal triage (NEW - Phase 3)
# Step 5: Entity extraction via GPT-4o-mini (NEW - Phase 3)
# Step 6: PDF generation (NEW - Phase 3)

# New Endpoints:
# POST /generate-pdf    — From existing case data → PDF
# GET  /legal-info      — Legal section reference lookup
```

#### 6.3.2 RAG Evaluation Plan
```python
# Test against train_split.csv and test_split.csv:
# 1. F1-Score > 0.85 for abuse category classification
# 2. Zero "Legal Hallucinations" — সব legal reference actual Act থেকে হতে হবে
# 3. Top-K Accuracy — correct section retrieved in top-3 results
# 4. PDF generation time < 5 seconds
```

#### 6.3.3 Phase 3 Deliverables
- [ ] `backend/app/rag_engine.py`
- [ ] `backend/app/entity_extractor.py`
- [ ] `backend/app/pdf_generator.py`
- [ ] `backend/vector_store/` (ChromaDB auto-generated)
- [ ] Updated `backend/app/main.py` with Phase 3 endpoints
- [ ] Updated `phase2_requirements.txt` with Phase 3 dependencies
- [ ] `backend/tests/test_rag.py`
- [ ] `backend/tests/test_pdf.py`

#### 6.3.4 Phase 3 Success Criteria
- F1-Score > 0.85 on test_split.csv
- Zero hallucinations (all legal citations verifiable)
- Entity extraction accuracy ≥ 90% for Name, Location, Abuser
- PDF generation < 5 seconds

---

### 🔲 PHASE 4 — Deployment & Automation (Frontend + Geospatial)
**Timeline:** June – August 2026
**Goal:** React Frontend, UNO map, Firebase integration, offline-first

#### 6.4.1 What to Build

**React App Structure:**
```
frontend/
├── src/
│   ├── components/
│   │   ├── VoiceRecorder.jsx     ← মাইক্রোফোন button, recording UI
│   │   ├── TranscriptDisplay.jsx ← Bangla transcript show
│   │   ├── AbuseResult.jsx       ← Category badge + severity meter
│   │   ├── LegalAdvice.jsx       ← Section-wise legal breakdown
│   │   ├── MapView.jsx           ← Leaflet.js UNO map
│   │   └── PDFDownload.jsx       ← PDF download button
│   ├── pages/
│   │   ├── Home.jsx              ← Landing page (senior-friendly)
│   │   └── Report.jsx            ← Main reporting page
│   ├── services/
│   │   ├── api.js                ← FastAPI calls
│   │   └── firebase.js           ← Firebase Firestore
│   └── App.jsx
```

**VoiceRecorder Component Logic:**
```javascript
// MediaRecorder API ব্যবহার করে audio capture
// Supported: webm/opus (Chrome), ogg (Firefox)
// UI: বড় লাল button, recording indicator, Bengali label
// Senior-friendly: বড় font, high contrast colors
// POST করবে /transcribe endpoint এ
```

**MapView Component (Leaflet.js):**
```javascript
// geospatial/uno_locations.json থেকে 495 UNO coordinates load
// Haversine formula দিয়ে user GPS থেকে nearest UNO calculate
// Leaflet.js এ:
//   - User location marker (blue)
//   - Nearest 3 UNO markers (red)
//   - Hospital markers (green)
//   - Distance labels
// Click on marker → UNO name, phone, address
```

**Haversine Formula:**
```javascript
function haversineDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2)**2 + 
              Math.cos(lat1*Math.PI/180) * Math.cos(lat2*Math.PI/180) * 
              Math.sin(dLon/2)**2;
    return R * 2 * Math.asin(Math.sqrt(a));
}
```

**Firebase Integration:**
```javascript
// Firestore structure:
// cases/{case_id}/
//   - timestamp
//   - transcript
//   - classification
//   - entities
//   - rag_result
//   - location_lat, location_lon
//   - status: "reported" | "filed" | "resolved"
//
// Firebase Storage:
//   - audio/{case_id}/recording.wav (AES-256 encrypted)
//   - pdfs/{case_id}/complaint.pdf
```

**UNO Database (`geospatial/uno_locations.json`):**
```json
[
  {
    "id": "UNO_001",
    "upazila": "Rupganj",
    "district": "Narayanganj",
    "division": "Dhaka",
    "lat": 23.7800,
    "lon": 90.5200,
    "phone": "+880-2-...",
    "address": "..."
  },
  // ... 495 UNO entries
]
```

#### 6.4.2 Phase 4 Deliverables
- [ ] `frontend/` — Complete React app (Vite)
- [ ] `geospatial/uno_locations.json` — 495 UNO GPS coordinates
- [ ] Firebase project setup (Firestore + Storage)
- [ ] Senior-friendly UI (large fonts, Bengali labels, minimal clicks)
- [ ] Offline-first functionality (Service Worker + Firestore offline)
- [ ] AES-256 encryption for sensitive data

#### 6.4.3 Phase 4 Success Criteria
- UNO distance accuracy within 10 meters
- Map render latency < 3 seconds
- App usable with 2G internet
- UI passes senior-friendly test (UAT)

---

### 🔲 PHASE 5 — Validation & Final Defense
**Timeline:** August 2026
**Goal:** System testing, benchmarking, thesis writing, final presentation

#### 6.5.1 What to Do

**System Integration Testing:**
```
Full Pipeline Test:
Audio Input → Whisper → Keyword → RAG → PDF → Map
↓
Measure: End-to-end latency (target < 10 seconds)
```

**Accuracy Benchmarking:**
```python
# test_split.csv (43 cases) এর উপর:
# 1. Abuse Category Classification:
#    - Precision, Recall, F1-Score per category
#    - Macro F1 > 0.85
#
# 2. WER Measurement:
#    - Record Bengali sentences → transcribe → measure WER
#    - Target: WER < 15% for regional dialects
#
# 3. Legal Section Accuracy:
#    - Gold standard annotations vs RAG output
#    - Zero hallucinations
#
# 4. Entity Extraction:
#    - Name extraction accuracy
#    - Location extraction accuracy
#    - Age extraction accuracy
```

**UAT (User Acceptance Testing):**
- ১০+ বয়স্ক ব্যবহারকারী দিয়ে test
- Task completion rate > 80%
- Average task time < 3 minutes

#### 6.5.2 Final Deliverables
- [ ] Complete integrated system (deployed on cloud)
- [ ] Benchmarking results report
- [ ] Final Senior Design Thesis (Blackbook)
- [ ] Final Presentation slides
- [ ] System demonstration video

---

## 7. COMPLETE ROADMAP (Gantt Summary)

```
PHASE          FEB    MAR    APR    MAY    JUN    JUL    AUG
─────────────────────────────────────────────────────────────
Phase 1        ████   ██
(Data Eng)

Phase 2               ████   ██
(Backend)

Phase 3                       ████   ████
(RAG + AI)

Phase 4                              ████   ████
(Frontend)

Phase 5                                     ████   ████
(Testing)
─────────────────────────────────────────────────────────────
PROJECT START: 02/02/2026         DUE DATE: 31/08/2026
```

---

## 8. IMPLEMENTATION ORDER (কোনটার পরে কোনটা করব)

```
Step 1: Phase 1 — Dataset clean + EDA
    ↓
Step 2: Phase 1 — keyword_dictionary.json + act_knowledge_base.json
    ↓
Step 3: Phase 2 — Backend setup (requirements.txt, .env, .gitignore)
    ↓
Step 4: Phase 2 — AudioPreprocessor (preprocessor.py)
    ↓
Step 5: Phase 2 — WhisperService (whisper_service.py)
    ↓
Step 6: Phase 2 — KeywordClassifier (keyword_classifier.py)
    ↓
Step 7: Phase 2 — FastAPI main.py (with /transcribe, /health)
    ↓
Step 8: Phase 2 — Test all endpoints
    ↓
Step 9: Phase 3 — ChromaDB vector store setup
    ↓
Step 10: Phase 3 — RAG Engine (rag_engine.py)
    ↓
Step 11: Phase 3 — Entity Extractor (entity_extractor.py)
    ↓
Step 12: Phase 3 — PDF Generator (pdf_generator.py)
    ↓
Step 13: Phase 3 — Update main.py with new endpoints
    ↓
Step 14: Phase 3 — Evaluate RAG (F1-Score on test set)
    ↓
Step 15: Phase 4 — UNO location database (uno_locations.json)
    ↓
Step 16: Phase 4 — React app setup (Vite)
    ↓
Step 17: Phase 4 — VoiceRecorder component
    ↓
Step 18: Phase 4 — MapView component (Leaflet.js)
    ↓
Step 19: Phase 4 — Firebase integration
    ↓
Step 20: Phase 5 — Integration testing + benchmarking
    ↓
Step 21: Phase 5 — Thesis writing + presentation
```

---

## 9. SUCCESS METRICS (Per Proposal)

| Objective | Target Metric | Measurement Method |
|-----------|-------------|-------------------|
| Dataset Quality | 100% Category-Reason correlation | Manual verification |
| Speech Accuracy | WER < 15% for regional dialects | Test recordings |
| Legal Triage | F1-Score > 0.85 | test_split.csv evaluation |
| Legal Reliability | Zero hallucinations | Manual audit of all citations |
| Entity Extraction | 100% for Name, Location, Abuser | test_split.csv evaluation |
| PDF Generation | < 5 seconds | Timer benchmark |
| UNO Navigation | Distance accuracy ±10 meters | GPS validation |
| Map Latency | < 3 seconds | Browser performance test |

---

## 10. KEY DESIGN DECISIONS

### 10.1 Why Whisper Large-v3?
- Bangla WER সবচেয়ে কম (~8-12% for standard, ~14-18% for dialects)
- Regional dialect (Sylhet, Chittagong, Noakhali) support
- Open-source, no per-API-call cost

### 10.2 Why RAG instead of fine-tuning?
- Training data কম (199 cases)
- Legal hallucination prevent করতে RAG সবচেয়ে effective
- Act update হলে শুধু knowledge base update করলেই হবে
- GPT-4o-mini সস্তা + fast

### 10.3 Why ChromaDB?
- Lightweight, local-first
- Easy to set up (no separate server needed)
- Good for small knowledge bases (12 sections)

### 10.4 Why React (Vite) instead of Flutter?
- Web-first approach (smartphone browser থেকেই access)
- Offline-first Firebase + Service Worker দিয়ে
- Leaflet.js integration সহজ

### 10.5 Why Keyword Classifier (Phase 2) + RAG (Phase 3) দুটোই?
- Keyword: Fast, no API cost, works offline
- RAG: Deep legal reasoning, better accuracy
- Hybrid: Keyword → initial triage, RAG → detailed legal advice

---

## 11. ENVIRONMENT SETUP

### 11.1 Python Environment
```bash
# Python 3.10+ required
python -m venv venv
source venv/bin/activate      # Linux/Mac
# OR
venv\Scripts\activate          # Windows

pip install -r phase2_requirements.txt

# ffmpeg install করতে হবে (audio conversion এর জন্য):
# Windows: winget install ffmpeg
# Linux: sudo apt install ffmpeg
```

### 11.2 Environment Variables (`.env`)
```
OPENAI_API_KEY=sk-...
FIREBASE_API_KEY=...
FIREBASE_AUTH_DOMAIN=...
FIREBASE_PROJECT_ID=...
FIREBASE_STORAGE_BUCKET=...
```

### 11.3 Run Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### 11.4 Run Frontend (Phase 4)
```bash
cd frontend
npm install
npm run dev     # Vite dev server on port 5173
```

---

## 12. CURRENT STATUS

| Phase | Status | Notes |
|-------|--------|-------|
| **Phase 1** — Data Engineering | 🔲 TO DO | Repo clean, needs to be re-implemented |
| **Phase 2** — Speech Backend | 🔲 TO DO | Repo clean, needs to be re-implemented |
| **Phase 3** — RAG + AI | 🔲 TO DO | Not yet started |
| **Phase 4** — Frontend | 🔲 TO DO | Not yet started |
| **Phase 5** — Validation | 🔲 TO DO | Not yet started |

> **Note:** পূর্বে Phase 1 ও Phase 2 সম্পূর্ণ করা হয়েছিল, কিন্তু branch mismatch এর কারণে repo clean করা হয়েছে। এখন fresh start করা হচ্ছে এই implementation-flow.md অনুযায়ী।

---

## 13. LEGAL FRAMEWORK REFERENCE

### Parents' Maintenance Act 2013 — Key Sections

| Section | বিষয় | Relevant For |
|---------|------|-------------|
| §2 | Definitions (Parents, Child, Maintenance, UNO) | All categories |
| §3 | সন্তানের ভরণপোষণের বাধ্যবাধকতা | Physical, Financial, Verbal |
| §4 | চিকিৎসা অবহেলা ও পরিত্যাগ | Neglect, Abandonment |
| §5 | অভিযোগ দাখিল পদ্ধতি (UNO-তে) | All categories |
| §6 | UNO-এর ক্ষমতা — শুনানি ও আদেশ | All categories |
| §7 | শাস্তি (১ মাস কারাদণ্ড বা ৫,০০০ টাকা জরিমানা) | All categories |
| §8 | জরুরি ও অন্তর্বর্তী সহায়তা | Emergency cases |

### Bangladesh Penal Code — Relevant Sections

| Section | বিষয় | Applicable Abuse |
|---------|------|-----------------|
| §302 | হত্যার শাস্তি | Murder |
| §304 | অনিচ্ছাকৃত হত্যা | Murder (negligent) |
| §323 | স্বেচ্ছায় আঘাত করা | Physical Abuse |
| §406 | বিশ্বাস ভঙ্গ | Financial Exploitation |
| §420 | প্রতারণা ও সম্পত্তি আত্মসাৎ | Financial Exploitation |
| §506 | ভয় দেখানো | Verbal Abuse |

---

## 14. NOTES FOR FUTURE UPDATE

এই ফাইলটি প্রতিটি phase শেষে update করতে হবে:
- Phase 1 শেষে: Current Status আপডেট করো
- Phase 2 শেষে: WER results যোগ করো
- Phase 3 শেষে: F1-Score results যোগ করো
- Phase 4 শেষে: UAT results যোগ করো
- Phase 5 শেষে: Final benchmark results যোগ করো

---

*Last Updated: 28 May 2026 — Initial Documentation*
*Next Update: After Phase 1 completion*
