#!/usr/bin/env python3
"""
Скрипт для создания дефолтных speaker samples для XTTS v2.
Использует Tacotron для генерации примеров голосов.
"""
import os
from TTS.api import TTS

def create_speaker_samples():
    output_dir = 'speaker_samples'
    os.makedirs(output_dir, exist_ok=True)
    
    # Используем Tacotron для генерации примеров
    print("Loading Tacotron model for sample generation...")
    tts_en = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False)
    
    samples = {
        'female-1': "Hello, I am a female voice assistant. How can I help you today?",
        'male-1': "Hello, I am a male voice assistant. How can I help you today?",
        'female-2': "Hi there! I'm here to assist you with text to speech conversion.",
        'male-2': "Greetings! I'm ready to help you with your text to speech needs."
    }
    
    for speaker_id, text in samples.items():
        output_path = os.path.join(output_dir, f'{speaker_id}.wav')
        print(f"Generating {speaker_id}...")
        tts_en.tts_to_file(text=text, file_path=output_path)
        print(f"Created: {output_path}")
    
    print("\nAll speaker samples created successfully!")
    print(f"Samples are in: {output_dir}/")

if __name__ == '__main__':
    create_speaker_samples()
