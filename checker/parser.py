import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

from lxml import etree

ENCODING: str = "utf-8"


class Parser:
    HEADING_LEVEL: int = 6
    METHOD_HTML: str = "html"

    def __init__(self, content: bytes, base_url: str) -> None:
        html_parser = etree.HTMLParser(encoding=ENCODING)
        self.content = etree.fromstring(
            text=content, parser=html_parser, base_url=base_url
        )
        self.base_url = base_url

        if self.content is None:
            raise ValueError("Cannot parse content")

    def _xpath(self, xpath: str, multiple: bool = False) -> Optional[str | list[str]]:
        elements = self.content.xpath(xpath)
        if not elements:
            return None

        if not multiple:
            return elements[0]
        return elements

    def _xpath_tags(self, xpath: str) -> Optional[list[str]]:
        elements = self.content.xpath(xpath)
        if not elements:
            return None

        tags: list[str] = list()
        for element in elements:
            tag = etree.tostring(
                element, encoding=ENCODING, method=self.METHOD_HTML
            ).decode(ENCODING)
            tags.append(re.search(r"<.*?>", tag).group())

        return tags if len(tags) > 0 else None

    @staticmethod
    def _clean_headings(
        level: int, headings: list[str]
    ) -> tuple[int, Optional[list[str]]]:
        if not headings:
            return level, None

        cleaned = list(filter(None, [heading.strip() for heading in headings]))
        return level, cleaned if len(cleaned) > 0 else None

    @staticmethod
    def _is_page_link(link: str) -> bool:
        if link in ("#", "/"):
            return False
        if link.startswith(("javascript:", "mailto:", "tel:")):
            return False
        return True

    def _get_page_link(self, link: str) -> str:
        if not link.startswith(("http://", "https://", "//")):
            return self.base_url + "/" + link.lstrip("/")
        if link.startswith("//"):
            return self.base_url.split(":")[0] + "//" + link.lstrip("/")
        return link

    @property
    def title(self) -> Optional[str]:
        return self._xpath("//title/text()")

    @property
    def description(self) -> Optional[str]:
        return self._xpath('//meta[@name="description"]/@content')

    @property
    def favicon(self) -> Optional[str]:
        link = self._xpath('//link[contains(@rel, "icon")]/@href')
        return self._get_page_link(link) if link else None

    @property
    def robots_meta(self) -> Optional[str]:
        return self._xpath('//meta[@name="robots"]/@content')

    @property
    def headings(self) -> Optional[dict[int, Optional[list[str]]]]:
        xpath_template = "//h{}//text()"

        results: list[tuple[int, Optional[list[str]]]] = []
        with ThreadPoolExecutor(max_workers=self.HEADING_LEVEL) as executor:
            tasks = list()
            for level in range(self.HEADING_LEVEL):
                headings = self._xpath(xpath_template.format(level + 1), multiple=True)
                tasks.append(executor.submit(self._clean_headings, level, headings))

            results.extend([future.result() for future in as_completed(tasks)])
            for future in as_completed(tasks):
                try:
                    results.append(future.result())
                except TimeoutError as e:
                    print(e)

        if not results:
            return None

        return {result[0] + 1: result[1] for result in results}

    @property
    def anchors(self) -> Optional[list[str]]:
        page_links: list[str] = list()

        links = self._xpath("//a/@href", multiple=True)
        for link in links:
            link = link.strip()
            if not self._is_page_link(link):
                continue
            page_links.append(self._get_page_link(link))

        page_links = list(set(page_links))
        return page_links if len(page_links) > 0 else None

    @property
    def inline_css(self) -> Optional[list[str]]:
        return self._xpath_tags("//@style/..")

    @property
    def images_miss_alt(self) -> Optional[list[str]]:
        return self._xpath_tags("//img[not(@alt)]")
