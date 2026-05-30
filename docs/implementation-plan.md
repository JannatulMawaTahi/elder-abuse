# Elder Abuse AI — Complete Implementation Plan
### (সহজ ভাষায় ব্যাখ্যা + সম্পূর্ণ গাইড)

> **For:** Lamia Islam Mim & Team — CSE 499A, NSU Spring 2026
> **Written by:** Claude (AI Assistant) — 28 May 2026

---

## PART 1: আমি প্রজেক্টটা কীভাবে বুঝেছি

### ১.১ সহজ ভাষায় — উদাহরণ দিয়ে

**Scenario কল্পনা করো:**

> রাবেয়া বেগম, বয়স ৭৫। ময়মনসিংহের একটি গ্রামে থাকেন।
> তার ছেলে সম্পত্তি লিখে না দেওয়ায় তাকে বাড়ি থেকে বের করে দিয়েছে।
> তিনি পড়তে পারেন না, স্মার্টফোন ব্যবহার জানেন না।
> তার প্রতিবেশীর কাছে একটি Android ফোন আছে।

**তোমার সিস্টেম কী করবে:**

```
Step 1: প্রতিবেশী ফোনে অ্যাপ খুলবে
        → বড় লাল button: "কথা বলুন" (Bangla UI)

Step 2: রাবেয়া বেগম কথা বলবেন:
        "আমার ছেলে আমাকে বাড়ি থেকে বের করে দিয়েছে,
         আমার জমি লিখে দেওয়ার জন্য মারধর করেছে"

Step 3: Whisper AI শুনে text বানাবে (Speech → Text)
        Output: "আমার ছেলে আমাকে বাড়ি থেকে বের করে দিয়েছে..."

Step 4: AI বুঝবে এটা কোন ধরনের নির্যাতন:
        Category: "Mixed - Financial & Physical"
        Severity: 4/5
        Legal: PMA 2013 Section 3 & 4, BPC §323

Step 5: AI legal advice দেবে (Bangla তে):
        "আপনার ছেলের বিরুদ্ধে UNO অফিসে অভিযোগ করুন।
         PMA 2013 Section 5 অনুযায়ী..."

Step 6: PDF তৈরি হবে — অভিযোগপত্র
        রাবেয়া বেগমের নাম, ঘটনা, আইনি ধারা, দাবি সহ

Step 7: Map দেখাবে:
        "আপনার নিকটতম UNO অফিস: ময়মনসিংহ সদর UNO — ৩.২ কিমি দূরে"
        Phone: 091-XXXXXX, Address: ...
```

**সহজ কথায়:** তোমার সিস্টেম একটা **"Digital Voice Lawyer"** — যে শুনতে পায়, বোঝে, এবং সঠিক কাগজ বানিয়ে দেয়।

---

### ১.২ সিস্টেমের ৫টি কাজ

| কাজ | কী হয় | Example |
|-----|--------|---------|
| **শোনা** | Voice → Bangla Text | "ছেলে মারধর করেছে" → text |
| **বোঝা** | Text → Abuse Category | "Physical Abuse, Severity 4" |
| **পরামর্শ** | Category → Legal Advice | "Section 3 PMA 2013 apply হবে" |
| **কাগজ** | Info → PDF Complaint | অভিযোগপত্র download |
| **পথ দেখানো** | GPS → Nearest UNO | "৩ কিমি দূরে UNO অফিস" |

---

### ১.৩ তোমার Dataset সম্পর্কে আমি কী বুঝেছি

তোমাদের ১৯৯টি real case আছে:

```
Secondary (News):      খবরের কাগজ থেকে (jugantor, prothomalo, etc.)
Secondary (Interview): TV channel interview থেকে (ATN, Channel I, etc.)
Primary (Interview):   তোমরা নিজেরা field এ গিয়ে interview করেছ
                       (Narayanganj, Comilla, Dhaka, Pabna... March-April 2026)
```

**Dataset এর গুরুত্বপূর্ণ pattern:**
- সবচেয়ে বেশি নির্যাতন করে: **ছেলে (Son)** — ২১.৫%
- পরিবারের মোট: **৪১.৮%** — এটাই "Trust Blind Spot"
- সবচেয়ে বেশি ধরন: **Abandonment** (পরিত্যাগ) — ২৪.১%
- Peak vulnerable age: **৭০ বছর**
- বেশিরভাগ victim: **মহিলা** (বিশেষত বিধবা)

---

## PART 2: সম্পূর্ণ System Architecture

### ২.১ সহজ Architecture (যেটা তোমাদের জন্য সঠিক)

```
┌─────────────────────────────────────────────────────┐
│                   USER (Smartphone)                  │
│           React Web App (Mobile Browser)             │
└─────────────────┬───────────────────────────────────┘
                  │ HTTP/HTTPS (JSON)
                  │
┌─────────────────▼───────────────────────────────────┐
│              FastAPI Backend Server                  │
│                                                      │
│  ┌─────────────┐  ┌──────────┐  ┌───────────────┐  │
│  │   Whisper   │  │  RAG     │  │  PDF Generator│  │
│  │ (Speech→Text│  │ (Legal   │  │  (Complaint   │  │
│  │  Service)   │  │  Triage) │  │   Draft)      │  │
│  └─────────────┘  └──────────┘  └───────────────┘  │
└─────────────────┬───────────────────────────────────┘
                  │
        ┌─────────┴──────────┐
        │                    │
┌───────▼──────┐    ┌────────▼──────┐
│  ChromaDB    │    │    Firebase   │
│ (Legal Laws  │    │  (Case Store  │
│  Vectors)    │    │   + Audio)    │
└──────────────┘    └───────────────┘
```

**কেন এই Architecture?**
- **Monolithic FastAPI** — Simple, easy to maintain, thesis এর জন্য perfect
- **না করার কারণ Microservices** — অনেক complex, thesis এ এত দরকার নেই
- **React Web App** — Phone এ browser থেকে কাজ করবে, আলাদা app install লাগবে না
- **Firebase** — Free tier আছে, offline support আছে

---

### ২.২ Data Flow (একটা request কীভাবে যায়)

```
1. User ফোনে "Record" button চাপে
   ↓
2. Browser MediaRecorder API → Audio file (WebM format)
   ↓
3. React → POST /transcribe → FastAPI
   ↓
4. FastAPI: Audio → preprocessor.py
   - ffmpeg দিয়ে WebM → WAV (16kHz, mono)
   - Noise remove
   - Volume normalize
   ↓
5. FastAPI: WAV → whisper_service.py
   - Whisper model run হয়
   - Bangla text বের হয়
   ↓
6. FastAPI: Text → keyword_classifier.py (fast, offline)
   - Initial category detect
   ↓
7. FastAPI: Text → rag_engine.py (smart, legal)
   - ChromaDB থেকে relevant law sections আনে
   - GPT-4o-mini / Gemini → legal reasoning
   ↓
8. FastAPI: Info → entity_extractor.py
   - Name, Age, Location, Abuser extract
   ↓
9. FastAPI: All info → pdf_generator.py
   - PDF complaint বানায়
   ↓
10. FastAPI: Response JSON → React
    - Transcript, Category, Legal Advice, PDF link
    ↓
11. React: Map দেখায় (Leaflet.js)
    - User GPS → Haversine → Nearest UNO
```

---

## PART 3: Technology Stack — কোনটা কেন?

### ৩.১ Backend Technologies

| Technology | কেন ব্যবহার | Free? | Alternative |
|-----------|-----------|-------|-------------|
| **FastAPI (Python)** | Fast, automatic API docs, easy | ✅ Free | Flask (older, slower) |
| **uvicorn** | FastAPI চালানোর server | ✅ Free | gunicorn |
| **pydantic** | Data validation (FastAPI এর সাথে) | ✅ Free | - |
| **python-multipart** | File upload handle | ✅ Free | - |

### ৩.২ Audio Processing

| Technology | কেন ব্যবহার | Free? |
|-----------|-----------|-------|
| **ffmpeg** | যেকোনো audio format → WAV | ✅ Free |
| **pydub** | Python দিয়ে ffmpeg control | ✅ Free |
| **librosa** | Audio analysis (RMS, noise gate) | ✅ Free |
| **soundfile** | WAV file read/write | ✅ Free |

### ৩.৩ AI/ML Technologies

| Technology | কেন ব্যবহার | Free? | Note |
|-----------|-----------|-------|------|
| **openai-whisper** | Speech → Bangla text (local) | ✅ Free | RAM দরকার |
| **OR Groq Whisper API** | Speech → Text (cloud, fast) | ✅ Free tier | Recommended |
| **LangChain** | RAG pipeline framework | ✅ Free | |
| **ChromaDB** | Vector database (local) | ✅ Free | |
| **sentence-transformers** | Text embedding (local) | ✅ Free | |
| **GPT-4o-mini** | Legal reasoning | 💲 Cheap | $0.15/1M tokens |
| **OR Groq Llama** | Legal reasoning | ✅ Free | Speed কম |
| **OR Gemini Flash** | Legal reasoning | ✅ Free tier | Good option |

