from django.http import JsonResponse
import requests

REQUEST_TIMEOUT = 10  # (s)


def get_status(request):
    """
    Method: POST
    Return: JSON{data{url, status, elapsed, encoding, content}, error}
    """
    url = request.POST.get('url', False)
    data = dict()
    if url and len(request.POST) == 1:
        data['url'] = url
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
            data['status'] = resp.status_code
            data['elapsed'] = resp.elapsed.total_seconds()
            if data['status'] == 200:
                return JsonResponse({'data': data, 'error': None})
            else:
                return JsonResponse({'data': data, 'error': 'Connection unavailable'})
        except requests.exceptions.ConnectionError:
            return JsonResponse({'data': data, 'error': 'Connection error'})
        except requests.exceptions.RequestException:
            return JsonResponse({'data': data, 'error': 'Request exception'})

    return JsonResponse(status=400, data={})
