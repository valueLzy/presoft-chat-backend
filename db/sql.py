from db.db import execute_query


def get_user_with_menus(username, password, language):
    query = """
    SELECT 
        u.userId, 
        u.userName, 
        u.roles, 
        GROUP_CONCAT(
            CASE 
                WHEN %s = 'zh' THEN m.zh_name 
                WHEN %s = 'ja' THEN m.ja_name 
                ELSE m.zh_name  -- 默认使用 zh_name 或者根据实际需求选择
            END 
            ORDER BY m.id SEPARATOR '，'
        ) as menuNames, 
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
    params = (language, language, username, password)
    return execute_query(query, params)


def check_username_exists(username):
    query = """
    SELECT 
        COUNT(*) AS userCount
    FROM 
        user u
    WHERE 
        u.userName = %s;
    """
    params = username
    result = execute_query(query, params)
    return result[0][0] > 0 if result else False


def insert_user(user_id, username, roles, menus, desc, password, company, nationality):
    query = """
    INSERT INTO `user` (
        `userId`, 
        `userName`, 
        `roles`, 
        `menus`, 
        `desc`, 
        `password`,
        `company`,
        `nationality`
    ) VALUES (
        %s, 
        %s, 
        %s, 
        %s, 
        %s, 
        %s, 
        %s, 
        %s
    );
    """
    params = (user_id, username, roles, menus, desc, password, company, nationality)
    return execute_query(query, params)
