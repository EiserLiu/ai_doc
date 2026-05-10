import json

import redis

from app.config import settings

r = redis.from_url(settings.REDIS_URL, decode_responses=True)


def cache_task_status(task_no: str, status: str, ttl: int = 300):
    r.set(f"task:status:{task_no}", status, ex=ttl)


def get_task_status(task_no: str) -> str | None:
    return r.get(f"task:status:{task_no}")


def invalidate_task_cache(task_no: str):
    r.delete(f"task:status:{task_no}")


def cache_task_detail(task_no: str, detail: dict, ttl: int = 300):
    r.set(f"task:detail:{task_no}", json.dumps(detail, ensure_ascii=False, default=str), ex=ttl)


def get_task_detail_cache(task_no: str) -> dict | None:
    data = r.get(f"task:detail:{task_no}")
    if data:
        return json.loads(data)
    return None


def invalidate_task_detail_cache(task_no: str):
    r.delete(f"task:detail:{task_no}")
