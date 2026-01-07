import logging
import torch
from PIL import Image
from transformers import AutoProcessor
from optimum.intel import OVModelForVisualCausalLM

logger = logging.getLogger(__name__)

class VisionAgent:
    def __init__(self, model_id="HuggingFaceTB/SmolVLM2-500M-Video-Instruct"):
        """
        Initialize SmolVLM2 Vision Agent with OpenVINO.
        Lazy loading enabled.
        """
        self.model_id = model_id
        # OpenVINO device: "GPU" for iGPU, "CPU" for fallback
        self.device = "GPU"
        self.model = None
        self.processor = None
        self.mock_mode = False

    def load_model(self):
        """
        Loads the model into memory.
        """
        if self.model is not None:
            return

        try:
            logger.info(f"Loading Vision Model ({self.model_id}) on {self.device} (OpenVINO)...")
            # Load with OpenVINO optimization
            self.model = OVModelForVisualCausalLM.from_pretrained(
                self.model_id,
                export=True, 
                device=self.device
            )
            self.processor = AutoProcessor.from_pretrained(self.model_id)
            logger.info("Vision Model loaded successfully on OpenVINO.")
        except RuntimeError as e:
            logger.warning(f"Failed to load on {self.device}: {e}. Falling back to CPU.")
            self.device = "CPU"
            self.model = OVModelForVisualCausalLM.from_pretrained(
                self.model_id,
                export=True, 
                device=self.device
            )
            self.processor = AutoProcessor.from_pretrained(self.model_id)
            logger.info("Vision Model loaded successfully on OpenVINO.")
            self.mock_mode = False
        except Exception as e:
            logger.error(f"Failed to load Vision Model: {e}. Falling back to MOCK mode.")
            self.mock_mode = True

    def analyze_frame(self, frame_path: str) -> str:
        """
        Analyzes a single image frame using SmolVLM2.
        """
        if self.model is None and not self.mock_mode:
            self.load_model()
            
        if self.mock_mode:
            return "This is a mock description of the video frame."

        try:
            image = Image.open(frame_path)
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Create message structure for SmolVLM2
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "image"},
                        {"type": "text", "text": "Describe this image in detail."}
                    ]
                }
            ]
            
            # Prepare inputs
            prompt = self.processor.apply_chat_template(messages, add_generation_prompt=True)
            inputs = self.processor(text=prompt, images=[image], return_tensors="pt")
            # OpenVINO model handles inputs directly, no .to(device) needed usually if model call handles it,
            # but usually inputs need to be on CPU for OV model.
            inputs = inputs.to("cpu")

            # Generate
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=False,
            )
            
            # Decode
            generated_texts = self.processor.batch_decode(
                generated_ids,
                skip_special_tokens=True,
            )
            
            # The output usually contains the prompt, we need to extract the assistant response
            # Note: batch_decode with skip_special_tokens might strip the role markers, making splitting hard.
            # But usually newer transformers handle this. Let's return the full text for now or simple strip.
            response = generated_texts[0]
            # Naive cleaning if prompt is included
            if "Assistant:" in response:
                response = response.split("Assistant:")[-1].strip()
            
            return response
            
        except Exception as e:
            logger.error(f"Error analyzing frame {frame_path}: {e}")
            return f"Error analyzing frame: {str(e)}"

    def unload(self):
        """
        Unload model to free RAM.
        """
        if not self.mock_mode:
            self.model = None
            self.processor = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("Vision Model unloaded.")
