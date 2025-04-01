"""This module contains the function to extract the return value of a tool."""

from typing import Any, TypeAlias, TypeVar

import jiter
from pydantic import BaseModel

from .._partial import partial
from ._base_type import BaseType, is_base_type
from ._convert_base_type_to_base_tool import convert_base_type_to_base_tool

_BaseModelT = TypeVar("_BaseModelT", bound=BaseModel)
_BaseTypeT = TypeVar("_BaseTypeT", bound=BaseType)

_ResponseModelT: TypeAlias = _BaseModelT | _BaseTypeT


def extract_tool_return(
    response_model: type[_ResponseModelT],
    json_output: str | object,
    allow_partial: bool,
    fields_from_call_args: dict[str, Any],
) -> _ResponseModelT:
    # Debug print to see raw json_output
    if isinstance(json_output, str):
        print(f"JSON OUTPUT STRING: {json_output}")  # noqa: T201
        # Optional: print it with line numbers for easier debugging
        for i, line in enumerate(json_output.splitlines(), 1):
            print(f"{i:>3}: {line}")  # noqa: T201
    else:
        print(f"JSON OUTPUT OBJECT: {type(json_output)}, {json_output}")  # noqa: T201

    json_obj = (
        jiter.from_json(
            json_output.encode(),
            partial_mode="trailing-strings" if allow_partial else "off",
        )
        if isinstance(json_output, str)
        else json_output
    )
    if is_base_type(response_model):
        temp_model = convert_base_type_to_base_tool(response_model, BaseModel)
        if allow_partial:
            return partial(temp_model).model_validate(json_obj).value  # pyright: ignore [reportAttributeAccessIssue]
        return temp_model.model_validate(json_obj).value  # pyright: ignore [reportAttributeAccessIssue]
    if fields_from_call_args and isinstance(json_obj, dict):
        # Support only top-level dict
        json_obj.update(fields_from_call_args)
    if allow_partial:
        return partial(response_model).model_validate(json_obj)
    return response_model.model_validate(json_obj)
