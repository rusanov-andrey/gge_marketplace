from django.core.files.storage import default_storage
from django.core.files.uploadedfile import UploadedFile


class TaskFileStorage:
    def save_task_file(self, task_id: int, uploaded_file: UploadedFile) -> str:
        file_name = f"task_{task_id}_{uploaded_file.name}"

        saved_path = default_storage.save(file_name, uploaded_file)
        return saved_path

    def delete_file(self, file_path: str) -> None:
        default_storage.delete(file_path)

    def open_task_file(self, file_path: str):
        return default_storage.open(file_path, 'rb')
