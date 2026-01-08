import logging
from PIL import Image
from transformers import AutoProcessor
from optimum.intel import OVModelForVisualCausalLM
from ..config import get_model_path

logger = logging.getLogger(__name__)

class VisionAgent:
    def __init__(self):
        """
        Initialize SmolVLM2 Vision Agent with OpenVINO.
        Lazy loading enabled.
        """
        self.model_id = get_model_path("vision")
        # OpenVINO device: "GPU" for iGPU, "CPU" for fallback
        # self.device = "GPU"
        self.device = "CPU"
        self.model = None
        self.processor = None

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
                device=self.device
            )
            self.processor = AutoProcessor.from_pretrained(self.model_id)
            logger.info("Vision Model loaded successfully on OpenVINO.")
        except RuntimeError as e:
            logger.warning(f"Failed to load on {self.device}: {e}. Falling back to CPU.")
            self.device = "CPU"
            self.model = OVModelForVisualCausalLM.from_pretrained(
                self.model_id,
                device=self.device
            )
            self.processor = AutoProcessor.from_pretrained(self.model_id)
            logger.info("Vision Model loaded successfully on OpenVINO.")
        except Exception as e:
            logger.error(f"Failed to load Vision Model: {e}.")

    def analyze_frame(self, frame_path: str) -> str:
        """
        Analyzes a single image frame using SmolVLM2.
        """
        if self.model is None:
            self.load_model()
            
        try:
            image = Image.open(frame_path)
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            prompt = "Describe this image in detail."

            model_inputs = self.model.preprocess_inputs(
                text=prompt,
                image=image,
                processor=self.processor
            )

            generated_ids = self.model.generate(
                **model_inputs,
                max_new_tokens=256,
                do_sample=False,
            )

            generated_texts = self.processor.batch_decode(
                generated_ids,
                skip_special_tokens=True,
            )
            
            print(f"Generated text ----> {generated_texts}")
            response = generated_texts[0]
        
            return response

            # image = Image.open(frame_path)
            # if image.mode != "RGB":
            #     image = image.convert("RGB")

            # # Create message structure for SmolVLM2
            # messages = [
            #     {
            #         "role": "user",
            #         "content": [
            #             {"type": "image"},
            #             {"type": "text", "text": "Describe this image in detail."}
            #         ]
            #     }
            # ]
            
            # # Prepare inputs
            # prompt = self.processor.apply_chat_template(messages, add_generation_prompt=True)
            # inputs = self.processor(text=prompt, images=[image], return_tensors="pt")
            # # # OpenVINO model handles inputs directly, no .to(device) needed usually if model call handles it,
            # # # but usually inputs need to be on CPU for OV model.
            # # inputs = inputs.to("cpu")

            # # Generate
            # generated_ids = self.model.generate(
            #     **inputs,
            #     max_new_tokens=256,
            #     do_sample=False,
            # )
            
            # # Decode
            # generated_texts = self.processor.batch_decode(
            #     generated_ids,
            #     skip_special_tokens=True,
            # )
            
            # # The output usually contains the prompt, we need to extract the assistant response
            # # Note: batch_decode with skip_special_tokens might strip the role markers, making splitting hard.
            # # But usually newer transformers handle this. Let's return the full text for now or simple strip.
            # response = generated_texts[0]
            # # Naive cleaning if prompt is included
            # if "Assistant:" in response:
            #     response = response.split("Assistant:")[-1].strip()
            
            # return response
            
        except Exception as e:
            logger.error(f"Error analyzing frame {frame_path}: {e}")
            return f"Error analyzing frame: {str(e)}"

    def unload(self):
        """
        Unload model to free RAM.
        """
        self.model = None
        self.processor = None
        logger.info("Vision Model unloaded.")
