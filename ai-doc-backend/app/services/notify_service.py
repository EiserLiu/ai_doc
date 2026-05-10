import logging

import requests

logger = logging.getLogger(__name__)


def send_feishu(webhook_url: str, title: str, content: str) -> bool:
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {"title": {"tag": "plain_text", "content": title}},
            "elements": [
                {"tag": "markdown", "content": content}
            ],
        },
    }
    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Feishu notify failed: {e}")
        return False


def send_wecom(webhook_url: str, content: str) -> bool:
    payload = {
        "msgtype": "markdown",
        "markdown": {"content": content},
    }
    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"WeCom notify failed: {e}")
        return False


def send_dingtalk(webhook_url: str, title: str, content: str) -> bool:
    payload = {
        "msgtype": "markdown",
        "markdown": {"title": title, "text": content},
    }
    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"DingTalk notify failed: {e}")
        return False


def send_notify(notify_type: str, webhook_url: str, title: str, content: str) -> bool:
    if notify_type == "feishu":
        return send_feishu(webhook_url, title, content)
    elif notify_type == "wecom":
        return send_wecom(webhook_url, content)
    elif notify_type == "dingtalk":
        return send_dingtalk(webhook_url, title, content)
    else:
        logger.error(f"Unknown notify type: {notify_type}")
        return False


def build_task_success_message(task_no: str, original_filename: str, analyze_type: str, summary: str) -> tuple[str, str]:
    type_name = "政策文件分析" if analyze_type == "policy" else "招标文件分析"
    title = "AI 文档分析完成"
    content = (
        f"**文件名称**：{original_filename}\n"
        f"**分析类型**：{type_name}\n"
        f"**任务编号**：{task_no}\n"
        f"**处理状态**：成功\n"
        f"**核心摘要**：{summary[:200]}\n\n"
        f"[查看报告](/tasks/{task_no})"
    )
    return title, content


def build_task_failed_message(task_no: str, original_filename: str, error_message: str) -> tuple[str, str]:
    title = "AI 文档分析失败"
    content = (
        f"**文件名称**：{original_filename}\n"
        f"**任务编号**：{task_no}\n"
        f"**处理状态**：失败\n"
        f"**错误信息**：{error_message}"
    )
    return title, content
