import io
import wave
from contextlib import nullcontext
from hashlib import sha256

import pytest
import soundfile as sf
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings

from apps.catalog.models import (
    Category,
    MasterAudioPreparation,
    Product,
    private_master_storage,
)
from apps.catalog.services import (
    prepare_master_audio,
    set_product_master_audio,
    validate_master_audio,
)
from apps.catalog.storage import PrivateMasterStorage


def _add_bwf_metadata(wav_bytes, sample_rate_hz, bit_depth):
    coding_history = (
        f"A=PCM,F={sample_rate_hz},W={bit_depth},M=mono,T=Foleyra test\r\n"
    ).encode("ascii")

    # Metadatos de un bloque bext versión 2.
    bext_data = b"".join(
        [
            b"Ambiente controlado RF-11".ljust(256, b"\x00"),
            b"Foleyra".ljust(32, b"\x00"),
            b"RF11-BWF-001".ljust(32, b"\x00"),
            b"2026-10-19",
            b"00:00:00",
            (0).to_bytes(8, "little"),  # Referencia temporal.
            (2).to_bytes(2, "little"),  # Versión del bloque.
            bytes(64),  # UMID sin asignar.
            b"\xff\x7f" * 5,  # Mediciones de sonoridad desconocidas.
            bytes(180),  # Espacio reservado.
            coding_history,
        ]
    )

    # Cada bloque contiene identificador, tamaño y contenido.
    bext_chunk = b"bext" + len(bext_data).to_bytes(4, "little") + bext_data

    # RIFF exige que los bloques ocupen un número par de bytes.
    if len(bext_data) % 2:
        bext_chunk += b"\x00"

    # Insertar bext conservando los bloques originales del WAV.
    riff_body = b"WAVE" + bext_chunk + wav_bytes[12:]

    # Actualizar el tamaño del contenedor.
    return b"RIFF" + len(riff_body).to_bytes(4, "little") + riff_body


@pytest.mark.parametrize("container", ["wav", "bwf"])
@pytest.mark.parametrize(
    ("sample_rate_hz", "bit_depth", "accepted"),
    [
        (48_000, 24, True),
        (96_000, 24, True),
        (48_000, 32, True),
        (44_100, 24, False),
        (48_000, 16, False),
    ],
    ids=[
        "minimum-48000-24",
        "higher-sample-rate-96000-24",
        "higher-bit-depth-48000-32",
        "reject-low-sample-rate",
        "reject-low-bit-depth",
    ],
)
def test_validate_master_audio_enforces_wav_minimums_without_modifying_file(
    tmp_path,
    container,
    sample_rate_hz,
    bit_depth,
    accepted,
):
    # Preparar: generar un WAV con propiedades reales conocidas.
    sample_width = bit_depth // 8
    sample = b"\x01" + b"\x00" * (sample_width - 1)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(sample_width)
        audio.setframerate(sample_rate_hz)
        audio.writeframes(sample * 48)

    original_bytes = buffer.getvalue()

    if container == "bwf":
        original_bytes = _add_bwf_metadata(
            original_bytes,
            sample_rate_hz,
            bit_depth,
        )
        assert original_bytes[12:16] == b"bext"

    with override_settings(BASE_DIR=tmp_path):
        storage = PrivateMasterStorage()

    master_file = Product().master_file
    master_file.storage = storage
    master_file.save(
        "ca-rf11-11-controlled.wav",
        ContentFile(original_bytes),
        save=False,
    )

    # Confirmar que se utiliza el archivo temporal correcto.
    with master_file.storage.open(master_file.name, "rb") as prepared:
        assert prepared.read() == original_bytes

    expected_response = nullcontext() if accepted else pytest.raises(ValidationError)

    # Actuar y comprobar: admitir o rechazar según el mínimo.
    with expected_response:
        validate_master_audio(
            master_file=master_file,
            declared_format="wav",
            declared_sample_rate_hz=sample_rate_hz,
            declared_bit_depth=bit_depth,
        )

    # Comprobar: conservar los bytes originales.
    with master_file.storage.open(master_file.name, "rb") as stored:
        assert stored.read() == original_bytes


