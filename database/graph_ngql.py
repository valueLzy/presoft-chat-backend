from nebula3.gclient.net import ConnectionPool
from nebula3.Config import Config


def create_nebula_space_and_schema(space_name):
    try:
        config = Config()
        config.max_connection_pool_size = 10
        config.timeout = 60000
        config.idle_time = 0
        config.interval_check = -1

        connection_pool = ConnectionPool()
        ok = connection_pool.init([('192.168.2.8', 9669)], config)

        if not ok:
            raise Exception("Failed to initialize connection pool")

        with connection_pool.session_context('root', 'nebula') as sess:
            sess.execute(f'''
                CREATE SPACE `{space_name}` (partition_num = 1, replica_factor = 1, charset = utf8, collate = utf8_bin, vid_type = FIXED_STRING(256));
                USE `{space_name}`;
                CREATE TAG `entity` ( `name` string NULL) ttl_duration = 0, ttl_col = "";
                CREATE EDGE `relationship` ( `relationship` string NULL) ttl_duration = 0, ttl_col = "";
                CREATE TAG INDEX `entity_index` ON `entity` ( `name`(256));
            ''')
    except Exception as e:
        raise e


def drop_space(space_name):
    try:
        config = Config()
        config.max_connection_pool_size = 10
        config.timeout = 60000
        config.idle_time = 0
        config.interval_check = -1

        connection_pool = ConnectionPool()
        ok = connection_pool.init([('192.168.2.8', 9669)], config)

        if not ok:
            raise Exception("Failed to initialize connection pool")

        with connection_pool.session_context('root', 'nebula') as sess:
            sess.execute(f'''
                DROP SPACE `{space_name}`;
            ''')
    except Exception as e:
        raise e


# 示例调用
if __name__ == '__main__':
    create_nebula_space_and_schema('test')
