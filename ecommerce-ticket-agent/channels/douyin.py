from channels.base import ChannelAdapter, ChannelMessage


class DouyinAdapter(ChannelAdapter):
    def normalize(self, raw_message: dict) -> ChannelMessage:
        return ChannelMessage(
            external_id=self.generate_external_id("douyin", str(raw_message.get("conversation_id", ""))),
            customer_name=raw_message.get("user_name", "未知用户"),
            customer_id=f"dy_{raw_message.get('open_id', '')}",
            title=raw_message.get("title", "咨询"),
            content=raw_message.get("content", ""),
            channel="douyin",
            raw_data=raw_message,
        )

    async def fetch_tickets(self) -> list[ChannelMessage]:
        return []
