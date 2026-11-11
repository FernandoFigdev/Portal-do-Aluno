import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateStorage(FileSystemStorage):
    """Armazenamento fora de MEDIA_URL: os arquivos nunca têm URL pública (RF20, RNF11).

    O download só ocorre por views autenticadas que verificam o dono do arquivo.
    O diretório é lido de settings.PRIVATE_MEDIA_ROOT a cada uso.
    """

    @property
    def base_location(self):
        return str(settings.PRIVATE_MEDIA_ROOT)

    @property
    def location(self):
        return os.path.abspath(self.base_location)

    @property
    def base_url(self):
        return None


private_storage = PrivateStorage()
