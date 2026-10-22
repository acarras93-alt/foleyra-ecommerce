import wave
from dataclasses import dataclass
from hashlib import sha256
from typing import cast
from uuid import uuid4

import soundfile as sf
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.catalog.models import MasterAudioPreparation, Product


@dataclass(frozen=True)
class MasterAudioValidation:
    storage_key: str
    sha256: str
    size_bytes: int
    audio_format: str
    sample_rate_hz: int
    bit_depth: int


def validate_master_audio(
    *,
    master_file,
    declared_format,
    declared_sample_rate_hz,
    declared_bit_depth,
) -> MasterAudioValidation:
    if declared_format not in {"wav", "flac", "aiff"}:
        raise ValidationError("Formato de maestro no admitido.")

    storage_key = master_file.name

    # Leer las propiedades reales con el lector correspondiente.
    try:
        with master_file.storage.open(storage_key, "rb") as stored:
            if declared_format == "wav":
                with wave.open(stored, "rb") as audio:
                    sample_rate_hz = audio.getframerate()
                    bit_depth = audio.getsampwidth() * 8

                    bytes_per_frame = audio.getnchannels() * audio.getsampwidth()
                    remaining_frames = audio.getnframes()

                    while remaining_frames:
                        requested_frames = min(remaining_frames, 4096)
                        chunk = audio.readframes(requested_frames)

                        if len(chunk) != requested_frames * bytes_per_frame:
                            raise ValidationError(
                                "El maestro WAV contiene audio incompleto."
                            )

                        remaining_frames -= requested_frames

            else:
                # AIFF: comprobar el tamaño anunciado por el contenedor.
                if declared_format == "aiff":
                    header = stored.read(12)

                    if (
                        len(header) != 12
                        or header[:4] != b"FORM"
                        or header[8:12] not in {b"AIFF", b"AIFC"}
                    ):
                        raise ValidationError("El contenedor AIFF no es válido.")

                    expected_size = int.from_bytes(header[4:8], "big") + 8

                    stored.seek(0, 2)
                    actual_size = stored.tell()
                    stored.seek(0)

                    if actual_size < expected_size:
                        raise ValidationError("El contenedor AIFF está incompleto.")

                with sf.SoundFile(stored, mode="r") as audio:
                    if audio.format != declared_format.upper():
                        raise ValidationError(
                            "El contenido del maestro no coincide "
                            "con el formato declarado."
                        )

                    sample_rate_hz = audio.samplerate
                    bit_depth = {
                        "PCM_S8": 8,
                        "PCM_16": 16,
                        "PCM_24": 24,
                        "PCM_32": 32,
                    }.get(audio.subtype)

                    if bit_depth is None:
                        raise ValidationError(
                            "La codificación del maestro no está admitida."
                        )

                    # Decodificar el audio completo en bloques.
                    remaining_frames = audio.frames

                    while remaining_frames:
                        requested_frames = min(remaining_frames, 4096)
                        chunk = audio.read(
                            requested_frames,
                            dtype="int32",
                            always_2d=True,
                        )

                        if len(chunk) != requested_frames:
                            raise ValidationError(
                                "El maestro contiene audio incompleto."
                            )

                        remaining_frames -= requested_frames
            # Identificar todos los bytes del mismo objeto leído.
            stored.seek(0)
            content_hash = sha256()
            size_bytes = 0

            while True:
                chunk = stored.read(64 * 1024)
                if not chunk:
                    break
                content_hash.update(chunk)
                size_bytes += len(chunk)

    except (OSError, EOFError, wave.Error, sf.SoundFileError):
        raise ValidationError("No se pudo leer el archivo maestro.") from None

    # Aplicar la misma regla de negocio a ambos formatos.
    if sample_rate_hz < 48_000 or bit_depth < 24:
        raise ValidationError("El maestro debe tener al menos 48000 Hz y 24 bits.")

    if sample_rate_hz != declared_sample_rate_hz or bit_depth != declared_bit_depth:
        raise ValidationError(
            "Las propiedades del maestro no coinciden con los datos declarados."
        )

    return MasterAudioValidation(
        storage_key=storage_key,
        sha256=content_hash.hexdigest(),
        size_bytes=size_bytes,
        audio_format=declared_format,
        sample_rate_hz=sample_rate_hz,
        bit_depth=bit_depth,
    )


def prepare_master_audio(
    *,
    master_file,
    declared_format,
    declared_sample_rate_hz,
    declared_bit_depth,
) -> MasterAudioPreparation:
    # 1. Validar el archivo real y obtener su evidencia.
    result = validate_master_audio(
        master_file=master_file,
        declared_format=declared_format,
        declared_sample_rate_hz=declared_sample_rate_hz,
        declared_bit_depth=declared_bit_depth,
    )

    # 2. Preparar los datos que deben conservarse.
    validated_values = {
        "sha256": result.sha256,
        "size_bytes": result.size_bytes,
        "audio_format": result.audio_format,
        "sample_rate_hz": result.sample_rate_hz,
        "bit_depth": result.bit_depth,
    }

    # 3.Crear el registro o recuperar la preparción existente.
    preparation, _ = MasterAudioPreparation.objects.get_or_create(
        storage_key=result.storage_key,
        defaults=validated_values,
    )

    # 4.Impedir que otra evidencia sustituya la preparacion anterior
    if any(
        getattr(preparation, field) != value
        for field, value in validated_values.items()
    ):
        raise ValidationError(
            "El archivo no coincide con su preparación anterior."
            "El nuevo maestro debe guardarse con otra clave privada."
        )

    return preparation


def set_product_master_audio(
    *,
    product_id,
    uploaded_file,
    declared_format,
    declared_sample_rate_hz,
    declared_bit_depth,
) -> MasterAudioPreparation:
    # Comprobar el formato antes de utilizarlo en el nombre interno.
    if declared_format not in Product.AudioFormat.values:
        raise ValidationError("Formato de maestro no admitido.")

    # Preparar un campo de archivo independiente del producto existente.
    candidate = Product().master_file
    storage = candidate.storage
    new_key = None

    try:
        with transaction.atomic():
            # 1. Recuperar y bloquear el producto durante la operación.
            product = cast(
                Product,
                Product.objects.select_for_update().get(pk=product_id),
            )

            # 2. Guardar el archivo con un nuevo interno nuevo.
            candidate.save(
                f"{uuid4().hex}.{declared_format}", uploaded_file, save=False
            )
            new_key = candidate.name

            # 3. Validar el archivo guardado y registrar su preparación.
            preparation = prepare_master_audio(
                master_file=candidate,
                declared_format=declared_format,
                declared_sample_rate_hz=declared_sample_rate_hz,
                declared_bit_depth=declared_bit_depth,
            )

            # 4. Asociar el maestro validado al producto.
            product.master_file.name = preparation.storage_key
            product.audio_format = preparation.audio_format
            product.sample_rate_hz = preparation.sample_rate_hz
            product.bit_depth = preparation.bit_depth

            product.save(
                update_fields=[
                    "master_file",
                    "audio_format",
                    "sample_rate_hz",
                    "bit_depth",
                ]
            )

        return preparation

    except Exception:
        # La transacción revierte los registros pero no lo archivos
        if new_key is not None:
            storage.delete(new_key)
        raise
