# Multi-Tenant RAG Platform (AWS Deployed)
A production-oriented RAG platform where users can upload, organise and query their own documents through multiple chats and folders with persistent memory.
> **Note:** The backend is the focus of this project and is entirely manually coded. The frontend (Vite + React) is very minimal and entirely AI-generated

### Key Features

- 🔐 User authentication with Clerk
- 👤 Multi-tenant user data isolation
- 📁 Create, rename and delete folders (CRUD)
- 📄 Upload, process and delete PDF, DOCX, TXT documents and more...
- 💬 Multiple chats per folder with persistent chat history
- 🧠 LLM-based intent classification to determine whether retrieval is required
- 🔎 Hybrid vector + PostgreSQL full-text search
- 🎯 Cohere reranking of retrieved chunks
- 🤖 LLM answer generation using retrieved context
- ☁️ AWS deployment with S3 file storage and Supabase PostgreSQL db
- 🗄️ Persistent application and vector data in Supabase PostgreSQL/PGVector
  

## Demo

The app has been deployed using AWS, try the link and check the deployment architecture listed below:
> **Note:** App may be undeployed due to AWS costs, if so take a look at the demo video or try the installation instructions below

http://new-rag-alb1-1227556087.eu-west-2.elb.amazonaws.com

https://github.com/user-attachments/assets/5627fe6f-0cc3-4914-8f5e-b9a22035e0c0

## App Architecture and Workflow
<img width="1402" height="377" alt="Screenshot 2026-09-24 190304" src="https://github.com/user-attachments/assets/10273a0f-8a79-4ab1-8483-172705841d59" />

The RAG aspect of this project consists of two main pipelines: 
- Ingestion: takes user files to be queried against
- Retrieval: allows users to query their uploaded files if needed

### Ingestion
1. User uploads document
2. File uploaded to AWS S3 file storage
3. Backend downloads the filestream from S3
4. Docling converts the filestream to markdown
5. LlamaIndex chunks the markdown (default Llamaindex token-split SentenceSplitter used)
6. Chunks are embedded (OpenAI embedding model is used) and inserted into Postgres, with a text tsvector column populated for hybrid search, and another column is populated with the text for each chunk
7. Because the folder_id is not set yet (which is needed to for retrieval later), a follow up SQL execution tags the newly inserted rows with folder_id,
   matched via the doc's S3 key stored in chunk metadata

### Retrieval
1. Connect to Postgres/PGVector database
2. User query is vector embedded using the same OpenAI embedding model as the ingestion workflow
3. Metadata filter is included in search to restrict retrieval to users current folder (one table includes every user and their folders document data)
4. Hybrid search is used to retrieve top 10 results (vector search using query embedding + Postgres text search using raw user query search)
5. Cohere reranks the 10 chunks and return the top 3
6. Top 3 chunks are passed to output LLM as context

### Database Schema
<img width="800" height="500" alt="Screenshot 2026-09-22 120738" src="https://github.com/user-attachments/assets/ac5c6700-cc10-4ae1-aef5-5d3befeab091" />

### Deployment
<img width="800" height="500" alt="Screenshot 2026-09-23 210402" src="https://github.com/user-attachments/assets/8a46cdd3-ec79-4297-82c3-809294494b29" />


## Currently working on
- Adding AI evaluation to test quality of RAG output
- Observability and latency/cost tracking
- Asynchronous document ingestion
- Multimodal document ingestion: images, tables and page layouts
- Upload multiple file at once
- Guardrails, usage limits and cost controls

## How to install
### Prerequisites
 
- Python 3.11
- Node.js 18+
- PostgreSQL with the `pgvector` extension enabled
- Accounts/API keys for Clerk, OpenAI, Cohere
### Backend
 
```bash
cd backend
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn src.router:app --reload
```
 
### Frontend
 
```bash
cd frontend
npm install
cp .env.example .env   # set VITE_CLERK_PUBLISHABLE_KEY and VITE_API_BASE_URL
npm run dev
```
