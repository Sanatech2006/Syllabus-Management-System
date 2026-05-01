import os
import time

from django.core.files.storage import FileSystemStorage


class OverwriteStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        if self.exists(name):
            file_path = self.path(name)
            last_error = None

            for _ in range(5):
                try:
                    os.remove(file_path)
                    last_error = None
                    break
                except PermissionError as exc:
                    last_error = exc
                    try:
                        os.chmod(file_path, 0o666)
                    except OSError:
                        pass
                    time.sleep(0.4)

            if last_error is not None:
                raise PermissionError(
                    f"Could not replace '{file_path}'. Close any open PDF tabs or file previews and try again."
                ) from last_error
        return name
