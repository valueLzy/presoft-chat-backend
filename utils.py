import os
import uuid

from minio import Minio
from passlib.context import CryptContext

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

minio_client = Minio(
    "192.168.1.21:19000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False,
)


def get_hashed_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, hashed_pass: str) -> bool:
    return password_context.verify(password, hashed_pass)


def download_file(bucket_name: str, file_name: str) -> str:
    unique_id = str(uuid.uuid4())
    folder_path = f'./data/{unique_id}'
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, file_name)
    try:
        minio_client.fget_object(
            bucket_name=bucket_name,
            object_name=file_name,
            file_path=file_path,
        )
        return str(file_path)
    except Exception as e:
        return ""


def put_file(bucket_name: str, file_name: str, file_path: str) -> bool:
    try:
        minio_client.fput_object(
            bucket_name=bucket_name,
            object_name=file_name,
            file_path=file_path,
        )
        return True
    except Exception as e:
        return False


if __name__ == '__main__':
    # print(put_file("vue-file", "test.xlsx", "data/test.xlsx"))
    print(download_file("vue-file", "test.xlsx"))
