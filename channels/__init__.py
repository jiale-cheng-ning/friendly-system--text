from channels.taobao import TaobaoAdapter
from channels.jd import JDAdapter
from channels.douyin import DouyinAdapter
from channels.base import ChannelAdapter, ChannelMessage

ADAPTERS: dict[str, ChannelAdapter] = {
    "taobao": TaobaoAdapter(),
    "jd": JDAdapter(),
    "douyin": DouyinAdapter(),
}


def get_adapter(channel: str) -> ChannelAdapter:
    return ADAPTERS.get(channel)
