import enum
import json


def _to_object(object_to_deserialize, object_type: type):
    object_deserialized = None
    if isinstance(object_to_deserialize, list):
        object_deserialized = []
        for object_to_deserialize_in_list in object_to_deserialize:
            object_deserialized.append(_to_object(object_to_deserialize_in_list, object_type))
    elif object_type in [int, str]:
        object_deserialized = object_to_deserialize
    elif issubclass(object_type, enum.Enum):
        object_deserialized = object_type(object_to_deserialize)
    elif hasattr(object_type, 'OBJECT_SERIALIZATION_DATA'):
        object_deserialized = object_type()
        for name_in_dict, name_in_object, type_in_object, is_mandatory in object_type.OBJECT_SERIALIZATION_DATA:
            if name_in_dict in object_to_deserialize:
                setattr(object_deserialized, name_in_object,
                        _to_object(object_to_deserialize[name_in_dict], type_in_object))
            elif is_mandatory:
                raise Exception(
                    "Deserialization error: can not find mandatory attribute '{}' to deserialize '{}'.".format(
                        name_in_dict, object_type))
        if hasattr(object_deserialized, 'serializer_update_object') and callable(
                getattr(object_deserialized, 'serializer_update_object')):
            object_deserialized.serializer_update_object()
    return object_deserialized


def _to_dictionary(object_to_serialize) -> dict:
    object_serialized = {}
    object_type = type(object_to_serialize)
    if object_type is list:
        object_serialized = [_to_dictionary(object_to_serialize_in_list) for object_to_serialize_in_list in
                             object_to_serialize]
    elif object_type in [int, str]:
        object_serialized = object_to_serialize
    elif issubclass(object_type, enum.Enum):
        object_serialized = object_to_serialize.value
    elif hasattr(object_type, 'OBJECT_SERIALIZATION_DATA'):
        for name_in_dict, name_in_object, type_in_object, is_mandatory in object_type.OBJECT_SERIALIZATION_DATA:
            if hasattr(object_to_serialize, name_in_object) and getattr(object_to_serialize, name_in_object):
                object_serialized[name_in_dict] = _to_dictionary(
                    getattr(object_to_serialize, name_in_object))
            elif is_mandatory:
                raise Exception(
                    "Serialization error: can not find mandatory attribute '{}' to serialize '{}'.".format(
                        name_in_dict, object_type))
    else:
        object_serialized = str(object_to_serialize)
    return object_serialized


def deserialize(str_to_deserialize, object_type: type):
    return _to_object(json.loads(str_to_deserialize), object_type)


def serialize(object_to_serialize) -> str:
    return json.dumps(_to_dictionary(object_to_serialize), sort_keys=True, indent=4, separators=(',', ': '))
