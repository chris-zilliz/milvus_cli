from tabulate import tabulate


def getPackageVersion():
    import pkg_resources  # part of setuptools
    return pkg_resources.require("milvus_cli")[0].version

class ParameterException(Exception):
    "Custom Exception for parameters checking."

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)

class ConnectException(Exception):
    "Custom Exception for milvus connection."

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)


FiledDataTypes = [
    "BOOL",
    "INT8",
    "INT16",
    "INT32",
    "INT64",
    "FLOAT",
    "DOUBLE",
    "STRING",
    "BINARY_VECTOR",
    "FLOAT_VECTOR"
]

IndexTypes = [
    "FLAT",
    "IVF_FLAT",
    "IVF_SQ8",
    # "IVF_SQ8_HYBRID",
    "IVF_PQ",
    "HNSW",
    # "NSG",
    "ANNOY",
    "RHNSW_FLAT",
    "RHNSW_PQ",
    "RHNSW_SQ",
    "BIN_FLAT",
    "BIN_IVF_FLAT"
]

IndexParams = [
    "nlist",
    "m",
    "nbits",
    "M",
    "efConstruction",
    "n_trees",
    "PQM"
]

MetricTypes = [
    "L2",
    "IP",
    "HAMMING",
    "TANIMOTO"
]

def validateParamsByCustomFunc(customFunc, errMsg, *params):
    try:
        customFunc(*params)
    except Exception as e:
        raise ParameterException(f"{errMsg}")


def validateCollectionParameter(collectionName, primaryField, fields):
    if not collectionName:
        raise ParameterException('Missing collection name.')
    if not primaryField:
        raise ParameterException('Missing primary field.')
    if not fields:
        raise ParameterException('Missing fields.')
    fieldNames = []
    for field in fields:
        fieldList = field.split(':')
        if not (len(fieldList) == 3):
            raise ParameterException(
                'Field should contain three paremeters and concat by ":".')
        [fieldName, fieldType, fieldData] = fieldList
        fieldNames.append(fieldName)
        if fieldType not in FiledDataTypes:
            raise ParameterException(
                'Invalid field data type, should be one of {}'.format(str(FiledDataTypes)))
        if fieldType in ['BINARY_VECTOR', 'FLOAT_VECTOR']:
            try:
                int(fieldData)
            except ValueError as e:
                raise ParameterException("""Vector's dim should be int.""")
    # Dedup field name.
    newNames = list(set(fieldNames))
    if not (len(newNames) == len(fieldNames)):
        raise ParameterException('Field names are duplicated.')
    if primaryField not in fieldNames:
        raise ParameterException(
            """Primary field name doesn't exist in input fields.""")


def validateIndexParameter(indexType, metricType, params):
    if indexType not in IndexTypes:
        raise ParameterException(
            'Invalid index type, should be one of {}'.format(str(IndexTypes)))
    if metricType not in MetricTypes:
        raise ParameterException(
            'Invalid index metric type, should be one of {}'.format(str(MetricTypes)))
    if not params:
        raise ParameterException('Missing params')
    paramNames = []
    for param in params:
        paramList = param.split(':')
        if not (len(paramList) == 2):
            raise ParameterException(
                'Params should contain two paremeters and concat by ":".')
        [paramName, paramValue] = paramList
        paramNames.append(paramName)
        if paramName not in IndexParams:
            raise ParameterException(
                'Invalid index param, should be one of {}'.format(str(IndexParams)))
        try:
            int(paramValue)
        except ValueError as e:
            raise ParameterException("""Index param's value should be int.""")
    # Dedup field name.
    newNames = list(set(paramNames))
    if not (len(newNames) == len(paramNames)):
        raise ParameterException('Index params are duplicated.')


def validateSearchParams(data, annsField, metricType, params, limit, expr, partitionNames, timeout):
    import json
    result = {}
    # Validate data
    try:
        result['data'] = json.loads(data.replace('\'', '').replace('\"', ''))
    except Exception as e:
        raise ParameterException(
            'Format(list[list[float]]) "Data" error! {}'.format(str(e)))
    # Validate annsField
    if not annsField:
        raise ParameterException('annsField is empty!')
    result['anns_field'] = annsField
    # Validate metricType
    if metricType not in MetricTypes:
        raise ParameterException(
            'Invalid index metric type, should be one of {}'.format(str(MetricTypes)))
    # Validate params
    paramDict = {}
    paramsList = params.replace(' ', '').split(',')
    for param in paramsList:
        if not param:
            continue
        paramList = param.split(':')
        if not (len(paramList) == 2):
            raise ParameterException(
                'Params should contain two paremeters and concat by ":".')
        [paramName, paramValue] = paramList
        paramDict[paramName] = paramValue
        if paramName not in IndexParams:
            raise ParameterException(
                'Invalid search parameter, should be one of {}'.format(str(IndexParams)))
        try:
            int(paramValue)
        except ValueError as e:
            raise ParameterException(
                """Search parameter's value should be int.""")
    result['param'] = {"metric_type": metricType}
    if paramDict.keys():
        result['param']['params'] = paramDict
    #  Validate limit
    try:
        result['limit'] = int(limit)
    except Exception as e:
        raise ParameterException(
            'Format(int) "limit" error! {}'.format(str(e)))
    # Validate expr
    if not expr:
        raise ParameterException('expr is empty!')
    result['expr'] = expr
    # Validate partitionNames
    if partitionNames:
        try:
            result['partition_names'] = partitionNames.replace(
                ' ', '').split(',')
        except Exception as e:
            raise ParameterException(
                'Format(list[str]) "partitionNames" error! {}'.format(str(e)))
    # Validate timeout
    if timeout:
        result['timeout'] = float(timeout)
    return result


