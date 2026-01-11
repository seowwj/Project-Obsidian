import logging
import os
from typing import List, Optional

from PIL import Image
from optimum.intel import OVModelForVisualCausalLM
from transformers import AutoProcessor
from langchain_core.messages import BaseMessage

from .base_llm import BaseLLMWrapper
from .config import get_model_path


class VLMWrapper(BaseLLMWrapper):
    """
    Visual Language Model wrapper using SmolVLM2 via OpenVINO.

    Uses OVModelForVisualCausalLM from optimum-intel for Intel-optimized inference.
    Supports both video frames and static images (jpg/png).
    """
    AUDIO_ALIGNED_PROMPT = """You are given video frames corresponding to spoken audio.
If you see any graph, be sure to describe it in detail.

Audio transcript: "{asr_context}"

Describe:
- What is visually happening
- How it relates to the spoken instruction
- Any relevant visual details not mentioned in speech

Be concise and factual."""

    VISION_ONLY_PROMPT = """Describe the visually observable action or state change in these frames.
If this is a static image, describe what you see.
Indicate whether any action appears to complete within this segment.
Be concise and factual."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model_path = get_model_path("vision")
        self.device = "CPU"
        self.model = None
        self.processor = None

        self.load_model()

    def load_model(self):
        """Load SmolVLM2 with OpenVINO backend."""
        self.logger.info(f"Loading VLM model from {self.model_path} on {self.device}...")

        try:
            # Load OpenVINO-optimized model
            self.model = OVModelForVisualCausalLM.from_pretrained(
                self.model_path,
                device=self.device,
                trust_remote_code=True
            )

            # Load processor for image preprocessing
            self.processor = AutoProcessor.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )

            self.logger.info("VLM model loaded successfully.")

        except Exception as e:
            self.logger.error(f"Failed to load VLM model: {e}")
            raise

    def unload_model(self):
        """Unload the VLM model to free memory."""
        self.logger.info("Unloading VLM model...")
        self.model = None
        self.processor = None

    def generate(self, messages: List[BaseMessage]) -> str:
        """
        BaseLLMWrapper requirement. VLM does not generate from messages directly.
        Use describe_frames() or describe_image() instead.
        """
        raise NotImplementedError(
            "VLMWrapper does not support generate(). "
            "Use describe_frames() or describe_image() instead."
        )

    def describe_frames(
        self,
        frame_paths: List[str],
        asr_context: Optional[str] = None,
        max_new_tokens: int = 256
    ) -> str:
        """
        Generate visual description from a sequence of video frames.

        Args:
            frame_paths: List of paths to frame images
            asr_context: Optional ASR transcript for audio-aligned prompting
            max_new_tokens: Maximum tokens to generate

        Returns:
            Visual description text
        """
        if self.model is None or self.processor is None:
            raise RuntimeError("VLM model not loaded. Call load_model() first.")

        if not frame_paths:
            raise ValueError("frame_paths cannot be empty")

        # Load images
        images = self._load_images(frame_paths)

        # Build prompt based on context
        if asr_context:
            prompt = self.AUDIO_ALIGNED_PROMPT.format(asr_context=asr_context)
        else:
            prompt = self.VISION_ONLY_PROMPT

        # Generate description
        return self._generate_with_images(images, prompt, max_new_tokens)

    def describe_image(
        self,
        image_path: str,
        prompt: Optional[str] = None,
        max_new_tokens: int = 256
    ) -> str:
        """
        Generate description for a single static image (jpg/png).

        Args:
            image_path: Path to image file
            prompt: Optional custom prompt (defaults to vision-only prompt)
            max_new_tokens: Maximum tokens to generate

        Returns:
            Image description text
        """
        if self.model is None or self.processor is None:
            raise RuntimeError("VLM model not loaded. Call load_model() first.")

        # Load image
        images = self._load_images([image_path])

        # Use custom prompt or default
        if prompt is None:
            prompt = self.VISION_ONLY_PROMPT

        return self._generate_with_images(images, prompt, max_new_tokens)

    def _load_images(self, paths: List[str]) -> List[Image.Image]:
        """Load images from paths and convert to RGB"""
        images = []
        for path in paths:
            if not os.path.exists(path):
                self.logger.warning(f"Image not found: {path}")
                continue
            try:
                img = Image.open(path).convert("RGB")
                images.append(img)
            except Exception as e:
                self.logger.warning(f"Failed to load image {path}: {e}")

        if not images:
            raise ValueError("No valid images could be loaded")

        return images

    def _generate_with_images(
        self,
        images: List[Image.Image],
        prompt: str,
        max_new_tokens: int
    ) -> str:
        """
        Generate text from images and prompt using SmolVLM2 chat format.

        SmolVLM2 expects a chat template format where images are specified
        as content entries with type "image".
        """
        self.logger.debug(f"Generating description for {len(images)} images...")

        try:
            # Build chat messages with images
            # SmolVLM2 expects: [{"type": "image", "image" : image}, ..., {"type": "text", "text": prompt}]
            content = []
            for img in images:
                content.append({"type": "image", "image": img})
            content.append({"type": "text", "text": prompt})

            messages = [{"role": "user", "content": content}]

            # Apply chat template to get proper input format
            text_input = self.processor.apply_chat_template(
                messages,
                add_generation_prompt=True,
                tokenize=False
            )

            # Process with images
            inputs = self.processor(
                text=text_input,
                images=images,
                return_tensors="pt"
            )

            # Generate
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False
            )

            # Decode output (skip input tokens)
            input_len = inputs["input_ids"].shape[1]
            generated_ids = output_ids[0, input_len:]
            description = self.processor.decode(generated_ids, skip_special_tokens=True)

            self.logger.debug(f"Generated description: {description[:100]}...")
            return description.strip()

        except Exception as e:
            self.logger.error(f"VLM generation failed: {e}")
            raise
