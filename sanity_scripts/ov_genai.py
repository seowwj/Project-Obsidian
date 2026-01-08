import openvino_genai as ov_genai
from openvino import Core

# if any("GPU" in device for device in Core().get_available_devices()):
#     device = "GPU"
# else:
#     device = "CPU"
device = "CPU"
print(f"Model will load on {device}")

model_path = "D:\\models\\OV_compiled\\OpenVINO_Qwen3-0.6B-int4-ov"

# Create a streamer function
def streamer(subword):
    print(subword, end='', flush=True)
    # Return flag corresponds whether generation should be stopped.
    return ov_genai.StreamingStatus.RUNNING

pipe = ov_genai.LLMPipeline(model_path, device)
pipe.get_tokenizer().set_chat_template(pipe.get_tokenizer().chat_template)

# LLM Generation
print(f"Model loaded on {device}. Starting generation")
print(pipe.generate("Tell me more about yourself", streamer=streamer))
print("End generation")