### ৩.৪ Frontend Technologies

| Technology | কেন ব্যবহার | Free? |
|-----------|-----------|-------|
| **React + Vite** | Fast UI development | ✅ Free |
| **Tailwind CSS** | Senior-friendly UI styling | ✅ Free |
| **Leaflet.js** | Interactive map (UNO location) | ✅ Free |
| **axios** | API calls to backend | ✅ Free |
| **react-leaflet** | React wrapper for Leaflet | ✅ Free |

### ৩.৫ Storage & Database

| Technology | কেন ব্যবহার | Free? |
|-----------|-----------|-------|
| **Firebase Firestore** | Case data store (offline-first) | ✅ Free tier | Spark plan: 1GB |
| **Firebase Storage** | Audio + PDF store | ✅ Free tier | 5GB |
| **ChromaDB** | Legal vectors (local folder) | ✅ Free | |

### ৩.৬ PDF Generation

| Technology | কেন ব্যবহার | Free? |
|-----------|-----------|-------|
| **fpdf2** | Simple PDF, Bangla font support | ✅ Free |
| **OR ReportLab** | Complex PDF, better formatting | ✅ Free |

---

## PART 4: Voice/Speech Model — কোনটা ব্যবহার করবে?

### ৪.১ Model Comparison

| Model | Bangla Accuracy | Speed | RAM | Cost | Recommendation |
|-------|----------------|-------|-----|------|----------------|
| **Whisper Large-v3** (local) | ⭐⭐⭐⭐⭐ Best | Slow | ~10GB | Free | Ideal for final product |
| **Whisper Medium** (local) | ⭐⭐⭐⭐ Good | Medium | ~5GB | Free | Dev এ use করো |
| **Whisper Base** (local) | ⭐⭐⭐ OK | Fast | ~1GB | Free | Testing এ |
| **Groq Whisper API** | ⭐⭐⭐⭐⭐ Best | ⚡ Very Fast | 0 (cloud) | Free tier | **Recommended** |
| **OpenAI Whisper API** | ⭐⭐⭐⭐⭐ Best | Fast | 0 (cloud) | $0.006/min | Cheap option |
| **Google Speech-to-Text** | ⭐⭐⭐ OK | Fast | 0 (cloud) | $0.016/15s | Bangla দুর্বল |
| **Azure Speech** | ⭐⭐⭐ OK | Fast | 0 (cloud) | Paid | Bangla দুর্বল |

### ৪.২ Recommendation: Groq Whisper API ব্যবহার করো

**কেন Groq?**
```
✅ সম্পূর্ণ FREE (free tier: 28,800 audio seconds/day)
✅ Whisper Large-v3 এর মতোই accurate
✅ Local GPU/RAM লাগবে না
✅ Response time: 2-3 seconds (local Whisper এর চেয়ে ৫x দ্রুত)
✅ API একদম simple
```

**Groq Whisper API code:**
```python
from groq import Groq

client = Groq(api_key="your_groq_api_key")

def transcribe_with_groq(audio_file_path: str, language: str = "bn") -> dict:
    with open(audio_file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3-turbo",  # free, fast, accurate
            language=language,               # "bn" for Bangla
            response_format="verbose_json",  # segments সহ
        )
    return {
        "text": transcription.text,
        "segments": transcription.segments,
        "language": transcription.language,
    }
```

**Groq API key পাওয়ার উপায়:**
1. https://console.groq.com এ যাও
2. Sign up (Google দিয়ে)
3. API Keys → Create API Key
4. `.env` তে রাখো: `GROQ_API_KEY=gsk_...`

---

## PART 5: Free API Options (সম্পূর্ণ বিনামূল্যে)

### ৫.১ সম্পূর্ণ Free Stack

```
Speech to Text:  Groq Whisper API     → FREE (28,800 sec/day)
LLM (Legal AI):  Google Gemini Flash  → FREE (15 RPM, 1M tokens/day)
Embedding:       HuggingFace local    → FREE (no API needed)
Vector DB:       ChromaDB local       → FREE
Maps:            Leaflet + OpenStreetMap → FREE
PDF:             fpdf2 (Python)       → FREE
Backend:         FastAPI              → FREE
Frontend:        React + Vite         → FREE
Database:        Firebase Free Tier   → FREE (1GB Firestore, 5GB Storage)
```

**তোমাদের project এর জন্য total monthly cost: $0.00** ✅

### ৫.২ Google Gemini Flash (Free LLM)

**কেন Gemini Flash?**
```
✅ Free tier: 15 requests/minute, 1 million tokens/day
✅ Bangla ভালো বোঝে
✅ Context window: 1M tokens (বিশাল, legal docs এর জন্য perfect)
✅ Fast response
```

**কীভাবে পাবে:**
1. https://aistudio.google.com এ যাও
2. Sign in with Google
3. "Get API Key" → Create API Key
4. `.env` তে: `GOOGLE_API_KEY=AIza...`

**Code:**
```python
import google.generativeai as genai

genai.configure(api_key="your_google_api_key")
model = genai.GenerativeModel("gemini-1.5-flash")

response = model.generate_content(
    f"""তুমি একজন বাংলাদেশী আইনি সহায়তা AI।
    শুধুমাত্র Parents' Maintenance Act 2013 এর উপর ভিত্তি করে উত্তর দাও।
    
    Context (Legal Sections): {retrieved_sections}
    
    User Query: {transcript}
    
    JSON format এ উত্তর দাও:
    {{
      "abuse_category": "...",
      "applicable_sections": [...],
      "recommended_action_bangla": "...",
      "civil_or_criminal": "..."
    }}"""
)
```

### ৫.৩ HuggingFace Sentence Transformers (Free Embedding)

```python
# No API key needed, runs locally
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
# এই model বাংলা সহ ৫০+ ভাষা বোঝে

embedding = model.encode("ছেলে মারধর করেছে")  # → 384-dim vector
```

### ৫.৪ OpenAI (If needed — Cheap, not free)

```
GPT-4o-mini:
- Input:  $0.15 per 1M tokens
- Output: $0.60 per 1M tokens
- 1 user request ≈ 500 tokens ≈ $0.0001 (মাত্র ০.০১ পয়সা!)
- Monthly 1000 requests ≈ $0.10 (মাত্র ১১ টাকা!)
```

**OpenAI API key:**
1. https://platform.openai.com এ যাও
2. Sign up → API Keys → Create
3. `.env` তে: `OPENAI_API_KEY=sk-...`

---

## PART 6: Phase-by-Phase সম্পূর্ণ Implementation Guide

### Phase 1: Dataset Preparation

**কী করতে হবে:**
```
1. Raw CSV load করো (data/Elder_abuse_Dataset.csv)
2. ১২টি raw column → ১৯টি clean column বানাও
3. Abuse category normalize করো (typo fix, standard name)
4. Severity score যোগ করো (1-5)
5. Trust Blind Spot flag যোগ করো
6. Age string → integer parse
7. Date string → datetime parse
8. Train/test split করো (80/20, stratified, seed=42)
9. keyword_dictionary.json তৈরি করো
10. act_knowledge_base.json তৈরি করো (PMA 2013 full text)
```

**Common Errors & Solutions:**
```python
# Error 1: Date parse failed (inconsistent format)
# Solution:
import pandas as pd
df['Date_Parsed'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)

# Error 2: Age "Unknown" → NaN
# Solution:
df['Age_Numeric'] = pd.to_numeric(df['Age'], errors='coerce')

# Error 3: Category name with trailing space
# Solution:
df['Abuse Category'] = df['Abuse Category'].str.strip()
```

---

### Phase 2: Backend Setup

**Step-by-step:**

```bash
# 1. Project folder structure তৈরি করো
mkdir -p elder-abuse-ai/backend/app
mkdir -p elder-abuse-ai/backend/phase1_outputs
mkdir -p elder-abuse-ai/backend/tests

# 2. Virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# 3. Requirements install
pip install fastapi uvicorn python-multipart
pip install openai-whisper librosa soundfile pydub  # or groq
pip install groq  # Groq Whisper API (recommended)
pip install pytest httpx

# 4. ffmpeg install (MUST)
winget install ffmpeg  # Windows
# ffmpeg PATH এ add হয়েছে verify করো:
ffmpeg -version
```

**Common Errors:**
```
Error: "ffmpeg not found"
Solution: winget install ffmpeg
          তারপর new terminal open করো (PATH refresh)

Error: "torch not found" (Whisper local এর জন্য)
Solution: pip install torch --index-url https://download.pytorch.org/whl/cpu

Error: CORS error (frontend থেকে backend call করলে)
Solution: main.py তে CORSMiddleware যোগ করো
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
```

---

### Phase 3: RAG Engine Setup

**ChromaDB + LangChain:**

