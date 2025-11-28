import os
import tempfile
from TTS.api import TTS
from pydub import AudioSegment
from typing import List

class TTSService:
    def __init__(self, use_gpu: bool = False, cache=None):
        self.use_gpu = use_gpu
        self.cache = cache
        # Конфигурация моделей
        self.models = {
            'tacotron-en': {
                'name': 'tts_models/en/ljspeech/tacotron2-DDC',
                'languages': ['en'],
                'label': 'Tacotron 2 (English)'
            },
            'tacotron-ru': {
                'name': 'tts_models/ru/mai/tacotron2',
                'languages': ['ru'],
                'label': 'Tacotron 2 (Russian)'
            },
            'xtts-v2': {
                'name': 'tts_models/multilingual/multi-dataset/xtts_v2',
                'languages': ['en', 'ru', 'de', 'es', 'fr', 'it', 'pt', 'pl', 'tr', 'ko', 'nl', 'cs', 'ar', 'zh-cn', 'ja', 'hu'],
                'label': 'XTTS v2 (Multilingual)'
            }
        }
        # Дефолтные спикеры для XTTS v2 (будут созданы при первом запуске)
        self.default_speakers = {
            'female-1': 'Female Voice 1',
            'male-1': 'Male Voice 1',
            'female-2': 'Female Voice 2',
            'male-2': 'Male Voice 2'
        }
        # Инициализация моделей (лениво)
        self._instances = {}
        self._speaker_samples_dir = '/app/speaker_samples'

    def _get_tts(self, model_id: str):
        if model_id not in self.models:
            # Fallback для обратной совместимости или дефолт
            if model_id == 'en': model_id = 'tacotron-en'
            elif model_id == 'ru': model_id = 'tacotron-ru'
            else: model_id = 'xtts-v2' # Default to XTTS if unknown

        if model_id not in self._instances:
            config = self.models.get(model_id)
            if not config:
                raise RuntimeError(f'Model not found: {model_id}')
            
            print(f"Loading model: {model_id}...")
            try:
                self._instances[model_id] = TTS(
                    model_name=config['name'], 
                    progress_bar=False, 
                    gpu=self.use_gpu
                )
            except Exception as e:
                import traceback
                traceback.print_exc()
                raise e
        return self._instances[model_id]

    def get_models(self):
        return self.models

    def get_speakers(self, model_id: str):
        try:
            tts = self._get_tts(model_id)
            # Для XTTS v2 возвращаем список дефолтных спикеров
            if model_id == 'xtts-v2':
                return list(self.default_speakers.keys())
            # Для других моделей проверяем наличие атрибута speakers
            if hasattr(tts, 'speakers') and tts.speakers:
                return tts.speakers
            return []
        except Exception as e:
            print(f"Error getting speakers for {model_id}: {e}")
            import traceback
            traceback.print_exc()
            return []

    def cache_key(self, text: str, model_id: str, language: str = 'en', speaker: str = None, fmt: str = 'wav') -> str:
        import hashlib
        k = hashlib.sha1(f"{model_id}|{language}|{speaker}|{text}|{fmt}".encode('utf-8')).hexdigest()
        return k

    def synthesize_to_file(self, parts: List[str], model_id: str, language: str = 'en', speaker: str = None, out_format: str = 'wav') -> str:
        tts = self._get_tts(model_id)
        tmp_files = []
        try:
            for i, p in enumerate(parts):
                fd = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                out = fd.name
                fd.close()
                
                # Параметры синтеза
                kwargs = {'text': p, 'file_path': out}
                
                # XTTS и мульти-язычные модели требуют language
                if hasattr(tts, 'is_multi_lingual') and tts.is_multi_lingual:
                    kwargs['language'] = language
                
                # Для XTTS v2 используем speaker_wav
                if model_id == 'xtts-v2':
                    # Используем дефолтный спикер если не указан
                    speaker_id = speaker if speaker else 'female-1'
                    speaker_wav_path = os.path.join(self._speaker_samples_dir, f'{speaker_id}.wav')
                    
                    if os.path.exists(speaker_wav_path):
                        kwargs['speaker_wav'] = speaker_wav_path
                        print(f"Using speaker sample: {speaker_id}")
                    else:
                        print(f"Warning: Speaker sample not found: {speaker_wav_path}, using default")
                        # Попробуем использовать первый доступный
                        for default_speaker in self.default_speakers.keys():
                            default_path = os.path.join(self._speaker_samples_dir, f'{default_speaker}.wav')
                            if os.path.exists(default_path):
                                kwargs['speaker_wav'] = default_path
                                print(f"Using fallback speaker: {default_speaker}")
                                break
                else:
                    # Для других моделей используем speaker name если доступен
                    if hasattr(tts, 'is_multi_speaker') and tts.is_multi_speaker:
                        if hasattr(tts, 'speakers') and tts.speakers and len(tts.speakers) > 0:
                            if speaker:
                                kwargs['speaker'] = speaker
                            else:
                                kwargs['speaker'] = tts.speakers[0]
                                print(f"Using default speaker: {tts.speakers[0]}")
                
                tts.tts_to_file(**kwargs)
                tmp_files.append(out)

            # Объединяем части
            combined = AudioSegment.empty()
            for f in tmp_files:
                seg = AudioSegment.from_wav(f)
                combined += seg

            out_path = tempfile.NamedTemporaryFile(suffix='.' + out_format, delete=False).name
            if out_format == 'wav':
                combined.export(out_path, format='wav')
            elif out_format == 'mp3':
                combined.export(out_path, format='mp3')
            else:
                raise RuntimeError('Unsupported format: ' + out_format)

            return out_path
        finally:
            for f in tmp_files:
                try:
                    os.remove(f)
                except Exception:
                    pass
