# Elder Abuse Detection & Legal Assistance — Implementation Flow

> **Project Title:** A Unified AI Framework for Elder Abuse Detection & Legal Assistance
> **Course:** CSE 499A — Undergraduate Thesis, North South University
> **Semester:** Spring 2026
> **Supervisor:** Dr. Sifat Momen, Professor, ECE
> **Team:**
> - Lamia Islam Mim (2212085042)
> - Jannatul Mawa Tahi (2212096042)
> - Umme Sani Ananna (2221618042)
> - Farihaa Khadija Ahmed (2221852042)

> **Target Deadline: 2 months from start**
> **Last Updated: 30 May 2026**
> **Legend:** `✅ Done` | `🔄 Partially Done` | `⬜ Pending` | `⏭️ Next Up`

---

## 1. PROJECT CONCEPT

### 1.1 What is This System?

একটি AI-চালিত বাংলাদেশী বৃদ্ধ নির্যাতন শনাক্তকরণ ও আইনি সহায়তা সিস্টেম যা:

1. **Voice Input নেয়** — বয়স্ক মানুষ বাংলায় / English এ / mixed ভাষায় কথা বলে সমস্যা জানায়
2. **নির্যাতন শনাক্ত করে** — AI বুঝতে পারে কোন ধরনের নির্যাতন হয়েছে
3. **আইনি পরামর্শ দেয়** — Parents' Maintenance Act 2013 ও Bangladesh Penal Code অনুযায়ী
4. **Legal Document তৈরি করে** — PDF আকারে complaint draft বানিয়ে দেয়
5. **নিকটতম সাহায্যকেন্দ্র দেখায়** — Map এ UNO অফিস + Emergency buttons

### 1.2 Why This System? (Core Problem Gaps)

| # | সমস্যা | কেন গুরুত্বপূর্ণ |
|---|--------|-----------------|
| 1 | **Literacy Barrier** | গ্রামের বয়স্ক মানুষ text-based system ব্যবহার করতে পারেন না |
| 2 | **Legal Knowledge Gap** | ৬০%+ বয়স্ক মানুষ PMA 2013 সম্পর্কে জানেন না |
| 3 | **Trust Blind Spot** | ৪১.৮% নির্যাতনকারী নিজের সন্তান — তাই রিপোর্ট করতে ভয় পান |
| 4 | **No Auto Triage** | কোন নির্যাতন কোন আইনে পড়ে তা automatically classify করার সিস্টেম নেই |
| 5 | **Geographic Gap** | কোথায় complaint করতে যাবেন তা জানেন না |

### 1.3 System Flow (সহজ ভাষায়)

```
User কথা বলে / টাইপ করে
        ↓
Whisper (Groq API) → Bangla/English text
        ↓
Keyword Classifier → abuse category + severity (1-5)
        ↓
RAG Engine (ChromaDB + Gemini Flash) → legal advice
        ↓
PDF Generator → complaint letter (Bangla / English / Bilingual)
        ↓
React UI → PDF download + UNO Map + Emergency buttons
```

---

## 2. DATASET OVERVIEW

| বৈশিষ্ট্য | তথ্য |
|---------|------|
| মোট Records | ১৯৯টি |
| Raw Columns | ১২টি |
| Cleaned Columns | ১৯টি (Phase 1 এ যোগ হবে) |
| ভাষা | বাংলা + English (bilingual) |
| Date Range | ২০১০ – ২০২৬ |

**Data Sources:**
- Secondary (News): jugantor.com, prothomalo.com, thedailystar.net ইত্যাদি
- Secondary (Interview): Shomoy TV, ATN News, Channel I ইত্যাদি
- Primary (Interview): Field Work — Narayanganj, Comilla, Dhaka, Pabna, Lakshmipur, Chittagong, Madaripur, Noakhali, Faridpur, Mymensingh, Kushtia, Rajshahi, Sylhet ইত্যাদি (March–April 2026)

**Abuse Categories (Normalized):**

| Category | Severity | Legal Section |
|----------|----------|---------------|
| Physical Abuse | 4 | PMA §3; BPC §323 |
| Abandonment | 3 | PMA §3 & §4 |
| Neglect | 2 | PMA §4 |
| Financial Exploitation | 2 | BPC §406, §420 |
| Verbal Abuse | 1 | BPC §506 |
| Murder | 5 | BPC §302 |
| Sexual Abuse | 4 | BPC §375 |

**Key Dataset Findings:**
- সবচেয়ে বেশি abuser: Son (21.5%)
- পরিবারের মোট: **41.8%** → "Trust Blind Spot"
- Peak vulnerable age: 70 বছর
- সবচেয়ে বেশি category: Abandonment (24.1%)

---

## 3. TECHNOLOGY STACK (সম্পূর্ণ Free)

| Component | Tool | Cost |
|-----------|------|------|
| Speech-to-Text | Groq Whisper API (`whisper-large-v3-turbo`) | Free |
| LLM / Legal AI | Google Gemini 1.5 Flash | Free |
| Embeddings | HuggingFace `paraphrase-multilingual-MiniLM-L12-v2` | Free (local) |
| Vector DB | ChromaDB (local folder) | Free |
| Backend | FastAPI + uvicorn | Free |
| Frontend | React + Vite + Tailwind CSS | Free |
| Map | Leaflet.js + OpenStreetMap | Free |
| PDF | fpdf2 + NotoSansBengali font | Free |
| Database | Firebase Firestore (Spark plan) | Free |
| Geocoding | Nominatim (OpenStreetMap) | Free |
| Deploy | Vercel (frontend) + Render (backend) | Free |

**API Keys দরকার:**
```
GROQ_API_KEY       → console.groq.com (free signup)
GOOGLE_API_KEY     → aistudio.google.com (free signup)
FIREBASE_*         → console.firebase.google.com (free Spark plan)
```

---

## 4. TEAM ASSIGNMENT (কে কী করবে)

> **বাস্তব সত্য:** Code সব Lamia করবে। বাকি ৩ জন অন্য গুরুত্বপূর্ণ কাজ করবে।
> **প্রতি সপ্তাহে Sir কে update দেখাবে — প্রত্যেকে তাদের নিজস্ব অংশ।**

