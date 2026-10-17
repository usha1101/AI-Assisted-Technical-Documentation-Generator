from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch


class DocGenerator:
    def __init__(self):
        print('Loading AI Model (Salesforce/codet5-base-multi-sum)...')
        self.model_name = 'Salesforce/codet5-base-multi-sum'
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name).to(self.device)
        except Exception as e:
            raise RuntimeError(f'Failed to load AI model: {e}')

    def generate_docstring(self, code_snippet: str, complexity: str = "concise") -> str:
        input_ids = self.tokenizer(code_snippet, return_tensors='pt').input_ids.to(self.device)

        # Adjust parameters based on user choice
        if complexity == "detailed":
            min_len, max_len = 50, 250
            repetition_penalty = 1.5
        else:  # concise
            min_len, max_len = 10, 100
            repetition_penalty = 1.0

        generated_ids = self.model.generate(
            input_ids,
            max_length=max_len,
            min_length=min_len,
            num_beams=5,
            repetition_penalty=repetition_penalty,
            early_stopping=True
        )
        return self.tokenizer.decode(generated_ids[0], skip_special_tokens=True)