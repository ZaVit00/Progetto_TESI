"""
API Key: 6805b1a48e97f4a433bf
API Secret: d0f3faa29d0acef0109fe95530cd7f3dacfc68b2e940c33890a5b605593cebe8
JWT: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiJhYWY3YjI5Ny03NDZlLTQzN2ItOGExMy04YTU0ODQ3ZjUwMTUiLCJlbWFpbCI6InYuemF6YTExQHN0dWRlbnRpLnVuaWJhLml0IiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInBpbl9wb2xpY3kiOnsicmVnaW9ucyI6W3siZGVzaXJlZFJlcGxpY2F0aW9uQ291bnQiOjEsImlkIjoiRlJBMSJ9LHsiZGVzaXJlZFJlcGxpY2F0aW9uQ291bnQiOjEsImlkIjoiTllDMSJ9XSwidmVyc2lvbiI6MX0sIm1mYV9lbmFibGVkIjpmYWxzZSwic3RhdHVzIjoiQUNUSVZFIn0sImF1dGhlbnRpY2F0aW9uVHlwZSI6InNjb3BlZEtleSIsInNjb3BlZEtleUtleSI6IjY4MDViMWE0OGU5N2Y0YTQzM2JmIiwic2NvcGVkS2V5U2VjcmV0IjoiZDBmM2ZhYTI5ZDBhY2VmMDEwOWZlOTU1MzBjZDdmM2RhY2ZjNjhiMmU5NDBjMzM4OTBhNWI2MDU1OTNjZWJlOCIsImV4cCI6MTc4MTM2MDE5NX0.FeL-mgm4bAa4UNMWoRhPpChIl_rJ6ElRIHvTm1VJP9M
"""
# Inserisci qui la tua JWT Key (consiglio: per produzione, usa variabili d'ambiente!)
JWT_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiJhYWY3YjI5Ny03NDZlLTQzN2ItOGExMy04YTU0ODQ3ZjUwMTUiLCJlbWFpbCI6InYuemF6YTExQHN0dWRlbnRpLnVuaWJhLml0IiwiZW1haWxfdmVyaWZpZWQiOnRydWUsInBpbl9wb2xpY3kiOnsicmVnaW9ucyI6W3siZGVzaXJlZFJlcGxpY2F0aW9uQ291bnQiOjEsImlkIjoiRlJBMSJ9LHsiZGVzaXJlZFJlcGxpY2F0aW9uQ291bnQiOjEsImlkIjoiTllDMSJ9XSwidmVyc2lvbiI6MX0sIm1mYV9lbmFibGVkIjpmYWxzZSwic3RhdHVzIjoiQUNUSVZFIn0sImF1dGhlbnRpY2F0aW9uVHlwZSI6InNjb3BlZEtleSIsInNjb3BlZEtleUtleSI6IjY4MDViMWE0OGU5N2Y0YTQzM2JmIiwic2NvcGVkS2V5U2VjcmV0IjoiZDBmM2ZhYTI5ZDBhY2VmMDEwOWZlOTU1MzBjZDdmM2RhY2ZjNjhiMmU5NDBjMzM4OTBhNWI2MDU1OTNjZWJlOCIsImV4cCI6MTc4MTM2MDE5NX0.FeL-mgm4bAa4UNMWoRhPpChIl_rJ6ElRIHvTm1VJP9M"

# Endpoint Pinata
PINATA_URL = "https://api.pinata.cloud/pinning/pinFileToIPFS"

import json
import requests

# 1. Simula un dizionario Merkle Path
merkle_path = {
    "101": {"d": "01", "h": ["hashA", "hashB"]},
    "102": {"d": "10", "h": ["hashC", "hashD"]}
}

# 2. Scrivi file JSON
file_name = "merkle_path.json"
with open(file_name, "w") as f:
    json.dump(merkle_path, f, indent=2)

# 3. Upload Pinata
url = "https://api.pinata.cloud/pinning/pinFileToIPFS"
headers = {"Authorization" : f"Bearer {JWT_KEY}"}
files = {'file': (file_name, open(file_name, 'rb'))}

res = requests.post(url, headers=headers, files=files)

# 4. Risultato
if res.status_code == 200:
    cid = res.json()["IpfsHash"]
    print(f"[OK] CID: {cid}")
    print(f"Link gateway: https://gateway.pinata.cloud/ipfs/{cid}")
else:
    print(f"[ERRORE {res.status_code}] {res.text}")
