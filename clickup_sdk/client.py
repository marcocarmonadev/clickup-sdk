from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

from clickup_sdk.settings import get_settings
from clickup_sdk.schemas import GetTasksResponse, Task, CustomField
from clickup_sdk.helpers import microseconds_string_to_date, get_custom_field_value
from httpx import HTTPStatusError

if TYPE_CHECKING:
    from clickup_sdk import Settings
    from httpx import AsyncClient


@dataclass
class Client:
    settings: ClassVar["Settings"] = get_settings()
    base_url: ClassVar[str] = "https://api.clickup.com/"

    http_client: "AsyncClient"

    async def get_tasks(
        self,
        list_id: int,
    ) -> GetTasksResponse:
        page = 0
        is_last_page = False
        tasks: list[Task] = []
        while not is_last_page:
            try:
                response = await self.http_client.get(
                    url=f"{self.base_url}api/v2/list/{list_id}/task",
                    headers={
                        "Authorization": self.settings.AUTHORIZATION,
                    },
                    params={
                        "page": page,
                        "include_closed": True,
                    },
                )
                response.raise_for_status()
            except HTTPStatusError as exc:
                raise exc
            else:
                response_dict: dict = response.json()
                is_last_page = response_dict["last_page"]
                page += 1
                tasks.extend(
                    [
                        Task(
                            id=task["id"],
                            name=task["name"],
                            date_updated=microseconds_string_to_date(
                                microseconds_string=task["date_updated"],
                            ),
                            date_created=microseconds_string_to_date(
                                microseconds_string=task["date_created"],
                            ),
                            status=task["status"]["status"],
                            custom_fields=[
                                CustomField(
                                    name=custom_field["name"],
                                    value=get_custom_field_value(custom_field),
                                )
                                for custom_field in task["custom_fields"]
                            ],
                        )
                        for task in response_dict["tasks"]
                    ]
                )
        return GetTasksResponse(
            tasks=tasks,
        )
