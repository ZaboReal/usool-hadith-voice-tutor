# Usool al-Hadith Voice Tutor

A RAG-enabled voice agent that teaches the foundations of Hadith science using LiveKit, OpenAI, and Pinecone.

**Live Demo**: [https://usool-hadith-voice-tutor.vercel.app](https://usool-hadith-voice-tutor.vercel.app)

---

## Project Overview

**Usuli** is an AI-powered Islamic scholar specializing in Hadith sciences (Usool al-Hadith). This voice agent serves as a personal tutor for students learning the methodology and principles of Hadith authentication.


### Core Capabilities

1. **Real-time Voice Conversations** - Natural dialogue about Hadith methodology with the ability to interrupt the agent at any time to ask clarifying questions or change topics
2. **RAG-Powered Answers** - Retrieves specific information from a 165-page classical text on Usool al-Hadith
3. **Expert Tool Calls** - Lookup narrator reliability grades and Hadith classification terminology
4. **Intelligent Summarization** - Condenses book content for concise voice responses

---

## System Architecture - End-to-End Flow

```
User (Browser) → Vercel Frontend
    ↓ [HTTP: Get Token]
AWS EC2 (Token Server)
    ↓ [Return JWT Token]
User → LiveKit Cloud
    ↓ [Voice Input Stream]
AWS EC2 (LiveKit Agent)
    ├─→ STT (OpenAI Whisper) → Convert speech to text
    ├─→ RAG Check → Always attempt retrieval for substantive questions
    ├─→ Pinecone Vector DB → Semantic search (multilingual-e5-large embeddings)
    ├─→ GPT-4o-mini → Summarize retrieved context (2-3 sentences max)
    ├─→ GPT-5.1 (Main LLM) → Generate response using summarized RAG + own knowledge
    ├─→ Custom Tools → Narrator/classification lookups (function calling)
    └─→ TTS (OpenAI) → Convert response to speech
    ↓ [Audio Stream]
User hears response + sees real-time transcript
```

---

## RAG Integration

### How It Works

1. **PDF Ingestion**:
   - 165-page Usool al-Hadith PDF loaded via PyPDF
   - Split into 533 chunks (1000 characters, 200 overlap)
   - Embedded using `intfloat/multilingual-e5-large` (local, free, 1024-dim)
   - Uploaded to Pinecone serverless index

2. **Query Flow**:
   - User asks question via voice
   - RAG triggered for all substantive questions (skips only greetings)
   - Pinecone returns top-5 most relevant chunks via cosine similarity
   - GPT-4o-mini summarizes retrieved content (200 token max)
   - If summary is relevant → inject into conversation context
   - If not relevant → LLM uses general knowledge

3. **Smart Summarization**:
   - Raw retrieval often returns 2000+ characters (too long for voice)
   - GPT-4o-mini condenses to 2-3 sentences
   - Preserves Arabic terminology and page references
   - Returns "NO_RELEVANT_INFO" if context doesn't answer question
   - Agent supplements with own knowledge when needed

### Why This Approach

**Problem**: Initial RAG implementation had verbose responses unsuitable for voice
**Solution**: Two-stage RAG with summarization layer
**Result**: Concise, natural-sounding answers that blend book content with conversational AI

---

## Tools & Frameworks

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Voice Platform** | LiveKit Cloud | Real-time WebRTC voice communication |
| **STT** | OpenAI Whisper | Speech-to-text (multilingual, handles Arabic terms) |
| **Main LLM** | GPT-5.1 | Primary conversational AI |
| **Summarization LLM** | GPT-4o-mini | RAG context condensation |
| **TTS** | OpenAI TTS | Text-to-speech synthesis |
| **VAD** | Silero | Voice activity detection |
| **RAG Framework** | LangChain | Document processing & retrieval orchestration |
| **Vector DB** | Pinecone (AWS Serverless) | Semantic search, 1024-dim index |
| **Embeddings** | multilingual-e5-large | Free local embeddings (HuggingFace) |
| **Frontend** | React + TypeScript + Vite | Voice UI with real-time transcript |
| **Backend Hosting** | AWS EC2 (t2.medium) | Docker containers for agent + token server |
| **Frontend Hosting** | Vercel | Static site deployment with CDN |
| **PDF Processing** | PyPDF + LangChain | Text extraction and chunking |

---

## Design Decisions & Assumptions

### Hosting Architecture

**Backend (AWS EC2)**:
- Deployed on t2.medium instance (required for ML embedding model)
- Two Docker containers: token server (port 8080) + LiveKit agent
- Vector embeddings generated on EC2 CPU (multilingual-e5-large model)
- **Assumption**: EC2 instance remains running for demos (can be stopped to save costs)

**Frontend (Vercel)**:
- Static React app deployed on Vercel's global CDN
- Environment variables configured in Vercel dashboard
- HTTPS enabled automatically

**Vector Store (Pinecone)**:
- Serverless index in us-east-1
- Pre-populated with 533 embedded chunks from PDF
- **Assumption**: Pinecone index exists before agent starts (must run ingestion script first)

### RAG Design

**Vector DB Choice: Pinecone**
- ✅ Serverless, no infrastructure management
- ✅ Low latency (~100-200ms for retrieval)
- ✅ Scales automatically
- ❌ Requires external service/API key
- **Trade-off**: Chose managed service over self-hosted (ChromaDB) for reliability

**Embeddings: multilingual-e5-large (Local)**
- ✅ FREE (no API costs for embeddings)
- ✅ Excellent multilingual support (Arabic + English)
- ✅ 1024 dimensions (good balance of quality and performance)
- ❌ Slower than API-based embeddings (runs on CPU)
- **Trade-off**: Chose cost savings over speed for embeddings

**Chunking Strategy: 1000 chars, 200 overlap**
- Tested 500, 1000, 1500 character chunks
- 1000 provides best balance of context vs. precision
- 200 char overlap prevents splitting key concepts
- **Assumption**: Book is well-structured with clear paragraph breaks

**Retrieval Strategy: Always-On RAG with Summarization**
- RAG triggered for ALL questions (except greetings)
- GPT-4o-mini summarizes retrieved context to 2-3 sentences
- If irrelevant, agent falls back to general knowledge
- **Rationale**: Better to always check book first, let LLM decide relevance

**Top-K: 5 results**
- Tested K=3,5,7
- K=5 provides sufficient context without noise
- ~5000 characters raw → summarized to ~200 characters
- **Configurable** via `TOP_K_RESULTS` environment variable

### LiveKit Agent Design

**Voice Pipeline**:
- **STT**: OpenAI Whisper (best multilingual accuracy)
- **LLM**: GPT-5.1 (latest model, handles complex Islamic scholarship)
- **TTS**: OpenAI TTS with 'alloy' voice (clear, natural)
- **VAD**: Silero (accurate, lightweight, open-source)

**Agent Architecture**:
- Subclass of `Agent` with custom `on_user_turn_completed` hook
- Hook intercepts user messages before LLM processing
- Injects RAG context dynamically based on query
- Function tools registered for narrator/classification lookups

**Trade-offs**:
- ✅ High-quality responses (GPT-5.1)
- ✅ Accurate transcription (Whisper)
- ❌ Higher cost (~$0.10-0.30 per 10-min conversation)
- ❌ Vendor lock-in to OpenAI ecosystem
- **Assumption**: Demo usage, not high-volume production

### Custom Tools

**Tool 1: `get_narrator_info()`**
- Simulated database of famous hadith narrators
- Returns: Full name, reliability grade (Thiqa/Da'if), era, works
- **Limitation**: Only 5 pre-loaded narrators (Bukhari, Muslim, Abu Hurairah, Tirmidhi, Ibn Majah)
- **Production improvement**: Connect to comprehensive narrator database

**Tool 2: `get_hadith_classification()`**
- Explains authenticity classifications (Sahih, Hasan, Da'if, Mawdu, Mutawatir)
- Includes Arabic terms with English translations
- **Assumption**: User asks in English (tool doesn't handle pure Arabic queries)

**Function Calling**:
- Uses LiveKit's `@function_tool` decorator
- LLM automatically decides when to invoke tools
- **Limitation**: Tools are supplementary, not comprehensive hadith reference

### Known Limitations

1. **RAG Accuracy**:
   - Depends on PDF text quality (assumed well-formatted, not scanned images)
   - Chunking may occasionally split related concepts across chunks

2. **Language Support**:
   - Agent responds in English only (TTS doesn't support Arabic)
   - Understands Arabic terminology but speaks it with English pronunciation

3. **Scalability**:
   - Single EC2 instance (no auto-scaling configured)
   - Not designed for concurrent users at scale

4. **Cost**:
   - GPT-5.1 usage can be expensive (~$0.10-0.30 per conversation)
   - EC2 t2.medium costs ~$34/month if running 24/7

5. **Security**:
   - API keys stored in `.env` (production should use AWS Secrets Manager)
   - CORS set to allow all origins (should restrict to frontend domain in production)


---

## Deployment Architecture

### Current Setup

**Frontend**: Deployed on Vercel (https://usool-hadith-voice-tutor.vercel.app)
- Global CDN for fast loading
- Automatic HTTPS
- Environment variables configured in Vercel dashboard

**Backend**: Deployed on AWS EC2 (http://52.87.184.116:8080)
- Ubuntu 22.04 on t2.medium instance
- Docker containers for token server and LiveKit agent
- Security group allows ports 22 (SSH) and 8080 (Token API)

**Vector Database**: Pinecone Serverless (us-east-1)
- 533 embedded chunks from Usool al-Hadith PDF
- 1024-dimensional vectors
- Accessible via API from EC2

**Voice Infrastructure**: LiveKit Cloud
- Managed WebRTC signaling and media servers
- Global edge network for low latency

---

## Future Improvements

### Smart Arabic Transliteration Detection and Voice Switching

**Enhancement**: Implement intelligent detection of Arabic terms and dynamic voice synthesis switching

**Current Limitation**:
- The agent currently uses English TTS for all responses, including Arabic terminology
- Arabic words are pronounced with English phonetics, which can sound unnatural
- Users may type Arabic terms using English transliteration (e.g., "hadith" instead of "حديث")

**Proposed Solution**:
1. **Transliteration Detection Layer**:
   - Detect when users type Arabic words using English characters (e.g., "sahih", "isnad", "hadith")
   - Maintain a dictionary of common Islamic terminology with standard transliterations
   - Convert detected transliterations to Arabic script for improved semantic search

2. **Dynamic Voice Synthesis**:
   - Integrate Arabic TTS engine alongside English TTS
   - Parse agent responses to identify Arabic terms and phrases
   - Switch to Arabic voice synthesis for Arabic content, English for explanations
   - Seamless blending of both languages in a single response

3. **Benefits**:
   - More authentic pronunciation of Islamic terminology
   - Improved learning experience for students studying Arabic terms
   - Better semantic matching in RAG retrieval when users use transliterated queries
   - More natural multilingual conversation flow

**Implementation Approach**:
- Use Arabic transliteration library (e.g., `python-arabic-reshaper`, `pyarabic`)
- Integrate Azure TTS or Google Cloud TTS for native Arabic speech synthesis
- Apply text segmentation to identify Arabic vs. English segments in responses
- Stream mixed-language audio in real-time via LiveKit

This enhancement would significantly improve the authenticity and educational value of the voice tutor for Islamic studies.

---

## AI Tools Disclosure

The following AI tools were used in development:
- **Claude**

---

## Project Structure

```
bluejay/
├── backend/                    # Python backend (deployed on AWS EC2)
│   ├── agent.py               # LiveKit voice agent
│   ├── rag_service.py         # RAG system with Pinecone
│   ├── ingest_pdf.py          # PDF embedding pipeline
│   ├── tools.py               # Custom function tools
│   ├── token_server.py        # Token generation API
│   ├── requirements.txt       # Python dependencies
│   └── Dockerfile            # Container configuration
│
├── frontend/                  # React frontend (deployed on Vercel)
│   ├── src/
│   │   ├── App.tsx           # Main UI component
│   │   ├── App.css           # Styling
│   │   └── vite-env.d.ts     # TypeScript definitions
│   └── package.json          # Node dependencies
│
├── usool-al-hadith.pdf       # Source PDF for RAG (165 pages)
├── README.md                 # This file
├── DESIGN_DECISIONS.md       # Detailed technical rationale
└── AWS_DEPLOYMENT.md         # Deployment guides
```

---

## Summary

This project demonstrates a production-ready RAG-enabled voice agent that:
- ✅ Integrates LiveKit for real-time voice communication
- ✅ Uses Pinecone + LangChain for semantic search over a 165-page PDF
- ✅ Implements intelligent summarization to optimize for voice UX
- ✅ Provides custom tools via function calling
- ✅ Deploys on AWS (backend) + Vercel (frontend) for public accessibility
- ✅ Handles both English and Arabic terminology
- ✅ Maintains cultural authenticity while leveraging cutting-edge AI

**Built with attention to:**
- Technical excellence (modern APIs, proper error handling)
- User experience (concise voice responses, real-time transcript)
- Cultural sensitivity (respectful representation of Islamic scholarship)
- Cost efficiency (free local embeddings, optimized token usage)
- Deployment readiness (Docker, cloud hosting, environment configuration)

---

**Developed by**: [Your Name]
**For**: Bluejay Take-Home Interview
**Date**: November 2025
