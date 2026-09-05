from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import hmac
import hashlib
from typing import Optional

app = FastAPI()

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stores latest transaction
latest_dispute = {}


# =========================================================
# WEBHOOK
# =========================================================

@app.post("/webhook/dispute")
async def handle_dispute_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None)
):

    global latest_dispute

    body_bytes = await request.body()

    secret = "rzp_test_secret_hackathon"

    expected_signature = hmac.new(
        secret.encode("utf-8"),
        body_bytes,
        hashlib.sha256
    ).hexdigest()

    # Check signature
    if x_razorpay_signature != expected_signature:
        raise HTTPException(
            status_code=400,
            detail="Invalid signature"
        )

    payload = await request.json()

    dispute_data = (
        payload
        .get("payload", {})
        .get("dispute", {})
        .get("entity", {})
    )

    ce_3_0_data = (
        dispute_data
        .get("enhanced_evidence", {})
        .get("visa_ce_3_0", {})
    )

    # Save transaction
    latest_dispute = {
        "id": dispute_data.get("id"),
        "status": dispute_data.get("status"),
        "amount": dispute_data.get("amount"),
        "currency": dispute_data.get("currency"),
        "visa_ce_3_0_status": ce_3_0_data.get(
            "eligibility_status"
        ),
        "message": "Fraudulent transaction detected"
    }

    # Terminal output
    print("\n========================================")
    print("     FRAUDULENT TRANSACTION RECEIVED")
    print("========================================")
    print("Dispute ID:", dispute_data.get("id"))
    print("Status:", dispute_data.get("status"))
    print("Amount:", dispute_data.get("amount"))
    print("Currency:", dispute_data.get("currency"))
    print(
        "Visa CE 3.0:",
        ce_3_0_data.get("eligibility_status")
    )
    print("========================================\n")

    return {
        "status": "success",
        "message": "Webhook processed successfully",
        "dispute": latest_dispute
    }


# =========================================================
# FRONTEND API
# =========================================================

@app.get("/api/dispute")
async def get_latest_dispute():

    return {
        "dispute": latest_dispute
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
async def health_check():

    return {
        "status": "Backend is running"
    }


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "component4:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
    