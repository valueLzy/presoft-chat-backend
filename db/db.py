import pymysql

# 数据库配置
db_config = {
    'host': '192.168.1.21',
    'user': 'your_username',  # 这里填写你的MySQL用户名
    'password': '123456',
    'database': 'your_database_name',  # 这里填写你的数据库名
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

def get_user_with_menus(username, password):
    query = """
    SELECT 
        u.userId, 
        u.userName, 
        u.roles, 
        GROUP_CONCAT(m.name ORDER BY m.id SEPARATOR '，') as menuNames, 
        u.desc, 
        u.password
    FROM 
        user u
    LEFT JOIN 
        menu m ON FIND_IN_SET(m.id, u.menus)
    WHERE 
        u.userName = %s AND 
        u.password = %s
    GROUP BY 
        u.userId, 
        u.userName, 
        u.roles, 
        u.desc, 
        u.password;
    """
    params = (username, password)
    return execute_query(query, params)