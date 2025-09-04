# langchain_service/langchain_pipeline.py
import os
import logging
from typing import Dict, Any, List
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.schema import Document
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleSustainableTravelRAG:
    """Simplified RAG service for sustainable travel"""
    
    def __init__(self):
        self.vectorstore = None
        self.embeddings = None
        self._initialize()
    
    def _initialize(self):
        """Initialize embeddings and load knowledge base"""
        try:
            # Initialize embeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
            
            # Load knowledge base
            self._load_knowledge_base()
            logger.info("Sustainable Travel RAG initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
    
    def _load_knowledge_base(self):
        """Load sustainable travel knowledge"""
        documents = [
            Document(
                page_content="""Costa Rica is a world leader in sustainable tourism with 99% renewable energy, 
                over 25% of land protected as national parks, and comprehensive eco-certification programs. 
                The country pioneered Payment for Ecosystem Services and carbon neutrality goals. 
                Best practices: stay in eco-lodges, use public transport, support local communities, 
                participate in conservation tours, visit during green season.""",
                metadata={"country": "costa_rica", "sustainability_score": 9.5, "category": "destination"}
            ),
            
            Document(
                page_content="""Iceland operates on 100% renewable energy from geothermal and hydroelectric sources. 
                The country promotes responsible tourism through the Icelandic Pledge and strict environmental regulations. 
                Sustainable practices: use geothermal facilities, follow marked trails, support local businesses, 
                choose eco-friendly accommodations, use public transport, respect fragile ecosystems.""",
                metadata={"country": "iceland", "sustainability_score": 9.2, "category": "destination"}
            ),
            
            Document(
                page_content="""Transportation accounts for 75% of travel emissions. Sustainable options: 
                trains reduce emissions by 75% compared to flying, direct flights cut emissions by 25%, 
                electric buses and public transport, cycling and walking for local exploration, 
                electric vehicle rentals. For trips under 1000km, ground transport is preferable.""",
                metadata={"category": "transportation", "emission_reduction": "up_to_75_percent"}
            ),
            
            Document(
                page_content="""Sustainable accommodations include eco-certified hotels with renewable energy, 
                water conservation systems, waste reduction programs, and local sourcing. Look for Green Key, 
                LEED, or local eco-certifications. Choose eco-lodges, farm stays, sustainable hostels, 
                and properties that employ local staff and support communities.""",
                metadata={"category": "accommodation", "certifications": ["green_key", "leed"]}
            ),
            
            Document(
                page_content="""Budget sustainable travel strategies: travel during shoulder seasons for 30-50% savings, 
                use public transportation, stay in eco-hostels or guesthouses, eat at local restaurants, 
                choose free outdoor activities like hiking, book accommodations with kitchens, 
                use travel apps for sustainable tour discounts.""",
                metadata={"category": "budget", "savings": "30_to_50_percent"}
            ),
            
            Document(
                page_content="""Carbon footprint by transport mode per km: flights 255g CO2, cars 120g CO2, 
                trains 35g CO2, buses 25g CO2. Reduction strategies: choose direct flights, pack light, 
                stay longer in destinations, use ground transport for short distances, 
                offset through Gold Standard or Verified Carbon Standard programs.""",
                metadata={"category": "carbon_footprint", "transport_emissions": True}
            )
        ]
        
        if self.embeddings:
            self.vectorstore = FAISS.from_documents(documents, self.embeddings)
            logger.info("Knowledge base loaded into vector store")
    
    def get_travel_advice(self, question: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get sustainable travel advice"""
        try:
            if not self.vectorstore:
                return self._fallback_response(question)
            
            # Search for relevant documents
            docs = self.vectorstore.similarity_search(question, k=3)
            
            if not docs:
                return self._fallback_response(question)
            
            # Combine content from retrieved documents
            context = "\n".join([doc.page_content for doc in docs])
            
            # Generate response based on context
            response = self._generate_response(question, context, user_context)
            
            return {
                "answer": response,
                "sources": [doc.metadata for doc in docs],
                "confidence": 0.8 if len(docs) >= 2 else 0.6
            }
            
        except Exception as e:
            logger.error(f"Error in get_travel_advice: {e}")
            return self._fallback_response(question)
    
    def _generate_response(self, question: str, context: str, user_context: Dict[str, Any] = None) -> str:
        """Generate response based on retrieved context"""
        question_lower = question.lower()
        
        # Context-aware responses
        if 'destination' in question_lower or 'where' in question_lower:
            if 'costa rica' in context.lower():
                return "Costa Rica is an excellent choice for sustainable travel! It runs on 99% renewable energy and has 25% of its land protected as national parks. Stay in eco-lodges, use public transport, and participate in conservation tours."
            elif 'iceland' in context.lower():
                return "Iceland is perfect for eco-conscious travelers! The country operates on 100% renewable energy from geothermal sources. Follow the Icelandic Pledge, stay on marked trails, and use geothermal facilities."
        
        elif any(word in question_lower for word in ['transport', 'flight', 'train']):
            return "For sustainable transportation: trains reduce emissions by 75% compared to flying. Choose direct flights when flying is necessary, use public transport at your destination, and consider electric vehicle rentals. For trips under 1000km, ground transport is more sustainable."
        
        elif any(word in question_lower for word in ['accommodation', 'hotel', 'stay']):
            return "Choose sustainable accommodations with eco-certifications like Green Key or LEED. Look for properties with renewable energy, water conservation, waste reduction, and local sourcing. Eco-lodges, farm stays, and sustainable hostels are great options."
        
        elif any(word in question_lower for word in ['budget', 'cheap', 'affordable']):
            return "Budget sustainable travel tips: travel during shoulder seasons for 30-50% savings, use public transportation, stay in eco-hostels, eat at local restaurants, and choose free outdoor activities like hiking."
        
        elif any(word in question_lower for word in ['carbon', 'footprint', 'emissions']):
            return "Transportation emissions by mode per km: flights 255g CO2, cars 120g CO2, trains 35g CO2, buses 25g CO2. Reduce your footprint by choosing direct flights, packing light, staying longer in destinations, and offsetting through verified programs."
        
        # Default response using context
        return f"Based on sustainable travel best practices: {context[:200]}..." if len(context) > 200 else context
    
    def _fallback_response(self, question: str) -> Dict[str, Any]:
        """Fallback when vectorstore is unavailable"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['destination', 'where', 'place']):
            response = "Top sustainable destinations include Costa Rica (renewable energy leader), Iceland (geothermal power), New Zealand (conservation focus), and countries with strong environmental policies."
        elif any(word in question_lower for word in ['transport', 'flight', 'travel']):
            response = "For sustainable transport: trains reduce emissions by 75% vs flights, choose direct flights, use public transport, walk/cycle locally, and consider electric rentals."
        elif any(word in question_lower for word in ['accommodation', 'hotel']):
            response = "Choose eco-certified accommodations with Green Key or LEED certification, renewable energy, water conservation, and local sourcing."
        else:
            response = "For sustainable travel: minimize flights, use public transport, support local businesses, choose eco-certified accommodations, pack light, and respect environments."
        
        return {
            "answer": response,
            "sources": [],
            "confidence": 0.5
        }

# Global instance for easy import
rag_service = SimpleSustainableTravelRAG()

# Simple function for backward compatibility
def get_langchain_response(query: str) -> str:
    """Simple function interface for basic usage"""
    result = rag_service.get_travel_advice(query)
    return result.get("answer", "I'm here to help with sustainable travel questions!")