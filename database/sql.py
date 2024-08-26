import uuid
from datetime import datetime

from database.db import execute_query


def get_user_with_menus(username, password, language):
    # 查询用户信息
    user_query = """
    SELECT 
        u.userId, 
        u.userName, 
        u.roles, 
        u.desc, 
        u.password
    FROM 
        user u
    WHERE 
        u.userName = %s AND 
        u.password = %s;
    """

    user_info = execute_query(user_query, (username, password))

    if not user_info:
        return None  # 如果没有找到用户，返回 None

    # 假设 user_info 只有一条记录
    user_info = user_info[0]

    # 获取父菜单
    parent_query = """
    SELECT 
        m.id,
        m.path,
        m.name,
        CASE 
            WHEN %s = 'zh' THEN m.zh_name 
            WHEN %s = 'ja' THEN m.ja_name 
            ELSE m.zh_name  -- 默认使用 zh_name 或者根据实际需求选择
        END as menuName,
        m.url,
        m.icon
    FROM 
        user u
    LEFT JOIN 
        menu m ON FIND_IN_SET(m.id, u.menus)
    WHERE 
        u.userName = %s AND 
        u.password = %s AND
        m.parent_id IS NULL
    ORDER BY m.id;
    """

    parent_menus = execute_query(parent_query, (language, language, username, password))

    # 如果没有父菜单，直接返回
    if not parent_menus:
        return {"user_info": user_info, "menuList": []}

    # 获取父菜单的ID列表
    parent_ids = [str(menu[0]) for menu in parent_menus]

    # 将父菜单的ID列表转换为字符串
    parent_ids_str = ','.join(parent_ids)

    # 获取子菜单
    child_query = f"""
    SELECT 
        m.id,
        m.path,
        m.name,
        CASE 
            WHEN %s = 'zh' THEN m.zh_name 
            WHEN %s = 'ja' THEN m.ja_name 
            ELSE m.zh_name
        END as menuName,
        m.url,
        m.parent_id,
        m.icon
    FROM 
        menu m
    WHERE 
        FIND_IN_SET(m.parent_id, '{parent_ids_str}')
    ORDER BY m.id;
    """

    child_menus = execute_query(child_query, (language, language))

    # 确保 menu_dict 中存储的是字典而非元组
    menu_dict = {menu[0]: {
        'id': menu[0],
        'path': menu[1],
        'name': menu[2],
        'meta': {
            'zh_title': menu[3],
            'ja_title': menu[3],  # 假设两者是一样的
            'icon': menu[5] or 'Monitor'  # 使用数据库中的图标字段，默认图标为 Monitor
        },
        'url': menu[4],  # 这里确保索引是4而不是5
        'children': []  # 初始化 children 为一个空列表
    } for menu in parent_menus}

    for child in child_menus:
        parent_id = child[5]
        if parent_id in menu_dict:
            menu_dict[parent_id]['children'].append({
                'path': child[1],
                'name': child[2],
                'meta': {
                    'zh_title': child[3],
                    'ja_title': child[3],  # 假设两者是一样的
                    'icon': child[6] or 'Monitor'  # 使用数据库中的图标字段
                },
                'url': child[4]  # 这里确保索引是4而不是5
            })

    # 构建菜单列表
    menu_list = [menu for menu in menu_dict.values()]

    return {"user_info": user_info, "menuList": menu_list}


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


def insert_knowledge(id, name, description, milvus_name, graph_name, user_id, create_time):
    try:
        query = """
        INSERT INTO `knowledge_manage` (
            `id`, 
            `name`, 
            `description`, 
            `milvus_name`, 
            `graph_name`, 
            `user_id`, 
            `create_time`
        ) VALUES (
            %s, 
            %s, 
            %s, 
            %s, 
            %s, 
            %s, 
            %s
        );
        """
        params = (id, name, description, milvus_name, graph_name, user_id, create_time)
        return execute_query(query, params)
    except Exception as e:
        raise e


def insert_history_qa(user_id, user_say, ai_say, type):
    try:
        query = """
        INSERT INTO `history_qa` (
            `id`, 
            `user_id`, 
            `user_say`, 
            `ai_say`, 
            `type`, 
            `time`
        ) VALUES (
            %s, 
            %s, 
            %s, 
            %s, 
            %s, 
            %s
        );
        """
        params = (str(uuid.uuid4()), user_id, user_say, ai_say, type, datetime.now())
        return execute_query(query, params)
    except Exception as e:
        raise e


def get_knowledge_by_user(user_id):
    query = """
    SELECT 
        id, 
        name, 
        description, 
        milvus_name, 
        graph_name, 
        user_id, 
        create_time
    FROM 
        knowledge_manage
    WHERE 
        %s = 1 OR user_id = %s;
    """
    params = (user_id, user_id)
    return execute_query(query, params)


def delete_knowledge_by_name_and_user(name, user_id):
    try:
        query = """
        DELETE FROM 
            knowledge_manage
        WHERE 
            name = %s AND user_id = %s;
        """
        params = (name, user_id)
        return execute_query(query, params)
    except Exception as e:
        raise e


def query_history_by_user_and_type(user_id, type):
    try:
        query = """
        SELECT `user_say`, `ai_say`, `time`
        FROM `history_qa`
        WHERE `user_id` = %s AND `type` = %s
        ORDER BY `time` DESC;
        """
        params = (user_id, type)
        return execute_query(query, params)
    except Exception as e:
        raise e