import hashlib


def md5_encrypt(password):
    # 创建一个md5哈希对象
    md5 = hashlib.md5()

    # 更新哈希对象以包含密码的二进制数据
    md5.update(password.encode('utf-8'))

    # 获取加密后的十六进制表示
    encrypted_password = md5.hexdigest()

    return encrypted_password
