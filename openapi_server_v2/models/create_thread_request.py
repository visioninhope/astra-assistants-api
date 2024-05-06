# coding: utf-8

"""
    OpenAI API

    The OpenAI REST API. Please see https://platform.openai.com/docs/api-reference for more details.

    The version of the OpenAPI document: 2.0.0
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


from __future__ import annotations
import pprint
import re  # noqa: F401
import json




from pydantic import BaseModel, ConfigDict, Field
from typing import Any, ClassVar, Dict, List, Optional
from openapi_server.models.create_message_request import CreateMessageRequest
from openapi_server.models.create_thread_request_tool_resources import CreateThreadRequestToolResources
try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

class CreateThreadRequest(BaseModel):
    """
    CreateThreadRequest
    """ # noqa: E501
    messages: Optional[List[CreateMessageRequest]] = Field(default=None, description="A list of [messages](/docs/api-reference/messages) to start the thread with.")
    tool_resources: Optional[CreateThreadRequestToolResources] = None
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Set of 16 key-value pairs that can be attached to an object. This can be useful for storing additional information about the object in a structured format. Keys can be a maximum of 64 characters long and values can be a maxium of 512 characters long. ")
    __properties: ClassVar[List[str]] = ["messages", "tool_resources", "metadata"]

    model_config = {
        "populate_by_name": True,
        "validate_assignment": True,
        "protected_namespaces": (),
    }


    def to_str(self) -> str:
        """Returns the string representation of the model using alias"""
        return pprint.pformat(self.model_dump(by_alias=True))

    def to_json(self) -> str:
        """Returns the JSON representation of the model using alias"""
        # TODO: pydantic v2: use .model_dump_json(by_alias=True, exclude_unset=True) instead
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> Self:
        """Create an instance of CreateThreadRequest from a JSON string"""
        return cls.from_dict(json.loads(json_str))

    def to_dict(self) -> Dict[str, Any]:
        """Return the dictionary representation of the model using alias.

        This has the following differences from calling pydantic's
        `self.model_dump(by_alias=True)`:

        * `None` is only added to the output dict for nullable fields that
          were set at model initialization. Other fields with value `None`
          are ignored.
        """
        _dict = self.model_dump(
            by_alias=True,
            exclude={
            },
            exclude_none=True,
        )
        # override the default output from pydantic by calling `to_dict()` of each item in messages (list)
        _items = []
        if self.messages:
            for _item in self.messages:
                if _item:
                    _items.append(_item.to_dict())
            _dict['messages'] = _items
        # override the default output from pydantic by calling `to_dict()` of tool_resources
        if self.tool_resources:
            _dict['tool_resources'] = self.tool_resources.to_dict()
        # set to None if tool_resources (nullable) is None
        # and model_fields_set contains the field
        if self.tool_resources is None and "tool_resources" in self.model_fields_set:
            _dict['tool_resources'] = None

        # set to None if metadata (nullable) is None
        # and model_fields_set contains the field
        if self.metadata is None and "metadata" in self.model_fields_set:
            _dict['metadata'] = None

        return _dict

    @classmethod
    def from_dict(cls, obj: Dict) -> Self:
        """Create an instance of CreateThreadRequest from a dict"""
        if obj is None:
            return None

        if not isinstance(obj, dict):
            return cls.model_validate(obj)

        _obj = cls.model_validate({
            "messages": [CreateMessageRequest.from_dict(_item) for _item in obj.get("messages")] if obj.get("messages") is not None else None,
            "tool_resources": CreateThreadRequestToolResources.from_dict(obj.get("tool_resources")) if obj.get("tool_resources") is not None else None,
            "metadata": obj.get("metadata")
        })
        return _obj