| Member | দায়িত্ব | Deliverable |
|--------|---------|------------|
| **Lamia Islam Mim** | সব code, backend, AI pipeline, deployment | Running system + demo |
| **Jannatul Mawa Tahi** | Dataset EDA, charts, notebook | Jupyter notebook (EDA) |
| **Umme Sani Ananna** | Literature review, thesis writing (Related Work, Methodology chapter) | Word document |
| **Farihaa Khadija Ahmed** | UNO data collection (lgd.gov.bd), user testing (5 জন বয়স্ক), feedback | Excel + test report |

---

## 5. 2-MONTH WEEKLY PLAN

**Start Date:** এখন (Week 1)
**End Date:** 8 সপ্তাহ পরে

```
WEEK    PHASE     LAMIA এর কাজ                    TEAM UPDATE
────────────────────────────────────────────────────────────────
Week 1  Phase 1   Dataset clean + EDA              Tahi: EDA notebook start
                  keyword_dictionary.json           Ananna: Related Work draft
                  act_knowledge_base.json

Week 2  Phase 1→2 knowledge base শেষ              Tahi: Charts complete
                  FastAPI setup + /health           Ananna: 5 papers summarize
                  Groq Whisper integration          Farihaa: UNO data (20 entries)

Week 3  Phase 2   /transcribe endpoint working      Tahi: EDA notebook final
                  AudioPreprocessor (ffmpeg)        Ananna: Methodology chapter
                  KeywordClassifier complete         Farihaa: UNO data (40 entries)

Week 4  Phase 2→3 Phase 2 test complete             Tahi: Severity analysis chart
                  ChromaDB vector store build        Ananna: System Design section
                  RAG Engine start                  Farihaa: UNO data (64 entries)

Week 5  Phase 3   RAG + Gemini → legal advice      Tahi: Trust Blind Spot analysis
                  Entity extraction (basic)          Ananna: Intro chapter draft
                  PDF Generator (1 page)             Farihaa: 5 user test (observe)

Week 6  Phase 3→4 Phase 3 test complete             Tahi: EDA final charts export
                  React app setup (Vite)             Ananna: Abstract + Conclusion draft
                  VoiceRecorder component            Farihaa: User feedback form fill

Week 7  Phase 4   MapView (Leaflet.js)              Tahi: Final notebook clean
                  Firebase Firestore                 Ananna: Thesis draft complete
                  Full pipeline connect              Farihaa: Test report write

Week 8  Phase 5   Bug fix + End-to-end test         ALL: Presentation slides
                  Vercel + Render deploy             ALL: Final demo rehearse
                  Thesis polish
────────────────────────────────────────────────────────────────
```

---

## 6. PHASE-BY-PHASE IMPLEMENTATION

---

### PHASE 1 — Dataset Preparation
**Timeline:** Week 1–2
**Owner:** Lamia (code) + Tahi (EDA notebook)

#### কী করতে হবে:

```
1. data/ folder বানাও
2. Elder_abuse_Dataset.csv রাখো সেখানে
3. notebooks/01_eda.ipynb বানাও
4. Dataset clean করো (7টি নতুন column যোগ):
   - Abuse_Category_Normalized  (typo fix, standard name)
   - Abuse_Relation_Normalized  (Son/Daughter/Spouse...)
   - Age_Numeric                (string → int, "Unknown" → NaN)
   - Date_Parsed                (string → datetime)
   - Year                       (date থেকে extract)
   - Trust_Blind_Spot           (1 = family member abuser, 0 = other)
   - Severity_Score             (1-5 based on category)
5. Train/test split: 80/20, stratified by category, random_state=42
6. keyword_dictionary.json তৈরি (Bangla + English keywords)
7. act_knowledge_base.json তৈরি (PMA 2013 + BPC sections)
```

#### Folder Structure (Phase 1):
```
elder-abuse/
├── data/
│   ├── Elder_abuse_Dataset.csv       ← raw dataset
│   ├── cleaned_dataset.csv           ← Phase 1 output
│   ├── train_split.csv               ← 80% (156 cases)
│   └── test_split.csv                ← 20% (43 cases)
├── notebooks/
│   └── 01_eda.ipynb                  ← EDA + charts
└── backend/
    └── phase1_outputs/
        ├── keyword_dictionary.json   ← classifier এর জন্য
        └── act_knowledge_base.json   ← RAG এর জন্য
```

#### keyword_dictionary.json structure:
```json
{
  "physical": {
    "bangla": ["মারধর", "আঘাত", "চড়", "লাথি", "মেরেছে"],
    "english": ["beat", "hit", "slap", "assault", "punch", "injury"],
    "mixed_forms": ["beat করেছে", "hit করেছে"]
  },
  "financial": {
    "bangla": ["সম্পত্তি", "টাকা", "জমি", "দলিল", "প্রতারণা"],
    "english": ["property", "money", "land", "fraud", "inheritance"],
    "mixed_forms": ["property নিয়েছে", "account থেকে টাকা নিয়েছে"]
  },
  "abandonment": {
    "bangla": ["বের করে দিয়েছে", "পরিত্যাগ", "রাস্তায় ফেলে"],
    "english": ["evict", "abandoned", "thrown out", "kicked out"],
    "mixed_forms": ["evict করে দিয়েছে"]
  },
  "verbal": {
    "bangla": ["গালি", "অপমান", "হুমকি", "ভয় দেখানো"],
    "english": ["insult", "threaten", "threat", "verbal abuse"],
    "mixed_forms": ["threaten করেছে"]
  },
  "neglect": {
    "bangla": ["খাবার দেয় না", "ওষুধ দেয় না", "অবহেলা"],
    "english": ["not feeding", "no food", "no medicine", "neglect"],
    "mixed_forms": ["medicine দেয় না"]
  }
}
```

