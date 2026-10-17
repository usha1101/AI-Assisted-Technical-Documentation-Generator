import os
import re
from abc import ABC, abstractmethod
from typing import Optional
import torch


class BaseGenerator(ABC):
    """Abstract base class for documentation generators."""

    @abstractmethod
    def generate_docstring(self, code_snippet: str, complexity: str = "concise") -> str:
        """Generate a natural language docstring from a code snippet."""
        pass


class CodeT5Generator(BaseGenerator):
    """
    Production AI generator using Salesforce/codet5-base-multi-sum.
    Runs locally using Hugging Face Transformers and PyTorch.
    """

    def __init__(self, model_name: str = 'Salesforce/codet5-base-multi-sum'):
        self.model_name = model_name
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Loading AI Model ({self.model_name}) on {self.device}...")

        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name).to(self.device)
        except Exception as e:
            raise RuntimeError(f"Failed to load AI model '{self.model_name}': {e}")

    def generate_docstring(self, code_snippet: str, complexity: str = "concise") -> str:
        input_ids = self.tokenizer(
            code_snippet,
            truncation=True,
            max_length=512,
            return_tensors='pt'
        ).input_ids.to(self.device)

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


class MockGenerator(BaseGenerator):
    """
    Lightweight rule-based generator for CI/CD test automation,
    offline development, and unit testing without requiring 900MB model weights.
    (Note: This is a deterministic rule-based generator, not an AI model).
    """

    def generate_docstring(self, code_snippet: str, complexity: str = "concise") -> str:
        snippet = code_snippet.strip()
        match = re.search(r'def\s+([a-zA-Z0-9_]+)\s*\(', snippet)
        if match:
            fn_name = match.group(1).replace('_', ' ')
            if complexity == "detailed":
                return f"Executes the {fn_name} procedure, processing input arguments and returning the computed result."
            return f"Performs the {fn_name} operation."

        cls_match = re.search(r'class\s+([a-zA-Z0-9_]+)', snippet)
        if cls_match:
            cls_name = cls_match.group(1)
            return f"Represents the {cls_name} component and manages its associated operations."

        return "Processes input code and produces output."


# Backward-compatible alias: DocGenerator defaults to CodeT5Generator
DocGenerator = CodeT5Generator


def get_generator(mode: Optional[str] = None) -> BaseGenerator:
    """Factory function returning the configured generator instance."""
    selected_mode = (mode or os.getenv("DOCGEN_MODE", "codet5")).lower()
    if selected_mode == "mock":
        return MockGenerator()
    return CodeT5Generator()