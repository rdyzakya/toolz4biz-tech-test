from transformers import pipeline
from datasets import load_dataset, Audio
import torch

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

pipe = None
model_name_or_path = "openai/whisper-small"

def start_pipeline():
    global pipe

    if pipe is None:
        pipe = pipeline("automatic-speech-recognition", model=model_name_or_path, device=device)

def run_asr_local(audio_path):
    start_pipeline()
    dataset = load_dataset('audiofolder', data_files=[audio_path], split="train")
    dataset = dataset.cast_column("audio", Audio(sampling_rate=16000))
    result = pipe(dataset["audio"][0]["array"])
    return result["text"].strip()