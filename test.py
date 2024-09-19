from nebula3.gclient.net import ConnectionPool
from nebula3.Config import Config

config = Config()
# 最大连接数
config.max_connection_pool_size = 10
# 连接超时时间
config.timeout = 60000
# 关闭空闲连接时间
config.idle_time = 0
# 检查空闲连接时间间隔
config.interval_check = -1
connection_pool = ConnectionPool()
ok = connection_pool.init([('192.168.2.8', 9669)], config)
with connection_pool.session_context('root', 'nebula') as sess:
    sess.execute('''
        # Create Space 
        CREATE SPACE `lzy` (partition_num = 1, replica_factor = 1, charset = utf8, collate = utf8_bin, vid_type = FIXED_STRING(256));
         USE `lzy`;
        # Create Tag: 
        CREATE TAG `entity` ( `name` string NULL, `belong_file_name` string NULL) ttl_duration = 0, ttl_col = "";
        CREATE EDGE `relationship` ( `relationship` string NULL) ttl_duration = 0, ttl_col = "";
        CREATE TAG INDEX `entity_index` ON `entity` ( `name`(256));
    ''')
