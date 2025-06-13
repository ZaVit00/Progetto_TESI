import requests

# CID del file su IPFS
cid = "QmeFmab9C38Fx2GBrKvGdhC9Gm9DYpZk9V3niCsz3vytFu"

# Gateway Pinata (più affidabile se hai caricato lì il file)
gateway_url = f"https://gateway.pinata.cloud/ipfs/{cid}"

try:
    response = requests.get(gateway_url, timeout=10)
    response.raise_for_status()  # Solleva eccezione se status ≠ 200

    # Mostra contenuto (assumiamo sia testo/JSON)
    print("[OK] File scaricato con successo!")
    print(response.text)

except requests.exceptions.RequestException as e:
    print(f"[ERRORE] Impossibile accedere al file IPFS: {e}")
