import re


def truncate(text: str, max_length: int = 300) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def extract_chapters(text: str) -> list[dict[str, str]]:
    pattern = r"(?:^|\n)([一二三四五六七八九十]+[、.]\s*[^\n]+)"
    matches = list(re.finditer(pattern, text))
    chapters = []
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        chapters.append({"title": title, "content": content})
    return chapters
