import hashlib
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


def md5_encrypt(password):
    # 创建一个md5哈希对象
    md5 = hashlib.md5()

    # 更新哈希对象以包含密码的二进制数据
    md5.update(password.encode('utf-8'))

    # 获取加密后的十六进制表示
    encrypted_password = md5.hexdigest()

    return encrypted_password


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
    print(get_hashed_password("123456"))
