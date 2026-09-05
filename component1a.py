import pandas as pd
import numpy as np
import uuid
import json
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split

# Config based on hackathon spec
TOTAL_RECORDS = 10000
DISTRIBUTIONS = {
    "normal": 0.85,
    "friendly_fraud": 0.08,
    "true_fraud": 0.05,
    "abuse_ring": 0.02
}

# How many distinct returning customers to simulate. Each gets a stable
# customer_id + card_hash + usual device/ip so repeat-transaction patterns
# (needed for things like CE3.0 matching) actually exist in the data.
NUM_RETURNING_CUSTOMERS = 800


def generate_razorpay_id(prefix):
    """Generates realistic looking Razorpay IDs (e.g., pay_Hxc...)"""
    suffix = uuid.uuid4().hex[:14]
    return f"{prefix}_{suffix}"


def build_customer_pool(num_customers):
    """
    Pre-generate a pool of returning customers, each with a stable identity:
    customer_id, card_hash, a 'usual' device fingerprint, and a 'usual' IP geo.
    Reusing these across multiple transactions is what makes it possible to
    later find '2 prior undisputed transactions on the same card' for CE3.0.
    """
    pool = []
    for _ in range(num_customers):
        pool.append({
            "customer_id": generate_razorpay_id("cust"),
            "card_hash": uuid.uuid4().hex[:16],
            "usual_device": uuid.uuid4().hex[:12],
            "usual_ip_geo": np.random.choice(["Mumbai, IN", "Delhi, IN", "Bangalore, IN", "Pune, IN"]),
        })
    return pool


def generate_transactions(num_records):
    np.random.seed(42)

    # Calculate counts
    counts = {k: int(v * num_records) for k, v in DISTRIBUTIONS.items()}
    # Adjust for rounding errors
    counts['normal'] += num_records - sum(counts.values())

    data = []
    base_time = datetime.now() - timedelta(days=180)  # 6 months of data

    # Generate Abuse Ring shared entities
    ring_devices = [f"dev_ring_{i}" for i in range(5)]
    ring_ips = [f"192.168.1.{i}" for i in range(5)]

    # Returning-customer pool. "normal" and "friendly_fraud" transactions
    # draw from this pool most of the time so the same card/customer shows
    # up across multiple transactions spread over the 6-month window —
    # otherwise every transaction is a one-off and nothing has real history.
    customer_pool = build_customer_pool(NUM_RETURNING_CUSTOMERS)
    RETURNING_CUSTOMER_PROB = 0.75  # how often a normal/friendly_fraud txn reuses a pool customer

    for category, count in counts.items():
        for _ in range(count):
            # Base variables
            timestamp = base_time + timedelta(
                days=np.random.randint(0, 180),
                hours=np.random.randint(0, 24),
                minutes=np.random.randint(0, 60)
            )
            amount = np.random.randint(500, 15000) * 100  # In paise, standard range

            # Defaults — one-off identity, used unless overridden below
            customer_id = generate_razorpay_id("cust")
            card_hash = uuid.uuid4().hex[:16]
            device = uuid.uuid4().hex[:12]
            ip_geo = np.random.choice(["Mumbai, IN", "Delhi, IN", "Bangalore, IN", "Pune, IN"])
            delivery_status = "delivered"
            is_disputed = False

            # Override based on category
            if category == "true_fraud":
                amount = np.random.randint(20000, 150000) * 100  # High amounts
                ip_geo = np.random.choice(["Lagos, NG", "Moscow, RU", "Unknown", "Delhi, IN"])
                timestamp = timestamp.replace(hour=np.random.choice([2, 3, 4]))
                delivery_status = np.random.choice(["failed", "delivered", "in_transit"])
                # True fraud stays a one-off identity — a fraudster using a
                # stolen card usually doesn't have a legitimate transaction
                # history on it, which is exactly why they won't pass CE3.0.

            elif category == "friendly_fraud":
                is_disputed = True
                # Friendly fraud disputes are the ones CE3.0 is meant to catch:
                # a real, returning customer disputing a legitimate purchase.
                # So these should draw from the returning-customer pool most
                # of the time, reusing their usual card/device/IP.
                if np.random.random() < RETURNING_CUSTOMER_PROB:
                    cust = customer_pool[np.random.randint(0, len(customer_pool))]
                    customer_id = cust["customer_id"]
                    card_hash = cust["card_hash"]
                    device = cust["usual_device"]
                    ip_geo = cust["usual_ip_geo"]

            elif category == "abuse_ring":
                device = np.random.choice(ring_devices)
                ip_geo = np.random.choice(ring_ips)
                amount = np.random.randint(1000, 5000) * 100  # Low amounts to fly under radar
                is_disputed = True  # Rings often end in mass chargebacks

            elif category == "normal":
                # Normal transactions also mostly come from returning
                # customers, so there's a realistic pool of prior undisputed
                # transactions for the CE3.0 engine to find later.
                if np.random.random() < RETURNING_CUSTOMER_PROB:
                    cust = customer_pool[np.random.randint(0, len(customer_pool))]
                    customer_id = cust["customer_id"]
                    card_hash = cust["card_hash"]
                    device = cust["usual_device"]
                    ip_geo = cust["usual_ip_geo"]

            record = {
                "payment_id": generate_razorpay_id("pay"),
                "order_id": generate_razorpay_id("order"),
                "customer_id": customer_id,
                "amount": amount,
                "currency": "INR",
                "timestamp": timestamp.isoformat(),
                "device_fingerprint": device,
                "ip_geo": ip_geo,
                "card_hash": card_hash,
                "merchant_category": "electronics",  # standardizing for MVP
                "delivery_status": delivery_status,
                "communication_log": np.random.choice(["email_sent", "chat_resolved", "no_contact"]),
                "category_label": category,
                "is_fraud": 1 if category in ["true_fraud", "abuse_ring"] else 0,
                "is_disputed": is_disputed
            }
            data.append(record)

    df = pd.DataFrame(data)
    # Shuffle the dataset
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    return df


def export_stratified_splits(df):
    """Splits data 80/20 ensuring fraud labels are proportionally represented"""
    X = df.drop(columns=['is_fraud'])
    y = df['is_fraud']

    # 80/20 train/test split with stratified sampling
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=42
    )

    # Recombine for saving
    train_df = pd.concat([X_train, y_train], axis=1)
    test_df = pd.concat([X_test, y_test], axis=1)

    train_df.to_json("data/synthetic_train.json", orient="records", indent=2)
    test_df.to_json("data/synthetic_test.json", orient="records", indent=2)
    print(f"Generated {len(train_df)} training and {len(test_df)} testing records.")

    # Sanity check: how many cards actually have 2+ undisputed transactions?
    # This is the population CE3.0 matching can possibly succeed against.
    full_df = pd.concat([train_df, test_df])
    undisputed = full_df[full_df['is_disputed'] == False]  # noqa: E712
    card_counts = undisputed.groupby('card_hash').size()
    reusable_cards = (card_counts >= 2).sum()
    print(f"Cards with 2+ undisputed transactions (CE3.0-testable): {reusable_cards}")


if __name__ == "__main__":
    print("Generating synthetic transactions...")
    df = generate_transactions(TOTAL_RECORDS)
    export_stratified_splits(df)