```python
# Step 1: act_knowledge_base.json → vector store বানাও
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
import json

# Legal knowledge load
with open("data/act_knowledge_base.json") as f:
    knowledge_base = json.load(f)

# Text chunks তৈরি
documents = []
for section_id, section_data in knowledge_base.items():
    documents.append({
        "text": section_data["text"],
        "metadata": {"section": section_data["section"], "id": section_id}
    })

# Embedding model (FREE - local)
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# Vector store তৈরি
vectorstore = Chroma.from_texts(
    texts=[d["text"] for d in documents],
    metadatas=[d["metadata"] for d in documents],
    embedding=embeddings,
    persist_directory="backend/vector_store"
)
vectorstore.persist()
print("Vector store built successfully!")
```

**RAG Query:**
```python
def get_legal_advice(transcript: str, category: str) -> dict:
    # 1. Similar sections খোঁজো
    results = vectorstore.similarity_search(
        query=f"{category}: {transcript}",
        k=3  # top 3 most relevant sections
    )

    # 2. Context বানাও
    context = "\n\n".join([r.page_content for r in results])

    # 3. Gemini Flash দিয়ে advice নাও (FREE)
    prompt = f"""
    তুমি একজন বাংলাদেশী আইনি সহায়তা AI।
    নিচের legal sections এর উপর ভিত্তি করে শুধুমাত্র উত্তর দাও।
    কোনো অনুমান করবে না।

    Legal Context:
    {context}

    ঘটনা (Transcript): {transcript}
    প্রাথমিক category: {category}

    JSON format এ উত্তর দাও:
    {{
      "abuse_type": "...",
      "applicable_sections": ["sec3", "sec4"],
      "legal_advice_bangla": "...",
      "recommended_action_bangla": "...",
      "civil_or_criminal": "Civil/Criminal",
      "urgency": 1-5
    }}
    """

    response = gemini_model.generate_content(prompt)
    return json.loads(response.text)
```

**Common Errors:**
```
Error: ChromaDB "Collection already exists"
Solution: if os.path.exists("backend/vector_store"):
              vectorstore = Chroma(persist_directory=..., embedding_function=...)
          else:
              vectorstore = Chroma.from_texts(...)

Error: HuggingFace model download slow
Solution: প্রথমবার download হয়, পরে cache থেকে load হবে
          Usually ~/.cache/huggingface/ তে save হয়

Error: JSON parse error from Gemini
Solution: response.text থেকে JSON extract করো:
          import re
          json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
          if json_match: return json.loads(json_match.group())
```

---

### Phase 4: PDF Generation (Bangla Support)

**fpdf2 দিয়ে Bangla PDF:**

```python
from fpdf import FPDF
import os

class LegalComplaintPDF(FPDF):
    def __init__(self):
        super().__init__()
        # Bangla font add করতে হবে
        # Download: https://fonts.google.com/noto/specimen/Noto+Sans+Bengali
        self.add_font("NotoSansBengali", "", "fonts/NotoSansBengali-Regular.ttf")
        self.add_font("NotoSansBengali", "B", "fonts/NotoSansBengali-Bold.ttf")

    def header(self):
        self.set_font("NotoSansBengali", "B", 14)
        self.cell(0, 10, "গণপ্রজাতন্ত্রী বাংলাদেশ সরকার", align="C", ln=True)
        self.cell(0, 8, "উপজেলা নির্বাহী অফিসার বরাবর", align="C", ln=True)
        self.cell(0, 8, "অভিযোগপত্র", align="C", ln=True)
        self.ln(5)

def generate_complaint_pdf(case_data: dict) -> bytes:
    pdf = LegalComplaintPDF()
    pdf.add_page()

    # Victim info
    pdf.set_font("NotoSansBengali", "B", 11)
    pdf.cell(0, 8, "অভিযোগকারীর তথ্য:", ln=True)
    pdf.set_font("NotoSansBengali", "", 10)
    pdf.cell(0, 7, f"নাম: {case_data.get('victim_name', 'অজ্ঞাত')}", ln=True)
    pdf.cell(0, 7, f"বয়স: {case_data.get('victim_age', 'অজ্ঞাত')}", ln=True)
    pdf.cell(0, 7, f"ঠিকানা: {case_data.get('location', 'অজ্ঞাত')}", ln=True)
    pdf.ln(3)

    # Incident
    pdf.set_font("NotoSansBengali", "B", 11)
    pdf.cell(0, 8, "ঘটনার বিবরণ:", ln=True)
    pdf.set_font("NotoSansBengali", "", 10)
    pdf.multi_cell(0, 7, case_data.get('transcript', ''))
    pdf.ln(3)

    # Legal sections
    pdf.set_font("NotoSansBengali", "B", 11)
    pdf.cell(0, 8, "প্রযোজ্য আইনি ধারাসমূহ:", ln=True)
    pdf.set_font("NotoSansBengali", "", 10)
    for section in case_data.get('applicable_sections', []):
        pdf.cell(0, 7, f"• {section}", ln=True)
    pdf.ln(3)

    # Recommendation
    pdf.set_font("NotoSansBengali", "B", 11)
    pdf.cell(0, 8, "সুপারিশকৃত পদক্ষেপ:", ln=True)
    pdf.set_font("NotoSansBengali", "", 10)
    pdf.multi_cell(0, 7, case_data.get('recommended_action', ''))

    # Signature area
    pdf.ln(15)
    pdf.cell(60, 7, "অভিযোগকারীর স্বাক্ষর", border="T")
    pdf.cell(60, 7, "তারিখ", border="T")

    return bytes(pdf.output())
```

**Font download করতে হবে:**
```
1. https://fonts.google.com/noto/specimen/Noto+Sans+Bengali এ যাও
2. "Download family" click করো
3. NotoSansBengali-Regular.ttf এবং NotoSansBengali-Bold.ttf
4. backend/fonts/ folder এ রাখো
```

---

### Phase 4: Frontend (React)

**Voice Recorder Component:**
```jsx
import { useState, useRef } from 'react';

export default function VoiceRecorder({ onRecordingComplete }) {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorderRef.current = new MediaRecorder(stream);

    mediaRecorderRef.current.ondataavailable = (e) => {
      chunksRef.current.push(e.data);
    };

    mediaRecorderRef.current.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
      onRecordingComplete(blob);
      chunksRef.current = [];
    };

    mediaRecorderRef.current.start();
    setIsRecording(true);
  };

  const stopRecording = () => {
    mediaRecorderRef.current.stop();
    setIsRecording(false);
  };

  return (
    <div className="flex flex-col items-center gap-4">
      <button
        onClick={isRecording ? stopRecording : startRecording}
        className={`w-32 h-32 rounded-full text-white text-xl font-bold
          ${isRecording ? 'bg-gray-500 animate-pulse' : 'bg-red-600 hover:bg-red-700'}`}
      >
        {isRecording ? 'থামুন ⏹' : 'কথা বলুন 🎤'}
      </button>
      {isRecording && (
        <p className="text-red-600 font-bold text-lg">● রেকর্ডিং চলছে...</p>
      )}
    </div>
  );
}
```

**Map Component (Leaflet.js):**
```jsx
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

export default function UNOMap({ userLocation, nearestUNOs }) {
  return (
    <MapContainer
      center={[userLocation.lat, userLocation.lon]}
      zoom={12}
      style={{ height: '400px', width: '100%' }}
    >
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

      {/* User location */}
      <Marker position={[userLocation.lat, userLocation.lon]}>
        <Popup>আপনি এখানে আছেন</Popup>
      </Marker>

      {/* Nearest UNOs */}
      {nearestUNOs.map((uno) => (
        <Marker key={uno.id} position={[uno.lat, uno.lon]}>
          <Popup>
            <b>{uno.upazila} UNO অফিস</b><br/>
            {uno.district}<br/>
            📞 {uno.phone}<br/>
            📍 {uno.address}<br/>
            🚶 {uno.distance_km.toFixed(1)} কিমি দূরে
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
```

---

## PART 7: PDF তৈরির পর User কী করবে?

### ৭.১ PDF এর ব্যবহার — বাংলাদেশ Context

PDF তৈরি হলে user ৪টি কাজ করতে পারবে:

```
Option 1: Print করে UNO অফিসে জমা দেওয়া
          ↓
          UNO (Upazila Nirbahi Officer) শুনানি করবে
          PMA 2013 Section 6 অনুযায়ী আদেশ দেবে
          Punishment: ১ মাস jail বা ৫,০০০ টাকা fine

Option 2: Police Station এ FIR করা
          ↓
          Physical abuse, Murder → Criminal case
          BPC §302/§323 apply হবে

Option 3: NLASO (বিনামূল্যে আইনজীবী) তে পাঠানো
          ↓
          National Legal Aid Services Organization
          Free legal representation পাওয়া যাবে
          Hotline: 16430

Option 4: NGO তে পাঠানো
          ↓
          BLAST, ASK, Naripokkho
          Free legal aid + social support
```

### ৭.২ PDF System এ "Share" Features যোগ করো

```javascript
// App এ এই buttons রাখো:

// Button 1: Print PDF
const printPDF = () => window.print();

// Button 2: WhatsApp এ share (family/trusted person কে)
const shareWhatsApp = () => {
  const text = `আমার অভিযোগপত্র তৈরি হয়েছে। নিকটতম UNO অফিস: ${nearestUNO.name}`;
  window.open(`https://wa.me/?text=${encodeURIComponent(text)}`);
};

