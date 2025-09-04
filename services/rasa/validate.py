import rasa
from rasa.model_testing import test_nlu
import os

# Path to the trained model and NLU data
def main():
    model_path = os.path.join('models')
    nlu_data_path = os.path.join('data', 'nlu.yml')
    if not os.path.exists(model_path):
        print("[ERROR] Trained model not found. Please train your model first.")
        return
    if not os.path.exists(nlu_data_path):
        print("[ERROR] NLU data not found at data/nlu.yml.")
        return
    print("Running NLU evaluation...")
    # This will output a report in results/nlu
    test_nlu(model=model_path, nlu_data=nlu_data_path, output_directory='results/nlu')
    print("NLU evaluation complete. Check results/nlu for detailed metrics.")

if __name__ == "__main__":
    main()