def validateQueryParams(expr, partitionNames, outputFields, timeout):
    result = {}
    if not expr:
        raise ParameterException('expr is empty!')
    result['expr'] = expr
    if not outputFields:
        result['output_fields'] = None
    else:
        nameList = outputFields.replace(' ', '').split(',')
        result['output_fields'] = nameList
    if not partitionNames:
        result['partition_names'] = None
    else:
        nameList = partitionNames.replace(' ', '').split(',')
        result['partition_names'] = nameList
    result['timeout'] = float(timeout) if timeout else None
    return result


checkEmpty = lambda x: not not x

class PyOrm(object):
    host = '127.0.0.1'
    port = 19530
    alias = 'default'

    def connect(self, alias=None, host=None, port=None):
        self.alias = alias
        self.host = host
        self.port = port
        from pymilvus_orm import connections
        connections.connect(self.alias, host=self.host, port=self.port)
    
    def checkConnection(self):
        from pymilvus_orm import list_collections
        try:
            list_collections(timeout=10.0, using=self.alias)
        except Exception as e:
            raise ConnectException(f'Connect to Milvus error!{str(e)}')

    def showConnection(self, alias="default", showAll=False):
        from pymilvus_orm import connections
        tempAlias = self.alias if self.alias else alias
        allConnections = connections.list_connections()
        if showAll:
            return tabulate(allConnections, headers=['Alias', 'Instance'], tablefmt='pretty')
        aliasList = map(lambda x: x[0], allConnections)
        if tempAlias in aliasList:
            host, port = connections.get_connection_addr(tempAlias).values()
            # return """Host: {}\nPort: {}\nAlias: {}""".format(host, port, alias)
            return tabulate([['Host', host], ['Port', port], ['Alias', tempAlias]], tablefmt='pretty')
        else:
            return "Connection not found!"

    def listCollections(self, timeout=None, showLoadedOnly=False):
        from pymilvus_orm import list_collections
        result = []
        collectionNames = list_collections(timeout, self.alias)
        for name in collectionNames:
            loadingProgress = self.showCollectionLoadingProgress(name)
            loaded, total = loadingProgress.values()
            # isLoaded = (total > 0) and (loaded == total)
            # shouldBeAdded = isLoaded if showLoadedOnly else True
            # if shouldBeAdded:
            result.append([name, "{}/{}".format(loaded, total)])
        return tabulate(result, headers=['Collection Name', 'Entities(Loaded/Total)'], tablefmt='grid', showindex=True)

    def showCollectionLoadingProgress(self, collectionName, partition_names=None):
        from pymilvus_orm import loading_progress
        return loading_progress(collectionName, partition_names, self.alias)

    def showIndexBuildingProgress(self, collectionName, index_name=""):
        from pymilvus_orm import index_building_progress
        return index_building_progress(collectionName, index_name, self.alias)

    def getTargetCollection(self, collectionName):
        from pymilvus_orm import Collection
        try:
            target = Collection(collectionName)
        except Exception as e:
            raise ParameterException('Collection error!\n')
        else:
            return target

    def loadCollection(self, collectionName):
        target = self.getTargetCollection(collectionName)
        target.load()
        result = self.showCollectionLoadingProgress(collectionName)
        return tabulate([[collectionName, result.get('num_loaded_entities'), result.get('num_total_entities')]], headers=['Collection Name', 'Loaded', 'Total'], tablefmt='grid')

    def releaseCollection(self, collectionName):
        target = self.getTargetCollection(collectionName)
        target.release()
        result = self.showCollectionLoadingProgress(collectionName)
        return tabulate([[collectionName, result.get('num_loaded_entities'), result.get('num_total_entities')]], headers=['Collection Name', 'Loaded', 'Total'], tablefmt='grid')

    def listPartitions(self, collectionName):
        target = self.getTargetCollection(collectionName)
        result = target.partitions
        rows = list(map(lambda x: [x.name, x.description], result))
        return tabulate(rows, headers=['Partition Name', 'Description'], tablefmt='grid', showindex=True)

    def listIndexes(self, collectionName):
        target = self.getTargetCollection(collectionName)
        result = target.indexes
        rows = list(map(lambda x: [x.field_name, x.params['index_type'],
                    x.params['metric_type'], x.params['params']['nlist']], result))
        return tabulate(rows, headers=['Field Name', 'Index Type', 'Metric Type', 'Nlist'], tablefmt='grid', showindex=True)

    def getCollectionDetails(self, collectionName='', collection=None):
        try:
            target = collection or self.getTargetCollection(collectionName)
        except Exception as e:
            return "Error!\nPlease check your input collection name."
        rows = []
        schema = target.schema
        partitions = target.partitions
        indexes = target.indexes
        fieldSchemaDetails = "\n  - " + "\n  - ".join(map(lambda x: "{} *primary".format(
            x.name) if x.is_primary else x.name, schema.fields))
        schemaDetails = """Description: {}\nFields:{}""".format(
            schema.description, fieldSchemaDetails)
        partitionDetails = "  - " + \
            "\n- ".join(map(lambda x: x.name, partitions))
        indexesDetails = "  - " + \
            "\n- ".join(map(lambda x: x.field_name, indexes))
        rows.append(['Name', target.name])
        rows.append(['Description', target.description])
        rows.append(['Is Empty', target.is_empty])
        rows.append(['Entities', target.num_entities])
        rows.append(['Primary Field', target.primary_field.name])
        rows.append(['Schema', schemaDetails])
        rows.append(['Partitions', partitionDetails])
        rows.append(['Indexes', indexesDetails])
        return tabulate(rows, tablefmt='grid')

    def getPartitionDetails(self, collection, partitionName=''):
        partition = collection.partition(partitionName)
        if not partition:
            return "No such partition!"
        rows = []
        rows.append(['Partition Name', partition.name])
        rows.append(['Description', partition.description])
        rows.append(['Is empty', partition.is_empty])
        rows.append(['Number of Entities', partition.num_entities])
        return tabulate(rows, tablefmt='grid')

    def getIndexDetails(self, collection):
        index = collection.index()
        if not index:
            return "No index!"
        rows = []
        rows.append(['Corresponding Collection', index.collection_name])
        rows.append(['Corresponding Field', index.field_name])
        rows.append(['Index Type', index.params['index_type']])
        rows.append(['Metric Type', index.params['metric_type']])
        rows.append(['Params', index.params['params']])
        return tabulate(rows, tablefmt='grid')

    def createCollection(self, collectionName, primaryField, autoId, description, fields):
        from pymilvus_orm import Collection, DataType, FieldSchema, CollectionSchema
        fieldList = []
        for field in fields:
            [fieldName, fieldType, fieldData] = field.split(':')
            isVector = False
            if fieldType in ['BINARY_VECTOR', 'FLOAT_VECTOR']:
                fieldList.append(FieldSchema(
                    name=fieldName, dtype=DataType[fieldType], dim=int(fieldData)))
            else:
                fieldList.append(FieldSchema(
                    name=fieldName, dtype=DataType[fieldType], description=fieldData))
        schema = CollectionSchema(
            fields=fieldList, primary_field=primaryField, auto_id=autoId, description=description)
        collection = Collection(name=collectionName, schema=schema)
        return self.getCollectionDetails(collection=collection)

    def createPartition(self, collectionName, description, partitionName):
        collection = self.getTargetCollection(collectionName)
        collection.create_partition(partitionName, description=description)
        return self.getPartitionDetails(collection, partitionName)

    def createIndex(self, collectionName, fieldName, indexType, metricType, params, timeout):
        collection = self.getTargetCollection(collectionName)
        indexParams = {}
        for param in params:
            paramList = param.split(':')
            [paramName, paramValue] = paramList
            indexParams[paramName] = int(paramValue)
        index = {"index_type": indexType,
                 "params": indexParams, "metric_type": metricType}
        collection.create_index(fieldName, index, timeout=timeout)
        return self.getIndexDetails(collection)

    def isCollectionExist(self, collectionName):
        from pymilvus_orm import has_collection
        return has_collection(collectionName, using=self.alias)

    def isPartitionExist(self, collection, partitionName):
        return collection.has_partition(partitionName)

    def isIndexExist(self, collection):
        return collection.has_index()

    def dropCollection(self, collectionName, timeout):
        collection = self.getTargetCollection(collectionName)
        collection.drop(timeout=timeout)
        return self.isCollectionExist(collectionName)

    def dropPartition(self, collectionName, partitionName, timeout):
        collection = self.getTargetCollection(collectionName)
        collection.drop_partition(partitionName, timeout=timeout)
        return self.isPartitionExist(collection, partitionName)

    def dropIndex(self, collectionName, timeout):
        collection = self.getTargetCollection(collectionName)
        collection.drop_index(timeout=timeout)
        return self.isIndexExist(collection)

    def search(self, collectionName, searchParameters):
        collection = self.getTargetCollection(collectionName)
        collection.load()
        res = collection.search(**searchParameters)
        hits = res[0]
        return f"- Total hits: {len(hits)}, hits ids: {hits.ids} \n- Top1 hit id: {hits[0].id}, distance: {hits[0].distance}, score: {hits[0].score} "

    def query(self, collectionName, queryParameters):
        collection = self.getTargetCollection(collectionName)
        collection.load()
        res = collection.query(**queryParameters)
        return f"- Query results: {res}"
