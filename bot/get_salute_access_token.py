import requests

SALUTE_SPEECH_API_KEY = "ODRlOGJmZGUtM2U2Ni00MWJkLWJkNTQtMWNkNzFlZWIwNzA0OjU1MjA3ZTU3LTljNjktNGY0MS1iMDhlLTNmODI2ZDA5ZjE5Yw=="

url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

payload={
          'scope': 'SALUTE_SPEECH_PERS'
          }
headers = {
          'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
              'RqUID': '61b769b0-32b6-41fc-a1bd-402d09d69813',
                'Authorization': f'Basic {SALUTE_SPEECH_API_KEY}'
                }

response = requests.post(url, headers=headers, data=payload, verify=False)

print(response.text)
