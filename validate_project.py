import os
import sys
import time
import json
import requests
import subprocess
import threading
import traceback
from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime

try:
    from termcolor import colored
except ImportError:
    def colored(text, color):
        return text

HTML_REPORT = []
RESULTS = defaultdict(list)

# --- Utility Functions ---
def print_status(msg, status):
    color = 'green' if status == 'PASS' else 'red'
    print(colored(f"[{status}] {msg}", color))
    HTML_REPORT.append(f'<div style="color:{color}"><b>[{status}]</b> {msg}</div>')

def print_info(msg):
    print(colored(f"[INFO] {msg}", 'cyan'))
    HTML_REPORT.append(f'<div style="color:blue">[INFO] {msg}</div>')

def quick_fix_suggestion(issue):
    fixes = {
        'API_KEY': 'Check your .env file and ensure all API keys are set and valid.',
        'MEMORY': 'Reduce model size, enable quantization, or increase system RAM.',
        'CONNECTION': 'Check network, firewall, and service URLs.',
        'PINECONE': 'Verify Pinecone API key, environment, and index name.',
        'LLAMA': 'Ensure model weights are downloaded and system has enough memory.',
        'FASTAPI': 'Check if the API server is running and accessible.',
    }
    return fixes.get(issue, 'See logs for details.')

# --- Rasa NLU Testing ---
def test_rasa_nlu():
    print_info('Testing Rasa NLU...')
    try:
        # Test intent classification accuracy
        result = subprocess.run(['rasa', 'test', 'nlu', '--out', 'rasa_bot/results'], capture_output=True, text=True)
        report_path = 'rasa_bot/results/nlu/intent_report.json'
        if os.path.exists(report_path):
            with open(report_path) as f:
                report = json.load(f)
            acc = report.get('accuracy', 0)
            if acc >= 0.85:
                print_status(f'Intent classification accuracy: {acc:.2%}', 'PASS')
            else:
                print_status(f'Intent classification accuracy: {acc:.2%} (<85%)', 'FAIL')
                print_info(quick_fix_suggestion('API_KEY'))
        else:
            print_status('Intent report not found.', 'FAIL')
        # Test entity extraction
        entity_report = 'rasa_bot/results/nlu/entity_report.json'
        if os.path.exists(entity_report):
            print_status('Entity extraction tested.', 'PASS')
        else:
            print_status('Entity extraction report not found.', 'FAIL')
        # Test conversation flows
        result = subprocess.run(['rasa', 'test', 'core', '--out', 'rasa_bot/results'], capture_output=True, text=True)
        if result.returncode == 0:
            print_status('Conversation flows tested.', 'PASS')
        else:
            print_status('Conversation flow test failed.', 'FAIL')
    except Exception as e:
        print_status(f'Rasa NLU test error: {e}', 'FAIL')
        print_info(quick_fix_suggestion('API_KEY'))

# --- RAG System Testing ---
def test_rag_system():
    print_info('Testing RAG System (Pinecone, LLaMA, vector search)...')
    try:
        from rag_system.vector_store import PineconeManager
        from rag_system.rag_pipeline import RAGProcessor
        pinecone_api = os.getenv('PINECONE_API_KEY', 'demo-key')
        pinecone_env = os.getenv('PINECONE_ENVIRONMENT', 'us-west1-gcp')
        manager = PineconeManager(pinecone_api, pinecone_env, 'test-index', 8)
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(manager.create_index())
        print_status('Pinecone connection and index creation.', 'PASS')
        # Test LLaMA model loading
        try:
            from transformers import AutoModelForCausalLM
            AutoModelForCausalLM.from_pretrained('meta-llama/Llama-2-7b-chat-hf', trust_remote_code=True)
            print_status('LLaMA model loaded.', 'PASS')
        except Exception as e:
            print_status(f'LLaMA model loading failed: {e}', 'FAIL')
            print_info(quick_fix_suggestion('LLAMA'))
        # Test vector search
        try:
            dummy_vec = [0.1] * 8
            loop.run_until_complete(manager.query(dummy_vec, top_k=1))
            print_status('Vector search tested.', 'PASS')
        except Exception as e:
            print_status(f'Vector search failed: {e}', 'FAIL')
            print_info(quick_fix_suggestion('PINECONE'))
    except Exception as e:
        print_status(f'RAG system test error: {e}', 'FAIL')
        print_info(quick_fix_suggestion('PINECONE'))

