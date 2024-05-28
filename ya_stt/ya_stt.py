import threading
import sounddevice as sd
import grpc
import queue
import numpy as np
import ya_stt.yandex.cloud.ai.stt.v3.stt_pb2 as stt_pb2
import ya_stt.yandex.cloud.ai.stt.v3.stt_service_pb2_grpc as stt_service_pb2_grpc
import time

from env import STT_API_KEY, FS, DURATION, CHANNELS, MAX_AUDIO_DURATION, MAX_DATA_SIZE, DEBUG
from utils import write_to_file

CHUNK_SIZE = FS * DURATION * CHANNELS * 2  # Размер чанка для отправки в Яндекс API

sentences_dict = {}
current_timestamp = None

audio_queue = queue.Queue(maxsize=10)  # Ограничение размера очереди, чтобы избежать переполнения
stop_event = threading.Event()

total_duration = 0  # Чтобы не вылезти за лимиты Яндекс API, отслеживаем длительность сессии...
total_data_size = 0  # ... и размер данных


def record_audio():
    global total_duration

    while not stop_event.is_set():
        if total_duration >= MAX_AUDIO_DURATION:
            total_duration = 0

        recording = sd.rec(int(DURATION * FS), samplerate=FS, channels=CHANNELS, dtype='int16', device='default')
        sd.wait()

        total_duration += DURATION

        try:
            audio_queue.put(recording, timeout=1)  # Используем timeout, чтобы избежать блокировки
        except queue.Full:
            write_to_file('errors.log', f'{int(time.time())}: Попытка записать в полную очередь.', add=True)


def generate_audio_chunks():
    global total_data_size

    recognize_options = stt_pb2.StreamingOptions(
        recognition_model=stt_pb2.RecognitionModelOptions(
            audio_format=stt_pb2.AudioFormatOptions(
                raw_audio=stt_pb2.RawAudio(
                    audio_encoding=stt_pb2.RawAudio.LINEAR16_PCM,
                    sample_rate_hertz=FS,
                    audio_channel_count=CHANNELS
                )
            ),
            text_normalization=stt_pb2.TextNormalizationOptions(
                text_normalization=stt_pb2.TextNormalizationOptions.TEXT_NORMALIZATION_ENABLED,
                profanity_filter=False,
                literature_text=True
            ),
            language_restriction=stt_pb2.LanguageRestrictionOptions(
                restriction_type=stt_pb2.LanguageRestrictionOptions.WHITELIST,
                language_code=['ru-RU']
            ),
            audio_processing_type=stt_pb2.RecognitionModelOptions.REAL_TIME
        )
    )

    try:
        yield stt_pb2.StreamingRequest(session_options=recognize_options)

        while not stop_event.is_set():
            if total_data_size >= MAX_DATA_SIZE:
                total_data_size = 0
                break

            try:
                audio_data = audio_queue.get(timeout=1)
            except queue.Empty:
                continue

            data_size = len(audio_data) * 2  # Размер данных в байтах (int16 = 2 байта)
            total_data_size += data_size

            audio_data = np.array(audio_data, dtype=np.int16).tobytes()
            yield stt_pb2.StreamingRequest(chunk=stt_pb2.AudioChunk(data=audio_data))

    except Exception as e:
        write_to_file('errors.log', str(e), add=True)


def transcribe_audio():
    while not stop_event.is_set():
        try:
            start_transcription_session()
        except grpc.RpcError as e:
            write_to_file('errors.log', str(e), add=True)
            time.sleep(0.1)
            if stop_event.is_set():
                break
        except Exception as e:
            write_to_file('errors.log', str(e), add=True)
            break


def start_transcription_session():
    global total_data_size, total_duration, current_timestamp

    try:
        cred = grpc.ssl_channel_credentials()
        channel = grpc.secure_channel('stt.api.cloud.yandex.net:443', cred)
        stub = stt_service_pb2_grpc.RecognizerStub(channel)

        while not stop_event.is_set():
            response_iterator = stub.RecognizeStreaming(generate_audio_chunks(), metadata=(
                ('authorization', f'Api-Key {STT_API_KEY}'),
            ))

            for res in response_iterator:
                if DEBUG:
                    write_to_file('res.log', res, add=True)

                if stop_event.is_set():
                    break

                event_type, alternatives = res.WhichOneof('Event'), None

                if current_timestamp is None or event_type == 'final_refinement':
                    current_timestamp = int(time.time() * 1000)

                if event_type in ['partial', 'final', 'final_refinement']:
                    sentences_dict[current_timestamp] = {'words': {}, 'sentence': ''}

                    if event_type == 'partial' and len(res.partial.alternatives) > 0:
                        alternatives = res.partial.alternatives[0]
                    elif event_type == 'final' and len(res.final.alternatives) > 0:
                        alternatives = res.final.alternatives[0]
                    elif event_type == 'final_refinement' and len(res.final_refinement.normalized_text.alternatives) > 0:
                        alternatives = res.final_refinement.normalized_text.alternatives[0]

                    if alternatives:
                        for word in alternatives.words:
                            sentences_dict[current_timestamp]['words'][word.start_time_ms] = word.text
                        sentences_dict[current_timestamp]['sentence'] = alternatives.text

                    if DEBUG:
                        write_to_file('sentences.json', sentences_dict, add=False)

    except grpc.RpcError:
        raise
    except Exception:
        raise


def stt_start_recording():
    global current_timestamp
    stop_event.clear()
    current_timestamp = None
    record_thread = threading.Thread(target=record_audio)
    transcribe_thread = threading.Thread(target=transcribe_audio)

    record_thread.start()
    transcribe_thread.start()
    return record_thread, transcribe_thread


def stt_stop_recording(record_thread, transcribe_thread):
    stop_event.set()
    if record_thread.is_alive():
        record_thread.join()
    if transcribe_thread.is_alive():
        transcribe_thread.join()


def stt_get_results():
    if sentences_dict:
        latest_timestamp = list(sentences_dict.keys())[-1]
        return {latest_timestamp: sentences_dict[latest_timestamp]}
    return {}
