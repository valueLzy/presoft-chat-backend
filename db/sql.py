from db.db import execute_query


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