import urllib.request
import traceback

try:
    resp = urllib.request.urlopen('http://127.0.0.1:8000/invoices')
    print('status', resp.status)
    print(resp.read().decode())
except Exception as e:
    traceback.print_exc()
    if hasattr(e, 'read'):
        try:
            data = e.read().decode(errors='ignore')
            print('body:', data)
        except Exception:
            pass
