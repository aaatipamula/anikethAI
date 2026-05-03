import re
from html.parser import HTMLParser


class HtmlToMarkdown(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._list_type_stack: list[str] = []
        self._list_counters: list[int] = []
        self._pending_href: str = ""
        self._anchor_start: int = -1

    def handle_starttag(self, tag: str, attrs: list) -> None:
        attr = dict(attrs)
        if tag in ("b", "strong"):
            self._parts.append("**")
        elif tag in ("i", "em"):
            self._parts.append("*")
        elif tag in ("s", "strike", "del"):
            self._parts.append("~~")
        elif tag == "u":
            self._parts.append("__")
        elif tag == "code":
            self._parts.append("`")
        elif tag == "pre":
            self._parts.append("```\n")
        elif tag in ("h1", "h2", "h3"):
            self._parts.append("\n" + "#" * int(tag[1]) + " ")
        elif tag in ("h4", "h5", "h6"):
            self._parts.append("\n### ")
        elif tag == "a":
            self._pending_href = attr.get("href") or ""
            self._anchor_start = len(self._parts)
        elif tag == "br":
            self._parts.append("\n")
        elif tag == "p":
            self._parts.append("\n")
        elif tag == "ul":
            self._list_type_stack.append("ul")
            self._list_counters.append(0)
        elif tag == "ol":
            self._list_type_stack.append("ol")
            self._list_counters.append(0)
        elif tag == "li":
            if self._list_type_stack and self._list_type_stack[-1] == "ol":
                self._list_counters[-1] += 1
                self._parts.append(f"\n{self._list_counters[-1]}. ")
            else:
                self._parts.append("\n- ")
        elif tag == "blockquote":
            self._parts.append("\n> ")
        elif tag == "hr":
            self._parts.append("\n---\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("b", "strong"):
            self._parts.append("**")
        elif tag in ("i", "em"):
            self._parts.append("*")
        elif tag in ("s", "strike", "del"):
            self._parts.append("~~")
        elif tag == "u":
            self._parts.append("__")
        elif tag == "code":
            self._parts.append("`")
        elif tag == "pre":
            self._parts.append("\n```")
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._parts.append("\n")
        elif tag == "a":
            inner = "".join(self._parts[self._anchor_start :])
            del self._parts[self._anchor_start :]
            if self._pending_href != inner:
                self._parts.append(f"[{inner}]({self._pending_href})")
            else:
                self._parts.append(self._pending_href)
            self._pending_href = ""
            self._anchor_start = -1
        elif tag == "p":
            self._parts.append("\n")
        elif tag in ("ul", "ol"):
            if self._list_type_stack:
                self._list_type_stack.pop()
                self._list_counters.pop()

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_markdown(self) -> str:
        result = "".join(self._parts)
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result.strip()

    @classmethod
    def parse_html(cls, html: str) -> str:
        parser = cls()
        parser.feed(html)
        return parser.get_markdown()