// Button 3: Emergency Call 999
const call999 = () => window.open('tel:999');

// Button 4: NLASO Call
const callNLASO = () => window.open('tel:16430');

// Button 5: Download PDF
const downloadPDF = () => {
  const link = document.createElement('a');
  link.href = pdfUrl;
  link.download = 'complaint.pdf';
  link.click();
};
```

---

## PART 8: 999 Integration — কীভাবে সংযুক্ত করবে?

### ৮.১ বাস্তবতা

**৯৯৯ সম্পর্কে গুরুত্বপূর্ণ তথ্য:**

| | Details |
|---|---|
| **999 কী?** | Bangladesh National Emergency Service (Police/Fire/Ambulance) |
| **Public API আছে?** | ❌ নেই (government system, closed) |
| **Automatic case send করা যায়?** | ❌ না |
| **কী করা সম্ভব?** | ✅ "Call 999" button যোগ করা |

### ৮.২ তোমার System এ কী করতে পারো

```
Severity 5 (Murder/Emergency):
  → App এ বড় লাল button: "এখনই 999 কল করুন"
  → tel:999 link

Severity 4 (Physical Abuse):
  → "নিকটতম থানায় যান" + Map
  → "UNO অফিসে অভিযোগ করুন" + PDF

Severity 1-3 (Neglect/Abandonment/Financial):
  → "UNO অফিসে যান" + PDF + Map
  → "NLASO কল করুন: 16430"
```

**Smart Triage Button Logic:**
```javascript
function getActionButtons(severity) {
  if (severity === 5) {
    return [
      { label: "🚨 এখনই 999 কল করুন", action: "tel:999", color: "red" },
      { label: "📋 PDF Download করুন", action: "download_pdf", color: "blue" }
    ];
  } else if (severity === 4) {
    return [
      { label: "🚔 নিকটতম থানায় যান", action: "show_police_map", color: "orange" },
      { label: "🏛️ UNO অফিসে অভিযোগ করুন", action: "show_uno_map", color: "blue" },
      { label: "📋 PDF Download করুন", action: "download_pdf", color: "green" }
    ];
  } else {
    return [
      { label: "🏛️ UNO অফিসে যান", action: "show_uno_map", color: "blue" },
      { label: "📞 NLASO: 16430", action: "tel:16430", color: "green" },
      { label: "📋 PDF Download করুন", action: "download_pdf", color: "gray" }
    ];
  }
}
```

---

## PART 9: User Location — UNO খোঁজার পদ্ধতি

### ৯.১ Browser Geolocation API (সম্পূর্ণ Free)

```javascript
// কোনো API key লাগবে না!
// সব modern smartphone এ কাজ করে

function getUserLocation() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject("Geolocation supported নয়");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          lat: position.coords.latitude,
          lon: position.coords.longitude,
          accuracy: position.coords.accuracy  // meters
        });
      },
      (error) => {
        reject(error.message);
      },
      {
        enableHighAccuracy: true,   // GPS use করবে (accurate)
        timeout: 10000,             // 10 second wait
        maximumAge: 60000           // 1 minute cached ok
      }
    );
  });
}
```

### ৯.২ Haversine Distance Calculation

```javascript
function haversineDistance(lat1, lon1, lat2, lon2) {
  const R = 6371;  // Earth radius km
  const toRad = (deg) => deg * Math.PI / 180;

  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a = Math.sin(dLat/2)**2 +
            Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
            Math.sin(dLon/2)**2;

  return R * 2 * Math.asin(Math.sqrt(a));
}

function findNearestUNOs(userLat, userLon, unoList, topN = 3) {
  return unoList
    .map(uno => ({
      ...uno,
      distance_km: haversineDistance(userLat, userLon, uno.lat, uno.lon)
    }))
    .sort((a, b) => a.distance_km - b.distance_km)
    .slice(0, topN);
}
```

### ৯.৩ UNO Database কোথায় পাবে?

**Step 1: LGD ওয়েবসাইট থেকে তথ্য সংগ্রহ**
```
Website: https://lgd.gov.bd
সেখানে ৬৪ জেলা ও ৪৯৫ উপজেলার তথ্য আছে
প্রতিটি উপজেলার UNO নাম ও contact আছে
```

**Step 2: GPS Coordinates — Nominatim API (Free)**
```python
# OpenStreetMap Nominatim — সম্পূর্ণ FREE
import requests
import time

def get_gps_coordinates(upazila: str, district: str) -> dict:
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": f"{upazila}, {district}, Bangladesh",
        "format": "json",
        "limit": 1,
        "countrycodes": "BD"
    }
    headers = {"User-Agent": "ElderAbuseAI/1.0"}

    response = requests.get(url, params=params, headers=headers)
    results = response.json()

    if results:
        return {
            "lat": float(results[0]["lat"]),
            "lon": float(results[0]["lon"])
        }
    return None

# Example:
# get_gps_coordinates("Rupganj", "Narayanganj")
# → {"lat": 23.78, "lon": 90.52}

# Rate limit: 1 request/second (Nominatim rule)
time.sleep(1)  # প্রতিটি request এর পরে ১ second wait
```

**Step 3: UNO JSON তৈরি করার script**
```python
import json, time, requests

# lgd.gov.bd থেকে manually তৈরি করা উপজেলার list
upazilas = [
    {"upazila": "Rupganj", "district": "Narayanganj", "division": "Dhaka", "phone": "02-XXXXXXX"},
    {"upazila": "Araihazar", "district": "Narayanganj", "division": "Dhaka", "phone": "02-XXXXXXX"},
    # ... 495 টি উপজেলা
]

uno_database = []
for i, u in enumerate(upazilas):
    coords = get_gps_coordinates(u["upazila"], u["district"])
    if coords:
        u.update(coords)
        u["id"] = f"UNO_{i+1:03d}"
        uno_database.append(u)
        print(f"✅ {u['upazila']}, {u['district']} → {coords}")
    time.sleep(1)  # Rate limit

with open("geospatial/uno_locations.json", "w", encoding="utf-8") as f:
    json.dump(uno_database, f, ensure_ascii=False, indent=2)
```

---

## PART 10: Bangladesh Context — Reference Links

### ১০.১ সরকারি আইনি Reference

| Resource | URL | কেন দরকার |
|----------|-----|----------|
| Bangladesh Laws Online | https://bdlaws.minlaw.gov.bd | PMA 2013 full text পাবে |
| Local Government Division | https://lgd.gov.bd | UNO contact info |
| Ministry of Public Administration | https://mopa.gov.bd | UNO directory |
| National Legal Aid Services | https://nlaso.gov.bd | Free legal aid info |

### ১০.২ Emergency & Legal Aid Helplines (Bangladesh)

| Service | Number | Notes |
|---------|--------|-------|
| **National Emergency** | **999** | Police, Fire, Ambulance |
| **Legal Aid (NLASO)** | **16430** | Free legal advice |
| **Women Helpline** | **10921** | Jatiyo Mohila Sangstha |
| **Child Helpline** | **1098** | Bangladesh Child Helpline |

> ⚠️ **Important:** এই নম্বরগুলো ব্যবহারের আগে verify করো — বাংলাদেশ সরকার সময়ে সময়ে পরিবর্তন করে।

### ১০.৩ NGO & Legal Aid Organizations

| Organization | সেবা | Contact |
|-------------|------|---------|
| **BLAST** (Bangladesh Legal Aid and Services Trust) | Free legal aid, court representation | blast.org.bd |
| **ASK** (Ain o Salish Kendra) | Legal aid, human rights | askbd.org |
| **BRAC Legal Aid** | Community legal support | brac.net |
| **Naripokkho** | Women's rights, elder women support | naripokkho.net |

### ১০.৪ Technical Reference

| Resource | URL | Purpose |
|----------|-----|---------|
| Groq API Console | https://console.groq.com | Free Whisper + LLM API |
| Google AI Studio | https://aistudio.google.com | Free Gemini API |
| OpenAI Platform | https://platform.openai.com | Whisper + GPT API |
| HuggingFace | https://huggingface.co | Free ML models |
| Leaflet.js Docs | https://leafletjs.com | Map library docs |
| Firebase Console | https://console.firebase.google.com | Backend setup |
| OSM Nominatim | https://nominatim.openstreetmap.org | Free geocoding |
| ChromaDB Docs | https://docs.trychroma.com | Vector DB docs |

---

## PART 11: Improvements & Suggestions

### ১১.১ আমার Suggestions (Priority অনুযায়ী)

**🔴 High Priority (Thesis এর জন্য জরুরি):**

```
1. Confidence Score দেখানো
   - Whisper এর confidence % দেখাও
   - "৮৭% নিশ্চিত" — user বুঝবে transcription কতটা accurate

2. Manual Edit করার সুবিধা
   - Transcript wrong হলে user edit করতে পারবে
   - তারপর আবার classify হবে

3. Audio Playback
   - Record করা audio শুনতে পারবে
   - Verify করে তারপর submit করবে

