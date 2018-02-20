timestamp_utc_created_lsi = "LSI_TIMESTAMP_UTC_CREATED_RANGE"
id_lsi = "LSI_ID_RANGE"
hash_key = 'user_uid'
range_key = 'timestamp_utc'
dynamodb_users_table_init_information = {
    "KeySchema": [
        {
            'AttributeName': hash_key,
            'KeyType': 'HASH'
        },
        {
            'AttributeName': range_key,
            'KeyType': 'RANGE'
        }
    ],
    "AttributeDefinitions": [
        {
            'AttributeName': hash_key,
            'AttributeType': 'S'
        },
        {
            'AttributeName': range_key,
            'AttributeType': 'S'
        },
        {
            "AttributeName": 'id',
            "AttributeType": "S"
        },
        {
            "AttributeName": 'timestamp_utc_created',
            "AttributeType": "S"
        },

    ],
    "LocalSecondaryIndexes": [
        {
            "IndexName": id_lsi,
            "KeySchema": [
                {"AttributeName": hash_key, "KeyType": "HASH"},
                {"AttributeName": 'id', "KeyType": "RANGE"},
            ],
            "Projection": {"ProjectionType": "ALL"}
        },
        {
            "IndexName": timestamp_utc_created_lsi,
            "KeySchema": [
                {"AttributeName": hash_key, "KeyType": "HASH"},
                {"AttributeName": 'timestamp_utc_created', "KeyType": "RANGE"},
            ],
            "Projection": {"ProjectionType": "ALL"}
        },

    ],
    "ProvisionedThroughput": {"ReadCapacityUnits": 25, "WriteCapacityUnits": 25}
}

# against each property is the name of the LSI, in which the property acts as a RANGE key.
# there's one entry with value None - that's the RANGE property of the base table
index_for_property = {
    range_key: None,  # use main table
    'timestamp_utc_created': timestamp_utc_created_lsi,
    'id': id_lsi
}  # TODO extract this from dynamodb_users_table_init_information

assert len([o for o in index_for_property.values() if
            o is None]) == 1, "There must be one and only one property with value None. " \
                              "This property is the RANGE key in the base table."
