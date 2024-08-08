from pymilvus import CollectionSchema, Collection, connections, FieldSchema, DataType
from pymilvus.orm import utility

connections.connect(
    alias="default",
    user='root',
    password='Milvus',
    host='192.168.1.21',
    port='19530',
)


def get_milvus_collections_info():
    # 获取所有集合的名称
    collection_names = utility.list_collections()

    collections_info = []
    for name in collection_names:
        # 获取集合的详细信息
        collection = Collection(name)
        collection_info = {
            'name': name,
            'description': collection.description if hasattr(collection, 'description') else 'No description available',
            'entity': collection.num_entities
        }
        collections_info.append(collection_info)

    return collections_info


def create_milvus(collection_name, description):
    try:
        id = FieldSchema(
            name='id',
            dtype=DataType.INT64,
            is_primary=True,
            auto_id=True
        )
        text = FieldSchema(
            name='text',
            dtype=DataType.VARCHAR,
            max_length=9999
        )
        embeddings = FieldSchema(
            name='embeddings',
            dtype=DataType.FLOAT_VECTOR,
            dim=1024
        )
        file_name = FieldSchema(
            name='file_name',
            dtype=DataType.VARCHAR,
            max_length=999
        )

        fields = [id, text, embeddings, file_name]

        schema = CollectionSchema(
            fields=fields,  # 字段,
            description=description,  # 描述
            enable_dynamic_field=False  # 启用动态模式
        )
        collection_name = collection_name

        Collection(
            name=collection_name,
            schema=schema,
            using='default'
        )
        create_milvus_index(collection_name)
        # Get an existing collection.
        collection = Collection(collection_name)
        collection.load()

        # Check the loading progress and loading status
        utility.load_state(collection_name)
        # Output: <LoadState: Loaded>

        utility.loading_progress(collection_name)
        return 'success'
    except Exception as e:
        return e


def insert_milvus(data, collection_name):
    collection = Collection(collection_name)
    mr = collection.insert(data)


def upsert_milvus(data, collection_name):
    collection = Collection(collection_name)
    mr = collection.upsert(data)


def search_milvus(vector, collection_name, matches_number):
    collection = Collection(collection_name)
    search_params = {
        "metric_type": "COSINE",
        "offset": 0,
        "ignore_growing": False
    }
    results = collection.search(
        data=[vector],
        anns_field="embeddings",
        param=search_params,
        limit=matches_number,
        expr=None,
        output_fields=['text'],
    )
    return results


def search_milvus_lunwen(vector, collection_name, matches_number, filter_expr):
    collection = Collection(collection_name)
    search_params = {
        "metric_type": "COSINE",
        "offset": 0,
        "ignore_growing": False
    }
    results = collection.search(
        data=[vector],
        anns_field="embeddings",
        param=search_params,
        limit=matches_number,
        expr=filter_expr,
        output_fields=['text', 'file_name'],
    )
    return results


def create_milvus_index(collection_name):
    collection = Collection(collection_name)
    index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 1024}
    }
    collection.create_index(
        field_name="embeddings",
        index_params=index_params
    )

    utility.index_building_progress(collection_name)


def query_milvus(collection_name):
    collection = Collection(collection_name)
    res = collection.query(
        expr=f"id > 0",
        output_fields=["text"],
    )
    return res


def del_entity(collection_name):
    collection = Collection(collection_name)
    expr = 'id > 0'
    collection.delete(expr)


def delete_milvus(collection_name):
    try:
        utility.drop_collection(collection_name)
        return 'success'
    except Exception as e:
        return e


if __name__ == '__main__':
    delete_milvus('1231')