4. Multi-page PDF
   - ১ page: বাংলা অভিযোগপত্র
   - ২ page: আইনি ধারার বিস্তারিত (বাংলা)
   - ৩ page: Recommended steps
```

**🟡 Medium Priority (Thesis কে strengthen করবে):**

```
5. Anonymous Reporting
   - নাম ছাড়াও report করার option
   - Trust Blind Spot এর জন্য গুরুত্বপূর্ণ

6. Case Reference Number
   - প্রতিটি report এ unique ID
   - User পরে track করতে পারবে
   - Firebase Firestore এ store হবে

7. Photo/Document Upload
   - Evidence হিসেবে photo add করার option
   - Medical certificate, injury photo

8. Audio Quality Indicator
   - "Audio quality: Good/Poor" দেখাও
   - Poor হলে "আরেকবার চেষ্টা করুন" বলো
```

**🟢 Low Priority (Future enhancement):**

```
9. Offline Mode
   - Internet ছাড়া keyword classification কাজ করবে
   - Firebase offline sync

10. SMS Notification
    - UNO অফিসে automatically SMS পাঠানো
    - Needs partnership with government

11. Multi-language
    - English, Bangla উভয়ে UI
    - Currently only Bangla needed

12. Case History
    - Previous reports দেখার সুবিধা
    - Case tracking status
```

### ১১.২ Current Implementation এ Improvements

**Keyword Classifier → More Robust করো:**
```python
# Current problem: "বের করে" → Abandonment detect
# But "বের করে দিয়েছে" vs "বের হয়ে গেছে" — different meaning!

# Improvement: Context-aware matching
def classify_with_context(text: str) -> dict:
    # 1. Keyword matching (fast)
    initial = keyword_match(text)

    # 2. Negation check
    negations = ["না", "নয়", "নি", "হয়নি", "করেনি"]
    for neg in negations:
        if neg in text:
            # Context বুঝে category adjust করো
            pass

    # 3. Confidence score
    score = calculate_confidence(text, initial["category"])
    initial["confidence"] = score
    return initial
```

**WER Evaluation যোগ করো:**
```python
# Test dataset এ WER measure করো
def evaluate_whisper_wer(test_cases: list) -> float:
    total_wer = 0
    for case in test_cases:
        # Ground truth Bangla text
        reference = case["scenario_bangla"]
        # Whisper output
        hypothesis = transcribe(case["audio_file"])
        # WER calculate
        wer = compute_wer(reference, hypothesis)
        total_wer += wer
    return total_wer / len(test_cases)
```

---

## PART 12: Common Errors এবং Solutions

### সবচেয়ে বেশি হওয়া Errors:

```
❌ Error: "No module named 'whisper'"
✅ Solution: pip install openai-whisper
            (NOT pip install whisper — এটা অন্য package)

❌ Error: CUDA out of memory
✅ Solution: whisper.load_model("medium")  # large-v3 এর বদলে
            অথবা: Groq API ব্যবহার করো

❌ Error: "ffmpeg not found in PATH"
✅ Solution: Windows: winget install --id Gyan.FFmpeg
            নতুন terminal খুলতে হবে PATH refresh এর জন্য

❌ Error: ChromaDB "InvalidCollectionException"
✅ Solution: প্রতিবার server start এ নতুন collection বানানোর বদলে:
            if collection_exists: load it
            else: create it

❌ Error: Gemini JSON parse failed
✅ Solution: response_mime_type="application/json" যোগ করো
            generation_config={"response_mime_type": "application/json"}

❌ Error: React CORS error
✅ Solution: FastAPI তে:
            app.add_middleware(CORSMiddleware,
              allow_origins=["http://localhost:5173"],
              allow_methods=["*"],
              allow_headers=["*"])

❌ Error: Bangla PDF blank squares
✅ Solution: NotoSansBengali font ব্যবহার করো
            fpdf.add_font("NotoSansBengali", "", "fonts/NotoSansBengali-Regular.ttf")

❌ Error: Geolocation "Permission denied"
✅ Solution: HTTPS ব্যবহার করতে হবে (HTTP তে geolocation কাজ করে না)
            Development: localhost is exempt
            Production: HTTPS deploy করো

❌ Error: Audio too noisy → WER high
✅ Solution: Noise gate threshold বাড়াও
            Whisper এর initial_prompt ব্যবহার করো dialect এর জন্য
```

---

## PART 13: সম্পূর্ণ Implementation Checklist

### Phase 1 Checklist ✅
```
□ Elder_abuse_Dataset.csv load এবং inspect
□ Abuse Category normalize (typo fix, standard names)
□ Age string → integer (Unknown → NaN)
□ Date string → datetime parse
□ Severity Score column (1-5)
□ Trust Blind Spot column (0/1)
□ Train/test split (80/20, stratified, seed=42)
□ keyword_dictionary.json তৈরি (7 categories, Bangla+English)
□ act_knowledge_base.json তৈরি (12 legal sections)
□ EDA visualizations (matplotlib/seaborn)
□ Phase 1 outputs data/ folder এ save
□ phase1_eda.py script commit করা
```

### Phase 2 Checklist ✅
```
□ Python venv তৈরি করা
□ requirements.txt এ সব dependencies
□ .gitignore তৈরি (venv/, __pycache__/, .env)
□ .env তৈরি (API keys)
□ backend/app/ folder structure
□ preprocessor.py (audio → 16kHz WAV)
□ whisper_service.py (OR groq_service.py)
□ keyword_classifier.py (keyword + entity extraction)
□ main.py (FastAPI, 4 endpoints)
□ /health endpoint test করা
□ /transcribe endpoint test করা
□ /transcribe/text endpoint test করা
□ Audio test (WAV file upload করে verify)
```

### Phase 3 Checklist 🔲
```
□ Gemini API key সেট করা
□ HuggingFace sentence-transformers install
□ ChromaDB install
□ act_knowledge_base.json → vector store build
□ rag_engine.py তৈরি
□ entity_extractor.py তৈরি (GPT/Gemini based)
□ pdf_generator.py তৈরি
□ NotoSansBengali font download ও setup
□ main.py update করা (Phase 3 endpoints)
□ RAG accuracy test করা (test_split.csv এ)
□ F1-Score calculate করা
□ PDF sample generate করে verify
```

### Phase 4 Checklist 🔲
```
□ React app create করা (npm create vite@latest)
□ Tailwind CSS setup
□ Leaflet.js + react-leaflet install
□ VoiceRecorder component
□ TranscriptDisplay component
□ AbuseResult component (category badge)
□ LegalAdvice component
□ MapView component (Leaflet.js)
□ PDFDownload component
□ Firebase project তৈরি করা
□ Firebase Firestore setup (offline mode)
□ UNO GPS database তৈরি করা (495 entries)
□ Haversine nearest UNO logic
□ Senior-friendly UI test করা (বড় font, বাংলা label)
□ HTTPS deploy করা (geolocation এর জন্য)
```

### Phase 5 Checklist 🔲
```
□ End-to-end integration test
□ WER measurement (Regional dialect recordings)
□ F1-Score report (test_split.csv)
□ PDF generation time benchmark
□ UNO distance accuracy test
□ Senior user acceptance test (UAT) — ১০+ জন
□ Security review (audio encryption, PII handling)
□ Final thesis (Blackbook) লেখা
□ Presentation slides তৈরি
□ System demo video record করা
```

---

## PART 14: Final Architecture Decision Summary

```
┌────────────────────────────────────────────────────────────┐
│                  RECOMMENDED STACK                         │
├──────────────────┬─────────────────────────────────────────┤
│ Speech-to-Text   │ Groq Whisper API (free, fast, accurate) │
│ LLM              │ Google Gemini 1.5 Flash (free tier)     │
│ Embedding        │ HuggingFace MiniLM multilingual (free)  │
│ Vector DB        │ ChromaDB local (free)                   │
│ Backend          │ FastAPI + uvicorn (free)                │
│ Frontend         │ React + Vite + Tailwind (free)          │
│ Map              │ Leaflet.js + OpenStreetMap (free)       │
│ PDF              │ fpdf2 + NotoSansBengali font (free)     │
│ Database         │ Firebase Firestore (free tier)          │
│ Storage          │ Firebase Storage (free tier)            │
│ Geocoding        │ Nominatim API (free)                    │
│ Emergency        │ tel:999 link (no API needed)            │
│ Legal Aid        │ tel:16430 link (NLASO)                  │
├──────────────────┼─────────────────────────────────────────┤
│ Monthly Cost     │ $0.00 (সম্পূর্ণ বিনামূল্যে)           │
└──────────────────┴─────────────────────────────────────────┘
```

---

---

## PART 15: Multilingual Support — English, Bangla, এবং Mixed

> **নতুন feature:** শুধু বাংলায় নয় — English অথবা English-Bangla mixed complain ও করা যাবে।
> Whisper নিজেই language detect করবে এবং system সেই ভাষায় response দেবে।

---

### ১৫.১ কেন Multilingual দরকার?

```
Case 1: শহুরে শিক্ষিত বয়স্ক মানুষ
        → "My son is not giving me food, he hit me yesterday"
        → English complaint → English advice দেওয়া উচিত

