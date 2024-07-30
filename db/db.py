import pymysql

# 数据库配置
db_config = {
    'host': '192.168.1.21',
    'user': 'root',
    'password': '123456',
    'database': 'persoft',
    'port': 3307
}

def get_db_connection():
    try:
        connection = pymysql.connect(**db_config)
        return connection
    except pymysql.MySQLError as e:
        print(f"Error connecting to MySQL Platform: {e}")
        return None

def execute_query(query, params=None):
    connection = get_db_connection()
    if connection is not None:
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchall()
                return result
        except pymysql.MySQLError as e:
            print(f"Error executing query: {e}")
        finally:
            connection.close()
    return None