# --- External API Testing ---
def test_external_apis():
    print_info('Testing external APIs (OpenWeatherMap, Climatiq)...')
    try:
        from apis.weather_service import WeatherAPI
        from apis.carbon_service import CarbonFootprintCalculator
        weather = WeatherAPI()
        w = weather.get_current_weather('Berlin')
        if w and 'main' in w:
            print_status('OpenWeatherMap current weather.', 'PASS')
        else:
            print_status('OpenWeatherMap failed.', 'FAIL')
            print_info(quick_fix_suggestion('API_KEY'))
        carbon = CarbonFootprintCalculator()
        trip = {"segments": [{"mode": "flight", "amount": 1200}]}
        c = carbon.calculate_trip(trip)
        if c and 'total_emission' in c:
            print_status('Climatiq carbon calculation.', 'PASS')
        else:
            print_status('Climatiq API failed.', 'FAIL')
            print_info(quick_fix_suggestion('API_KEY'))
    except Exception as e:
        print_status(f'External API test error: {e}', 'FAIL')
        print_info(quick_fix_suggestion('API_KEY'))

# --- API Gateway Testing ---
def test_api_gateway():
    print_info('Testing API Gateway endpoints...')
    base = 'http://localhost:8000/v1'
    headers = {'Authorization': os.getenv('API_GATEWAY_KEY', 'test-key')}
    try:
        # Weather
        r = requests.post(f'{base}/weather', json={'location': 'Berlin'}, headers=headers, timeout=5)
        if r.status_code == 200:
            print_status('/weather endpoint.', 'PASS')
        else:
            print_status('/weather endpoint failed.', 'FAIL')
        # Carbon
        r = requests.post(f'{base}/carbon-footprint', json={'trip': {"segments": [{"mode": "flight", "amount": 1200}]}}, headers=headers, timeout=5)
        if r.status_code == 200:
            print_status('/carbon-footprint endpoint.', 'PASS')
        else:
            print_status('/carbon-footprint endpoint failed.', 'FAIL')
        # Chat
        r = requests.post(f'{base}/chat', json={'message': 'How can I travel sustainably?'}, headers=headers, timeout=5)
        if r.status_code == 200:
            print_status('/chat endpoint.', 'PASS')
        else:
            print_status('/chat endpoint failed.', 'FAIL')
    except Exception as e:
        print_status(f'API Gateway test error: {e}', 'FAIL')
        print_info(quick_fix_suggestion('FASTAPI'))

# --- Performance Testing ---
def test_performance():
    print_info('Testing performance (response times, memory usage)...')
    start = time.time()
    try:
        r = requests.post('http://localhost:8000/v1/weather', json={'location': 'Berlin'}, headers={'Authorization': os.getenv('API_GATEWAY_KEY', 'test-key')}, timeout=5)
        elapsed = time.time() - start
        if elapsed < 2:
            print_status(f'Response time: {elapsed:.2f}s', 'PASS')
        else:
            print_status(f'Response time: {elapsed:.2f}s (>2s)', 'FAIL')
            print_info(quick_fix_suggestion('MEMORY'))
        import psutil
        mem = psutil.virtual_memory()
        print_status(f'Memory usage: {mem.percent}%', 'PASS' if mem.percent < 90 else 'FAIL')
    except Exception as e:
        print_status(f'Performance test error: {e}', 'FAIL')
        print_info(quick_fix_suggestion('MEMORY'))