#### act_knowledge_base.json structure:
```json
{
  "sec3": {
    "section": "PMA 2013 — Section 3",
    "text": "প্রতিটি সন্তান তাদের পিতামাতার ভরণপোষণ করতে বাধ্য..."
  },
  "sec4": {
    "section": "PMA 2013 — Section 4",
    "text": "চিকিৎসা অবহেলা ও পরিত্যাগ নিষিদ্ধ..."
  },
  "sec5": {
    "section": "PMA 2013 — Section 5",
    "text": "UNO অফিসে অভিযোগ দাখিল করার পদ্ধতি..."
  },
  "sec6": {
    "section": "PMA 2013 — Section 6",
    "text": "UNO-এর ক্ষমতা — শুনানি ও আদেশ..."
  },
  "sec7": {
    "section": "PMA 2013 — Section 7",
    "text": "শাস্তি: অনূর্ধ্ব ১,০০,০০০ টাকা অর্থদণ্ড এবং অনাদায়ে অনূর্ধ্ব ৩ মাস কারাদণ্ড..."
  },
  "bpc_323": {
    "section": "BPC §323 — Voluntarily Causing Hurt",
    "text": "স্বেচ্ছায় আঘাত করার শাস্তি..."
  },
  "bpc_420": {
    "section": "BPC §420 — Cheating & Fraud",
    "text": "প্রতারণা ও সম্পত্তি আত্মসাতের শাস্তি..."
  },
  "bpc_506": {
    "section": "BPC §506 — Criminal Intimidation",
    "text": "ভয় দেখানোর শাস্তি..."
  }
}
```

#### Phase 1 Deliverables:
```
✅ data/Elder_abuse_Dataset.csv          (199 rows — loaded)
✅ notebooks/01_eda.ipynb               (53 cells, 11 charts — done)
✅ data/chart_01 to chart_11.png        (EDA charts — done)
✅ data/cleaned_dataset.csv             (199 rows, 20 cols, 86.1 KB)
✅ data/train_split.csv                 (159 rows, 20 cols)
✅ data/test_split.csv                  (40 rows, 20 cols)
✅ backend/phase1_outputs/keyword_dictionary.json   (6 categories, 231 keywords)
✅ backend/phase1_outputs/act_knowledge_base.json   (16 sections, 9 PMA + 7 BPC)
```

#### Common Errors (Phase 1):
```python
# Date parse error → inconsistent format
df['Date_Parsed'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)

# Age "Unknown" → NaN
df['Age_Numeric'] = pd.to_numeric(df['Age'], errors='coerce')

# Category typo fix
df['Abuse Category'] = df['Abuse Category'].str.strip()
category_map = {
    'Physcial': 'Physical Abuse',
    'Physical': 'Physical Abuse',
    'Neglect ': 'Neglect',
}
df['Abuse_Category_Normalized'] = df['Abuse Category'].replace(category_map)
```

---

### PHASE 2 — Speech Backend
**Timeline:** Week 2–3
**Owner:** Lamia

#### কী করতে হবে:

```
1. backend/app/ folder structure তৈরি
2. Virtual environment + requirements install
3. preprocessor.py — audio → 16kHz WAV (ffmpeg)
4. whisper_service.py — Groq API দিয়ে speech-to-text
5. keyword_classifier.py — keyword matching + severity
6. main.py — FastAPI (3 endpoints)
7. Test: /health, /transcribe, /transcribe/text
```

#### Folder Structure (Phase 2):
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py               ← FastAPI app
│   ├── preprocessor.py       ← audio → WAV
│   ├── whisper_service.py    ← Groq Whisper
│   └── keyword_classifier.py ← category + severity
├── phase1_outputs/
│   ├── keyword_dictionary.json
│   └── act_knowledge_base.json
├── requirements.txt
├── .env                      ← API keys (gitignored)
└── .gitignore
```

#### requirements.txt:
```
fastapi==0.115.0
uvicorn[standard]==0.30.0
python-multipart==0.0.9
pydub==0.25.1
groq==0.9.0
google-generativeai==0.7.0
langchain-community==0.2.0
chromadb==0.5.0
sentence-transformers==3.0.0
fpdf2==2.8.0
python-dotenv==1.0.0
pytest==8.2.2
httpx==0.27.0
```

#### whisper_service.py (Groq API):
```python
from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def transcribe(audio_path: str) -> dict:
    with open(audio_path, "rb") as f:
        result = client.audio.transcriptions.create(
            file=f,
            model="whisper-large-v3-turbo",
            response_format="verbose_json"
            # language বলছি না → auto-detect করবে (Bangla/English/Mixed)
        )
    text = result.text
    # Detect language mode
    has_bangla  = any('ঀ' <= ch <= '৿' for ch in text)
    has_english = any('a' <= ch.lower() <= 'z' for ch in text)
    if has_bangla and has_english:
        lang_mode = "mixed"
    elif has_bangla:
        lang_mode = "bangla"
    else:
        lang_mode = "english"

    return {
        "text":          text,
        "language_mode": lang_mode,
        "confidence":    getattr(result, 'confidence', 0.9)
    }
```

#### keyword_classifier.py:
```python
import json

class KeywordClassifier:
    def __init__(self, dict_path: str):
        with open(dict_path, encoding="utf-8") as f:
            self.keywords = json.load(f)

    def classify(self, text: str) -> dict:
        text_lower = text.lower()
        scores = {}
        for category, kw_group in self.keywords.items():
            all_kw = (kw_group.get("bangla", []) +
                      kw_group.get("english", []) +
                      kw_group.get("mixed_forms", []))
            scores[category] = sum(1 for kw in all_kw if kw.lower() in text_lower)

        if not any(scores.values()):
            return {"category": "unknown", "severity": 1, "confidence": 0.0}

        top = max(scores, key=scores.get)
        severity_map = {
            "physical": 4, "financial": 2, "abandonment": 3,
            "verbal": 1, "neglect": 2, "sexual": 4, "murder": 5
        }
        total = sum(scores.values())
        return {
            "category": top,
            "severity": severity_map.get(top, 2),
            "confidence": round(scores[top] / total, 2) if total > 0 else 0.0,
            "all_scores": scores
        }
```

#### main.py (FastAPI — Phase 2):
```python
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import tempfile, os, shutil
from .preprocessor import preprocess_audio
from .whisper_service import transcribe
from .keyword_classifier import KeywordClassifier

app = FastAPI(title="Elder Abuse AI API")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

classifier = KeywordClassifier("phase1_outputs/keyword_dictionary.json")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        shutil.copyfileobj(audio.file, tmp)
        tmp_path = tmp.name
    try:
        wav_path   = preprocess_audio(tmp_path)
        whisper    = transcribe(wav_path)
        classify   = classifier.classify(whisper["text"])
        return {"transcript": whisper, "classification": classify}
    finally:
        os.unlink(tmp_path)

