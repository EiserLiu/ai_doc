import json
import re
import logging
from pathlib import Path

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

client = OpenAI(
    base_url=settings.LLM_BASE_URL,
    api_key=settings.LLM_API_KEY,
    timeout=settings.LLM_TIMEOUT,
)

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

POLICY_SCHEMA = {
    "policy_title": "政策标题",
    "publish_department": "发布部门",
    "publish_date": "发布日期",
    "support_target": ["支持对象"],
    "support_industry": ["支持行业"],
    "apply_conditions": ["申报条件"],
    "support_measures": ["支持措施"],
    "subsidy_amount": ["补贴金额或奖励标准"],
    "apply_materials": ["申报材料"],
    "deadline": "申报截止时间",
    "process": ["申报流程"],
    "risks": ["注意事项或风险点"],
    "summary": "300字以内摘要",
    "suggestions": ["建议行动"],
}

BIDDING_SCHEMA = {
    "project_name": "项目名称",
    "buyer": "采购人",
    "agency": "代理机构",
    "budget": "预算金额",
    "bid_deadline": "投标截止时间",
    "bid_open_time": "开标时间",
    "qualification_requirements": ["资质要求"],
    "performance_requirements": ["业绩要求"],
    "technical_requirements": ["技术要求"],
    "score_rules": ["评分标准"],
    "required_materials": ["投标材料清单"],
    "invalid_bid_risks": ["废标风险"],
    "key_points": ["重点关注事项"],
    "summary": "300字以内摘要",
    "suggestions": ["投标准备建议"],
}


def _load_prompt(analyze_type: str) -> str:
    prompt_file = PROMPTS_DIR / f"{analyze_type}_prompt.txt"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    return prompt_file.read_text(encoding="utf-8")


def _load_merge_prompt() -> str:
    prompt_file = PROMPTS_DIR / "merge_prompt.txt"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Merge prompt file not found: {prompt_file}")
    return prompt_file.read_text(encoding="utf-8")


def _parse_json(text: str) -> dict | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _record_cost(task_no: str, response):
    """Record token usage via RabbitMQ."""
    try:
        from app.services import rabbitmq_service
        usage = response.usage
        if usage and task_no:
            rabbitmq_service.send_cost_log(
                task_no, settings.LLM_PROVIDER, settings.LLM_MODEL,
                usage.prompt_tokens, usage.completion_tokens,
            )
    except Exception as e:
        logger.warning(f"Failed to record cost: {e}")


def analyze(text: str, analyze_type: str, task_no: str = "") -> dict:
    prompt_template = _load_prompt(analyze_type)
    prompt = prompt_template.replace("{{text}}", text)

    for attempt in range(settings.LLM_MAX_RETRY + 1):
        try:
            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            _record_cost(task_no, response)
            raw = response.choices[0].message.content
            result = _parse_json(raw)
            if result:
                return result
            logger.warning(f"LLM returned non-JSON on attempt {attempt + 1}")
        except Exception as e:
            logger.error(f"LLM call failed on attempt {attempt + 1}: {e}")
            if attempt == settings.LLM_MAX_RETRY:
                raise

    raise ValueError("模型未返回合法 JSON")


def merge_results(partials: list[dict], analyze_type: str, task_no: str = "") -> dict:
    if len(partials) == 1:
        return partials[0]

    schema = POLICY_SCHEMA if analyze_type == "policy" else BIDDING_SCHEMA
    merge_prompt = _load_merge_prompt()
    prompt = merge_prompt.replace("{{schema}}", json.dumps(schema, ensure_ascii=False, indent=2))
    prompt = prompt.replace("{{partials}}", json.dumps(partials, ensure_ascii=False, indent=2))

    for attempt in range(settings.LLM_MAX_RETRY + 1):
        try:
            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            _record_cost(task_no, response)
            raw = response.choices[0].message.content
            result = _parse_json(raw)
            if result:
                return result
        except Exception as e:
            logger.error(f"Merge LLM call failed on attempt {attempt + 1}: {e}")
            if attempt == settings.LLM_MAX_RETRY:
                raise

    raise ValueError("合并结果时模型未返回合法 JSON")
