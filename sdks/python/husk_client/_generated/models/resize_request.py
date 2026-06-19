from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast






T = TypeVar("T", bound="ResizeRequest")



@_attrs_define
class ResizeRequest:
    """ 
        Attributes:
            cpu (int | None | Unset):
            memory_mb (int | None | Unset):
            disk_gb (int | None | Unset):
     """

    cpu: int | None | Unset = UNSET
    memory_mb: int | None | Unset = UNSET
    disk_gb: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        cpu: int | None | Unset
        if isinstance(self.cpu, Unset):
            cpu = UNSET
        else:
            cpu = self.cpu

        memory_mb: int | None | Unset
        if isinstance(self.memory_mb, Unset):
            memory_mb = UNSET
        else:
            memory_mb = self.memory_mb

        disk_gb: int | None | Unset
        if isinstance(self.disk_gb, Unset):
            disk_gb = UNSET
        else:
            disk_gb = self.disk_gb


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if cpu is not UNSET:
            field_dict["cpu"] = cpu
        if memory_mb is not UNSET:
            field_dict["memory_mb"] = memory_mb
        if disk_gb is not UNSET:
            field_dict["disk_gb"] = disk_gb

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        def _parse_cpu(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        cpu = _parse_cpu(d.pop("cpu", UNSET))


        def _parse_memory_mb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        memory_mb = _parse_memory_mb(d.pop("memory_mb", UNSET))


        def _parse_disk_gb(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        disk_gb = _parse_disk_gb(d.pop("disk_gb", UNSET))


        resize_request = cls(
            cpu=cpu,
            memory_mb=memory_mb,
            disk_gb=disk_gb,
        )


        resize_request.additional_properties = d
        return resize_request

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
