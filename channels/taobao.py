from channels.base import ChannelAdapter, ChannelMessage


class TaobaoAdapter(ChannelAdapter):
    def normalize(self, raw_message: dict) -> ChannelMessage:
        buyer = raw_message.get("buyer", {})
        return ChannelMessage(
            external_id=self.generate_external_id("taobao", str(raw_message.get("tid", ""))),
            customer_name=buyer.get("nick", "未知用户"),
            customer_id=f"tb_{buyer.get('id', '')}",
            title=raw_message.get("title", "咨询"),
            content=raw_message.get("content", ""),
            channel="taobao",
            raw_data=raw_message,
        )

    async def fetch_tickets(self) -> list[ChannelMessage]:
        """Simulate fetching unread messages from Taobao open platform."""
        return []
