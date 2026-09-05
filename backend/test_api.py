import urllib.request, json
try:
    r = urllib.request.urlopen('http://localhost:8000/api/v1/employees')
    data = json.loads(r.read())
    print('Status: 200')
    print('Success:', data.get('success'))
    print('Total:', data.get('total'))
    items = data.get('data', data.get('items', []))
    print('Items count:', len(items))
    if items:
        print('First item keys:', list(items[0].keys()))
except Exception as e:
    print('ERROR:', e)
