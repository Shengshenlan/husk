from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, BinaryIO, TextIO, TYPE_CHECKING, Generator

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

from ..types import UNSET, Unset
from typing import cast
import datetime

if TYPE_CHECKING:
  from ..models.sandbox_response_labels import SandboxResponseLabels





T = TypeVar("T", bound="SandboxResponse")



@_attrs_define
class SandboxResponse:
    """ 
        Attributes:
            id (str):
            name (str):
            state (str):
            cpu (int):
            memory_mb (int):
            disk_gb (int):
            labels (SandboxResponseLabels):
            runner_id (str):
            region (str):
            created_at (datetime.datetime):
            updated_at (datetime.datetime):
            snapshot_id (None | str | Unset):
            auto_stop_interval (int | None | Unset):
            last_activity_at (datetime.datetime | None | Unset):
     """

    id: str
    name: str
    state: str
    cpu: int
    memory_mb: int
    disk_gb: int
    labels: SandboxResponseLabels
    runner_id: str
    region: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    snapshot_id: None | str | Unset = UNSET
    auto_stop_interval: int | None | Unset = UNSET
    last_activity_at: datetime.datetime | None | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)





    def to_dict(self) -> dict[str, Any]:
        from ..models.sandbox_response_labels import SandboxResponseLabels
        id = self.id

        name = self.name

        state = self.state

        cpu = self.cpu

        memory_mb = self.memory_mb

        disk_gb = self.disk_gb

        labels = self.labels.to_dict()

        runner_id = self.runner_id

        region = self.region

        created_at = self.created_at.isoformat()

        updated_at = self.updated_at.isoformat()

        snapshot_id: None | str | Unset
        if isinstance(self.snapshot_id, Unset):
            snapshot_id = UNSET
        else:
            snapshot_id = self.snapshot_id

        auto_stop_interval: int | None | Unset
        if isinstance(self.auto_stop_interval, Unset):
            auto_stop_interval = UNSET
        else:
            auto_stop_interval = self.auto_stop_interval

        last_activity_at: None | str | Unset
        if isinstance(self.last_activity_at, Unset):
            last_activity_at = UNSET
        elif isinstance(self.last_activity_at, datetime.datetime):
            last_activity_at = self.last_activity_at.isoformat()
        else:
            last_activity_at = self.last_activity_at


        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({
            "id": id,
            "name": name,
            "state": state,
            "cpu": cpu,
            "memory_mb": memory_mb,
            "disk_gb": disk_gb,
            "labels": labels,
            "runner_id": runner_id,
            "region": region,
            "created_at": created_at,
            "updated_at": updated_at,
        })
        if snapshot_id is not UNSET:
            field_dict["snapshot_id"] = snapshot_id
        if auto_stop_interval is not UNSET:
            field_dict["auto_stop_interval"] = auto_stop_interval
        if last_activity_at is not UNSET:
            field_dict["last_activity_at"] = last_activity_at

        return field_dict



    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.sandbox_response_labels import SandboxResponseLabels
        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        state = d.pop("state")

        cpu = d.pop("cpu")

        memory_mb = d.pop("memory_mb")

        disk_gb = d.pop("disk_gb")

        labels = SandboxResponseLabels.from_dict(d.pop("labels"))




        runner_id = d.pop("runner_id")

        region = d.pop("region")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))




        updated_at = datetime.datetime.fromisoformat(d.pop("updated_at"))




        def _parse_snapshot_id(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        snapshot_id = _parse_snapshot_id(d.pop("snapshot_id", UNSET))


        def _parse_auto_stop_interval(data: object) -> int | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(int | None | Unset, data)

        auto_stop_interval = _parse_auto_stop_interval(d.pop("auto_stop_interval", UNSET))


        def _parse_last_activity_at(data: object) -> datetime.datetime | None | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                last_activity_at_type_0 = datetime.datetime.fromisoformat(data)



                return last_activity_at_type_0
            except (TypeError, ValueError, AttributeError, KeyError):
                pass
            return cast(datetime.datetime | None | Unset, data)

        last_activity_at = _parse_last_activity_at(d.pop("last_activity_at", UNSET))


        sandbox_response = cls(
            id=id,
            name=name,
            state=state,
            cpu=cpu,
            memory_mb=memory_mb,
            disk_gb=disk_gb,
            labels=labels,
            runner_id=runner_id,
            region=region,
            created_at=created_at,
            updated_at=updated_at,
            snapshot_id=snapshot_id,
            auto_stop_interval=auto_stop_interval,
            last_activity_at=last_activity_at,
        )


        sandbox_response.additional_properties = d
        return sandbox_response

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
