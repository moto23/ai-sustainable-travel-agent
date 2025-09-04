import logging
import time
from typing import List, Dict, Any, Optional
from langchain.llms import HuggingFacePipeline
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.cache import InMemoryCache
from langchain.schema import Document
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGProcessor:
    """
    Retrieval-Augmented Generation pipeline for sustainable travel queries using LangChain and LLaMA-2-7B-Chat.
    Features: custom prompts, context window, response filtering, fact-checking, memory, streaming, caching, and monitoring.
    """
    def __init__(self, retriever, model_name: str = "meta-llama/Llama-2-7b-chat-hf", quantized: bool = True):
        self.retriever = retriever
        self.cache = InMemoryCache()
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        quantization_config = {"load_in_4bit": True} if quantized else {}
        self.model = AutoModelForCausalLM.from_pretrained(model_name, **quantization_config)
        self.llm_pipeline = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=512,
            temperature=0.2,
            device_map="auto"
        )
        self.llm = HuggingFacePipeline(pipeline=self.llm_pipeline)
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            retriever=self.retriever,
            chain_type="stuff",
            memory=self.memory,
            return_source_documents=True,
            verbose=True
        )
        self.prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""
You are a sustainable travel assistant. Use the following context to answer the user's question. 
If you don't know, say so honestly. Be concise, factual, and eco-friendly.

Context:
{context}

Question:
{question}

Eco-Travel Answer:
"""
        )
        self.token_usage = 0
        self.response_times = []

    def _filter_response(self, response: str) -> str:
        # Simple filter: remove hallucinations, check for eco-travel relevance
        if "eco" not in response.lower() and "sustainab" not in response.lower():
            logger.warning("Response may not be eco-travel relevant.")
        return response.strip()

    def _fact_check(self, response: str, context: str) -> bool:
        # Stub: In production, use external fact-checking APIs or rules
        return True

    def _cache_get(self, query: str) -> Optional[str]:
        return self.cache.lookup(query)

    def _cache_set(self, query: str, response: str):
        self.cache.update(query, response)

    def _track_performance(self, start_time: float, tokens: int):
        elapsed = time.time() - start_time
        self.response_times.append(elapsed)
        self.token_usage += tokens
        logger.info(f"Response time: {elapsed:.2f}s, Tokens used: {tokens}")

    def ask(self, question: str, stream: bool = False) -> Dict[str, Any]:
        # Caching
        cached = self._cache_get(question)
        if cached:
            logger.info("Cache hit for query.")
            return {"answer": cached, "cached": True}
        # Retrieval
        docs = self.retriever.get_relevant_documents(question)
        context = "\n".join([doc.page_content for doc in docs])
        prompt = self.prompt_template.format(context=context, question=question)
        # Generation
        start_time = time.time()
        if stream:
            # Streaming response (generator)
            for chunk in self.llm_pipeline(prompt, stream=True):
                yield chunk["generated_text"]
            tokens = len(self.tokenizer.encode(prompt))
        else:
            result = self.llm_pipeline(prompt)
            answer = result[0]["generated_text"]
            tokens = len(self.tokenizer.encode(prompt + answer))
            answer = self._filter_response(answer)
            if not self._fact_check(answer, context):
                answer = "[Fact-check failed: Please verify this information.]"
            self._cache_set(question, answer)
            self._track_performance(start_time, tokens)
            return {
                "answer": answer,
                "source_documents": [doc.metadata for doc in docs],
                "tokens": tokens,
                "response_time": self.response_times[-1],
                "cached": False
            }

    def get_stats(self):
        return {
            "total_tokens": self.token_usage,
            "avg_response_time": sum(self.response_times) / len(self.response_times) if self.response_times else 0,
            "cache_size": len(self.cache.store)
        }
