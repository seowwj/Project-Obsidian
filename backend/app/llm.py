import threading
import asyncio
from typing import List
from optimum.intel import OVModelForCausalLM
from transformers import AutoTokenizer, pipeline, TextIteratorStreamer
from langchain_core.messages import BaseMessage

from .base_llm import BaseLLMWrapper
from .config import get_model_path

import logging

class SLMWrapper(BaseLLMWrapper):
    """Small language model wrapper"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(self.__class__.__name__)

        self.model_id = get_model_path("chat")
        self.device = "CPU"
        self.model = None
        self.tokenizer = None
        self.pipeline = None
        
        self.load_model()

    def load_model(self):
        self.logger.info(f"Loading {self.model_id} on {self.device}...")

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

        self.logger.info(f"Chat Model loaded successfully on {self.device} (OpenVINO).")

    def unload_model(self):
        self.logger.info(f"Unloading {self.model_id}")
        self.model = None

    async def generate(self, messages: List[BaseMessage], stream_callback=None) -> str:
        if self.model is None:
            raise RuntimeError("SLM not loaded")
        
        # Convert LangChain messages to Hugging Face format
        chat_history = []
        # If message history is empty, add system prompt
        if not messages:
            chat_history.append({"role": "system", "content": "You are a helpful assistant."})
        for msg in messages:
            content = msg.content
            if msg.type == "human":
                role = "user"
            elif msg.type == "system":
                # Ensure system messages are treated as system role
                role = "system"
            elif msg.type == "tool":
                # Treat tool outputs as user messages to prompt the model to respond to them
                role = "user"
                # Explicity label tool output so model doesn't confuse it with human conversation
                content = f"Tool output: {content}"
            else:
                role = "assistant"
            
            chat_history.append({"role": role, "content": content})
        
        # Apply chat template
        prompt = self.tokenizer.apply_chat_template(chat_history, tokenize=False, add_generation_prompt=True)
        
        # Using TextIteratorStreamer for streaming text
        streamer = TextIteratorStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)
        
        generation_kwargs = dict(
            text_inputs=prompt,
            streamer=streamer,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.7
        )
        
        # Run generation in a separate thread so we can iterate the streamer
        thread = threading.Thread(target=self.pipeline, kwargs=generation_kwargs)
        thread.start()
        
        full_response = ""
        loop = asyncio.get_running_loop()
        
        def get_next_token():
            try:
                return next(streamer)
            except StopIteration:
                return None

        while True:
            # Run blocking iterator in a separate thread to avoid blocking the event loop
            new_text = await loop.run_in_executor(None, get_next_token)
            
            if new_text is None:
                break
                
            if stream_callback:
                if asyncio.iscoroutinefunction(stream_callback) or (callable(stream_callback) and asyncio.iscoroutinefunction(getattr(stream_callback, "__call__", None))):
                    await stream_callback(new_text)
                else:
                    stream_callback(new_text)
            full_response += new_text
            
        return full_response