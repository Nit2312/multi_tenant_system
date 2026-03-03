# Operations AI Copilot (Flask RAG)

A Flask-based Retrieval-Augmented Generation (RAG) app that answers elevator maintenance and troubleshooting questions using Astra DB vector search and Groq-hosted Llama 4.

## Features

- Web UI with chat experience
- Astra DB vector store for retrieval
- Groq LLM (Llama 4 Maverick) for responses
- Hugging Face Inference API embeddings
- Simple ingestion script for Excel data

## Tech Stack

- Flask + Flask-CORS
- LangChain
- Astra DB Vector Store
- Groq LLM
- Hugging Face Embeddings

## Project Structure

- [app.py](app.py) — Vercel entrypoint
- [api/app.py](api/app.py) — Flask API + RAG chain
- [ingest_astra.py](ingest_astra.py) — Data ingestion
- [templates/index.html](templates/index.html) — UI
- [static/](static) — Frontend assets


# multi_tenant_system