@pytest.mark.parametrize(
    ("sample_rate_hz", "bit_depth", "accepted"),
    [
        (48_000, 24, True),
        (96_000, 24, True),
        (192_000, 24, True),
        (44_100, 24, False),
        (48_000, 16, False),
    ],
    ids=[
        "minimum-48000-24",
        "higher-sample-rate-96000-24",
        "higher-sample-rate-192000-24",
        "reject-low-sample-rate",
        "reject-low-bit-depth",
    ],
)
def test_validate_master_audio_enforces_flac_minimums_without_modifying_file(
    tmp_path,
    sample_rate_hz,
    bit_depth,
    accepted,
):
    # Preparar: generar un FLAC con propiedades conocidas.
    buffer = io.BytesIO()
    sf.write(
        buffer,
        [0.25] * 48,
        sample_rate_hz,
        format="FLAC",
        subtype=f"PCM_{bit_depth}",
    )
    original_bytes = buffer.getvalue()

    # Confirmar que la preparación produjo el formato esperado.
    with sf.SoundFile(io.BytesIO(original_bytes)) as prepared:
        assert prepared.format == "FLAC"
        assert prepared.samplerate == sample_rate_hz
        assert prepared.subtype == f"PCM_{bit_depth}"

    with override_settings(BASE_DIR=tmp_path):
        storage = PrivateMasterStorage()

    master_file = Product().master_file
    master_file.storage = storage
    master_file.save(
        "ca-rf11-11-controlled.flac",
        ContentFile(original_bytes),
        save=False,
    )

    expected_response = nullcontext() if accepted else pytest.raises(ValidationError)

    # Actuar y comprobar: aplicar la misma regla de calidad.
    with expected_response:
        validate_master_audio(
            master_file=master_file,
            declared_format="flac",
            declared_sample_rate_hz=sample_rate_hz,
            declared_bit_depth=bit_depth,
        )

    # Comprobar: conservar el archivo original.
    with master_file.storage.open(master_file.name, "rb") as stored:
        assert stored.read() == original_bytes


@pytest.mark.parametrize(
    ("sample_rate_hz", "bit_depth", "accepted"),
    [
        (48_000, 24, True),
        (96_000, 24, True),
        (48_000, 32, True),
        (44_100, 24, False),
        (48_000, 16, False),
    ],
    ids=[
        "minimum-48000-24",
        "higher-sample-rate-96000-24",
        "higher-bit-depth-48000-32",
        "reject-low-sample-rate",
        "reject-low-bit-depth",
    ],
)
def test_validate_master_audio_enforces_aiff_minimums_without_modifying_file(
    tmp_path,
    sample_rate_hz,
    bit_depth,
    accepted,
):
    # Preparar: generar un AIFF PCM con propiedades conocidas.
    buffer = io.BytesIO()
    sf.write(
        buffer,
        [0.25] * 48,
        sample_rate_hz,
        format="AIFF",
        subtype=f"PCM_{bit_depth}",
    )
    original_bytes = buffer.getvalue()

    # Confirmar las propiedades del archivo preparado.
    with sf.SoundFile(io.BytesIO(original_bytes)) as prepared:
        assert prepared.format == "AIFF"
        assert prepared.samplerate == sample_rate_hz
        assert prepared.subtype == f"PCM_{bit_depth}"

    with override_settings(BASE_DIR=tmp_path):
        storage = PrivateMasterStorage()

    master_file = Product().master_file
    master_file.storage = storage
    master_file.save(
        "ca-rf11-11-controlled.aiff",
        ContentFile(original_bytes),
        save=False,
    )

    expected_response = nullcontext() if accepted else pytest.raises(ValidationError)

    # Actuar y comprobar: aplicar la regla de calidad.
    with expected_response:
        validate_master_audio(
            master_file=master_file,
            declared_format="aiff",
            declared_sample_rate_hz=sample_rate_hz,
            declared_bit_depth=bit_depth,
        )

    # Comprobar: conservar los bytes originales.
    with master_file.storage.open(master_file.name, "rb") as stored:
        assert stored.read() == original_bytes


