# Multi-tenancy Enterprise Rag App
RAG platform where each user manages their own folder of documents and chats.

User data, folder data, document data, vector stores, chat data, messages are all stored in supabase
Users create their own login, Clerk was used for auth. Users can then create folders which contains documents to be queried within chats, users can have multiple chats per folder. Users can create, rename and delete folders, documents and chats. Many file types are supported such as pdf, txt, docx.

> **Note:** The backend is the focus of this project and is entirely manually coded. The frontend (Vite + React) is very minimal and entirely AI-generated
 
clerk used for authentication
user signs in, creates folders, multiple folders can be created, folders can be renamed or deleted
within folders you can upload multiple documents, create chats to query documents, chats can be renamed, deleted, documents can be deleted

search
initial user query is sent to intent classifier to see if rag vector search is needed or not, small gpt 5 nano model, pydantic is used
if query is normal search, query is sent to gpt llm model to return answer
if query needs rag search, llamaindex is used to take query and run a vector search and retrieve top chunks which are reranked using cohere, the context is then provided to a summarizer and that is used alongside the original user query to produce an output

ingestion


### Demo

The app has been deployed using AWS with the system architecture below, try the link below:

http://new-rag-alb1-1227556087.eu-west-2.elb.amazonaws.com

> **Note:** App may be undeployed due to AWS costs, if so there are installation instructions below


https://github.com/user-attachments/assets/5627fe6f-0cc3-4914-8f5e-b9a22035e0c0

## App Architecture and Workflow
The RAG aspect of this project consists of two main parts: the ingestion (which takes user files to be queried against), and the retrieval (which allows users to query their uploaded files if needed).

<img width="1402" height="377" alt="Screenshot 2026-09-24 190304" src="https://github.com/user-attachments/assets/10273a0f-8a79-4ab1-8483-172705841d59" />


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
6. Top 3 chunks are passed to output LLM as context rr  rrr

### Database Scheme
<img width="800" height="500" alt="Screenshot 2026-09-22 120738" src="https://github.com/user-attachments/assets/ac5c6700-cc10-4ae1-aef5-5d3befeab091" />

### Deployment
<img width="800" height="500" alt="Screenshot 2026-09-23 210402" src="https://github.com/user-attachments/assets/8a46cdd3-ec79-4297-82c3-809294494b29" />


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
