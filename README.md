# Sustainable Travel Planner

A production-ready platform for planning sustainable travel using Agentic AI and Retrieval-Augmented Generation (RAG).

## Project Structure

- `rasa_bot/` — Conversational AI powered by Rasa
- `rag_system/` — Retrieval-Augmented Generation system
- `apis/` — FastAPI-based microservices (weather, emissions, etc.)
- `monitoring/` — Monitoring and metrics (Prometheus, etc.)
- `docker/` — Dockerfiles and related assets

## Features
- Conversational travel planning with Rasa
- RAG for up-to-date, context-aware recommendations
- Integrations: OpenWeatherMap, Climatiq, Pinecone, HuggingFace
- FastAPI microservices for modular APIs
- Monitoring with Prometheus
- Production-ready Docker and orchestration

## Setup Instructions

1. **Clone the repository**
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment variables**
   - Copy `.env.example` to `.env` and fill in your API keys
4. **Run services**
   - Using Docker Compose:
     ```bash
     docker-compose up --build
     ```
5. **Access the platform**
   - Rasa Bot: [http://localhost:5005](http://localhost:5005)
   - APIs: [http://localhost:8000](http://localhost:8000)
   - Monitoring: [http://localhost:9090](http://localhost:9090)

## Contributing
Pull requests are welcome. For major changes, please open an issue first.

## License
[MIT](LICENSE)
