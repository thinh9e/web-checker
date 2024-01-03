import concurrent.futures
import re

import httpx
import requests
from django.conf import settings
from lxml import html

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


def get_link_img(elm, url_domain):
    """
    Get full link image
    - Input: content.xpath(img), urlDomain
    - Output: link image
    """
    if elm and elm[:2] not in {"ht", "//"}:
        elm = url_domain + "/" + elm.lstrip("/")
    return elm


def clean_elms(elms):
    """
    Clean elements
    - Input: content.xpath(elems)
    - Output: remove spaces
    """
    if elms:
        for idx, _ in enumerate(elms):
            elms[idx] = elms[idx].strip()
        elms = list(filter(None, elms))
    return elms


def getlink_robots(session, url_domain):
    """
    Get link robots.txt
    - Input: url domain
    - Output: link robots.txt or false
    """
    try:
        value = session.get(url_domain + "/robots.txt", timeout=REQUEST_TIMEOUT)
    except (requests.exceptions.RequestException, Exception):
        print("robots.txt not found!")
        return None
    if value.status_code != 200 or "plain" not in value.headers["Content-Type"]:
        return None
    return url_domain + "/robots.txt"


def getlink_sitemap(session, url_domain, robots):
    """
    Get link sitemap.xml
    - Input: url domain, robots.txt
    - Output: link sitemap.xml or false
    """
    try:
        value = session.get(url_domain + "/sitemap.xml", timeout=REQUEST_TIMEOUT)
    except (requests.exceptions.RequestException, Exception):
        print("sitemap.xml not found!")
        return None
    if robots:
        txt = session.get(robots).content.decode("utf-8")
        txt = txt.replace("\n", "")
        sitemap = re.findall(r"Sitemap:.*xml", txt)
        if sitemap:
            sitemap = sitemap[0].split("Sitemap: ")[1:]
            return sitemap
    if value.status_code != 200 or "xml" not in value.headers["Content-Type"]:
        return None
    sitemap = [url_domain + "/sitemap.xml"]
    return sitemap


def check_broken_link(session, elm):
    """
    Check broken link
    - Input: a link
    - Output: elm if broken
    """
    try:
        value = session.get(elm, timeout=REQUEST_TIMEOUT)
    except (requests.exceptions.RequestException, Exception):
        return elm
    if 400 <= value.status_code <= 599:
        return elm
    return None


def get_broken_link(session, elms):
    """
    Get broken links
    - Input: list all link
    - Output: list broken link
    """
    res = list()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(check_broken_link, session, elm): elm for elm in elms
        }
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                res.append(future.result())
    return res


def getlink_a(elms, url_domain):
    """
    Get full link from a tag
    - Input: list a, urlDomain
    - Output: link a
    """
    idx = 0
    while idx < len(elms):
        elm = elms[idx]
        if elm in ("#", "/") or elm.split(":")[0] in ("tel", "mailto", "javascript"):
            elms.pop(idx)
            idx -= 1
        elif elm[:2] not in ("ht", "//"):
            elms[idx] = url_domain + "/" + elm.lstrip("/")
        elif elm[:2] == "//":
            elms[idx] = "https:" + elm
        idx += 1
    return set(elms)


def get_css_inlines(elms):
    """
    Get css inlines
    - Input: list elements
    - Output: list tags have css inline
    """
    for idx, value in enumerate(elms):
        tmp = html.tostring(value, encoding="utf-8").decode("utf-8")
        elms[idx] = re.search(r"<.*?>", tmp).group()
    return elms


def check_miss_alts(elms):
    """
    Check alt attribute in img tag
    - Input: list img tags
    - Output: list img tags not have alt
    """
    res = list()
    for elm in elms:
        tmp = html.tostring(elm, encoding="utf-8").decode("utf-8")
        if not re.search(r"alt=[\'\"].+[\'\"]", tmp):
            res.append(re.search(r"<img.*?>", tmp).group())
    return res


def get_page_rank(domain):
    """
    Get page rank using data from Open PageRank
    - Input: domain website
    - Output: rank of domain
    """
    if settings.DEBUG:
        return 0
    url = "https://openpagerank.com/api/v1.0/getPageRank?domains[0]=" + domain
    headers = {"API-OPR": settings.OPEN_PAGERANK_KEY}
    data = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
    result = data.json()["response"][0]
    return result["rank"]


def parsing(url):
    """
    Parsing website from url
    - Input: url
    - Output: dict(value)
    """
    try:
        session = requests.Session()
        page = session.get(url, timeout=REQUEST_TIMEOUT)
        content = html.fromstring(page.content.decode("utf-8"))
    except (requests.exceptions.RequestException, Exception):
        print("Cannot get url!")
        return False

    value = dict()
    domain = url.split("/")[2]
    url_domain = url.split("/")[0] + "//" + domain

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
            value[k] = None
            print(k, "not found!")

    for k, v in elms.items():
        try:
            value[k] = content.xpath(v)
        except (html.etree.XPathError, Exception):
            value[k] = None
            print(k, "not found!")

    try:
        value["favicon"] = get_link_img(value["favicon"], url_domain)
        value["h1Tags"] = clean_elms(value["h1Tags"])
        value["h2Tags"] = clean_elms(value["h2Tags"])
        value["robotsTxt"] = getlink_robots(session, url_domain)
        value["sitemaps"] = getlink_sitemap(session, url_domain, value["robotsTxt"])
        value["aTags"] = getlink_a(value["aTags"], url_domain)
        value["aBrokens"] = get_broken_link(session, value["aTags"])
        value["cssInlines"] = get_css_inlines(value["cssInlines"])
        value["missAlts"] = check_miss_alts(value["imgTags"])
        value["pageRank"] = get_page_rank(domain)
    finally:
        session.close()

    return value