@pytest.mark.parametrize("container", ["wav", "bwf", "flac", "aiff"])
def test_validate_master_audio_rejects_truncated_audio(tmp_path, container):
    # Preparar: crear un maestro completo de 48 kHz y 24 bits.
    buffer = io.BytesIO()

    if container in {"wav", "bwf"}:
        with wave.open(buffer, "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(3)
            audio.setframerate(48_000)
            audio.writeframes(b"\x01\x00\x00" * 48)
    else:
        sf.write(
            buffer,
            [0.25] * 48,
            48_000,
            format=container.upper(),
            subtype="PCM_24",
        )

    complete_bytes = buffer.getvalue()
    declared_format = "wav" if container == "bwf" else container

    if container == "bwf":
        complete_bytes = _add_bwf_metadata(complete_bytes, 48_000, 24)
        assert complete_bytes[12:16] == b"bext"

    # Confirmar que el original contiene todo el audio previsto.
    with sf.SoundFile(io.BytesIO(complete_bytes)) as prepared:
        assert prepared.format == declared_format.upper()
        assert prepared.samplerate == 48_000
        assert prepared.subtype == "PCM_24"
        assert len(prepared.read(dtype="int32")) == 48

    # Quitar bytes del final sin actualizar la información del contenedor.
    truncated_bytes = complete_bytes[:-3]

    with override_settings(BASE_DIR=tmp_path):
        storage = PrivateMasterStorage()

    master_file = Product().master_file
    master_file.storage = storage
    master_file.save(
        f"ca-rf11-11-truncated-{container}.{declared_format}",
        ContentFile(truncated_bytes),
        save=False,
    )

    # Actuar y comprobar: rechazar el maestro incompleto.
    with pytest.raises(ValidationError):
        validate_master_audio(
            master_file=master_file,
            declared_format=declared_format,
            declared_sample_rate_hz=48_000,
            declared_bit_depth=24,
        )

    # Comprobar: conservar el archivo rechazado sin modificaciones.
    with master_file.storage.open(master_file.name, "rb") as stored:
        assert stored.read() == truncated_bytes


@pytest.mark.parametrize(
    ("declared_format", "mime_type"),
    [
        ("wav", "audio/wav"),
        ("flac", "audio/flac"),
        ("aiff", "audio/aiff"),
    ],
)
def test_validate_master_audio_rejects_unsupported_content_with_allowed_labels(
    tmp_path,
    declared_format,
    mime_type,
):
    # Preparar: generar un OGG/Vorbis válido.
    buffer = io.BytesIO()
    sf.write(
        buffer,
        [0.25] * 480,
        48_000,
        format="OGG",
        subtype="VORBIS",
    )
    original_bytes = buffer.getvalue()

    # Confirmar que el contenido real es OGG/Vorbis y se puede leer.
    with sf.SoundFile(io.BytesIO(original_bytes)) as prepared:
        assert prepared.format == "OGG"
        assert prepared.subtype == "VORBIS"
        assert prepared.samplerate == 48_000
        assert len(prepared.read(dtype="float32")) == 480

    # Presentarlo con extensión y MIME de un formato admitido.
    uploaded = SimpleUploadedFile(
        f"ca-rf11-11-disguised.{declared_format}",
        original_bytes,
        content_type=mime_type,
    )

    with override_settings(BASE_DIR=tmp_path):
        storage = PrivateMasterStorage()

    master_file = Product().master_file
    master_file.storage = storage
    master_file.save(uploaded.name, uploaded, save=False)

    # Actuar y comprobar: las etiquetas no hacen admisible el contenido.
    with pytest.raises(ValidationError):
        validate_master_audio(
            master_file=master_file,
            declared_format=declared_format,
            declared_sample_rate_hz=48_000,
            declared_bit_depth=24,
        )

    # Comprobar: conservar los bytes del archivo rechazado.
    with master_file.storage.open(master_file.name, "rb") as stored:
        assert stored.read() == original_bytes


@pytest.mark.parametrize(
    ("declared_format", "subtype"),
    [
        ("wav", "IMA_ADPCM"),
        ("aiff", "ULAW"),
    ],
    ids=["wav-adpcm", "aiff-ulaw"],
)
def test_validate_master_audio_rejects_unsupported_encoding(
    tmp_path,
    declared_format,
    subtype,
):
    # Preparar: crear audio legible con una codificación no admitida.
    buffer = io.BytesIO()
    sf.write(
        buffer,
        [0.25] * 480,
        48_000,
        format=declared_format.upper(),
        subtype=subtype,
    )
    original_bytes = buffer.getvalue()

    # Confirmar que el contenedor y su contenido son legibles.
    with sf.SoundFile(io.BytesIO(original_bytes)) as prepared:
        assert prepared.format == declared_format.upper()
        assert prepared.subtype == subtype
        assert prepared.samplerate == 48_000
        assert len(prepared.read()) > 0

    with override_settings(BASE_DIR=tmp_path):
        storage = PrivateMasterStorage()

    master_file = Product().master_file
    master_file.storage = storage
    master_file.save(
        f"ca-rf11-11-unsupported-encoding.{declared_format}",
        ContentFile(original_bytes),
        save=False,
    )

    # Actuar y comprobar: el contenedor admitido no basta.
    with pytest.raises(ValidationError):
        validate_master_audio(
            master_file=master_file,
            declared_format=declared_format,
            declared_sample_rate_hz=48_000,
            declared_bit_depth=24,
        )

    # Comprobar: conservar los bytes originales.
    with master_file.storage.open(master_file.name, "rb") as stored:
        assert stored.read() == original_bytes


@pytest.mark.parametrize(
    ("actual_format", "declared_format"),
    [
        ("wav", "flac"),
        ("wav", "aiff"),
        ("flac", "wav"),
        ("flac", "aiff"),
        ("aiff", "wav"),
        ("aiff", "flac"),
    ],
)
def test_validate_master_audio_rejects_format_mismatch(
    tmp_path,
    actual_format,
    declared_format,
):
    # Preparar: generar un archivo válido que cumple ambos mínimos.
    buffer = io.BytesIO()
    sf.write(
        buffer,
        [0.25] * 480,
        48_000,
        format=actual_format.upper(),
        subtype="PCM_24",
    )
    original_bytes = buffer.getvalue()

    # Confirmar el formato y las propiedades reales.
    with sf.SoundFile(io.BytesIO(original_bytes)) as prepared:
        assert prepared.format == actual_format.upper()
        assert prepared.samplerate == 48_000
        assert prepared.subtype == "PCM_24"
        assert len(prepared.read(dtype="int32")) == 480

    with override_settings(BASE_DIR=tmp_path):
        storage = PrivateMasterStorage()

    master_file = Product().master_file
    master_file.storage = storage
    master_file.save(
        f"ca-rf11-11-mismatched.{declared_format}",
        ContentFile(original_bytes),
        save=False,
    )

    # Actuar y comprobar: rechazar la discrepancia.
    with pytest.raises(ValidationError):
        validate_master_audio(
            master_file=master_file,
            declared_format=declared_format,
            declared_sample_rate_hz=48_000,
            declared_bit_depth=24,
        )

    # Comprobar: conservar los bytes originales.
    with master_file.storage.open(master_file.name, "rb") as stored:
        assert stored.read() == original_bytes


@pytest.mark.parametrize("audio_format", ["wav", "flac", "aiff"])
@pytest.mark.parametrize(
    ("actual_sample_rate_hz", "declared_sample_rate_hz"),
    [
        (48_000, 96_000),
        (96_000, 48_000),
    ],
)
def test_validate_master_audio_rejects_sample_rate_mismatch(
    tmp_path,
    audio_format,
    actual_sample_rate_hz,
    declared_sample_rate_hz,
):
    # Preparar: generar audio válido con frecuencia real conocida.
    buffer = io.BytesIO()
    sf.write(
        buffer,
        [0.25] * 480,
        actual_sample_rate_hz,
        format=audio_format.upper(),
        subtype="PCM_24",
    )
    original_bytes = buffer.getvalue()

    with sf.SoundFile(io.BytesIO(original_bytes)) as prepared:
        assert prepared.format == audio_format.upper()
        assert prepared.samplerate == actual_sample_rate_hz
        assert prepared.subtype == "PCM_24"
        assert len(prepared.read(dtype="int32")) == 480

    with override_settings(BASE_DIR=tmp_path):
        storage = PrivateMasterStorage()

    master_file = Product().master_file
    master_file.storage = storage
    master_file.save(
        f"ca-rf11-11-rate-mismatch.{audio_format}",
        ContentFile(original_bytes),
        save=False,
    )

    # Actuar: declarar otra frecuencia que también cumple el mínimo.
    with pytest.raises(ValidationError, match="no coinciden"):
        validate_master_audio(
            master_file=master_file,
            declared_format=audio_format,
            declared_sample_rate_hz=declared_sample_rate_hz,
            declared_bit_depth=24,
        )

    # Comprobar: conservar el archivo original.
    with master_file.storage.open(master_file.name, "rb") as stored:
        assert stored.read() == original_bytes


@pytest.mark.parametrize(
    ("audio_format", "actual_bit_depth", "declared_bit_depth"),
    [
        ("wav", 24, 32),
        ("wav", 32, 24),
        ("flac", 24, 32),
        ("aiff", 24, 32),
        ("aiff", 32, 24),
    ],
)
def test_validate_master_audio_rejects_bit_depth_mismatch(
    tmp_path,
    audio_format,
    actual_bit_depth,
    declared_bit_depth,
):
    # Preparar: generar audio válido con profundidad real conocida.
    buffer = io.BytesIO()
    sf.write(
        buffer,
        [0.25] * 480,
        48_000,
        format=audio_format.upper(),
        subtype=f"PCM_{actual_bit_depth}",
    )
    original_bytes = buffer.getvalue()

    with sf.SoundFile(io.BytesIO(original_bytes)) as prepared:
        assert prepared.format == audio_format.upper()
        assert prepared.samplerate == 48_000
        assert prepared.subtype == f"PCM_{actual_bit_depth}"
        assert len(prepared.read(dtype="int32")) == 480

    with override_settings(BASE_DIR=tmp_path):
        storage = PrivateMasterStorage()

    master_file = Product().master_file
    master_file.storage = storage
    master_file.save(
        f"ca-rf11-11-depth-mismatch.{audio_format}",
        ContentFile(original_bytes),
        save=False,
    )

    # Actuar: declarar una profundidad diferente de la real.
    with pytest.raises(ValidationError, match="no coinciden"):
        validate_master_audio(
            master_file=master_file,
            declared_format=audio_format,
            declared_sample_rate_hz=48_000,
            declared_bit_depth=declared_bit_depth,
        )

    # Comprobar: conservar el archivo original.
    with master_file.storage.open(master_file.name, "rb") as stored:
        assert stored.read() == original_bytes


@pytest.mark.parametrize("audio_format", ["wav", "flac", "aiff"])
@pytest.mark.parametrize(
    "original_bytes",
    [
        b"",
        b"Esto no contiene audio: archivo de prueba RF-11.",
    ],
    ids=["empty", "not-audio"],
)
def test_validate_master_audio_rejects_empty_or_unreadable_file(
    tmp_path,
    audio_format,
    original_bytes,
):
    # Preparar: guardar contenido vacío o ilegible como supuesto maestro.
    with override_settings(BASE_DIR=tmp_path):
        storage = PrivateMasterStorage()

    master_file = Product().master_file
    master_file.storage = storage
    master_file.save(
        f"ca-rf11-11-unreadable.{audio_format}",
        ContentFile(original_bytes),
        save=False,
    )

    # Actuar: declarar propiedades aparentemente admisibles.
    with pytest.raises(ValidationError):
        validate_master_audio(
            master_file=master_file,
            declared_format=audio_format,
            declared_sample_rate_hz=48_000,
            declared_bit_depth=24,
        )

    # Comprobar: conservar el archivo rechazado sin modificaciones.
    with master_file.storage.open(master_file.name, "rb") as stored:
        assert stored.read() == original_bytes


def test_validate_master_audio_returns_result_bound_to_stored_file(tmp_path):
    # Preparar: crear un maestro válido con contenido conocido.
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(3)
        audio.setframerate(48_000)
        audio.writeframes(b"\x01\x00\x00" * 48)
    original_bytes = buffer.getvalue()

    with override_settings(BASE_DIR=tmp_path):
        storage = PrivateMasterStorage()

    master_file = Product().master_file
    master_file.storage = storage
    master_file.save(
        "ca-rf11-11-bound-master.wav",
        ContentFile(original_bytes),
        save=False,
    )

    # Actuar: validar y recoger el resultado.
    result = validate_master_audio(
        master_file=master_file,
        declared_format="wav",
        declared_sample_rate_hz=48_000,
        declared_bit_depth=24,
    )

    # Comprobar: identificar la referencia y el contenido validado.
    assert result is not None
    assert result.storage_key == master_file.name
    assert result.sha256 == sha256(original_bytes).hexdigest()
    assert result.size_bytes == len(original_bytes)
    assert result.audio_format == "wav"
    assert result.sample_rate_hz == 48_000
    assert result.bit_depth == 24

    # Comprobar: conservar el archivo original.
    with master_file.storage.open(master_file.name, "rb") as stored:
        assert stored.read() == original_bytes


@pytest.mark.django_db
def test_prepare_master_audio_persists_validation_for_stored_file(tmp_path):
    # Preparar: crear y guardar un maestro válido.
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(3)
        audio.setframerate(48_000)
        audio.writeframes(b"\x01\x00\x00" * 48)
    original_bytes = buffer.getvalue()

    with override_settings(BASE_DIR=tmp_path):
        storage = PrivateMasterStorage()

    master_file = Product().master_file
    master_file.storage = storage
    master_file.save(
        "ca-rf11-11-persisted-master.wav",
        ContentFile(original_bytes),
        save=False,
    )

    # Actuar: validar el maestro y registrar su preparación.
    preparation = prepare_master_audio(
        master_file=master_file,
        declared_format="wav",
        declared_sample_rate_hz=48_000,
        declared_bit_depth=24,
    )

    # Comprobar: existe un registro y podemos recuperarlo de PostgreSQL.
    assert preparation.pk is not None
    preparation.refresh_from_db()

    assert preparation.storage_key == master_file.name
    assert preparation.sha256 == sha256(original_bytes).hexdigest()
    assert preparation.size_bytes == len(original_bytes)
    assert preparation.audio_format == "wav"
    assert preparation.sample_rate_hz == 48_000
    assert preparation.bit_depth == 24

    # Comprobar: registrar la preparación no modifica el maestro.
    with master_file.storage.open(master_file.name, "rb") as stored:
        assert stored.read() == original_bytes


@pytest.mark.django_db
def test_prepare_master_audio_is_idempotent_for_same_stored_file(tmp_path):
    # Preparar: guardar un maestro válido en almacenamiento temporal.
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(3)
        audio.setframerate(48_000)
        audio.writeframes(b"\x01\x00\x00" * 48)
    original_bytes = buffer.getvalue()

    with override_settings(BASE_DIR=tmp_path):
        storage = PrivateMasterStorage()

    master_file = Product().master_file
    master_file.storage = storage
    master_file.save(
        "ca-rf11-11-idempotent-master.wav",
        ContentFile(original_bytes),
        save=False,
    )

    # Actuar: preparar por primera vez y conservar su fecha
    first = prepare_master_audio(
        master_file=master_file,
        declared_format="wav",
        declared_sample_rate_hz=48_000,
        declared_bit_depth=24,
    )
    first.refresh_from_db()
    original_prepared_at = first.prepared_at

    # Actuar: repetir la preparación del mismo archivo
    second = prepare_master_audio(
        master_file=master_file,
        declared_format="wav",
        declared_sample_rate_hz=48_000,
        declared_bit_depth=24,
    )
    second.refresh_from_db()

    # Comprobar: se reutiliza el registro y conserva su evidencia.
    assert second.pk == first.pk
    assert MasterAudioPreparation.objects.count() == 1
    assert second.prepared_at == original_prepared_at
    assert second.storage_key == master_file.name
    assert second.sha256 == sha256(original_bytes).hexdigest()
    assert second.size_bytes == len(original_bytes)
    assert second.audio_format == "wav"
    assert second.sample_rate_hz == 48_000
    assert second.bit_depth == 24

    # Comprobar el archivo mantiene sus bytes originales.
    with master_file.storage.open(master_file.name, "rb") as stored:
        assert stored.read() == original_bytes


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("sample_rate_hz", "bit_depth"),
    [
        pytest.param(44_100, 24, id="low-sample-rate"),
        pytest.param(48_000, 16, id="low-bit-depth"),
    ],
)
def test_prepare_master_audio_does_not_persist_invalid_master(
    tmp_path,
    sample_rate_hz,
    bit_depth,
):
    # Preparar: crear un WAV por debajo de uno de los mínimos.
    sample_width = bit_depth // 8
    sample = b"\x01" + b"\x00" * (sample_width - 1)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(sample_width)
        audio.setframerate(sample_rate_hz)
        audio.writeframes(sample * 48)
    original_bytes = buffer.getvalue()

    with override_settings(BASE_DIR=tmp_path):
        storage = PrivateMasterStorage()

    master_file = Product().master_file
    master_file.storage = storage
    master_file.save(
        "ca-rf11-11-invalid-master.wav",
        ContentFile(original_bytes),
        save=False,
    )

    assert not MasterAudioPreparation.objects.exists()

    # Actuar: intentar preparar el maestro y comprobar su rechazo
    with pytest.raises(ValidationError, match="al menos"):
        prepare_master_audio(
            master_file=master_file,
            declared_format="wav",
            declared_sample_rate_hz=sample_rate_hz,
            declared_bit_depth=bit_depth,
        )

    # Comprobar no queda una preparación registrada
    assert not MasterAudioPreparation.objects.exists()

    # Comprobar tampoco se modifica el archivo para hacerlo admisible
    with master_file.storage.open(master_file.name, "rb") as stored:
        assert stored.read() == original_bytes