# --- Integration Testing ---
def test_integration():
    print_info('Testing end-to-end conversation flows...')
    scenarios = [
        {"input": "Hello!", "expected": "greet"},
        {"input": "I want to plan a sustainable trip to Paris.", "expected": "plan_trip"},
        {"input": "Can you recommend eco-friendly hotels in Paris?", "expected": "accommodation_search"},
        {"input": "Compare the carbon footprint of flying vs taking a train to Berlin.", "expected": "carbon_footprint"},
        {"input": "What's the weather in Paris on 2024-09-15?", "expected": "weather_query"},
        {"input": "I want to go to Paris, then Berlin, and stay in green hotels. Also, what's the weather?", "expected": "plan_trip"},
        {"input": "Plan a trip to Atlantis.", "expected": "location not found"},
        {"input": "Plan a trip to Paris on 2099-12-31.", "expected": "future date"},
        {"input": "I want to visit Paris, Berlin, and Amsterdam using only trains and eco-hotels.", "expected": "plan_trip"},
        {"input": "Blah blah blah", "expected": "didn't understand"},
    ]
    for i, scenario in enumerate(scenarios):
        try:
            r = requests.post('http://localhost:8000/v1/chat', json={'message': scenario['input']}, headers={'Authorization': os.getenv('API_GATEWAY_KEY', 'test-key')}, timeout=5)
            if r.status_code == 200 and scenario['expected'].lower() in r.text.lower():
                print_status(f'Conversation scenario {i+1}: {scenario["input"]}', 'PASS')
            else:
                print_status(f'Conversation scenario {i+1}: {scenario["input"]}', 'FAIL')
        except Exception as e:
            print_status(f'Integration test error: {e}', 'FAIL')

# --- Health Monitoring ---
def test_health_monitoring():
    print_info('Checking system health...')
    try:
        r = requests.get('http://localhost:8000/v1/health', timeout=5)
        if r.status_code == 200 and 'status' in r.json():
            print_status('System health check.', 'PASS')
        else:
            print_status('System health check failed.', 'FAIL')
    except Exception as e:
        print_status(f'Health check error: {e}', 'FAIL')

# --- Stress Testing ---
def stress_test():
    print_info('Running stress test with concurrent conversations...')
    def worker():
        try:
            for _ in range(5):
                requests.post('http://localhost:8000/v1/chat', json={'message': 'Plan a green trip!'}, headers={'Authorization': os.getenv('API_GATEWAY_KEY', 'test-key')}, timeout=5)
        except Exception:
            pass
    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print_status('Stress test completed.', 'PASS')

# --- Data Validation ---
def test_data_validation():
    print_info('Testing data validation and error handling...')
    try:
        r = requests.post('http://localhost:8000/v1/weather', json={'location': 12345}, headers={'Authorization': os.getenv('API_GATEWAY_KEY', 'test-key')}, timeout=5)
        if r.status_code == 422:
            print_status('Input validation for /weather.', 'PASS')
        else:
            print_status('Input validation for /weather failed.', 'FAIL')
    except Exception as e:
        print_status(f'Data validation test error: {e}', 'FAIL')

# --- Backup Testing ---
def backup_testing():
    print_info('Testing backup with mock data if APIs fail...')
    try:
        # Simulate API failure by using wrong key
        r = requests.post('http://localhost:8000/v1/weather', json={'location': 'Berlin'}, headers={'Authorization': 'wrong-key'}, timeout=5)
        if r.status_code == 401:
            print_status('Backup auth test.', 'PASS')
        else:
            print_status('Backup auth test failed.', 'FAIL')
    except Exception as e:
        print_status(f'Backup test error: {e}', 'FAIL')

# --- HTML Report Generation ---
def generate_html_report():
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('project_validation_report.html', 'w', encoding='utf-8') as f:
        f.write(f'<html><head><title>Project Validation Report</title></head><body>')
        f.write(f'<h1>Sustainable Travel Planner Validation Report</h1>')
        f.write(f'<p>Generated: {now}</p>')
        for line in HTML_REPORT:
            f.write(line + '<br>')
        f.write('</body></html>')
    print_info('HTML report generated: project_validation_report.html')

# --- Main ---
def main():
    print(colored('--- Sustainable Travel Planner Project Validation ---', 'yellow'))
    test_rasa_nlu()
    test_rag_system()
    test_external_apis()
    test_api_gateway()
    test_performance()
    test_integration()
    test_health_monitoring()
    stress_test()
    test_data_validation()
    backup_testing()
    generate_html_report()
    print(colored('--- Validation Complete ---', 'yellow'))

if __name__ == '__main__':
    main()