Case 2: NRB (বিদেশে থাকা বাংলাদেশি) family member রিপোর্ট করছে
        → "আমার বাবাকে ছেলে বাড়ি থেকে evict করে দিয়েছে"
        → Mixed complaint → Mixed response

Case 3: গ্রামের বয়স্ক
        → "আমার ছেলে আমারে মাইরা ফালাইছে"
        → Pure Bangla (dialect) → Bangla advice
```

---

### ১৫.২ Language Detection — Whisper দিয়ে (Step 1)

**সবচেয়ে সহজ পদ্ধতি:** `language` parameter না দিলে Whisper নিজেই detect করে।

```python
# whisper_service.py — Updated for multilingual support

from groq import Groq
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def transcribe_multilingual(audio_file_path: str) -> dict:
    """
    Language auto-detect করে। Bangla, English, এবং mixed সব handle করে।
    """
    with open(audio_file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3-turbo",
            # language parameter দিচ্ছি না → Whisper নিজেই detect করবে
            response_format="verbose_json",
            prompt="This is a complaint about elder abuse in Bangladesh. "
                   "Speaker may use Bangla, English, or mix of both."
        )

    detected_lang = transcription.language  # "bn" বা "en" বা "hi" etc.
    text = transcription.text

    # "mixed" detect করা — উভয় script আছে কিনা দেখো
    has_bangla  = any('ঀ' <= ch <= '৿' for ch in text)
    has_english = any('a' <= ch.lower() <= 'z' for ch in text)

    if has_bangla and has_english:
        language_mode = "mixed"
    elif has_bangla:
        language_mode = "bangla"
    else:
        language_mode = "english"

    return {
        "text":          text,
        "detected_lang": detected_lang,
        "language_mode": language_mode,     # "bangla" | "english" | "mixed"
        "segments":      transcription.segments,
    }
```

**Output example:**
```json
{
  "text": "আমার ছেলে আমাকে বাড়ি থেকে evict করে দিয়েছে, সে আমার property নিয়ে নিয়েছে",
  "detected_lang": "bn",
  "language_mode": "mixed",
  "segments": [...]
}
```

---

### ১৫.৩ Keyword Classifier — Multilingual (Step 2)

**বাংলা + English উভয় keyword রাখো:**

```python
# keyword_classifier.py — Multilingual version

MULTILINGUAL_KEYWORDS = {
    "physical": [
        # Bangla
        "মারধর", "আঘাত", "চড়", "লাথি", "মেরেছে", "ব্যথা", "রক্ত",
        "হাসপাতাল", "জখম", "আহত",
        # English
        "beat", "hit", "slap", "punch", "kick", "assault", "injury",
        "hospital", "hurt", "wound", "attack", "bruise", "fracture",
        # Mixed common forms
        "beat করেছে", "hit করেছে", "assault করা হয়েছে"
    ],
    "financial": [
        # Bangla
        "সম্পত্তি", "টাকা", "জমি", "ব্যাংক", "অ্যাকাউন্ট", "চুরি",
        "প্রতারণা", "দলিল", "সই করানো", "জোর করে",
        # English
        "property", "money", "land", "bank", "account", "steal",
        "fraud", "deed", "signature", "forced", "pension", "savings",
        "inheritance", "assets", "dispossess",
        # Mixed
        "property নিয়ে গেছে", "account থেকে টাকা নিয়েছে"
    ],
    "abandonment": [
        # Bangla
        "বের করে দিয়েছে", "বাড়ি থেকে তাড়িয়ে", "রাস্তায় ফেলে",
        "পরিত্যাগ", "একা ফেলে", "চলে গেছে", "দেখে না",
        # English
        "evict", "thrown out", "kicked out", "abandoned", "left alone",
        "deserted", "homeless", "shelter", "expelled", "removed from home",
        # Mixed
        "evict করে দিয়েছে", "abandon করা হয়েছে"
    ],
    "verbal": [
        # Bangla
        "গালি", "অপমান", "হুমকি", "ভয় দেখানো", "চিৎকার",
        "কথা শোনায় না", "তিরস্কার",
        # English
        "insult", "humiliate", "threaten", "threat", "yell", "scream",
        "verbal abuse", "curse", "intimidate", "disrespect",
        # Mixed
        "threaten করেছে", "insult করে"
    ],
    "neglect": [
        # Bangla
        "খাবার দেয় না", "ওষুধ দেয় না", "যত্ন নেয় না", "অবহেলা",
        "চিকিৎসা করায় না", "ভাত দেয় না",
        # English
        "not feeding", "no food", "no medicine", "neglect", "not caring",
        "no medical", "starvation", "deprive", "deny food", "ignore",
        # Mixed
        "medicine দেয় না", "care করে না"
    ],
    "sexual": [
        # Bangla
        "যৌন হয়রানি", "অশ্লীল", "স্পর্শ",
        # English
        "sexual abuse", "harassment", "inappropriate touch", "molest",
        "sexual assault"
    ],
    "psychological": [
        # Bangla
        "মানসিক নির্যাতন", "কষ্ট দেওয়া", "কাঁদানো",
        # English
        "mental abuse", "psychological", "emotional abuse", "trauma",
        "distress", "depression caused", "mental torture"
    ]
}

def classify_multilingual(text: str) -> dict:
    text_lower = text.lower()
    scores = {}

    for category, keywords in MULTILINGUAL_KEYWORDS.items():
        match_count  = sum(1 for kw in keywords if kw.lower() in text_lower)
        match_weight = sum(len(kw.split()) for kw in keywords if kw.lower() in text_lower)
        scores[category] = match_count + (match_weight * 0.1)

    if not any(scores.values()):
        return {"category": "unknown", "confidence": 0.0, "all_scores": scores}

    top_category  = max(scores, key=scores.get)
    total         = sum(scores.values())
    confidence    = scores[top_category] / total if total > 0 else 0

    return {
        "category":   top_category,
        "confidence": round(confidence, 2),
        "all_scores": scores
    }
```

---

### ১৫.৪ Gemini — Language-Aware Legal Advice (Step 3)

**Gemini কে বলো:** user যে ভাষায় কথা বলেছে সেই ভাষায় respond করো।

```python
# rag_engine.py — Multilingual version

def get_legal_advice_multilingual(
    transcript:    str,
    category:      str,
    language_mode: str,   # "bangla" | "english" | "mixed"
    vectorstore,
    gemini_model
) -> dict:

    # 1. RAG: ChromaDB থেকে relevant law sections খোঁজো
    #    Multilingual embedding model — Bangla + English দুইটাই বোঝে
    results = vectorstore.similarity_search(
        query=f"{category}: {transcript}",
        k=3
    )
    context = "\n\n".join([r.page_content for r in results])

    # 2. Language-aware prompt তৈরি করো
    if language_mode == "english":
        response_instruction = "Respond ENTIRELY in English."
        advice_field         = "legal_advice_english"
        action_field         = "recommended_action_english"
    elif language_mode == "bangla":
        response_instruction = "সম্পূর্ণ বাংলায় উত্তর দাও।"
        advice_field         = "legal_advice_bangla"
        action_field         = "recommended_action_bangla"
    else:  # mixed
        response_instruction = (
            "Respond in both Bangla and English. "
            "Provide Bangla advice first, then English translation."
        )
        advice_field = "legal_advice_bangla"
        action_field = "recommended_action_bangla"

    prompt = f"""
You are a legal assistance AI specialized in Bangladesh elder abuse law.
Answer ONLY based on the legal sections provided below.
Do NOT make up laws. {response_instruction}

Legal Context (Bangladesh Laws):
{context}

Complaint (Transcript): {transcript}
Initial Category: {category}
Complaint Language: {language_mode}

Respond in JSON format:
{{
  "abuse_type": "...",
  "applicable_sections": ["PMA 2013 Section X", "BPC §XXX"],
  "legal_advice_bangla": "...",
  "legal_advice_english": "...",
  "recommended_action_bangla": "...",
  "recommended_action_english": "...",
  "civil_or_criminal": "Civil | Criminal | Both",
  "urgency": 1-5,
  "response_language": "{language_mode}"
}}
"""

    # 3. Gemini Flash এ পাঠাও
    import google.generativeai as genai
    response = gemini_model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"}
    )

    import json, re
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"error": "Could not parse response", "raw": response.text}
```

---

### ১৫.৫ PDF Generation — Bilingual Complaint Letter (Step 4)

**English complaint → English PDF**
**Bangla complaint → Bangla PDF**
**Mixed → Bilingual PDF (দুই ভাষায়)**

```python
# pdf_generator.py — Multilingual version

from fpdf import FPDF

