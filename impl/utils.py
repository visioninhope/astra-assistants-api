import json
import logging
from typing import Type, Dict, Any, List, get_origin, Annotated, get_args

from fastapi import HTTPException
from pydantic import BaseModel

from impl.astra_vector import CassandraClient

logger = logging.getLogger(__name__)

def map_model(source_instance: BaseModel, target_model_class: Type[BaseModel],
              extra_fields: Dict[str, Any] = {}) -> BaseModel:
    combined_fields = combine_fields(extra_fields, source_instance, target_model_class)

    # Create an instance of the target model class using the extracted and adjusted fields
    return target_model_class(**combined_fields)


def combine_fields(extra_fields, source_instance, target_model_class):
    field_values = {}
    # Iterate over the fields in the target model class
    for field_name, field_type in target_model_class.__fields__.items():
        value = None
        if field_name in source_instance.__fields__:
            value = getattr(source_instance, field_name)
        # extra_fields can override source_instance values
        if field_name in extra_fields:
            value = extra_fields[field_name]

        # Handle Annotated type by extracting the base type
        origin_type = get_origin(field_type.annotation)

        # if origin_type is Annotated:
        #    base_type = get_args(field_type)[0]
        #    origin_type = get_origin(base_type)
        #    if origin_type is None:
        #        origin_type = base_type

        # Check if the field type is a List and the value is None
        if origin_type is list and value is None:
            field_values[field_name] = []
        else:
            field_values[field_name] = value
    # Merge field_values with extra_fields, where extra_fields take precedence
    combined_fields = {**field_values, **extra_fields}
    return combined_fields


async def store_object(astradb: CassandraClient, obj: BaseModel, target_class: Type[BaseModel], table_name: str,
                       extra_fields: Dict[str, Any]):
    try:
        combined_fields = combine_fields(extra_fields, obj, target_class)
        combined_obj: target_class = target_class.construct(**combined_fields)

        # TODO is there a better way to do this
        # flatten nested objects into json
        obj_dict = combined_obj.to_dict()
        for key, value in obj_dict.items():
            if isinstance(value, list):
                if len(value) == 0:
                    obj_dict[key] = None
                else:
                    for i in range(len(value)):
                        if isinstance(value[i], list):
                            obj_dict[key][i] = json.dumps(value[i])
                        if isinstance(value[i], dict):
                            obj_dict[key][i] = json.dumps(value[i])
            # special handling for metadata column which is actually stored as a map in cassandra
            # (other objects are json strings)
            if key != "metadata" and isinstance(value, dict):
                obj_dict[key] = json.dumps(value)

        astradb.upsert_table_from_dict(table_name=table_name, obj=obj_dict)
        return combined_obj
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading {table_name}: {e}")


def read_object(astradb: CassandraClient, target_class: Type[BaseModel], table_name: str, partition_keys: List[str],
                 args: Dict[str, Any]):
    objs = read_objects(astradb, target_class, table_name, partition_keys, args)
    if len(objs) == 0:
        # Maybe pass down name
        raise HTTPException(status_code=404, detail=f"{target_class.__name__} not found.")
    return objs[0]



def read_objects(astradb: CassandraClient, target_class: Type[BaseModel], table_name: str, partition_keys: List[str],
                args: Dict[str, Any]):
    try:
        json_objs = astradb.select_from_table_by_pk(table=table_name, partitionKeys=partition_keys, args=args)
        if len(json_objs) == 0:
            raise HTTPException(status_code=404, detail=f"{table_name} not found.")

        obj_list = []
        for json_obj in json_objs:
            for field_name, field_type in target_class.__fields__.items():
                annotation = field_type.annotation
                if (
                        annotation is not None
                        and json_obj[field_name] is not None
                        and hasattr(annotation, 'from_json')
                ):
                    if 'actual_instance' in annotation.__fields__:
                        json_obj[field_name] = annotation(actual_instance=json_obj[field_name])
                    else:
                        json_obj[field_name] = annotation.from_json(json_obj[field_name])
                elif get_origin(annotation) is list:
                    for i in range(len(json_obj[field_name])):
                        if isinstance(json_obj[field_name][i], str):
                            json_obj[field_name][i] = annotation.__args__[0].from_json(json_obj[field_name][i])
                        else:
                            if 'actual_instance' in annotation.__args__[0].__fields__:
                                 json_obj[field_name][i] = annotation.__args__[0](actual_instance=json_obj[field_name][i])
                            else:
                                logger.error(f"error reading object from {table_name} - {field_name} is an object: {json_obj[field_name][i]}  but {annotation} does not take objects.")
                                raise HTTPException(status_code=500, detail=f"Error reading {table_name}: {field_name}.")

            obj = target_class(**json_obj)
            obj_list.append(obj)
        return obj_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading {table_name}: {e}")