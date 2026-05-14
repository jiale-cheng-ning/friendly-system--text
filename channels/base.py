from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class ChannelMessage:
    external_id: str
    customer_name: str
    customer_id: str
    title: str
    content: str
    channel: str
    raw_data: dict = field(default_factory=dict)


class ChannelAdapter(ABC):
    @abstractmethod
    def normalize(self, raw_message: dict) -> ChannelMessage:
        ...

    @abstractmethod
    async def fetch_tickets(self) -> list[ChannelMessage]:
        ...

    def generate_external_id(self, channel: str, raw_id: str) -> str:
        return f"{channel}_{raw_id}"