class BilingualComplaintPDF(FPDF):
    def __init__(self, language_mode: str = "bangla"):
        super().__init__()
        self.language_mode = language_mode

        # Bangla font (NotoSansBengali — Bangla + Latin support)
        self.add_font("Bengali", fname="fonts/NotoSansBengali-Regular.ttf")
        self.add_font("BengaliBold", fname="fonts/NotoSansBengali-Bold.ttf")

    def header(self):
        self.set_font("BengaliBold", size=13)
        if self.language_mode == "english":
            self.cell(0, 10, "Government of the People's Republic of Bangladesh", align="C", new_x="LMARGIN", new_y="NEXT")
            self.cell(0, 8,  "Office of the Upazila Nirbahi Officer (UNO)", align="C", new_x="LMARGIN", new_y="NEXT")
            self.cell(0, 8,  "COMPLAINT LETTER", align="C", new_x="LMARGIN", new_y="NEXT")
        elif self.language_mode == "bangla":
            self.cell(0, 10, "গণপ্রজাতন্ত্রী বাংলাদেশ সরকার", align="C", new_x="LMARGIN", new_y="NEXT")
            self.cell(0, 8,  "উপজেলা নির্বাহী অফিসার বরাবর", align="C", new_x="LMARGIN", new_y="NEXT")
            self.cell(0, 8,  "অভিযোগপত্র", align="C", new_x="LMARGIN", new_y="NEXT")
        else:  # mixed
            self.cell(0, 10, "গণপ্রজাতন্ত্রী বাংলাদেশ সরকার / Government of Bangladesh", align="C", new_x="LMARGIN", new_y="NEXT")
            self.cell(0, 8,  "উপজেলা নির্বাহী অফিসার / Upazila Nirbahi Officer (UNO)", align="C", new_x="LMARGIN", new_y="NEXT")
            self.cell(0, 8,  "অভিযোগপত্র / COMPLAINT LETTER", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)


