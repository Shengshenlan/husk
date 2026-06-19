from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast
import datetime






T = TypeVar("T", bound="SnapshotResponse")



@_attrs_define
class SnapshotResponse:
    """ 
        Attributes:
            id (str):
            name (str):
            image_ref (str):
            state (str):
            created_at (datetime.datetime):
            size_bytes (int | None | Unset):
     """

    id: str
    name: str
    image_ref: str
    state: str
    created_at: datetime.datetime
    size_bytes: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        image_ref = self.image_ref

        state = self.state

        created_at = self.created_at.isoformat()

        size_bytes: int | None | Unset
        if isinstance(self.size_bytes, Unset):
            size_bytes = UNSET
        else:
            size_bytes = self.size_bytes


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "id": id,
            "name": name,
            "image_ref": image_ref,
            "state": state,
            "created_at": created_at,
        })
        if size_bytes is not UNSET:
            field_dict["size_bytes"] = size_bytes

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        image_ref = d.pop("image_ref")

        state = d.pop("state")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))




        def _parse_size_bytes(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        size_bytes = _parse_size_bytes(d.pop("size_bytes", UNSET))


        snapshot_response = cls(
            id=id,
            name=name,
            image_ref=image_ref,
            state=state,
            created_at=created_at,
            size_bytes=size_bytes,
        )


        snapshot_response.additional_properties = d
        return snapshot_response

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
