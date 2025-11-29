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

    def create_speaker(self, speaker_id: str, audio_file) -> dict:
        """Создание нового спикера из аудиофайла"""
        import shutil
        from datetime import datetime
        
        print(f"\n{'='*60}")
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Начало создания спикера: {speaker_id}")
        print(f"{'='*60}")
        
        # Проверка валидности speaker_id
        if not speaker_id or not speaker_id.replace('-', '').replace('_', '').isalnum():
            error_msg = "Speaker ID должен содержать только буквы, цифры, дефисы и подчеркивания"
            print(f"❌ ОШИБКА: {error_msg}")
            raise ValueError(error_msg)
        
        print(f"✓ Валидация speaker_id пройдена: {speaker_id}")
        
        # Проверка, что это не дефолтный спикер
        if speaker_id in self.default_speakers:
            error_msg = f"Нельзя перезаписать дефолтный спикер: {speaker_id}"
            print(f"❌ ОШИБКА: {error_msg}")
            raise ValueError(error_msg)
        
        print(f"✓ Проверка на дефолтный спикер пройдена")
        
        # Создаем директорию если не существует
        os.makedirs(self._speaker_samples_dir, exist_ok=True)
        print(f"✓ Директория создана/проверена: {self._speaker_samples_dir}")
        
        # Сохраняем аудиофайл
        speaker_path = os.path.join(self._speaker_samples_dir, f'{speaker_id}.wav')
        print(f"📝 Сохранение аудиофайла: {speaker_path}")
        
        try:
            # Если файл уже существует, перезаписываем
            with open(speaker_path, 'wb') as f:
                shutil.copyfileobj(audio_file, f)
            
            file_size = os.path.getsize(speaker_path)
            print(f"✓ Аудиофайл сохранен успешно ({file_size} bytes)")
        except Exception as e:
            print(f"❌ ОШИБКА при сохранении файла: {e}")
            raise
        
        result = {
            'speaker_id': speaker_id,
            'path': speaker_path,
            'is_default': False
        }
        
        print(f"\n{'='*60}")
        print(f"✅ УСПЕХ: Спикер '{speaker_id}' создан и готов к использованию!")
        print(f"{'='*60}\n")
        
        return result
    
    def delete_speaker(self, speaker_id: str) -> bool:
        """Удаление пользовательского спикера"""
        # Нельзя удалять дефолтные спикеры
        if speaker_id in self.default_speakers:
            raise ValueError(f"Нельзя удалить дефолтный спикер: {speaker_id}")
        
        speaker_path = os.path.join(self._speaker_samples_dir, f'{speaker_id}.wav')
        
        if os.path.exists(speaker_path):
            os.remove(speaker_path)
            return True
        return False
    
    def get_all_speakers(self) -> list:
        """Получение списка всех спикеров (дефолтных и пользовательских)"""
        speakers = []
        
        # Добавляем дефолтные спикеры
        for speaker_id, label in self.default_speakers.items():
            speakers.append({
                'speaker_id': speaker_id,
                'label': label,
                'is_default': True
            })
        
        # Добавляем пользовательские спикеры
        if os.path.exists(self._speaker_samples_dir):
            for filename in os.listdir(self._speaker_samples_dir):
                if filename.endswith('.wav'):
                    speaker_id = filename[:-4]  # убираем .wav
                    if speaker_id not in self.default_speakers:
                        speakers.append({
                            'speaker_id': speaker_id,
                            'label': speaker_id.replace('-', ' ').replace('_', ' ').title(),
                            'is_default': False
                        })
        
        return speakers
    
    def get_speaker_audio_path(self, speaker_id: str) -> str:
        """Получение пути к аудиофайлу спикера"""
        speaker_path = os.path.join(self._speaker_samples_dir, f'{speaker_id}.wav')
        if os.path.exists(speaker_path):
            return speaker_path
        raise FileNotFoundError(f"Speaker {speaker_id} not found")
