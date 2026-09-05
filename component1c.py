import json
import numpy as np

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta

def load_disputed_transactions():
    """Loads test/train data and extracts transactions flagged as disputes"""
    try:
        df_train = pd.read_json("data/synthetic_train.json")
        df_test = pd.read_json("data/synthetic_test.json")
        df = pd.concat([df_train, df_test])
        return df[df['is_disputed'] == True].copy()
    except Exception as e:
        print(f"Error loading base transactions: {e}")
        return pd.DataFrame()

def generate_chargeback_cases(disputes_df):
    cases = []
    
    # Reason codes mapped to standard networks
    REASON_CODES = [
        {"code": "13.1", "desc": "Merchandise Not Received"},
        {"code": "13.2", "desc": "Not as Described"},
        {"code": "10.4", "desc": "Fraud - Card Not Present"},
        {"code": "13.6", "desc": "Credit Not Processed"}
    ]
    
    for idx, row in disputes_df.iterrows():
        # Assign a random reason code
        reason = np.random.choice(REASON_CODES)
        
        # Dispute date is 10-45 days after the transaction
        txn_date = pd.to_datetime(row['timestamp'])
        dispute_date = txn_date + timedelta(days=np.random.randint(10, 45))
        
        # Deadline is 7-21 days after dispute date
        deadline_days = np.random.randint(7, 21)
        deadline_date = dispute_date + timedelta(days=deadline_days)
        
        # Generate plausible evidence based on reason code
        evidence = {
            "avs_match": np.random.choice([True, False], p=[0.7, 0.3]),
            "cvv_verified": True,
            "device_fingerprint": row['device_fingerprint']
        }
        
        if reason['code'] == "13.1":
            evidence["tracking_number"] = f"AWB{np.random.randint(10000000, 99999999)}"
            evidence["delivery_proof"] = row['delivery_status'] == "delivered"
        elif reason['code'] == "13.2":
            evidence["return_policy_accepted"] = True
            evidence["customer_emails"] = 2
        
        # Win-rate predictor labels (Known outcomes)
        # If true fraud, usually lost. If friendly fraud and delivered, usually won.
        if row['category_label'] == "true_fraud":
            outcome = np.random.choice(["won", "lost"], p=[0.1, 0.9])
        else:
            outcome = np.random.choice(["won", "lost"], p=[0.6, 0.4])
            
        case = {
            "dispute_id": f"disp_{row['payment_id'].split('_')[1]}",
            "payment_id": row['payment_id'],
            "reason_code": reason['code'],
            "reason_desc": reason['desc'],
            "dispute_date": dispute_date.isoformat(),
            "respond_by": deadline_date.isoformat(),
            "evidence_available": evidence,
            "historic_outcome": outcome
        }
        cases.append(case)
        
        # Cap at 500+ cases as requested
        if len(cases) >= 550: 
            break
            
    return cases

if __name__ == "__main__":
    print("Generating chargeback dispute cases...")
    base_df = load_disputed_transactions()
    
    if not base_df.empty:
        cases = generate_chargeback_cases(base_df)
        with open("data/chargeback_cases.json", "w") as f:
            json.dump(cases, f, indent=2, cls=NumpyEncoder)
        print(f"Successfully generated {len(cases)} synthetic chargeback cases.")
    else:
        print("Please run synthetic_generator.py first to create base transactions.")