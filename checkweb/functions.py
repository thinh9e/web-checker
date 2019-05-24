from concurrent.futures import ThreadPoolExecutor
import re
import requests
from lxml import html
from django.conf import settings


def reCaptcha(response, userIP):
    """
    Check reCaptcha
    - Input: POST['g-recaptcha-response'], META['HTTP_X_FORWARDED_FOR']
    - Output: True if pass
    """
    # data = {
    #     'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
    #     'response': response,
    #     'remoteip': userIP,
    # }
    # verify = requests.post(
    #     'https://www.google.com/recaptcha/api/siteverify', data=data)
    # result = verify.json()
    # return result['success']
    print(response, userIP)
    return True


def getLinkImg(elm, urlDomain):
    """
    Get full link image
    - Input: content.xpath(img), urlDomain
    - Output: link image
    """
    if elm and elm[:2] not in {'ht', '//'}:
        elm = urlDomain + "/" + elm.lstrip('/')
    return elm


def cleanElms(elms):
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


def getlinkRobots(urlDomain):
    """
    Get link robots.txt
    - Input: url domain
    - Output: link robots.txt or false
    """
    try:
        value = requests.get(urlDomain + '/robots.txt')
    except BaseException:
        print('robots.txt not found!')
        return None
    if value.status_code != 200 or 'plain' not in value.headers['Content-Type']:
        return None
    return urlDomain + '/robots.txt'


def getlinkSitemap(urlDomain, robots):
    """
    Get link sitemap.xml
    - Input: url domain, robots.txt
    - Output: link sitemap.xml or false
    """
    try:
        value = requests.get(urlDomain + '/sitemap.xml')
    except BaseException:
        print('sitemap.xml not found!')
        return None
    if robots:
        txt = requests.get(robots).content.decode('utf-8')
        txt = txt.replace('\n', '')
        sitemap = re.findall(r'Sitemap:.*xml', txt)
        if sitemap:
            sitemap = sitemap[0].split('Sitemap: ')[1:]
            return sitemap
    if value.status_code != 200 or 'xml' not in value.headers['Content-Type']:
        return None
    sitemap = [urlDomain + '/sitemap.xml']
    return sitemap


def checkBrokenLink(elm):
    """
    Check broken link
    - Input: a link
    - Output: elm if broken
    """
    try:
        value = requests.get(elm, timeout=5)
    except BaseException:
        return elm
    if value.status_code != 200:
        return elm
    return None


def getBrokenLink(elms):
    """
    Get broken links
    - Input: list all link
    - Output: list broken link
    """
    res = list()
    with ThreadPoolExecutor() as executor:
        for elm in executor.map(checkBrokenLink, elms):
            if elm:
                res.append(elm)
    return res


def getlinkA(elms, urlDomain):
    """
    Get full link from a tag
    - Input: list a, urlDomain
    - Output: link a
    """
    idx = 0
    while idx < len(elms):
        elm = elms[idx]
        if elm in ('#', '/') or elm.split(':')[0] in ('tel', 'mailto', 'javascript'):
            elms.pop(idx)
            idx -= 1
        elif elm[:2] not in ('ht', '//'):
            elms[idx] = urlDomain + "/" + elm.lstrip('/')
        elif elm[:2] == '//':
            elms[idx] = 'https:' + elm
        idx += 1
    return set(elms)


def getCSSInlines(elms):
    """
    Get css inlines
    - Input: list elements
    - Output: list tags have css inline
    """
    for idx, value in enumerate(elms):
        tmp = html.tostring(value, encoding='utf-8').decode('utf-8')
        elms[idx] = re.search(r'<.*?>', tmp).group()
    return elms


def checkMissAlts(elms):
    """
    Check alt attribute in img tag
    - Input: list img tags
    - Output: list img tags not have alt
    """
    res = list()
    for elm in elms:
        tmp = html.tostring(elm, encoding='utf-8').decode('utf-8')
        if not re.search(r'alt=(\'|\").+(\'|\")', tmp):
            res.append(re.search(r'<img.*?>', tmp).group())
    return res


def getPageRank(domain):
    """
    Get page rank using data from Open PageRank
    - Input: domain website
    - Output: rank of domain
    """
    # url = 'https://openpagerank.com/api/v1.0/getPageRank?domains[0]=' + domain
    # headers = {
    #     'API-OPR': settings.OPEN_PAGERANK_KEY
    # }
    # data = requests.get(url, headers=headers)
    # result = data.json()['response'][0]
    # return result['rank']
    return 0


def parsing(url):
    """
    Parsing website from url
    - Input: url
    - Output: dict(value)
    """
    try:
        page = requests.get(url, timeout=5)
        content = html.fromstring(page.content.decode('utf-8'))
    except BaseException:
        print('Cannot get url!')
        return False

    value = dict()
    domain = url.split('/')[2]
    urlDomain = url.split('/')[0] + '//' + domain

    elm = {
        'title': '//title/text()',
        'description': '//meta[@name="description"]/@content',
        'favicon': '//link[contains(@rel, "icon")]/@href',
        'robotsMeta': '//meta[@name="robots"]/@content',
    }
    elms = {
        'h1Tags': '//h1//text()',
        'h2Tags': '//h2//text()',
        'aTags': '//a/@href',
        'cssInlines': '//@style/..',
        'imgTags': '//img',
    }

    for k, v in elm.items():
        try:
            value[k] = content.xpath(v)[0]
        except BaseException:
            value[k] = None
            print(k, 'not found!')

    for k, v in elms.items():
        try:
            value[k] = content.xpath(v)
        except BaseException:
            value[k] = None
            print(k, 'not found!')

    value['favicon'] = getLinkImg(value['favicon'], urlDomain)
    value['h1Tags'] = cleanElms(value['h1Tags'])
    value['h2Tags'] = cleanElms(value['h2Tags'])
    value['robotsTxt'] = getlinkRobots(urlDomain)
    value['sitemaps'] = getlinkSitemap(urlDomain, value['robotsTxt'])
    value['aTags'] = getlinkA(value['aTags'], urlDomain)
    value['aBrokens'] = getBrokenLink(value['aTags'])
    value['cssInlines'] = getCSSInlines(value['cssInlines'])
    value['missAlts'] = checkMissAlts(value['imgTags'])
    value['pageRank'] = getPageRank(domain)

    return value
