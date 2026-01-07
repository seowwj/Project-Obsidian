import logging
import torch
from transformers import AutoTokenizer, pipeline
from optimum.intel import OVModelForCausalLM

logger = logging.getLogger(__name__)

class GenerationAgent:
    def __init__(self, model_id="OpenVINO/Phi-3-mini-4k-instruct-int4-ov"):
        """
        Initialize Generation Agent with Phi-3 (OpenVINO Optimized).
        """
        self.model_id = model_id
        # OpenVINO device: "GPU" for iGPU, "CPU" for fallback
        self.device = "GPU" 
        self.model = None
        self.tokenizer = None
        self.pipeline = None

    def load_model(self):
        """
        Loads the LLM into memory.
        """
        if self.pipeline is not None:
            return

        logger.info(f"Loading Gen Model ({self.model_id}) on {self.device} (OpenVINO)...")
        try:
            self.model = OVModelForCausalLM.from_pretrained(
                self.model_id, 
                device=self.device
            )
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            
            self.pipeline = pipeline(
                "text-generation", 
                model=self.model, 
                tokenizer=self.tokenizer,
                max_new_tokens=512,
            )
            logger.info("Gen Model loaded successfully on OpenVINO.")
            
        except RuntimeError as e:
            logger.warning(f"Failed to load on {self.device}: {e}. Falling back to CPU.")
            self.device = "CPU"
            self.model = OVModelForCausalLM.from_pretrained(
                self.model_id, 
                device=self.device
            )
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self.pipeline = pipeline(
                "text-generation", 
                model=self.model, 
                tokenizer=self.tokenizer,
                max_new_tokens=512,
            )
            
        except Exception as e:
             logger.error(f"Failed to load Gen Model: {e}")
             raise e

    def generate_response(self, context: str, user_query: str) -> str:
        """
        Generates a response using Phi-3.
        """
        if self.pipeline is None:
            self.load_model()
            
        # Construct Prompt for Phi-3
        # Strict prompt formatting to ensure it uses the context
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Answer the user's question based ONLY on the provided Context. If the answer is not in the context, say you don't know."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_query}"}
        ]
        
        input_text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        
        logger.info("Generating response...")
        output = self.pipeline(input_text, do_sample=True, temperature=0.7)
        # Output format: [{'generated_text': '...'}]
        generated_text = output[0]['generated_text']
        
        # Extract only the assistant's reply (remove prompt)
        # Phi-3 typically separates with <|assistant|> or similar tokens in the template
        # The pipeline output usually includes the full prompt if not configured otherwise.
        # But we can try to split by the prompt end if we knew it, or use the length.
        
        # Simpler approach: find the last occurrence of the "assistant" header if strictly templated
        # For simplicity with Pipeline, we can just return the text after the input_text
        if generated_text.startswith(input_text):
             response = generated_text[len(input_text):].strip()
        else:
             response = generated_text
             
        return response

    def unload(self):
        """
        Unload model to free RAM.
        """
        if self.pipeline is not None:
            del self.pipeline
            del self.model
            del self.tokenizer
            self.pipeline = None
            self.model = None
            self.tokenizer = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("Gen Model unloaded.")
