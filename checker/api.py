import requests
from django.http import JsonResponse


def parse_content(request):
    """
    Method: POST

    :param request: to get url
    :return: JSON{data{encoding, content, time}, error}
    """
    url = request.POST.get('url', False)
    data = dict()
    if url and len(request.POST) == 1:
        try:
            resp = requests.get(url, timeout=3 * 10)
            data['encoding'] = resp.encoding
            data['content'] = resp.content.decode(data['encoding'])
            data['time'] = resp.elapsed.total_seconds()
            if resp.status_code == 200:
                return JsonResponse({'data': data, 'error': None})
            else:
                return JsonResponse({'data': data, 'error': 'Connection unavailable'})
        except requests.exceptions.RequestException:
            return JsonResponse({'data': data, 'error': 'Request exception'})

    return JsonResponse(status=400, data={})


def get_status(request):
    """
    Method: POST

    :param request: to get url
    :return: JSON{data{url, status, time}, error}
    """
    url = request.POST.get('url', False)
    data = dict()
    if url and len(request.POST) == 1:
        data['url'] = url
        try:
            resp = requests.get(url, timeout=10)
            data['status'] = resp.status_code
            data['time'] = resp.elapsed.total_seconds()
            if data['status'] == 200:
                return JsonResponse({'data': data, 'error': None})
            else:
                return JsonResponse({'data': data, 'error': 'Connection unavailable'})
        except requests.exceptions.RequestException:
            return JsonResponse({'data': data, 'error': 'Request exception'})

    return JsonResponse(status=400, data={})