def generate_multilingual_pdf(case_data: dict, language_mode: str) -> bytes:
    pdf = BilingualComplaintPDF(language_mode=language_mode)
    pdf.add_page()
    pdf.set_font("Bengali", size=10)

    # ── Victim Info section ──────────────────────────────────────────
    if language_mode == "english":
        pdf.set_font("BengaliBold", size=11)
        pdf.cell(0, 8, "COMPLAINANT INFORMATION:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Bengali", size=10)
        pdf.cell(0, 7, f"Name: {case_data.get('victim_name', 'Not provided')}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 7, f"Age:  {case_data.get('victim_age', 'Not provided')}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 7, f"Location: {case_data.get('location', 'Not provided')}", new_x="LMARGIN", new_y="NEXT")
    elif language_mode == "bangla":
        pdf.set_font("BengaliBold", size=11)
        pdf.cell(0, 8, "অভিযোগকারীর তথ্য:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Bengali", size=10)
        pdf.cell(0, 7, f"নাম: {case_data.get('victim_name', 'অজ্ঞাত')}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 7, f"বয়স: {case_data.get('victim_age', 'অজ্ঞাত')}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 7, f"ঠিকানা: {case_data.get('location', 'অজ্ঞাত')}", new_x="LMARGIN", new_y="NEXT")
    else:  # mixed — bilingual
        pdf.set_font("BengaliBold", size=11)
        pdf.cell(0, 8, "অভিযোগকারীর তথ্য / Complainant Information:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Bengali", size=10)
        pdf.cell(0, 7, f"নাম / Name: {case_data.get('victim_name', 'অজ্ঞাত / Not provided')}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 7, f"বয়স / Age: {case_data.get('victim_age', 'অজ্ঞাত')}", new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 7, f"ঠিকানা / Location: {case_data.get('location', 'Not provided')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # ── Transcript section ───────────────────────────────────────────
    pdf.set_font("BengaliBold", size=11)
    label = {
        "english": "COMPLAINT STATEMENT:",
        "bangla":  "ঘটনার বিবরণ:",
        "mixed":   "ঘটনার বিবরণ / Complaint Statement:"
    }[language_mode]
    pdf.cell(0, 8, label, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Bengali", size=10)
    pdf.multi_cell(0, 7, case_data.get("transcript", ""))
    pdf.ln(3)

    # ── Legal Sections ───────────────────────────────────────────────
    pdf.set_font("BengaliBold", size=11)
    label2 = {
        "english": "APPLICABLE LEGAL SECTIONS:",
        "bangla":  "প্রযোজ্য আইনি ধারাসমূহ:",
        "mixed":   "প্রযোজ্য আইনি ধারাসমূহ / Applicable Legal Sections:"
    }[language_mode]
    pdf.cell(0, 8, label2, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Bengali", size=10)
    for section in case_data.get("applicable_sections", []):
        pdf.cell(0, 7, f"• {section}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # ── Legal Advice ─────────────────────────────────────────────────
    pdf.set_font("BengaliBold", size=11)
    pdf.cell(0, 8, "আইনি পরামর্শ / Legal Advice:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Bengali", size=10)

    if language_mode in ("bangla", "mixed"):
        pdf.multi_cell(0, 7, case_data.get("legal_advice_bangla", ""))
    if language_mode in ("english", "mixed"):
        if language_mode == "mixed":
            pdf.ln(2)
            pdf.set_font("BengaliBold", size=10)
            pdf.cell(0, 7, "English:", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Bengali", size=10)
        pdf.multi_cell(0, 7, case_data.get("legal_advice_english", ""))
    pdf.ln(3)

    # ── Recommended Actions ──────────────────────────────────────────
    pdf.set_font("BengaliBold", size=11)
    pdf.cell(0, 8, "সুপারিশকৃত পদক্ষেপ / Recommended Steps:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Bengali", size=10)
    if language_mode in ("bangla", "mixed"):
        pdf.multi_cell(0, 7, case_data.get("recommended_action_bangla", ""))
    if language_mode in ("english", "mixed"):
        pdf.multi_cell(0, 7, case_data.get("recommended_action_english", ""))
    pdf.ln(10)

    # ── Helplines ────────────────────────────────────────────────────
    pdf.set_font("BengaliBold", size=10)
    pdf.cell(0, 7, "জরুরি নম্বর / Emergency Contacts:", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Bengali", size=10)
    pdf.cell(0, 6, "• Emergency (Police/Fire/Ambulance): 999", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "• Free Legal Aid (NLASO): 16430", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, "• Women Helpline: 10921", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    # ── Signature ────────────────────────────────────────────────────
    pdf.cell(60, 7, "স্বাক্ষর / Signature", border="T")
    pdf.cell(10, 7, "")
    pdf.cell(60, 7, "তারিখ / Date", border="T")

    return bytes(pdf.output())
```

---

### ১৫.৬ FastAPI Endpoint — Multilingual (Step 5)

```python
# main.py — Updated /transcribe endpoint

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import tempfile, os, shutil

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

@app.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    # 1. Audio সাময়িকভাবে save করো
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
        shutil.copyfileobj(audio.file, tmp)
        tmp_path = tmp.name

    try:
        # 2. Preprocess → WAV
        wav_path = preprocess_audio(tmp_path)          # preprocessor.py

        # 3. Whisper — Language auto-detect
        result = transcribe_multilingual(wav_path)     # whisper_service.py
        transcript    = result["text"]
        language_mode = result["language_mode"]        # "bangla"|"english"|"mixed"

        # 4. Keyword classify
        classification = classify_multilingual(transcript)

        # 5. RAG + Gemini — Language-aware advice
        legal = get_legal_advice_multilingual(
            transcript, classification["category"], language_mode,
            vectorstore, gemini_model
        )

        # 6. PDF generate
        case_data = {
            "transcript":             transcript,
            "abuse_type":             legal["abuse_type"],
            "applicable_sections":    legal["applicable_sections"],
            "legal_advice_bangla":    legal.get("legal_advice_bangla", ""),
            "legal_advice_english":   legal.get("legal_advice_english", ""),
            "recommended_action_bangla":  legal.get("recommended_action_bangla", ""),
            "recommended_action_english": legal.get("recommended_action_english", ""),
        }
        pdf_bytes = generate_multilingual_pdf(case_data, language_mode)

        # 7. Firebase তে save করো
        pdf_url = upload_pdf_to_firebase(pdf_bytes)

        return {
            "transcript":    transcript,
            "language_mode": language_mode,
            "category":      classification["category"],
            "confidence":    classification["confidence"],
            "legal_advice":  legal,
            "pdf_url":       pdf_url,
            "urgency":       legal.get("urgency", 1)
        }
    finally:
        os.unlink(tmp_path)
        if os.path.exists(wav_path):
            os.unlink(wav_path)
```

---

### ১৫.৭ Frontend — Language Indicator + Text Input (Step 6)

**User যেন text দিয়েও complain করতে পারে (typing):**

```jsx
// ComplaintInput.jsx — Voice + Text input, multilingual

import { useState } from 'react';

const LANG_LABELS = {
  bangla:  { badge: "🇧🇩 বাংলা",  color: "bg-green-100 text-green-800" },
  english: { badge: "🇬🇧 English", color: "bg-blue-100 text-blue-800" },
  mixed:   { badge: "🔀 Mixed",    color: "bg-purple-100 text-purple-800" },
  null:    { badge: "...",         color: "bg-gray-100 text-gray-600" }
};

export default function ComplaintInput({ onSubmit }) {
  const [mode,          setMode]          = useState("voice"); // "voice"|"text"
  const [textInput,     setTextInput]     = useState("");
  const [detectedLang,  setDetectedLang]  = useState(null);
  const [isProcessing,  setIsProcessing]  = useState(false);

  // Voice complaint submit
  const handleVoiceComplete = async (audioBlob) => {
    setIsProcessing(true);
    const formData = new FormData();
    formData.append("audio", audioBlob, "recording.webm");

    const res    = await fetch("http://localhost:8000/transcribe", { method: "POST", body: formData });
    const result = await res.json();
    setDetectedLang(result.language_mode);
    onSubmit(result);
    setIsProcessing(false);
  };

  // Text complaint submit (English, Bangla, or mixed typing)
  const handleTextSubmit = async () => {
    if (!textInput.trim()) return;
    setIsProcessing(true);

    const res    = await fetch("http://localhost:8000/transcribe/text", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ text: textInput })
    });
    const result = await res.json();
    setDetectedLang(result.language_mode);
    onSubmit(result);
    setIsProcessing(false);
  };

  const langInfo = LANG_LABELS[detectedLang] || LANG_LABELS[null];

  return (
    <div className="flex flex-col gap-4 p-4">
      {/* Mode toggle */}
      <div className="flex gap-2">
        <button
          onClick={() => setMode("voice")}
          className={`flex-1 py-2 rounded-lg font-bold ${mode === "voice" ? "bg-red-600 text-white" : "bg-gray-200"}`}
        >
          🎤 কথা বলুন / Speak
        </button>
        <button
          onClick={() => setMode("text")}
          className={`flex-1 py-2 rounded-lg font-bold ${mode === "text" ? "bg-blue-600 text-white" : "bg-gray-200"}`}
        >
          ✍️ টাইপ করুন / Type
        </button>
      </div>

      {/* Language badge */}
      {detectedLang && (
        <div className={`px-3 py-1 rounded-full text-sm font-medium w-fit ${langInfo.color}`}>
          {langInfo.badge} Detected
        </div>
      )}

      {/* Voice mode */}
      {mode === "voice" && (
        <VoiceRecorder onRecordingComplete={handleVoiceComplete} />
      )}

      {/* Text mode — English, Bangla, or mixed */}
      {mode === "text" && (
        <div className="flex flex-col gap-3">
          <p className="text-sm text-gray-500">
            বাংলায় বা English এ বা দুইটা মিলিয়ে লিখতে পারেন।
            <br/>You can write in Bangla, English, or both.
          </p>
          <textarea
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            className="w-full h-40 p-3 border-2 rounded-lg text-lg"
            placeholder="আপনার অভিযোগ এখানে লিখুন... / Write your complaint here..."
            dir="auto"  // ← RTL/LTR auto-detect
          />
          <button
            onClick={handleTextSubmit}
            disabled={isProcessing || !textInput.trim()}
            className="bg-blue-600 text-white py-3 rounded-lg font-bold text-lg disabled:opacity-50"
          >
            {isProcessing ? "Processing..." : "Submit / জমা দিন"}
          </button>
        </div>
      )}
    </div>
  );
}
```

---

### ১৫.৮ Text-Input Endpoint — FastAPI (Typing এর জন্য)

```python
# main.py — /transcribe/text endpoint যোগ করো

from pydantic import BaseModel

class TextComplaintRequest(BaseModel):
    text:       str
    victim_name: str | None = None
    victim_age:  str | None = None
    location:    str | None = None

@app.post("/transcribe/text")
async def transcribe_text(request: TextComplaintRequest):
    """Voice ছাড়াও text দিয়ে complain করার endpoint"""
    transcript = request.text

    # Language detect (Whisper ছাড়াই)
    has_bangla  = any('ঀ' <= ch <= '৿' for ch in transcript)
    has_english = any('a' <= ch.lower() <= 'z'   for ch in transcript)

    if has_bangla and has_english:
        language_mode = "mixed"
    elif has_bangla:
        language_mode = "bangla"
    else:
        language_mode = "english"

    # Classify + RAG + PDF (same as voice endpoint)
    classification = classify_multilingual(transcript)
    legal = get_legal_advice_multilingual(
        transcript, classification["category"], language_mode,
        vectorstore, gemini_model
    )

    case_data = {
        "transcript":                 transcript,
        "victim_name":                request.victim_name or ("অজ্ঞাত" if language_mode != "english" else "Not provided"),
        "victim_age":                 request.victim_age or ("অজ্ঞাত" if language_mode != "english" else "Not provided"),
        "location":                   request.location or ("অজ্ঞাত" if language_mode != "english" else "Not provided"),
        "applicable_sections":        legal["applicable_sections"],
        "legal_advice_bangla":        legal.get("legal_advice_bangla", ""),
        "legal_advice_english":       legal.get("legal_advice_english", ""),
        "recommended_action_bangla":  legal.get("recommended_action_bangla", ""),
        "recommended_action_english": legal.get("recommended_action_english", ""),
    }
    pdf_bytes = generate_multilingual_pdf(case_data, language_mode)
    pdf_url   = upload_pdf_to_firebase(pdf_bytes)

    return {
        "transcript":    transcript,
        "language_mode": language_mode,
        "category":      classification["category"],
        "confidence":    classification["confidence"],
        "legal_advice":  legal,
        "pdf_url":       pdf_url,
        "urgency":       legal.get("urgency", 1)
    }
```

---

### ১৫.৯ Multilingual এ কোন Language তে কী হবে

| Input Language | Whisper | Keyword Dict | Gemini Response | PDF |
|---|---|---|---|---|
| শুধু বাংলা | `language_mode = "bangla"` | Bangla keywords match | সম্পূর্ণ বাংলায় | বাংলা অভিযোগপত্র |
| শুধু English | `language_mode = "english"` | English keywords match | Entirely English | English Complaint Letter |
| Mixed (Banglish) | `language_mode = "mixed"` | Both match | Bangla + English both | Bilingual PDF |
| Typing (text input) | Script detection দিয়ে | Same | Same | Same |

---

### ১৫.১০ Keyword Dictionary Update — Checklist

Phase 1 এ `keyword_dictionary.json` বানানোর সময় এই format follow করো:

```json
{
  "physical": {
    "bangla": ["মারধর", "আঘাত", "চড়", "লাথি", "মেরেছে"],
    "english": ["beat", "hit", "slap", "assault", "punch", "kick", "injury"],
    "mixed_forms": ["beat করেছে", "hit করা হয়েছে", "assault করা হয়েছে"]
  },
  "financial": {
    "bangla": ["সম্পত্তি", "টাকা", "জমি", "দলিল", "প্রতারণা"],
    "english": ["property", "money", "land", "deed", "fraud", "savings", "inheritance"],
    "mixed_forms": ["property নিয়েছে", "account থেকে টাকা নিয়েছে"]
  },
  "abandonment": {
    "bangla": ["বের করে দিয়েছে", "পরিত্যাগ", "রাস্তায় ফেলে", "একা ফেলে"],
    "english": ["evict", "abandoned", "thrown out", "kicked out", "homeless"],
    "mixed_forms": ["evict করে দিয়েছে", "abandon করা হয়েছে"]
  },
  "verbal": {
    "bangla": ["গালি", "অপমান", "হুমকি", "ভয় দেখানো"],
    "english": ["insult", "threaten", "threat", "verbal abuse", "humiliate"],
    "mixed_forms": ["threaten করেছে", "insult করে"]
  },
  "neglect": {
    "bangla": ["খাবার দেয় না", "ওষুধ দেয় না", "যত্ন নেয় না", "অবহেলা"],
    "english": ["not feeding", "no food", "no medicine", "neglect", "deprive"],
    "mixed_forms": ["medicine দেয় না", "care করে না", "feed করে না"]
  }
}
```

---

### ১৫.১১ Multilingual Checklist (Phase 2 এ যোগ করো)

```
□ whisper_service.py — language parameter remove করো (auto-detect)
□ keyword_classifier.py — English + Bangla + mixed keywords যোগ করো
□ keyword_dictionary.json — bilingual format (bangla/english/mixed_forms)
□ rag_engine.py — language_mode parameter যোগ করো
□ Gemini prompt — language-aware instruction যোগ করো
□ pdf_generator.py — BilingualComplaintPDF class তৈরি করো
□ main.py — /transcribe endpoint এ language_mode return করো
□ main.py — /transcribe/text endpoint তৈরি করো (typing এর জন্য)
□ Frontend — mode toggle (Voice / Type) তৈরি করো
□ Frontend — Language badge দেখানো ("বাংলা" / "English" / "Mixed")
□ Test: English complaint → English PDF verify করো
□ Test: Bangla complaint → Bangla PDF verify করো
□ Test: Mixed complaint → Bilingual PDF verify করো
```

---

*Document Created: 28 May 2026*
*Last Updated: 29 May 2026 — Added PART 15: Multilingual Support (English, Bangla, Mixed)*
*Maintained by: Lamia Islam Mim (2212085042)*