class TextRequest(BaseModel):
    text: str

@app.post("/transcribe/text")
def transcribe_text(req: TextRequest):
    classify = classifier.classify(req.text)
    return {"transcript": {"text": req.text}, "classification": classify}
```

#### Phase 2 Deliverables:
```
□ backend/app/__init__.py
□ backend/app/main.py
□ backend/app/preprocessor.py
□ backend/app/whisper_service.py
□ backend/app/keyword_classifier.py
□ backend/requirements.txt
□ backend/.env (gitignored)
□ backend/.gitignore
□ Test: curl localhost:8000/health → {"status": "ok"}
□ Test: audio file upload → transcript + category
```

#### Common Errors (Phase 2):
```
Error: "ffmpeg not found"
Fix:   winget install --id Gyan.FFmpeg
       তারপর নতুন terminal খোলো

Error: CORS error (frontend থেকে call করলে)
Fix:   CORSMiddleware এ allow_origins=["*"] যোগ করো

Error: "groq module not found"
Fix:   pip install groq
```

---

### PHASE 3 — AI Core: RAG + PDF
**Timeline:** Week 4–5
**Owner:** Lamia

#### কী করতে হবে:

```
1. ChromaDB vector store build করো (act_knowledge_base.json থেকে)
2. rag_engine.py — ChromaDB + Gemini Flash → legal advice
3. pdf_generator.py — fpdf2 দিয়ে complaint PDF
4. entity_extractor.py — basic regex (name, age, location)
5. main.py update করো (Phase 3 endpoints যোগ)
6. Test: RAG accuracy on test_split.csv
```

#### rag_engine.py:
```python
import os, json, re
import google.generativeai as genai
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
gemini = genai.GenerativeModel(
    "gemini-1.5-flash",
    generation_config={"response_mime_type": "application/json"}
)

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

def build_vector_store(kb_path: str, store_path: str):
    with open(kb_path, encoding="utf-8") as f:
        kb = json.load(f)
    texts     = [v["text"]    for v in kb.values()]
    metadatas = [{"section": v["section"]} for v in kb.values()]
    vs = Chroma.from_texts(texts, embeddings,
                           metadatas=metadatas,
                           persist_directory=store_path)
    vs.persist()
    return vs

def load_vector_store(store_path: str):
    return Chroma(persist_directory=store_path, embedding_function=embeddings)

def get_legal_advice(transcript: str, category: str,
                     language_mode: str, vectorstore) -> dict:
    results = vectorstore.similarity_search(f"{category}: {transcript}", k=3)
    context = "\n\n".join([r.page_content for r in results])

    if language_mode == "english":
        lang_instruction = "Respond entirely in English."
    elif language_mode == "bangla":
        lang_instruction = "সম্পূর্ণ বাংলায় উত্তর দাও।"
    else:
        lang_instruction = "Provide advice in both Bangla and English."

    prompt = f"""
You are a Bangladesh elder abuse legal assistance AI.
Answer ONLY based on the legal sections provided below. Do NOT make up laws.
{lang_instruction}

Legal Context:
{context}

Complaint: {transcript}
Category: {category}

Respond in JSON:
{{
  "abuse_type": "...",
  "applicable_sections": ["PMA 2013 Section X", "BPC §XXX"],
  "legal_advice_bangla": "...",
  "legal_advice_english": "...",
  "recommended_action_bangla": "...",
  "recommended_action_english": "...",
  "civil_or_criminal": "Civil | Criminal | Both",
  "urgency": 1
}}
"""
    response = gemini.generate_content(prompt)
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        return json.loads(match.group()) if match else {}
```

#### pdf_generator.py:
```python
from fpdf import FPDF
from datetime import date

