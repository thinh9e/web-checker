import concurrent.futures
import re
from urllib.parse import urlsplit

import httpx
import requests
from django.conf import settings
from lxml import html

ENCODING = "utf-8"
REQUEST_TIMEOUT = 30


async def re_captcha(response: str, user_ip: str) -> bool:
    """
    Check reCaptcha

    :param response: g-recaptcha-response
    :param user_ip: IP address
    :return: True if pass
    """
    if settings.DEBUG:
        return True

    url = "https://www.google.com/recaptcha/api/siteverify"
    data = {
        "secret": settings.GOOGLE_RECAPTCHA_SECRET_KEY,
        "response": response,
        "remoteip": user_ip,
    }

    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(url=url, data=data)
            r.raise_for_status()
    except httpx.HTTPError as exp:
        print("Error re_captcha():", exp)
        return False

    return r.json().get("success", False)


def get_link_img(elm: str, base_url: str) -> str:
    """
    Get full link image

    :param elm: content.xpath(img)
    :param base_url:
    :return: link image
    """
    if elm and elm[:2] not in {"ht", "//"}:
        elm = base_url + "/" + elm.lstrip("/")
    return elm


def clean_elms(elms: list) -> list:
    """
    Clean elements

    :param elms: content.xpath(elems)
    :return: remove spaces
    """
    if elms:
        for idx, _ in enumerate(elms):
            elms[idx] = elms[idx].strip()
        elms = list(filter(None, elms))
    return elms


def getlink_robots(client, base_url: str) -> str | None:
    """
    Get link robots.txt

    :param client:
    :param base_url:
    :return: link robots.txt or None
    """
    url = base_url + "/robots.txt"
    try:
        r = client.get(url, timeout=REQUEST_TIMEOUT)
    except (requests.exceptions.RequestException, Exception):
        print("robots.txt not found!")
        return None
    if r.status_code != 200 or "plain" not in r.headers["Content-Type"]:
        return None
    return url


def getlink_sitemap(client, base_url: str, robots: str) -> list | None:
    """
    Get link sitemap.xml

    :param client:
    :param base_url:
    :param robots: robots.txt
    :return: link sitemap.xml or None
    """
    url = base_url + "/sitemap.xml"
    try:
        r = client.get(url, timeout=REQUEST_TIMEOUT)
    except (requests.exceptions.RequestException, Exception):
        print("sitemap.xml not found!")
        return None
    if robots:
        r_txt = client.get(robots)
        txt = r_txt.content.decode(ENCODING).replace("\n", "")
        sitemap = re.findall(r"Sitemap:.*xml", txt)
        if sitemap:
            sitemap = sitemap[0].split("Sitemap: ")[1:]
            return sitemap
    if r.status_code != 200 or "xml" not in r.headers["Content-Type"]:
        return None
    return [url]


def check_broken_link(client, elm: str) -> str | None:
    """
    Check broken link

    :param client:
    :param elm: a link
    :return: elm if broken or None
    """
    try:
        r = client.get(elm, timeout=REQUEST_TIMEOUT)
    except (requests.exceptions.RequestException, Exception):
        return elm
    if r.status_code >= 400:
        return elm
    return None


def get_broken_link(client, elms: list) -> list:
    """
    Get broken links

    :param client:
    :param elms: list all link
    :return: list broken link
    """
    res = list()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(check_broken_link, client, elm): elm for elm in elms}
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                res.append(future.result())
    return res


def getlink_a(elms: list, base_url: str) -> set:
    """
    Get full link from a tag

    :param elms: list <a>
    :param base_url:
    :return: link <a>
    """
    idx = 0
    while idx < len(elms):
        elm = elms[idx]
        if elm in ("#", "/") or elm.split(":")[0] in ("tel", "mailto", "javascript"):
            elms.pop(idx)
            idx -= 1
        elif elm[:2] not in ("ht", "//"):
            elms[idx] = base_url + "/" + elm.lstrip("/")
        elif elm[:2] == "//":
            elms[idx] = "https:" + elm
        idx += 1
    return set(elms)


def get_css_inlines(elms: list) -> list:
    """
    Get css inlines

    :param elms: list elements
    :return: list tags have css inline
    """
    for idx, value in enumerate(elms):
        tmp = html.tostring(value, encoding=ENCODING).decode(ENCODING)
        elms[idx] = re.search(r"<.*?>", tmp).group()
    return elms


def check_miss_alts(elms: list) -> list:
    """
    Check alt attribute in img tag

    :param elms: list img tags
    :return: list img tags not have alt
    """
    res = list()
    for elm in elms:
        tmp = html.tostring(elm, encoding="utf-8").decode("utf-8")
        if not re.search(r"alt=[\'\"].+[\'\"]", tmp):
            res.append(re.search(r"<img.*?>", tmp).group())
    return res


def get_page_rank(client, domain: str) -> int:
    """
    Get page rank using data from Open PageRank

    :param client:
    :param domain: domain website
    :return: rank of domain, update date
    """
    if settings.DEBUG:
        return 0

    url = "https://openpagerank.com/api/v1.0/getPageRank?domains[0]=" + domain
    headers = {"API-OPR": settings.OPEN_PAGERANK_KEY}
    try:
        r = client.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    except (requests.exceptions.RequestException, Exception) as exp:
        print("Error get_page_rank():", exp)
        return 0

    r_json = r.json()
    if r_json["response"][0]["status_code"] == 200:
        return int(r_json["response"][0]["rank"])
    return 0


def parsing(url: str) -> dict | None:
    """
    Parsing website from url

    :param url: URL from input
    :return: dict(value)
    """
    client = requests.Session()
    try:
        r = client.get(url, timeout=REQUEST_TIMEOUT)
    except (requests.exceptions.RequestException, Exception) as exp:
        print("Error parsing():", exp)
        client.close()
        return None

    # TODO: get content of the javascript-rendered page
    content = html.fromstring(r.content.decode(ENCODING))

    value = dict()

    u = urlsplit(url, allow_fragments=False)
    domain = u.netloc
    base_url = f"{u.scheme}://{domain}"

    elm = {
        "title": "//title/text()",
        "description": '//meta[@name="description"]/@content',
        "favicon": '//link[contains(@rel, "icon")]/@href',
        "robotsMeta": '//meta[@name="robots"]/@content',
    }
    elms = {
        "h1Tags": "//h1//text()",
        "h2Tags": "//h2//text()",
        "aTags": "//a/@href",
        "cssInlines": "//@style/..",
        "imgTags": "//img",
    }

    for k, v in elm.items():
        try:
            value[k] = content.xpath(v)[0]
        except (html.etree.XPathError, Exception):
            print(k, "not found!")
            value[k] = None

    for k, v in elms.items():
        try:
            value[k] = content.xpath(v)
        except (html.etree.XPathError, Exception):
            print(k, "not found!")
            value[k] = None

    try:
        value["favicon"] = get_link_img(value["favicon"], base_url)
        value["h1Tags"] = clean_elms(value["h1Tags"])
        value["h2Tags"] = clean_elms(value["h2Tags"])
        value["robotsTxt"] = getlink_robots(client, base_url)
        value["sitemaps"] = getlink_sitemap(client, base_url, value["robotsTxt"])
        value["aTags"] = getlink_a(value["aTags"], base_url)
        value["aBrokens"] = get_broken_link(client, value["aTags"])
        value["cssInlines"] = get_css_inlines(value["cssInlines"])
        value["missAlts"] = check_miss_alts(value["imgTags"])
        value["pageRank"] = get_page_rank(client, domain)
    finally:
        client.close()

    return value
