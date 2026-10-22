import io
import wave

from django.core.files.uploadedfile import SimpleUploadedFile

from apps.catalog.services import set_product_master_audio


def create_master_wav_bytes(*, sample_value):
    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(3)
        audio.setframerate(48_000)
        audio.writeframes(sample_value.to_bytes(3, "little", signed=True) * 48)

    return buffer.getvalue()


def prepare_product_master(product):
    """Preparar un WAV real para una oferta de prueba que debe permitir comprar."""
    preparation = set_product_master_audio(
        product_id=product.pk,
        uploaded_file=SimpleUploadedFile(
            "master-de-prueba.wav",
            create_master_wav_bytes(sample_value=1),
            content_type="audio/wav",
        ),
        declared_format="wav",
        declared_sample_rate_hz=48_000,
        declared_bit_depth=24,
    )
    product.refresh_from_db()
    return preparation
