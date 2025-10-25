import json
import urllib.request
import time

def get(url, timeout=5):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode()

def post(url, data, timeout=5):
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type':'application/json'}, method='POST')
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode()

if __name__ == '__main__':
    base = 'http://127.0.0.1:8000'
    # wait for health
    for i in range(10):
        try:
            status, body = get(base + '/health')
            print('HEALTH', status, body)
            break
        except Exception as e:
            print('health wait', i, 'error', e)
            time.sleep(1)
    else:
        print('health check failed, abort')
        raise SystemExit(1)

    payload = {
        'name': '自动测试项目',
        'wish': '实现更多',
        'obstacle': '时间',
        'plan': '分步执行',
        'outcome': '成功',
        'description': '由自动化测试创建'
    }

    try:
        status, body = post(base + '/woops/', payload)
        print('POST', status, body)
    except Exception as e:
        print('POST failed', e)

    try:
        status, body = get(base + '/woops/')
        print('GET', status, body)
    except Exception as e:
        print('GET failed', e)
