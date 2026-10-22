import pytest

from apps.catalog.models import private_master_storage


@pytest.fixture(autouse=True)
def isolate_private_master_storage(tmp_path, monkeypatch):
    """Mantener los archivos de las pruebas de pedidos fuera del almacenamiento real."""
    monkeypatch.setattr(
        private_master_storage,
        "location",
        str(tmp_path / "private_media"),
    )