@pytest.mark.django_db
def test_prepare_master_audio_rejects_changed_content_under_same_key(tmp_path):
    # Preparar: generar dos WAV válidos con distinto contenido.
    original_buffer = io.BytesIO()
    with wave.open(original_buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(3)
        audio.setframerate(48_000)
        audio.writeframes(b"\x01\x00\x00" * 48)
    original_bytes = original_buffer.getvalue()

    replacement_buffer = io.BytesIO()
    with wave.open(replacement_buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(3)
        audio.setframerate(48_000)
        audio.writeframes(b"\x02\x00\x00" * 48)
    replacement_bytes = replacement_buffer.getvalue()

    assert original_bytes != replacement_bytes
    assert len(original_bytes) == len(replacement_bytes)

    with override_settings(BASE_DIR=tmp_path):
        storage = PrivateMasterStorage()

    master_file = Product().master_file
    master_file.storage = storage
    master_file.save(
        "ca-rf11-11-replaced-master.wav",
        ContentFile(original_bytes),
        save=False,
    )

    # Preparar: registrar la validación del archivo original.
    preparation = prepare_master_audio(
        master_file=master_file,
        declared_format="wav",
        declared_sample_rate_hz=48_000,
        declared_bit_depth=24,
    )
    original_evidence = MasterAudioPreparation.objects.values().get(
        pk=preparation.pk,
    )

    # Simular una sustitución física conservando la misma clave.
    with master_file.storage.open(master_file.name, "wb") as stored:
        stored.write(replacement_bytes)

    # Actuar: intentar preparar el contenido sutituido.
    with pytest.raises(ValidationError, match="preparación anterior"):
        prepare_master_audio(
            master_file=master_file,
            declared_format="wav",
            declared_sample_rate_hz=48_000,
            declared_bit_depth=24,
        )

    # Comprobar: no se duplica ni se modifica la evidencia anterior.
    assert MasterAudioPreparation.objects.count() == 1
    assert (
        MasterAudioPreparation.objects.values().get(pk=preparation.pk)
        == original_evidence
    )

    # Comprobar: el servicio tampoco modifica el archivo recibido.
    with master_file.storage.open(master_file.name, "rb") as stored:
        assert stored.read() == replacement_bytes


@pytest.mark.django_db
def test_prepare_master_audio_prepares_new_key_without_changing_original(tmp_path):
    # Preparar: generar dos WAV válidos con distinto contenido.
    original_buffer = io.BytesIO()
    with wave.open(original_buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(3)
        audio.setframerate(48_000)
        audio.writeframes(b"\x01\x00\x00" * 48)
    original_bytes = original_buffer.getvalue()

    replacement_buffer = io.BytesIO()
    with wave.open(replacement_buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(3)
        audio.setframerate(48_000)
        audio.writeframes(b"\x02\x00\x00" * 48)
    replacement_bytes = replacement_buffer.getvalue()

    assert original_bytes != replacement_bytes
    assert len(original_bytes) == len(replacement_bytes)

    with override_settings(BASE_DIR=tmp_path):
        storage = PrivateMasterStorage()

    master_file = Product().master_file
    master_file.storage = storage
    master_file.save(
        "ca-rf11-11-replaced-master.wav",
        ContentFile(original_bytes),
        save=False,
    )

    # Registrar la preparación del maestro original.
    preparation = prepare_master_audio(
        master_file=master_file,
        declared_format="wav",
        declared_sample_rate_hz=48_000,
        declared_bit_depth=24,
    )

    # Conservar su evidencia para compararla después.
    original_evidence = MasterAudioPreparation.objects.values().get(
        pk=preparation.pk,
    )

    # Preparar: guardar el maestro corregido con una clave diferente.
    new_master_file = Product().master_file
    new_master_file.storage = storage
    new_master_file.save(
        "ca-rf11-corrected-master.waw",
        ContentFile(replacement_bytes),
        save=False,
    )

    assert new_master_file.name != master_file.name

    # Actuar: preparar el nuevo maestro.
    new_preparation = prepare_master_audio(
        master_file=new_master_file,
        declared_format="wav",
        declared_sample_rate_hz=48_000,
        declared_bit_depth=24,
    )
    new_preparation.refresh_from_db()

    # Comprobar: cada archivo tiene su propio registro y huella
    assert MasterAudioPreparation.objects.count() == 2
    assert new_preparation.pk != preparation.pk
    assert new_preparation.pk != preparation.pk
    assert new_preparation.storage_key == new_master_file.name
    assert new_preparation.sha256 == sha256(replacement_bytes).hexdigest()
    assert new_preparation.sha256 != preparation.sha256

    # Comprobar: la evidencia del original permanece intacta.
    assert (
        MasterAudioPreparation.objects.values().get(pk=preparation.pk)
        == original_evidence
    )

    # Comprobar que ambos archivos conservan su contenido.
    with master_file.storage.open(master_file.name, "rb") as stored:
        assert stored.read() == original_bytes

    with new_master_file.storage.open(new_master_file.name, "rb") as stored:
        assert stored.read() == replacement_bytes


@pytest.mark.django_db
def test_set_product_master_audio_stores_prepares_and_assigns_first_master(
    tmp_path,
    monkeypatch,
):
    # Preparar: dirigir el almacenamiento privado a una carpeta temporal.
    monkeypatch.setattr(
        private_master_storage,
        "location",
        str(tmp_path / "private_media"),
    )

    # Preparar: crear un producto que todavía no tiene maestro.
    category = Category.objects.create(
        name="Ambientes",
        slug="ambientes",
    )
    product = Product.objects.create(
        category=category,
        name="Ambiente de bosque",
        slug="ambiente-de-bosque",
        sku="AMB-001",
        summary="Ambiente de prueba.",
        description="Grabación controlada para la prueba.",
        duration_ms=1,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
    )
    assert not product.master_file

    # Preparar: crear el archivo que recibirá el servicio.
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(3)
        audio.setframerate(48_000)
        audio.writeframes(b"\x01\x00\x00" * 48)
    original_bytes = buffer.getvalue()

    uploaded_file = SimpleUploadedFile(
        "ambiente.wav",
        original_bytes,
        content_type="audio/wav",
    )

    # Actuar: entregar el archivo al servicio coordinador.
    preparation = set_product_master_audio(
        product_id=product.pk,
        uploaded_file=uploaded_file,
        declared_format="wav",
        declared_sample_rate_hz=48_000,
        declared_bit_depth=24,
    )

    # Comprobar: el producto referencia el maestro preparado.
    product.refresh_from_db()
    preparation.refresh_from_db()

    assert product.master_file.name
    assert product.master_file.name == preparation.storage_key
    assert MasterAudioPreparation.objects.count() == 1
    assert preparation.sha256 == sha256(original_bytes).hexdigest()
    assert preparation.size_bytes == len(original_bytes)
    assert preparation.audio_format == product.audio_format == "wav"
    assert preparation.sample_rate_hz == product.sample_rate_hz == 48_000
    assert preparation.bit_depth == product.bit_depth == 24

    # Comprobar: los bytes recibidos se conservan en el almacenamiento.
    with product.master_file.storage.open(
        product.master_file.name,
        "rb",
    ) as stored:
        assert stored.read() == original_bytes


@pytest.mark.django_db
def test_set_product_master_audio_replaces_master_and_preserves_original(
    tmp_path,
    monkeypatch,
):
    # Preparar: utilizar almacenamiento privado temporal.
    monkeypatch.setattr(
        private_master_storage,
        "location",
        str(tmp_path / "private_media"),
    )

    category = Category.objects.create(
        name="Ambientes",
        slug="ambientes",
    )
    product = Product.objects.create(
        category=category,
        name="Ambiente de bosque",
        slug="ambiente-de-bosque",
        sku="AMB-001",
        summary="Ambiente de prueba.",
        description="Grabación controlada para la prueba.",
        duration_ms=1,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
    )

    # Preparar: generar el maestro original A.
    original_buffer = io.BytesIO()
    with wave.open(original_buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(3)
        audio.setframerate(48_000)
        audio.writeframes(b"\x01\x00\x00" * 48)
    original_bytes = original_buffer.getvalue()

    # Preparar: generar el maestro corregido B.
    replacement_buffer = io.BytesIO()
    with wave.open(replacement_buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(3)
        audio.setframerate(48_000)
        audio.writeframes(b"\x02\x00\x00" * 48)
    replacement_bytes = replacement_buffer.getvalue()

    assert original_bytes != replacement_bytes

    # Preparar: asignar A al producto mediante el servicio.
    original_preparation = set_product_master_audio(
        product_id=product.pk,
        uploaded_file=SimpleUploadedFile(
            "bosque.wav",
            original_bytes,
            content_type="audio/wav",
        ),
        declared_format="wav",
        declared_sample_rate_hz=48_000,
        declared_bit_depth=24,
    )
    product.refresh_from_db()
    original_key = product.master_file.name

    assert original_key == original_preparation.storage_key

    original_evidence = MasterAudioPreparation.objects.values().get(
        pk=original_preparation.pk,
    )

    # Actuar: llamar al mismo servicio para sustituir A por B.
    new_preparation = set_product_master_audio(
        product_id=product.pk,
        uploaded_file=SimpleUploadedFile(
            "bosque.wav",
            replacement_bytes,
            content_type="audio/wav",
        ),
        declared_format="wav",
        declared_sample_rate_hz=48_000,
        declared_bit_depth=24,
    )

    # Comprobar: el producto ahora referencia B con otra clave.
    product.refresh_from_db()
    new_preparation.refresh_from_db()

    assert product.master_file.name == new_preparation.storage_key
    assert product.master_file.name != original_key
    assert new_preparation.pk != original_preparation.pk
    assert new_preparation.sha256 == sha256(replacement_bytes).hexdigest()
    assert MasterAudioPreparation.objects.count() == 2

    # Comprobar: la evidencia de A permanece intacta.
    assert (
        MasterAudioPreparation.objects.values().get(
            pk=original_preparation.pk,
        )
        == original_evidence
    )

    # Comprobar: ambos archivos mantienen sus bytes.
    storage = product.master_file.storage

    with storage.open(original_key, "rb") as stored:
        assert stored.read() == original_bytes

    with storage.open(new_preparation.storage_key, "rb") as stored:
        assert stored.read() == replacement_bytes


@pytest.mark.django_db
def test_set_product_master_audio_rejects_invalid_replacement_without_changes(
    tmp_path,
    monkeypatch,
):
    # Preparar: utilizar almacenamiento privado temporal.
    private_directory = tmp_path / "private_media"
    monkeypatch.setattr(
        private_master_storage,
        "location",
        str(private_directory),
    )

    category = Category.objects.create(
        name="Ambientes",
        slug="ambientes",
    )
    product = Product.objects.create(
        category=category,
        name="Ambiente de bosque",
        slug="ambiente-de-bosque",
        sku="AMB-001",
        summary="Ambiente de prueba.",
        description="Grabación controlada para la prueba.",
        duration_ms=1,
        audio_format="wav",
        sample_rate_hz=48_000,
        bit_depth=24,
    )

    # Preparar: generar y asignar el maestro original válido.
    original_buffer = io.BytesIO()
    with wave.open(original_buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(3)
        audio.setframerate(48_000)
        audio.writeframes(b"\x01\x00\x00" * 48)
    original_bytes = original_buffer.getvalue()

    original_preparation = set_product_master_audio(
        product_id=product.pk,
        uploaded_file=SimpleUploadedFile(
            "bosque.wav",
            original_bytes,
            content_type="audio/wav",
        ),
        declared_format="wav",
        declared_sample_rate_hz=48_000,
        declared_bit_depth=24,
    )
    product.refresh_from_db()
    original_key = product.master_file.name

    # Conservar el estado previo del producto, su evidencia y los archivos.
    original_product_data = Product.objects.values().get(pk=product.pk)
    original_evidence = MasterAudioPreparation.objects.values().get(
        pk=original_preparation.pk,
    )
    files_before = {
        path.relative_to(private_directory)
        for path in private_directory.rglob("*")
        if path.is_file()
    }
    assert files_before

    # Preparar: generar un WAV de 16 bits, inferior al mínimo.
    invalid_buffer = io.BytesIO()
    with wave.open(invalid_buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(48_000)
        audio.writeframes(b"\x02\x00" * 48)
    invalid_bytes = invalid_buffer.getvalue()

    # Actuar: intentar sustituir el maestro por el archivo inválido.
    with pytest.raises(ValidationError, match="al menos"):
        set_product_master_audio(
            product_id=product.pk,
            uploaded_file=SimpleUploadedFile(
                "bosque.wav",
                invalid_bytes,
                content_type="audio/wav",
            ),
            declared_format="wav",
            declared_sample_rate_hz=48_000,
            declared_bit_depth=16,
        )

    # Comprobar: el producto conserva su referencia y sus datos.
    product.refresh_from_db()
    assert product.master_file.name == original_key
    assert Product.objects.values().get(pk=product.pk) == original_product_data

    # Comprobar: solo permanece la preparación original, sin cambios.
    assert MasterAudioPreparation.objects.count() == 1
    assert (
        MasterAudioPreparation.objects.values().get(
            pk=original_preparation.pk,
        )
        == original_evidence
    )

    # Comprobar: el archivo rechazado no permanece almacenado.
    files_after = {
        path.relative_to(private_directory)
        for path in private_directory.rglob("*")
        if path.is_file()
    }
    assert files_after == files_before

    # Comprobar: el maestro original mantiene sus bytes.
    with product.master_file.storage.open(original_key, "rb") as stored:
        assert stored.read() == original_bytes
