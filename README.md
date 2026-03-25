# Ban Notice Blocker - 禁言通知拦截插件

用于拦截和屏蔽 QQ 群禁言系统通知消息的 KiraAI 插件。

## 功能特性

- **正则表达式匹配**：通过可配置的正则表达式匹配禁言相关消息
- **is_notice 标志检查**：同时验证消息的 `is_notice` 系统通知标志
- **事件拦截**：调用 `event.stop()` 阻止消息继续传递
- **完整日志**：输出详细的调试日志，方便排查问题

## 支持的消息类型

插件可匹配以下格式的消息：

- `[System 用户1683728778禁言了你600秒]` - 禁言通知
- `[System 你之前被禁言了，用户1683728778解除了你的禁言]` - 解除禁言通知

## 安装方法

1. 将 `ban_notice_blocker` 文件夹放入 `data/plugins/` 目录
2. 在 KiraAI WebUI 中启用插件
3. 插件将自动加载默认配置

## 配置选项

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `enabled` | boolean | `true` | 是否启用插件 |
| `log_all_messages` | boolean | `true` | 输出所有消息的调试日志 |
| `ban_pattern` | string | `\[System.*禁言了.*\]` | 匹配禁言通知的正则表达式 |
| `check_is_notice` | boolean | `true` | 是否同时检查 `is_notice` 标志 |

## 正则表达式说明

默认正则 `\[System.*禁言了.*\]` 解释：

- `\[` - 匹配左方括号 `[`
- `System` - 匹配字符串 "System"
- `.*` - 匹配任意字符
- `禁言了` - 匹配字符串 "禁言了"
- `.*` - 匹配任意字符
- `\]` - 匹配右方括号 `]`

### 自定义正则

如果需要更精确的匹配，可以修改 `ban_pattern` 配置：

- 仅拦截禁言：`\[System.*禁言了你\d+秒\]`
- 仅拦截解除：`\[System.*解除了你的禁言\]`
- 仅拦截他人禁言：`\[System 用户\d+禁言了你\d+秒\]`

## 日志输出示例

```
[BanNoticeBlocker] 收到消息 - is_notice: True, text: '[System 用户1683728778禁言了你600秒]'
[BanNoticeBlocker] 开始检测 - is_notice: True, 内容: '[System 用户1683728778禁言了你600秒]'
[BanNoticeBlocker] 正则匹配成功！完整匹配: '[System 用户1683728778禁言了你600秒]'
[BanNoticeBlocker] ========== 拦截禁言消息 ==========
[BanNoticeBlocker] 发送者: None(3962960704)
[BanNoticeBlocker] 群组: 115985242
[BanNoticeBlocker] 原始消息: [System 用户1683728778禁言了你600秒]
[BanNoticeBlocker] ===========================================
[BanNoticeBlocker] 已调用 event.stop() 阻止消息传递
```

## 工作原理

1. 插件在 `im_message` 事件（高优先级）中监听所有传入消息
2. 从消息的 `chain` 中提取文本内容
3. 使用正则表达式匹配禁言相关消息格式
4. 验证消息的 `is_notice` 标志（可配置）
5. 调用 `event.stop()` 阻止消息继续传递

## 文件结构

```
ban_notice_blocker/
├── __init__.py          # 包入口
├── main.py              # 插件主逻辑
├── manifest.json        # 插件元数据
├── schema.json          # 配置定义
└── README.md            # 本文档
```

## 注意事项

- 插件使用高优先级 (`Priority.HIGH`) 确保在消息处理早期拦截
- 正则表达式匹配所有包含"禁言了"的系统消息
- 日志默认开启，方便调试；生产环境可设置 `log_all_messages: false`
