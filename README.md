# AI-Powered Sustainable Travel Agent 🌍

This is a sophisticated, AI-driven travel assistant built with Rasa and Docker. It functions as an intelligent agent capable of understanding complex, natural language queries to help users plan eco-friendly trips. The agent uses a multi-tool architecture to integrate with real-time, external APIs and provide comprehensive, context-aware travel plans.

## Key Features

-   **🧠 Intelligent Conversational AI:** Built on a robust Rasa framework, the agent handles multi-turn conversations, remembers context using slots, and asks clarifying questions to resolve ambiguity (e.g., "London, UK or London, Ontario?").
-   **🛠️ Multi-Tool Integration:** The agent dynamically selects the correct tool for any user query:
    -   **📍 Google Maps Platform:** Utilizes the Directions, Geocoding, and Places APIs for real-time route planning, travel time estimation, and landmark discovery.
    -   **☀️ OpenWeatherMap API:** Fetches live weather forecasts for any destination worldwide.
    -   **📚 RAG Knowledge Base:** Implements a Retrieval-Augmented Generation pipeline with Pinecone and Sentence-Transformers to answer complex questions about sustainable travel practices.
-   **🐳 Containerized & Scalable:** The entire multi-service application (Rasa, Action Server, APIs, RAG) is fully containerized with Docker and orchestrated with Docker Compose, ensuring a clean, reproducible, and professional deployment.

## Tech Stack

-   **Core:** Python, Rasa, Docker, Docker Compose
-   **AI & NLP:** Rasa NLU, Sentence-Transformers, Pinecone (Vector DB)
-   **APIs:** Google Maps Platform (Directions, Geocoding, Places), OpenWeatherMap, RESTful APIs
-   **Version Control:** Git

## 🚀 Getting Started

This project uses pre-built images from Docker Hub for a fast and reliable setup.

### Prerequisites

-   Docker and Docker Compose must be installed.
-   You need API keys for Google Maps and OpenWeatherMap.

### Setup

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/moto23/ai-sustainable-travel-agent.git](https://github.com/moto23/ai-sustainable-travel-agent.git)
    cd ai-sustainable-travel-agent.git
    ```
2.  **Create your environment file:**
    Create a `.env` file in the root directory and add your API keys.
    ```
    GOOGLE_PLACES_API_KEY=your_google_key
    OPENWEATHER_API_KEY=your_weather_key
    # ... and other keys as needed
    ```
3.  **Run the application:**
    This single command will download the pre-built images from Docker Hub and start all services.
    ```bash
    docker compose up
    ```
    The bot will be available at `http://localhost:5005`.

## Demo

*(This is where you should insert a GIF of your `chat.html` in action!)*

**Example `curl` commands:**

-   **Get a travel plan:**
    ```bash
    curl -X POST -H "Content-Type: application/json" -d '{"sender": "test_user", "message": "give me a plan to travel from Pune to Rajgad Fort"}' http://localhost:5005/webhooks/rest/webhook
    ```
-   **Start a multi-turn conversation:**
    ```bash
    curl -X POST -H "Content-Type: application/json" -d '{"sender": "test_user", "message": "find a hotel for me"}' http://localhost:5005/webhooks/rest/webhook
    ```