class ComplaintPDF(FPDF):
    def header(self):
        self.set_font("Bengali", size=12)
        self.cell(0, 8, "গণপ্রজাতন্ত্রী বাংলাদেশ সরকার", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 7, "উপজেলা নির্বাহী অফিসার বরাবর — অভিযোগপত্র", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

def generate_pdf(case_data: dict, language_mode: str = "bangla") -> bytes:
    pdf = ComplaintPDF()
    pdf.add_font("Bengali", fname="fonts/NotoSansBengali-Regular.ttf")
    pdf.add_font("Latin",   fname="fonts/NotoSans-Regular.ttf")
    pdf.set_fallback_fonts(["Latin"], exact_match=False)
    pdf.add_page()
    pdf.set_font("Bengali", size=10)

    fields = [
        ("নাম / Name",        case_data.get("victim_name", "—")),
        ("বয়স / Age",         case_data.get("victim_age",  "—")),
        ("ঠিকানা / Location", case_data.get("location",    "—")),
        ("নির্যাতনের ধরন",    case_data.get("abuse_type",  "—")),
    ]
    for label, value in fields:
        pdf.cell(0, 7, f"{label}: {value}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font("Bengali", size=11)
    pdf.cell(0, 8, "ঘটনার বিবরণ / Complaint:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Bengali", size=10)
    pdf.multi_cell(0, 6, case_data.get("transcript", ""))
    pdf.ln(3)

    pdf.set_font("Bengali", size=11)
    pdf.cell(0, 8, "প্রযোজ্য আইন / Applicable Sections:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Bengali", size=10)
    for sec in case_data.get("applicable_sections", []):
        pdf.cell(0, 6, f"  • {sec}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font("Bengali", size=11)
    pdf.cell(0, 8, "আইনি পরামর্শ / Legal Advice:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Bengali", size=10)
    advice = case_data.get("legal_advice_bangla", "") or case_data.get("legal_advice_english", "")
    pdf.multi_cell(0, 6, advice)
    pdf.ln(3)

    pdf.set_font("Bengali", size=10)
    pdf.cell(0, 6, "জরুরি: 999  |  বিনামূল্যে আইনি সহায়তা: 16430", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    pdf.cell(0, 6, f"তারিখ / Date: {date.today().strftime('%d %B %Y')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    pdf.cell(60, 7, "স্বাক্ষর / Signature", border="T")

    return bytes(pdf.output())
```

#### Phase 3 Deliverables:
```
□ backend/app/rag_engine.py
□ backend/app/pdf_generator.py
□ backend/app/entity_extractor.py (basic regex)
□ backend/vector_store/ (ChromaDB — auto-generated)
□ backend/fonts/NotoSansBengali-Regular.ttf
□ backend/fonts/NotoSans-Regular.ttf
□ main.py updated with /legal-advice + /generate-pdf endpoints
□ Test: RAG query → legal advice JSON
□ Test: PDF generated for 3 sample cases (Bangla, English, Mixed)
```

#### Common Errors (Phase 3):
```
Error: ChromaDB "Collection already exists"
Fix:   os.path.exists("vector_store") হলে load করো, না হলে build করো

Error: Gemini JSON parse failed
Fix:   generation_config={"response_mime_type": "application/json"}

Error: Bangla PDF blank squares
Fix:   NotoSansBengali-Regular.ttf font ব্যবহার করো
       Download: fonts.google.com/noto/specimen/Noto+Sans+Bengali
```

---

### PHASE 4 — Frontend + Map
**Timeline:** Week 6–7
**Owner:** Lamia

#### কী করতে হবে:

```
1. React + Vite app তৈরি
2. Tailwind CSS setup
3. VoiceRecorder component (mic button + recording UI)
4. ResultDisplay component (transcript + category + advice)
5. MapView component (Leaflet.js + UNO locations)
6. Emergency buttons (999, 16430)
7. PDF download button
8. Firebase Firestore basic setup (case save)
9. Vercel deploy
```

#### Folder Structure (Phase 4):
```
frontend/
├── src/
│   ├── components/
│   │   ├── VoiceRecorder.jsx
│   │   ├── ResultDisplay.jsx
│   │   ├── MapView.jsx
│   │   └── EmergencyButtons.jsx
│   ├── pages/
│   │   ├── Home.jsx
│   │   └── Report.jsx
│   ├── services/
│   │   ├── api.js
│   │   └── firebase.js
│   └── App.jsx
├── public/
└── package.json
```

#### VoiceRecorder.jsx:
```jsx
import { useState, useRef } from 'react';

export default function VoiceRecorder({ onComplete }) {
  const [recording, setRecording] = useState(false);
  const mediaRef = useRef(null);
  const chunksRef = useRef([]);

  const start = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRef.current = new MediaRecorder(stream);
    mediaRef.current.ondataavailable = e => chunksRef.current.push(e.data);
    mediaRef.current.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
      onComplete(blob);
      chunksRef.current = [];
    };
    mediaRef.current.start();
    setRecording(true);
  };

  const stop = () => { mediaRef.current.stop(); setRecording(false); };

  return (
    <div className="flex flex-col items-center gap-4">
      <button
        onClick={recording ? stop : start}
        className={`w-36 h-36 rounded-full text-white text-xl font-bold
          ${recording ? 'bg-gray-500 animate-pulse' : 'bg-red-600 hover:bg-red-700'}`}
      >
        {recording ? 'থামুন ⏹' : 'কথা বলুন 🎤'}
      </button>
      {recording && <p className="text-red-600 font-bold">● রেকর্ডিং চলছে...</p>}
    </div>
  );
}
```

#### MapView.jsx (Leaflet.js):
```jsx
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

function haversine(lat1, lon1, lat2, lon2) {
  const R = 6371, toR = d => d * Math.PI / 180;
  const a = Math.sin(toR(lat2-lat1)/2)**2 +
            Math.cos(toR(lat1)) * Math.cos(toR(lat2)) *
            Math.sin(toR(lon2-lon1)/2)**2;
  return R * 2 * Math.asin(Math.sqrt(a));
}

export default function MapView({ userLat, userLon, unoList }) {
  const nearest = unoList
    .map(u => ({ ...u, dist: haversine(userLat, userLon, u.lat, u.lon) }))
    .sort((a, b) => a.dist - b.dist)
    .slice(0, 3);

  return (
    <MapContainer center={[userLat, userLon]} zoom={11}
                  style={{ height: '350px', width: '100%' }}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {nearest.map(u => (
        <Marker key={u.id} position={[u.lat, u.lon]}>
          <Popup>
            <b>{u.district} UNO অফিস</b><br/>
            📞 {u.phone}<br/>
            🚶 {u.dist.toFixed(1)} কিমি
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
```

#### uno_locations.json (Phase 4 শুরুতে ৬৪ district HQ দিয়ে শুরু):
```json
[
  {"id": "UNO_01", "district": "Dhaka",        "upazila": "Savar",    "lat": 23.8581, "lon": 90.2659, "phone": "02-XXXXXXX"},
  {"id": "UNO_02", "district": "Narayanganj",  "upazila": "Rupganj",  "lat": 23.7800, "lon": 90.5200, "phone": "02-XXXXXXX"},
  {"id": "UNO_03", "district": "Chittagong",   "upazila": "Sitakunda","lat": 22.6200, "lon": 91.6600, "phone": "031-XXXXXX"}
]
```

#### Emergency Buttons:
```jsx
export default function EmergencyButtons({ severity }) {
  return (
    <div className="flex flex-col gap-3 mt-4">
      {severity >= 4 && (
        <a href="tel:999"
           className="bg-red-600 text-white text-center py-4 rounded-xl text-xl font-bold">
          🚨 এখনই 999 কল করুন
        </a>
      )}
      <a href="tel:16430"
         className="bg-green-600 text-white text-center py-3 rounded-xl font-bold">
        📞 বিনামূল্যে আইনি সহায়তা: 16430
      </a>
    </div>
  );
}
```

#### Phase 4 Deliverables:
```
□ frontend/ React app (Vite)
□ VoiceRecorder.jsx
□ ResultDisplay.jsx
□ MapView.jsx (Leaflet.js)
□ EmergencyButtons.jsx (severity-based)
□ geospatial/uno_locations.json (64 district entries)
□ Firebase Firestore — basic case save
□ Vercel deploy (HTTPS — geolocation এর জন্য দরকার)
□ Full demo: voice → text → advice → PDF → map
```

---

### PHASE 5 — Testing + Deploy + Thesis
**Timeline:** Week 8
**Owner:** Lamia (testing) + Ananna (thesis) + Farihaa (user test)

#### কী করতে হবে:

```
1. End-to-end test (3 sample cases: Bangla, English, Mixed)
2. Bug fix (যা test এ বের হবে)
3. Render.com এ backend deploy
4. Vercel এ frontend deploy
5. 5 জন বয়স্ক user দিয়ে test (Farihaa করবে)
6. Thesis final polish
7. Demo video record করো (5-10 মিনিট)
8. Presentation slides তৈরি
```

#### Evaluation (Simplified):
```python
# test_split.csv (43 cases) দিয়ে test:
# 1. Abuse Category Accuracy:
#    - Keyword classifier: correct category / total × 100
#    - Target: > 75% accuracy
#
# 2. RAG Legal Section:
#    - Manually check 10 cases: legal section সঠিক কিনা
#    - Target: ≥ 8/10 সঠিক
#
# 3. Whisper WER:
#    - 5টি test audio record করো (নিজে বলো)
#    - Ground truth text লিখে রাখো
#    - WER calculate করো
#    - Target: < 20% WER
```

#### Phase 5 Deliverables:
```
□ Deployed backend URL (Render)
□ Deployed frontend URL (Vercel)
□ Accuracy report (classifier + RAG)
□ 5 user test feedback summary (Farihaa করবে)
□ Final thesis (Blackbook)
□ Presentation slides (10-12 slides)
□ Demo video (5-10 min)
```

---

## 7. SIMPLIFIED 2-MONTH ROADMAP

```
         WEEK 1    WEEK 2    WEEK 3    WEEK 4
         ────────────────────────────────────
Phase 1  ██████████████
Phase 2            ██████████████████
                   WEEK 4    WEEK 5    WEEK 6    WEEK 7    WEEK 8
                   ──────────────────────────────────────────────
Phase 3            ██████████████████
Phase 4                               ██████████████████
Phase 5                                                   ████████

Start: Now           End: Week 8
```

---

## 8. IMPLEMENTATION ORDER (Step by Step)

```
── PHASE 1 ──────────────────────────────────────────────────────
✅ Step 1:  data/ folder + dataset load + EDA notebook (11 charts)
✅ Step 2:  cleaned_dataset.csv + train/test split
✅ Step 3:  keyword_dictionary.json তৈরি
✅ Step 4:  act_knowledge_base.json তৈরি (16 sections)

── PHASE 2 ──────────────────────────────────────────────────────
✅ Step 5:  backend/app/ setup + requirements.txt + .env
✅ Step 6:  preprocessor.py (audio → WAV)
✅ Step 7:  whisper_service.py (Groq API)
✅ Step 8:  keyword_classifier.py
✅ Step 9:  main.py — /health + /transcribe + /transcribe/text
✅ Step 10: Phase 2 test complete (3 real audio tests, English perfect)

── PHASE 3 ──────────────────────────────────────────────────────
✅ Step 11: RAG retrieval (Option C: keyword/category, not ChromaDB)
✅ Step 12: rag_engine.py (Gemini 2.5 Flash) — solves Whisper typos
✅ Step 13: entity_extractor.py + reporter-mode (self/third-party)
🔄 Step 14: pdf_generator.py — format + Bengali rendering verified, generator pending ← NEXT
⬜ Step 15: main.py update — Phase 3 endpoints
⬜ Step 16: Phase 3 test complete

── PHASE 4 ──────────────────────────────────────────────────────
⬜ Step 17: uno_locations.json (64 entries)
⬜ Step 18: React app + VoiceRecorder
⬜ Step 19: MapView (Leaflet.js)
⬜ Step 20: EmergencyButtons + PDF download
⬜ Step 21: Firebase Firestore basic save
⬜ Step 22: Vercel + Render deploy

── PHASE 5 ──────────────────────────────────────────────────────
⬜ Step 23: End-to-end test + bug fix
⬜ Step 24: Thesis + demo video + presentation
```

**Progress: 13 / 24 Steps complete (54%)** — Phase 3 চলছে (RAG + entity done)

> **Phase 3 Architecture Decision (Option C):** ChromaDB vector store বাদ দিয়ে
> keyword/category-based retrieval + Gemini ব্যবহার করা হয়েছে। কারণ:
> (১) Bangla embedding models (MiniLM 2/5, e5-base 4/5) Whisper typo case এ fail করে;
> (২) Gemini typo সঠিক বোঝে; (৩) কোনো 1GB model নেই → free-tier deploy সহজ।
> `vector_store.py` thesis comparison হিসেবে রাখা হয়েছে।

---

## 9. SUCCESS METRICS (Realistic Targets)

| Metric | Target | Method |
|--------|--------|--------|
| Whisper WER | < 20% | 5 test recordings |
| Category Accuracy | > 75% | test_split.csv (43 cases) |
| RAG Legal Accuracy | ≥ 8/10 | Manual check (10 cases) |
| PDF Generation Time | < 10 seconds | Timer test |
| UNO Map Load | < 5 seconds | Browser test |
| User Task Completion | ≥ 4/5 users complete | Farihaa's 5-person UAT |

---

## 10. ENVIRONMENT SETUP

```bash
# Backend setup
python -m venv venv
venv\Scripts\activate          # Windows

pip install -r requirements.txt
winget install --id Gyan.FFmpeg   # ffmpeg (MUST)

# .env file তৈরি করো (gitignored):
GROQ_API_KEY=gsk_...
GOOGLE_API_KEY=AIza...
FIREBASE_API_KEY=...
FIREBASE_PROJECT_ID=...

# Backend run
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend setup (Phase 4)
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install -D tailwindcss postcss autoprefixer
npm install leaflet react-leaflet axios firebase
npm run dev
```

---

## 11. KEY DESIGN DECISIONS

| Decision | কেন |
|----------|-----|
| Groq Whisper API (not local) | Local Whisper Large-v3 এ GPU দরকার — Groq free + fast |
| Gemini Flash (not GPT-4) | Gemini free tier 1M tokens/day — GPT-4 paid |
| HuggingFace embeddings (not OpenAI) | Free, local, multilingual — OpenAI paid |
| ChromaDB (not Pinecone) | Local folder — Pinecone server দরকার |
| React PWA (not native app) | Browser এ চলে — Play Store upload লাগে না |
| 64 UNO locations (not 495) | 64 district HQ দিয়ে শুরু — 495 later |
| fpdf2 (not ReportLab) | Simple API, Bangla font support — ReportLab complex |
| fpdf2 + **uharfbuzz** text shaping | বাংলা যুক্তাক্ষর সঠিক render করতে HarfBuzz দরকার; ছাড়া text অগোছালো হয় |
| List items = single multi_cell (`\n`) | fpdf2 bug: পরপর multi_cell + shaping এ glyph হারায় — এক multi_cell এ join করে এড়ানো |
| PDF = clean letter only | কোনো banner/disclaimer/submission text PDF এ নয় (authentic থাকে); ওগুলো screen এ (Phase 4) |
| Reporter mode → advice/PDF | self / third-party / anonymous — auto-detected, কোনো বাড়তি প্রশ্ন নেই |

---

## 12. CURRENT STATUS

### Overall Progress

| Phase | Status | Week | Done | Pending |
|-------|--------|------|------|---------|
| **Phase 1** — Dataset & EDA | ✅ **Done** | Week 1–2 | Steps 1, 2, 3, 4 | — |
| **Phase 2** — Backend + Whisper | ✅ **Done** | Week 2–3 | Steps 5–10 | — |
| **Phase 3** — RAG + PDF | 🔄 In Progress | Week 4–5 | Steps 11, 12, 13 | Steps 14–16 |
| **Phase 4** — Frontend + Map | ⬜ Pending | Week 6–7 | — | Steps 17–22 |
| **Phase 5** — Test + Deploy | ⬜ Pending | Week 8 | — | Steps 23–24 |

---

### Phase 1 — Detailed Tracking

| Item | Status | Notes |
|------|--------|-------|
| `data/` folder | ✅ Done | Created |
| `notebooks/` folder | ✅ Done | Created |
| `backend/phase1_outputs/` folder | ✅ Done | Created |
| `Elder_abuse_Dataset.csv` | ✅ Done | 199 rows, 12 columns |
| `notebooks/01_eda.ipynb` | ✅ Done | 21 cells, run complete |
| Column normalization (Category, Relation) | ✅ Done | In notebook Cell 6 |
| Severity Score column | ✅ Done | In notebook Cell 6 |
| Trust Blind Spot column | ✅ Done | In notebook Cell 6 |
| 11 EDA charts | ✅ Done | Saved in `data/` folder |
| `.gitignore` | ✅ Done | data CSV + venv excluded |
| **Step 1 — Dataset Load + EDA** | ✅ **DONE** | Confirmed by Lamia |
| `data/cleaned_dataset.csv` | ✅ Done | 199 rows, 20 cols, 86.1 KB |
| `data/train_split.csv` | ✅ Done | 159 rows, 20 cols |
| `data/test_split.csv` | ✅ Done | 40 rows, 20 cols |
| **Step 2 — Cleaning + Train/Test Split** | ✅ **DONE** | Confirmed by Lamia |
| `backend/phase1_outputs/keyword_dictionary.json` | ✅ Done | 6 categories, 231 keywords, 6.4 KB |
| **Step 3 — keyword_dictionary.json** | ✅ **DONE** | Confirmed by Lamia |
| `backend/phase1_outputs/act_knowledge_base.json` | ✅ Done | 16 sections (9 PMA + 7 BPC), 14.7 KB |
| **Step 4 — act_knowledge_base.json** | ✅ **DONE** | Confirmed by Lamia |
| **PHASE 1 — Dataset & EDA** | 🎉 **COMPLETE** | All 4 steps done |

---

### Phase 2 — Detailed Tracking

| Item | Status | Notes |
|------|--------|-------|
| `backend/app/` folder structure | ✅ Done | Created with __init__.py |
| `requirements.txt` | ✅ Done | 14 packages + audioop-lts for Python 3.14 |
| `.env` file | ✅ Done | GROQ_API_KEY configured |
| `venv/` virtual environment | ✅ Done | All packages installed & verified |
| **Step 5 — Backend Setup** | ✅ **DONE** | Confirmed by Lamia |
| `preprocessor.py` | ✅ Done | 8/8 tests passed, ffmpeg + pydub working |
| `tests/test_preprocessor.py` | ✅ Done | 8 test cases for format conversion |
| **Step 6 — Audio Preprocessor** | ✅ **DONE** | Confirmed by Lamia |
| `whisper_service.py` (Groq API) | ✅ Done | 12/12 tests passed inc. real API call |
| `tests/test_whisper_service.py` | ✅ Done | Language detection + mock + real API |
| **Step 7 — Whisper Service (Groq)** | ✅ **DONE** | Confirmed by Lamia |
| `keyword_classifier.py` | ✅ Done | 29/29 tests passed, multilingual + entity extract |
| `tests/test_keyword_classifier.py` | ✅ Done | Category, legal, entity, edge cases |
| **Step 8 — Keyword Classifier** | ✅ **DONE** | Confirmed by Lamia |
| `main.py` (FastAPI) | ✅ Done | 3 endpoints + CORS + lifespan, 15/15 tests passed |
| `tests/test_main.py` | ✅ Done | Health, /transcribe, /transcribe/text + CORS |
| Browser test (Swagger /docs) | ✅ Done | Confirmed by Lamia (financial detected from text) |
| **Step 9 — FastAPI Server** | ✅ **DONE** | Confirmed by Lamia |
| End-to-end test — English audio | ✅ Done | 100% accurate, abandonment detected |
| End-to-end test — Bangla audio | ✅ Done | Pipeline OK; Whisper typos → Phase 3 RAG |
| End-to-end test — Mixed audio | ✅ Done | Pipeline OK; Whisper mangles EN words → Phase 3 |
| Entity false-positive bug fix | ✅ Done | Token-based Bangla matching, 34 classifier tests |
| **Step 10 — Phase 2 E2E Test** | ✅ **DONE** | Confirmed by Lamia — 66 tests passing |
| **PHASE 2 — Backend + Whisper** | 🎉 **COMPLETE** | All 6 steps done |

---

### Phase 3 — Detailed Tracking

| Item | Status | Notes |
|------|--------|-------|
| `vector_store.py` (ChromaDB) | ✅ Done | Built & tested; kept as thesis comparison (not in main pipeline) |
| Embedding model evaluation | ✅ Done | MiniLM 2/5, e5-base 4/5 — both fail Whisper typo case |
| RAG retrieval (Option C) | ✅ Done | keyword/category retrieval in rag_engine.py |
| `rag_engine.py` (Gemini 2.5 Flash) | ✅ Done | 18/18 tests; real typo complaint → correct classification |
| **Step 11+12 — RAG Engine** | ✅ **DONE** | Confirmed by Lamia (Whisper typo now classified correctly) |
| `entity_extractor.py` | ✅ Done | Gemini extraction; null for unknown (no hallucination) |
| Reporter mode (self / third-party) | ✅ Done | Neighbor reports → reporter-aware advice; anonymous-ready |
| `tests/test_entity_extractor.py` | ✅ Done | 16 tests inc. neighbor-unknown-victim case |
| **Step 13 — Entity Extractor** | ✅ **DONE** | Confirmed by Lamia (34 tests pass) |
| Bengali PDF rendering fix | ✅ Done | uharfbuzz + `set_text_shaping(True)` → correct যুক্তাক্ষর; verified by reading PDF |
| Bengali font setup | ✅ Done | backend/fonts/ — NotoSansBengali Regular+Bold + NotoSans (Latin fallback) |
| Complaint PDF format (দরখাস্ত) | ✅ Validated | Sample reviewed by Lamia; clean letter, no banner/submission text inside PDF |
| `pdf_generator.py` (the real generator) | ⏭️ **NEXT** | Step 14 — build from validated format |
| Phase 3 endpoints in `main.py` | ⬜ Pending | Step 15 |
| RAG accuracy test | ⬜ Pending | Step 16 |

---

### Phase 4 — Detailed Tracking

| Item | Status | Notes |
|------|--------|-------|
| `geospatial/uno_locations.json` | ⬜ Pending | Step 17 |
| React app (Vite) | ⬜ Pending | Step 18 |
| `VoiceRecorder.jsx` | ⬜ Pending | Step 18 |
| `MapView.jsx` (Leaflet.js) | ⬜ Pending | Step 19 |
| `EmergencyButtons.jsx` | ⬜ Pending | Step 20 |
| `PDFDownload` component | ⬜ Pending | Step 20 |
| Firebase Firestore setup | ⬜ Pending | Step 21 |
| Vercel + Render deploy | ⬜ Pending | Step 22 |

---

### Phase 5 — Detailed Tracking

| Item | Status | Notes |
|------|--------|-------|
| End-to-end test (3 cases) | ⬜ Pending | Step 23 |
| Bug fix | ⬜ Pending | Step 23 |
| Thesis (Blackbook) | ⬜ Pending | Step 24 |
| Demo video | ⬜ Pending | Step 24 |
| Presentation slides | ⬜ Pending | Step 24 |

---

> **Rule:** প্রতিটা Step শেষ হলে Lamia confirm করবে → তারপর পরের Step শুরু হবে।
> **Next:** Step 14 — `pdf_generator.py` (validated দরখাস্ত format এ real generator;
> self / third-party / anonymous handle করবে; RAG + entity data থেকে auto-fill)।
>
> **Note (Anonymous reporting):** backend ইতিমধ্যে নাম ছাড়া complaint handle করে
> (Step 13)। User-facing "anonymous" toggle + privacy storage Phase 4 এ যোগ হবে।
>
> **Note (Frontend user flow — Phase 4, deferred):** voice record → "শেষ?" confirm
> popup → transcript দেখানো + edit (এক screen এ "নাম গোপন রাখুন" checkbox সহ) →
> clean PDF download/print → screen এ submission guidance + নিকটস্থ UNO/থানা map।
> এই UI/UX এখন design হবে না — Phase 4 এ backend-এর সাথে align করে করা হবে।

---

## 13. LEGAL FRAMEWORK REFERENCE

### Parents' Maintenance Act 2013

| Section | বিষয় |
|---------|------|
| §3 | সন্তানের ভরণপোষণের বাধ্যবাধকতা |
| §4 | চিকিৎসা অবহেলা ও পরিত্যাগ নিষিদ্ধ |
| §5 | UNO অফিসে অভিযোগ দাখিলের পদ্ধতি |
| §6 | UNO-এর ক্ষমতা (শুনানি ও আদেশ) |
| §7 | শাস্তি: অনূর্ধ্ব ১,০০,০০০ টাকা জরিমানা, অনাদায়ে অনূর্ধ্ব ৩ মাস কারাদণ্ড |
| §8 | জরুরি সহায়তার বিধান |

### Bangladesh Penal Code

| Section | বিষয় |
|---------|------|
| §302 | হত্যার শাস্তি |
| §323 | স্বেচ্ছায় আঘাত |
| §406 | বিশ্বাস ভঙ্গ |
| §420 | প্রতারণা ও সম্পত্তি আত্মসাৎ |
| §506 | ভয় দেখানো |

### Emergency Contacts

| Service | Number |
|---------|--------|
| জাতীয় জরুরি সেবা | 999 |
| বিনামূল্যে আইনি সহায়তা (NLASO) | 16430 |
| মহিলা হেল্পলাইন | 10921 |

---

## 14. FUTURE WORK (এই thesis এ নেই — পরে করা যাবে)

> এগুলো over-engineered বা time-consuming — 2 মাসের thesis এ দরকার নেই।
> পরে research paper বা Version 2 তে add করা যাবে।

```
1. AES-256 encryption for audio/PDF files
2. Service Worker — full offline mode
3. QR Code in PDF
4. 495 UNO GPS entries (এখন 64 district HQ দিয়ে শুরু)
5. Admin pattern dashboard (case trends, district map)
6. SMS notification to UNO office
7. Case history tracking + case status
8. Dialect-specific fine-tuning (Sylheti, Chittagong)
9. Multi-abuse detection (one complaint → multiple categories simultaneously)
10. Photo/document evidence upload
11. Anonymous reporting with case reference number
12. Community Reporter Mode (NGO worker reports on behalf of elder)
```

---

## 15. NOTES FOR PHASE-END UPDATE

এই ফাইলটি প্রতিটি phase শেষে update করো:
- Phase 1 শেষে: Current Status ✅ + EDA findings যোগ করো
- Phase 2 শেষে: WER result + API response time যোগ করো
- Phase 3 শেষে: RAG accuracy (8/10 বা কত?) যোগ করো
- Phase 4 শেষে: Deploy URL যোগ করো
- Phase 5 শেষে: Final metrics + thesis link যোগ করো

---

*Last Updated: 29 May 2026 — Simplified for 2-month timeline*
