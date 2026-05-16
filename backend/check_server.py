import urllib.request
try:
    with urllib.request.urlopen("http://localhost:8000/health") as response:
        print(f"Status: {response.status}")
        print(f"Data: {response.read().decode()}")
except Exception as e:
    print(f"Error: {e}")
