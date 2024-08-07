# 给定的列表
data = [
    {'description': '论文', 'name': 'damage_explosion_v1'},
    {'description': 'open_project', 'name': 'open_project'},
    {'description': 'v2', 'name': 'damage_explosion_v2'},
    {'description': '', 'name': '_3'}
]

# 要判断的字符串
target_string = '_3'

# 判断字符串是否在列表的 name 值中
is_in_name = any(item['name'] == target_string for item in data)

# 输出结果
if is_in_name:
    print(f"'{target_string}' 是列表中的一个 name 值")
else:
    print(f"'{target_string}' 不是列表中的一个 name 值")