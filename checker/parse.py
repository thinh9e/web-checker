import re
from urllib.parse import urlparse

import requests
from lxml import html


class ParseError(Exception):
    """
    Base exception class
    """

    def __init__(self, msg: tuple, prefix: str):
        """
        Re-format message

        :param msg: tuple(message, error) || str(message)
        :param prefix: str
        """
        self.msg = str()
        self.prefix = 'ParseError'
        if prefix is not None and len(prefix) > 0:
            self.prefix = prefix
        if isinstance(msg, tuple) and len(msg) == 2:
            message = msg[0]
            error = msg[1]
            self.msg = message
            if error != '':
                self.msg += f'\n{error}'
        elif isinstance(msg, str):
            self.msg = msg[0]
        super(ParseError, self).__init__(f'{self.prefix}: {self.msg}')


class ContentError(ParseError):
    """
    Content error
    """

    def __init__(self, msg: tuple):
        prefix = 'ContentError'
        super(ContentError, self).__init__(msg, prefix)


class ParseContent:
    """
    Get source code from URL and then parse it
    Example::
        parse = ParseContent()
        try:
            parse.get('https://example.com')
        except ParseError as e:
            print(e)
        finally:
            parse.close()
    """

    def __init__(self):
        self._session = requests.Session()
        self._url, self._parse_url, self._base_url = '', None, None
        self._data = {}
        self._error = None
        self._content = None
        self._tree = None

    def get(self, url: str):
        if url and len(url) > 0:
            self._url = url
            self._parse_url = urlparse(url)
            self._base_url = f'{self._parse_url.scheme}://{self._parse_url.netloc}'
            self._set_content()

        self._check_available()
        self._tree = html.fromstring(self._content)

    def close(self):
        """
        Close the current session
        """
        self._session.close()

    @property
    def error(self) -> str:
        return self._error

    @property
    def content(self) -> str:
        return self._content

    def _check_available(self):
        """
        Check the content is available

        :raise: ContentError
        """
        if self._content is None or self._content == '':
            raise ContentError(('The content is blank', self._error))

    def _set_content(self):
        """
        Data: {encoding, time}
        """
        try:
            resp = self._session.get(self._url, timeout=3 * 10)
            self._data['encoding'] = resp.encoding.upper()
            self._data['time'] = resp.elapsed.total_seconds()
            self._content = resp.content.decode(self._data['encoding'])
        except requests.exceptions.RequestException:
            self._error = f'Request exception: url={self._url}'
            self._content = None

    def _get_link_resource(self, resource: str):
        """
        Convert to url resource link

        :param resource: str
        :return: url resource link
        """
        if resource is None or len(resource) == 0:
            return None
        if resource.startswith('//'):
            # //domain.com/image.jpg -> https://domain.com/image.jpg
            resource = f'{self._parse_url.scheme}://{resource.lstrip("/")}'
        elif resource.startswith('/'):
            # /image.jpg -> https://domain.com/image.jpg
            resource = f'{self._base_url}/{resource.lstrip("/")}'
        return resource

    def _get_link_hyperlinks(self, links: list) -> set:
        """
        Get full link and remove unavailable link

        :param links: a list of links
        :return: a set of links (only distinct)
        """
        results = set()
        for link in links:
            if link.startswith('//'):
                # //domain.com/link -> https://domain.com/link
                results.add(f'{self._parse_url.scheme}://{link.lstrip("/")}')
            elif link.startswith('/') and len(link) > 1:
                # /link -> https://domain.com/link
                results.add(f'{self._base_url}/{link.lstrip("/")}')
            elif link.startswith('http'):
                # https://domain.com/link
                results.add(link)
        return results

    def _get_xpath_value(self, xpath: str, help_text: str, is_list: bool = False):
        """
        Get a/list value from xpath string

        :param xpath: string xpath
        :param help_text: element name, using for exception message
        :param is_list: determine the return type, default False
        :return: a/list result or None
        """
        self._check_available()
        value = None
        try:
            result = self._tree.xpath(xpath)
            if result is not None and len(result) > 0:
                if is_list:
                    value = result
                else:
                    value = result[0]
        except html.etree.XPathError as exp:
            self._error = f'Get xpath {help_text} error: {exp}'
        return value

    @staticmethod
    def _clean_list_values(values: list):
        """
        Remove space and invalid string from a list values

        :param values: list of strings
        :return: a cleaned list or None
        """
        if values is None or len(values) < 1:
            return None
        result = []
        for value in values:
            # check type is HtmlElement to get all the text content of the element
            if isinstance(value, html.HtmlElement):
                value = value.text_content()
            if isinstance(value, str):
                # remove space
                value = value.strip()
                # remove whitespace character and duplicate space inside a string (\t\n\x0B\f\r)
                value = re.sub(r'\s+', ' ', value)
                if len(value) > 0:
                    result.append(value)
        return result

    @property
    def title(self) -> str:
        xpath = '//title/text()'
        return self._get_xpath_value(xpath, 'title')

    @property
    def description(self) -> str:
        xpath = '//meta[@name="description"]/@content'
        return self._get_xpath_value(xpath, 'description')

    @property
    def favicon(self) -> str:
        xpath = '//link[contains(@rel, "icon")]/@href'
        return self._get_link_resource(self._get_xpath_value(xpath, 'favicon'))

    @property
    def meta_robot(self) -> str:
        xpath = '//meta[@name="robots"]/@content'
        return self._get_xpath_value(xpath, 'meta robot')

    @property
    def heading_tags(self) -> dict:
        heading = dict()
        heading['h1'] = self._get_xpath_value('//h1', 'h1 tags', True)
        heading['h2'] = self._get_xpath_value('//h2', 'h2 tags', True)
        heading['h3'] = self._get_xpath_value('//h3', 'h3 tags', True)
        heading['h4'] = self._get_xpath_value('//h4', 'h4 tags', True)
        heading['h5'] = self._get_xpath_value('//h5', 'h5 tags', True)
        heading['h6'] = self._get_xpath_value('//h6', 'h6 tags', True)
        for key, val in heading.items():
            # val: list<HtmlElement>
            heading[key] = self._clean_list_values(val)
        return heading

    @property
    def hyperlinks(self) -> set:
        xpath = '//a/@href'
        return self._get_link_hyperlinks(self._get_xpath_value(xpath, 'hyperlinks', True))
