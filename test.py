import hashlib
import hmac
import json
import requests


url = "http://127.0.0.1:8000/webhook/dispute"

secret = "rzp_test_secret_hackathon"


payload = {
    "payload": {
        "dispute": {
            "entity": {
                "id": "disp_987654321",
                "status": "open",
                "amount": 499900,
                "currency": "INR",

                "enhanced_evidence": {
                    "visa_ce_3_0": {
                        "eligibility_status":
                            "COMPLIANT_LIABILITY_SHIFT"
                    }
                }
            }
        }
    }
}


body_bytes = json.dumps(
    payload
).encode("utf-8")


signature = hmac.new(
    secret.encode("utf-8"),
    body_bytes,
    hashlib.sha256
).hexdigest()


headers = {
    "Content-Type": "application/json",
    "X-Razorpay-Signature": signature
}


response = requests.post(
    url,
    data=body_bytes,
    headers=headers
)


print("Status Code:", response.status_code)

print("Response:", response.json())