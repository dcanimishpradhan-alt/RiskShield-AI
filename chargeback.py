import pandas as pd
import numpy as np
import uuid
from datetime import datetime, timedelta
import os

def generate_chargeback_cases(num_cases=550):
    np.random.seed(42)
    cases = []
    
    # Reason codes mapped to standard networks
    reason_codes = [
        {"code": "13.1", "desc": "Merchandise Not Received"},
        {"code": "13.2", "desc": "Not as Described"},
        {"code": "10.4", "desc": "Fraud - Card Not Present"},
        {"code": "13.6", "desc": "Credit Not Processed"}
    ]
    
    for _ in range(num_cases):
        reason = np.random.choice(reason_codes)
        created_at = datetime.now() - timedelta(days=np.random.randint(1, 180))
        # Standard 7-21 day window for evidence submission
    )deadline = created_at + timedelta(days=int(np.random.choice([7, 14, 21])))
        
        # Generate available evidence based on the dispute reason
        evidence = {}
        if reason["code"] == "13.1":
            evidence["delivery_proof"] = np.random.choice([True, False], p=[0.7, 0.3])
            evidence["tracking_number"] = f"TRK{uuid.uuid4().hex[:10].upper()}"
        elif reason["code"] == "13.2":
            evidence["return_policy_accepted"] = True
            evidence["communication_log"] = "Customer emailed support; resolution pending."
        elif reason["code"] == "10.4":
            evidence["ip_log_match"] = bool(np.random.choice([True, False]))
            evidence["device_fingerprint_match"] = bool(np.random.choice([True, False]))
            evidence["3ds_authenticated"] = bool(np.random.choice([True, False]))
        elif reason["code"] == "13.6":
            evidence["refund_receipt"] = f"RFND_{uuid.uuid4().hex[:8]}"
            
        # Simulate known outcome labels (won/lost) for training the win-rate predictor
        win_prob = 0.3 # Default low win-rate (~30% industry average)
        if reason["code"] == "10.4" and evidence.get("3ds_authenticated"):
            win_prob = 0.95 # Liability shift to issuer
        elif reason["code"] == "13.1" and evidence.get("delivery_proof"):
            win_prob = 0.85 # Strong proof of delivery
            
        outcome = "won" if np.random.random() < win_prob else "lost"
        
        case = {
            "dispute_id": f"disp_{uuid.uuid4().hex[:14]}",
            "payment_id": f"pay_{uuid.uuid4().hex[:14]}",
            "reason_code": reason["code"],
            "reason_desc": reason["desc"],
            "created_at": created_at.isoformat(),
            "respond_by": deadline.isoformat(),
            "evidence_available": evidence,
            "outcome_label": outcome
        }
        cases.append(case)
        
    df = pd.DataFrame(cases)
    
    # Ensure data directory exists and save
    os.makedirs("data", exist_ok=True)
    file_path = "data/chargeback_cases.json"
    df.to_json(file_path, orient="records", indent=2)
    print(f"✅ Generated {len(df)} synthetic chargeback cases at {file_path}")
    return df

if __name__ == "__main__":
    generate_chargeback_cases()