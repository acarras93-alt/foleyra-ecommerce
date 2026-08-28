from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PreviewStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(
            location=settings.BASE_DIR / "media",
            base_url="/media/",
        )


class PrivateMasterStorage(FileSystemStorage):
    def __init__(self):
        super().__init__(location=settings.BASE_DIR / "private_media")

    def url(self, name):
        raise NotImplementedError("Private storage does not provide public URLs.")
