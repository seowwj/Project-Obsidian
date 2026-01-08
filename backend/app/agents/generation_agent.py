import logging
import json
import torch
import threading
from transformers import AutoTokenizer, pipeline, TextIteratorStreamer
from optimum.intel import OVModelForCausalLM
from ..config import get_model_path

logger = logging.getLogger(__name__)

class GenerationAgent:
    def __init__(self):
        """
        Initialize Generation Agent with Phi-3 (OpenVINO Optimized).
        """
        self.model_id = get_model_path("generation")
        # OpenVINO device: "GPU" for iGPU, "CPU" for fallback
        # self.device = "GPU" 
        self.device = "CPU"     # Force set to CPU (Debugging)
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        
        # Loading state management
        self._is_loading = False
        self._lock = threading.Lock()

    def is_loaded(self):
        return self.pipeline is not None

    def load_model(self):
        """
        Loads the LLM into memory. Thread-safe.
        """
        if self.pipeline is not None:
            return

        with self._lock:
            if self._is_loading or self.pipeline is not None:
                return
            self._is_loading = True

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
            logger.info(f"Chat Model loaded successfully on {self.device} (OpenVINO).")
            
        except RuntimeError as e:
            logger.warning(f"Failed to load on {self.device}: {e}. Falling back to CPU.")
            try:
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
                logger.info("Chat Model loaded successfully on CPU fallback.")
            except Exception as e2:
                 logger.error(f"Failed to load Chat Model even on CPU: {e2}")
                 # Reset loading flag?
        except Exception as e:
             logger.error(f"Failed to load Chat Model: {e}")
        finally:
            with self._lock:
                self._is_loading = False

    def generate_response_stream(self, context: str, user_query: str, history: list = None):
        """
        Generates a streaming response using Phi-3.
        Yields chunks of text.
        """
        if self.pipeline is None:
            yield "Model is still loading... please wait."
            return

        # Start with System Message
        messages = [
            {"role": "system", "content": "You are a helpful, concise, and friendly assistant. Answer clearly and accurately, ask clarifying questions when needed, and avoid unnecessary verbosity."},
        ]

        # Add History
        if history:
            messages.extend(history)

        # Add User Query
        if context and context.strip():
            content = f"Context:\n{context}\n\nQuestion: {user_query}"
        else:
            content = user_query
            
        messages.append({"role": "user", "content": content})
        
        print(f"DEBUG PROMPT: {json.dumps(messages, indent=2)}")
        logger.info(f"Generating with messages: {json.dumps(messages, indent=2)}")

        input_text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        
        # Using TextIteratorStreamer for streaming text
        streamer = TextIteratorStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)
        
        generation_kwargs = dict(
            text_inputs=input_text,
            streamer=streamer,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.7
        )
        
        # Run generation in a separate thread so we can iterate the streamer
        thread = threading.Thread(target=self.pipeline, kwargs=generation_kwargs)
        thread.start()
        
        for new_text in streamer:
            yield new_text

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
            logger.info("Chat Model unloaded.")
