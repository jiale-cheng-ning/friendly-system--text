from channels.base import ChannelAdapter, ChannelMessage


class JDAdapter(ChannelAdapter):
    def normalize(self, raw_message: dict) -> ChannelMessage:
        return ChannelMessage(
            external_id=self.generate_external_id("jd", str(raw_message.get("msg_id", ""))),
            customer_name=raw_message.get("nickname", "未知用户"),
            customer_id=f"jd_{raw_message.get('pin', '')}",
            title=raw_message.get("title", "咨询"),
            content=raw_message.get("content", ""),
            channel="jd",
            raw_data=raw_message,
        )

    async def fetch_tickets(self) -> list[ChannelMessage]:
        return []
