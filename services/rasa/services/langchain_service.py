# rasa_bot/services/langchain_service.py
import os
import logging
from typing import List, Dict, Any, Optional
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Pinecone as PineconeVectorStore
from langchain.llms import HuggingFacePipeline
from langchain.chains import RetrievalQA, ConversationalRetrievalChain
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import pinecone
from sentence_transformers import SentenceTransformer
import torch
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class SustainableTravelRAGService:
    """Enhanced RAG service for sustainable travel recommendations"""
    
    def __init__(self):
        self.embedding_model = None
        self.vectorstore = None
        self.llm = None
        self.qa_chain = None
        self.memory = ConversationBufferWindowMemory(
            k=10,
            memory_key="chat_history",
            return_messages=True
        )
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all RAG components"""
        try:
            # Initialize embeddings
            self._init_embeddings()
            # Initialize vector store
            self._init_vectorstore()
            # Initialize LLM
            self._init_llm()
            # Initialize QA chain
            self._init_qa_chain()
            # Load sustainable travel knowledge
            self._load_travel_knowledge()
            
            logger.info("SustainableTravelRAGService initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            raise
    
    def _init_embeddings(self):
        """Initialize embedding model"""
        model_name = os.getenv('EMBEDDING_MODEL_NAME', 'sentence-transformers/all-MiniLM-L6-v2')
        device = os.getenv('EMBEDDING_DEVICE', 'cpu')
        
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': device},
            encode_kwargs={'normalize_embeddings': True}
        )
        logger.info(f"Embeddings initialized with model: {model_name}")
    
    def _init_vectorstore(self):
        """Initialize Pinecone vector store"""
        api_key = os.getenv('PINECONE_API_KEY')
        environment = os.getenv('PINECONE_ENVIRONMENT', 'gcp-starter')
        index_name = os.getenv('PINECONE_INDEX_NAME', 'sustainable-travel-knowledge')
        
        if not api_key:
            logger.warning("No Pinecone API key found, using in-memory vector store")
            from langchain.vectorstores import FAISS
            self.vectorstore = None  # Will be initialized when documents are added
            return
        
        try:
            pinecone.init(api_key=api_key, environment=environment)
            
            # Create index if it doesn't exist
            if index_name not in pinecone.list_indexes():
                dimension = int(os.getenv('PINECONE_DIMENSION', '384'))
                metric = os.getenv('PINECONE_METRIC', 'cosine')
                
                pinecone.create_index(
                    name=index_name,
                    dimension=dimension,
                    metric=metric
                )
                logger.info(f"Created new Pinecone index: {index_name}")
            
            self.vectorstore = PineconeVectorStore.from_existing_index(
                index_name=index_name,
                embedding=self.embedding_model
            )
            logger.info(f"Connected to Pinecone index: {index_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            # Fallback to FAISS
            from langchain.vectorstores import FAISS
            self.vectorstore = None
    
    def _init_llm(self):
        """Initialize Hugging Face LLM"""
        model_name = os.getenv('HUGGINGFACE_MODEL', 'meta-llama/Llama-2-7b-chat-hf')
        
        try:
            # Check if CUDA is available
            device = 0 if torch.cuda.is_available() else -1
            
            # Load tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Create text generation pipeline
            text_gen_pipeline = pipeline(
                "text-generation",
                model=model_name,
                tokenizer=tokenizer,
                max_length=int(os.getenv('MODEL_MAX_LENGTH', '4096')),
                temperature=float(os.getenv('TEMPERATURE', '0.7')),
                do_sample=True,
                device=device
            )
            
            self.llm = HuggingFacePipeline(
                pipeline=text_gen_pipeline,
                model_kwargs={
                    "temperature": float(os.getenv('TEMPERATURE', '0.7')),
                    "max_length": int(os.getenv('MAX_TOKENS', '512'))
                }
            )
            
            logger.info(f"LLM initialized with model: {model_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            # Fallback to a smaller model or OpenAI
            try:
                from langchain.llms import OpenAI
                self.llm = OpenAI(
                    temperature=float(os.getenv('TEMPERATURE', '0.7')),
                    max_tokens=int(os.getenv('MAX_TOKENS', '512'))
                )
                logger.info("Fallback to OpenAI LLM")
            except:
                raise Exception("No LLM available")
    
    def _init_qa_chain(self):
        """Initialize QA chain with custom prompt"""
        
        # Custom prompt for sustainable travel
        prompt_template = """
        You are an expert sustainable travel advisor with deep knowledge of eco-friendly tourism, carbon footprint reduction, and responsible travel practices.
        
        Context information:
        {context}
        
        Chat History:
        {chat_history}
        
        Human: {question}
        
        Please provide helpful, accurate, and actionable advice focusing on:
        - Sustainable travel options and eco-friendly practices
        - Carbon footprint reduction strategies
        - Local community support and responsible tourism
        - Environmental conservation during travel
        - Budget-conscious sustainable travel tips
        
        If the question is not related to travel or sustainability, politely redirect the conversation back to sustainable travel topics.
        
        Assistant:"""
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "chat_history", "question"]
        )
        
        if self.vectorstore and self.llm:
            self.qa_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.vectorstore.as_retriever(
                    search_kwargs={
                        "k": int(os.getenv('TOP_K_RETRIEVAL', '5'))
                    }
                ),
                memory=self.memory,
                combine_docs_chain_kwargs={"prompt": PROMPT},
                return_source_documents=True,
                verbose=True
            )
            logger.info("QA chain initialized successfully")
    
    def _load_travel_knowledge(self):
        """Load sustainable travel knowledge base"""
        knowledge_documents = [
            # Sustainable Destinations
            Document(
                page_content="""Costa Rica is a leading sustainable tourism destination with over 99% renewable energy, 
                extensive national parks covering 25% of the country, and strong eco-certification programs for accommodations. 
                The country pioneered Payment for Ecosystem Services and has reversed deforestation. Best practices include 
                staying in eco-certified lodges, using public transport, supporting local communities, and participating in 
                conservation activities.""",
                metadata={"category": "destinations", "country": "costa_rica", "sustainability_score": 9.5}
            ),
            
            Document(
                page_content="""Iceland runs entirely on renewable energy (geothermal and hydroelectric), has strict 
                environmental regulations, and promotes responsible tourism through the Icelandic Pledge. Sustainable 
                practices include using geothermal heating, electric transportation, staying on marked paths, and 
                supporting local communities. The country has excellent public transport and eco-friendly accommodations.""",
                metadata={"category": "destinations", "country": "iceland", "sustainability_score": 9.2}
            ),
            
            # Transportation
            Document(
                page_content="""Transportation is the largest source of travel emissions. Sustainable options include: 
                1) Train travel reduces emissions by 75% vs flying 2) Direct flights reduce emissions by 25% vs connecting 
                3) Electric buses and public transport 4) Cycling and walking for local exploration 5) Electric vehicle 
                rentals 6) Carpooling and ridesharing. For long distances, consider overland routes and longer stays 
                to offset transportation impact.""",
                metadata={"category": "transportation", "emission_reduction": "up_to_75_percent"}
            ),
            
            # Accommodations
            Document(
                page_content="""Sustainable accommodations include eco-certified hotels with renewable energy, water 
                conservation, waste reduction, and local sourcing. Look for certifications like Green Key, LEED, or 
                local eco-labels. Alternatives include eco-lodges, farm stays, hostels with sustainability programs, 
                and vacation rentals with green practices. Avoid daily towel/sheet changes, use refillable water bottles, 
                and support properties that employ local staff.""",
                metadata={"category": "accommodations", "certification_types": "green_key,leed,local_eco_labels"}
            ),
            
            # Carbon Footprint
            Document(
                page_content="""Average carbon footprints by transport: Domestic flight: 255g CO2/km, International flight: 
                195g CO2/km, Car: 120g CO2/km, Train: 35g CO2/km, Bus: 25g CO2/km. Reduction strategies: Choose direct 
                flights, pack light, stay longer, use ground transport for <1000km, offset through verified programs like 
                Gold Standard or Verified Carbon Standard. A typical 2-week European trip generates 2-4 tons CO2.""",
                metadata={"category": "carbon_footprint", "unit": "grams_co2_per_km"}
            ),
            
            # Budget Tips
            Document(
                page_content="""Budget sustainable travel tips: 1) Travel during shoulder seasons for lower prices and 
                less crowding 2) Use public transport and walk/cycle 3) Stay in hostels, guesthouses, or eco-lodges 
                4) Eat at local restaurants and markets 5) Free activities like hiking, beaches, museums on free days 
                6) Book accommodation with kitchens 7) Use apps for discounts on sustainable tours 8) Consider slow 
                travel to reduce transport costs.""",
                metadata={"category": "budget", "cost_reduction": "30_to_50_percent"}
            )
        ]
        
        if self.vectorstore is None and self.embedding_model:
            # Use FAISS as fallback
            from langchain.vectorstores import FAISS
            self.vectorstore = FAISS.from_documents(
                knowledge_documents,
                self.embedding_model
            )
            logger.info("Loaded travel knowledge into FAISS vector store")
        elif self.vectorstore:
            # Add to existing Pinecone index
            texts = [doc.page_content for doc in knowledge_documents]
            metadatas = [doc.metadata for doc in knowledge_documents]
            self.vectorstore.add_texts(texts, metadatas)
            logger.info("Loaded travel knowledge into Pinecone vector store")
    
    def get_travel_advice(self, question: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get travel advice using RAG"""
        try:
            if not self.qa_chain:
                return {
                    "answer": "I'm sorry, but my knowledge base is not available right now. However, I can provide basic sustainable travel advice based on general principles.",
                    "sources": [],
                    "confidence": 0.5
                }
            
            # Enhance question with context
            enhanced_question = self._enhance_question(question, user_context)
            
            # Get answer from RAG chain
            result = self.qa_chain({"question": enhanced_question})
            
            return {
                "answer": result.get("answer", ""),
                "sources": [doc.metadata for doc in result.get("source_documents", [])],
                "confidence": self._calculate_confidence(result),
                "chat_history": self.memory.chat_memory.messages[-10:]  # Last 10 messages
            }
            
        except Exception as e:
            logger.error(f"Error getting travel advice: {e}")
            return {
                "answer": f"I encountered an error while processing your question. Please try rephrasing it.",
                "sources": [],
                "confidence": 0.0
            }
    
    def _enhance_question(self, question: str, user_context: Dict[str, Any] = None) -> str:
        """Enhance question with user context"""
        if not user_context:
            return question
        
        context_parts = []
        if user_context.get("destination"):
            context_parts.append(f"traveling to {user_context['destination']}")
        if user_context.get("budget"):
            context_parts.append(f"with a budget of {user_context['budget']}")
        if user_context.get("duration"):
            context_parts.append(f"for {user_context['duration']}")
        if user_context.get("interests"):
            context_parts.append(f"interested in {', '.join(user_context['interests'])}")
        
        if context_parts:
            return f"{question} (Context: I am {', '.join(context_parts)})"
        return question
    
    def _calculate_confidence(self, result: Dict[str, Any]) -> float:
        """Calculate confidence score based on retrieval results"""
        source_docs = result.get("source_documents", [])
        if not source_docs:
            return 0.3
        
        # Basic confidence based on number of sources and answer length
        num_sources = len(source_docs)
        answer_length = len(result.get("answer", ""))
        
        confidence = min(0.9, 0.5 + (num_sources * 0.1) + (min(answer_length, 500) / 1000))
        return round(confidence, 2)
    
    def add_travel_document(self, content: str, metadata: Dict[str, Any]):
        """Add new travel document to knowledge base"""
        if self.vectorstore and self.embedding_model:
            self.vectorstore.add_texts([content], [metadata])
            logger.info(f"Added new document to knowledge base: {metadata}")
    
    def clear_conversation_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
        logger.info("Conversation memory cleared")

# Initialize global service instance
rag_service = SustainableTravelRAGService()