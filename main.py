"""
禁言通知拦截插件

通过正则表达式匹配QQ群禁言系统通知消息，并结合is_notice标志判断是否为禁言通知。
支持灵活的日志输出配置，方便调试和排查问题。
"""

import re
from typing import Optional

from core.plugin import BasePlugin, logger, on, Priority
from core.chat.message_utils import KiraMessageEvent
from core.chat.message_elements import Text


class BanNoticeBlockerPlugin(BasePlugin):
    """
    禁言通知拦截插件

    主要功能：
    1. 在消息到达时检查是否匹配禁言通知的正则表达式
    2. 结合is_notice标志综合判断是否为禁言消息
    3. 灵活的日志输出配置，支持调试模式
    4. 可选替换被拦截的消息内容
    """

    def __init__(self, ctx, cfg: dict):
        super().__init__(ctx, cfg)
        self.enabled = bool(cfg.get("enabled", True))
        self.log_all_messages = bool(cfg.get("log_all_messages", True))
        self.log_matched_only = bool(cfg.get("log_matched_only", False))
        self.check_is_notice = bool(cfg.get("check_is_notice", True))
        self.replace_message = bool(cfg.get("replace_message", True))
        self.replacement_text = cfg.get("replacement_text", "")
        self._default_pattern = r"\[System.*禁言了.*\]"

        pattern_str = cfg.get("ban_pattern", self._default_pattern)
        if pattern_str:
            try:
                self.ban_pattern = re.compile(pattern_str)
            except re.error:
                self.ban_pattern = re.compile(self._default_pattern)
        else:
            self.ban_pattern = re.compile(self._default_pattern)

    async def initialize(self):
        """初始化插件，加载配置"""
        try:
            logger.info(f"[BanNoticeBlocker] 初始化完成 | 启用:{self.enabled} | 全量日志:{self.log_all_messages} | 检查notice:{self.check_is_notice}")
            if self.log_all_messages:
                logger.debug(f"[BanNoticeBlocker] 配置详情: 仅匹配日志={self.log_matched_only}, 替换消息={self.replace_message}, 替换文本='{self.replacement_text[:20] if self.replacement_text else '(空)'}'")
        except Exception as e:
            logger.error(f"[BanNoticeBlocker] 初始化失败: {e}")
            self.enabled = False

    async def terminate(self):
        """插件卸载时的清理工作"""
        logger.info("[BanNoticeBlocker] 已卸载")

    def _get_message_text(self, event: KiraMessageEvent) -> str:
        """
        从消息事件中提取文本内容

        优先尝试从chain获取文本，如果失败则回退到message_str

        Args:
            event: 消息事件对象

        Returns:
            消息文本内容
        """
        try:
            if hasattr(event.message, 'chain') and event.message.chain:
                parts = []
                for elem in event.message.chain:
                    if isinstance(elem, Text):
                        parts.append(elem.text)
                    elif hasattr(elem, 'text'):
                        parts.append(elem.text)
                    elif hasattr(elem, 'to_string'):
                        parts.append(elem.to_string())
                    else:
                        parts.append(str(elem))
                if parts:
                    return "".join(parts)
        except Exception as e:
            logger.debug(f"[BanNoticeBlocker] 从chain提取文本失败: {e}")

        return event.message.message_str or ""

    def _match_ban_notice(self, text: str) -> Optional[re.Match]:
        """
        使用正则表达式匹配禁言通知

        Args:
            text: 消息文本内容

        Returns:
            匹配对象（成功）或None（失败）
        """
        if not text or not self.ban_pattern:
            return None

        try:
            return self.ban_pattern.search(text)
        except Exception as e:
            logger.warning(f"[BanNoticeBlocker] 正则匹配出错: {e}, text={text[:50] if text else 'None'}")
            return None

    def _is_ban_notice(self, event: KiraMessageEvent, message_text: str) -> tuple[bool, Optional[str]]:
        """
        综合判断消息是否为禁言通知

        判断条件：
        1. 消息内容匹配禁言正则表达式
        2. is_notice标志检查（可选）

        Args:
            event: 消息事件对象
            message_text: 消息文本内容（外部已处理None情况）

        Returns:
            (是否为禁言通知, 匹配到的时长字符串或None)
        """
        if self.log_all_messages:
            logger.debug(f"[BanNoticeBlocker] 检测消息 | is_notice:{event.message.is_notice} | 内容:'{message_text[:50] if message_text else '(空)'}'")

        match = self._match_ban_notice(message_text)
        if not match:
            return False, None

        if self.check_is_notice and not event.message.is_notice:
            if self.log_all_messages:
                logger.debug(f"[BanNoticeBlocker] 正则匹配但is_notice=False，放行")
            return False, None

        return True, None

    def _block_message(self, event: KiraMessageEvent, ban_duration: Optional[str]):
        """
        拦截并处理禁言消息

        Args:
            event: 消息事件对象
            ban_duration: 禁言时长（秒）
        """
        sender_nickname = event.message.sender.nickname if event.message.sender else "未知"
        group_id = event.message.group.group_id if event.message.group else "无群"

        logger.info(f"[BanNoticeBlocker] 拦截禁言通知 | 群:{group_id} | 发送者:{sender_nickname}")

        if hasattr(event, 'stop'):
            event.stop()

    @on.im_message(priority=Priority.HIGH)
    async def handle_im_message(self, event: KiraMessageEvent):
        """处理单条IM消息到达事件"""
        if not self.enabled:
            return

        try:
            message_text = self._get_message_text(event)
            is_ban, ban_duration = self._is_ban_notice(event, message_text)

            if is_ban:
                self._block_message(event, ban_duration)

        except Exception as e:
            logger.error(f"[BanNoticeBlocker] 处理消息时发生错误: {e}")

    @on.im_batch_message(priority=Priority.HIGH)
    async def handle_batch_message(self, event):
        """处理批量消息事件"""
        pass


__all__ = ['BanNoticeBlockerPlugin']