from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast

if TYPE_CHECKING:
  from ..models.create_request_labels import CreateRequestLabels





T = TypeVar("T", bound="CreateRequest")



@_attrs_define
class CreateRequest:
    """ 
        Attributes:
            name (None | str | Unset):
            snapshot_id (None | str | Unset):
            cpu (int | Unset):  Default: 2.
            memory_mb (int | Unset):  Default: 2048.
            disk_gb (int | Unset):  Default: 10.
            labels (CreateRequestLabels | Unset):
            auto_stop_interval (int | None | Unset):
     """

    name: None | str | Unset = UNSET
    snapshot_id: None | str | Unset = UNSET
    cpu: int | Unset = 2
    memory_mb: int | Unset = 2048
    disk_gb: int | Unset = 10
    labels: CreateRequestLabels | Unset = UNSET
    auto_stop_interval: int | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        from ..models.create_request_labels import CreateRequestLabels
        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        snapshot_id: None | str | Unset
        if isinstance(self.snapshot_id, Unset):
            snapshot_id = UNSET
        else:
            snapshot_id = self.snapshot_id

        cpu = self.cpu

        memory_mb = self.memory_mb

        disk_gb = self.disk_gb

        labels: dict[str, Any] | Unset = UNSET
        if not isinstance(self.labels, Unset):
            labels = self.labels.to_dict()

        auto_stop_interval: int | None | Unset
        if isinstance(self.auto_stop_interval, Unset):
            auto_stop_interval = UNSET
        else:
            auto_stop_interval = self.auto_stop_interval


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
        })
        if name is not UNSET:
            field_dict["name"] = name
        if snapshot_id is not UNSET:
            field_dict["snapshot_id"] = snapshot_id
        if cpu is not UNSET:
            field_dict["cpu"] = cpu
        if memory_mb is not UNSET:
            field_dict["memory_mb"] = memory_mb
        if disk_gb is not UNSET:
            field_dict["disk_gb"] = disk_gb
        if labels is not UNSET:
            field_dict["labels"] = labels
        if auto_stop_interval is not UNSET:
            field_dict["auto_stop_interval"] = auto_stop_interval

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_request_labels import CreateRequestLabels
        d = dict(src_dict)
        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))


        def _parse_snapshot_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        snapshot_id = _parse_snapshot_id(d.pop("snapshot_id", UNSET))


        cpu = d.pop("cpu", UNSET)

        memory_mb = d.pop("memory_mb", UNSET)

        disk_gb = d.pop("disk_gb", UNSET)

        _labels = d.pop("labels", UNSET)
        labels: CreateRequestLabels | Unset
        if isinstance(_labels,  Unset):
            labels = UNSET
        else:
            labels = CreateRequestLabels.from_dict(_labels)




        def _parse_auto_stop_interval(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        auto_stop_interval = _parse_auto_stop_interval(d.pop("auto_stop_interval", UNSET))


        create_request = cls(
            name=name,
            snapshot_id=snapshot_id,
            cpu=cpu,
            memory_mb=memory_mb,
            disk_gb=disk_gb,
            labels=labels,
            auto_stop_interval=auto_stop_interval,
        )


        create_request.additional_properties = d
        return create_request

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
