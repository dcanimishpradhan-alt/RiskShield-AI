import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import xgboost as xgb

class RiskScorer:
    def __init__(self):
        # Unsupervised: Catches novel fraud patterns
        self.iso_forest = IsolationForest(contamination=0.05, random_state=42)
        
        # Supervised: High precision on known fraud patterns
        self.xgb_model = xgb.XGBClassifier(
            n_estimators=100, 
            max_depth=4,
            learning_rate=0.1,
            objective='binary:logistic',
            eval_metric='auc'
        )
        self.is_trained = False
        
    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Feature engineering pipeline for tabular transaction data."""
        df_feat = pd.DataFrame()
        df_feat['amount'] = df['amount']
        
        # Ensure timestamp is datetime
        timestamps = pd.to_datetime(df['timestamp'])
        df_feat['hour_of_day'] = timestamps.dt.hour
        
        # Simulate velocity and location features for the hackathon pipeline
        df_feat['velocity_1h'] = np.random.randint(1, 10, size=len(df))
        df_feat['distance_from_billing'] = np.random.uniform(0, 1000, size=len(df))
        
        return df_feat

    def train(self, X_train_df: pd.DataFrame, y_train: pd.Series):
        X_features = self.extract_features(X_train_df)
        
        self.iso_forest.fit(X_features)
        self.xgb_model.fit(X_features, y_train)
        self.is_trained = True
        
    def predict_risk(self, transaction_data: dict) -> dict:
        if not self.is_trained:
            raise ValueError("Models must be trained before prediction.")
            
        df = pd.DataFrame([transaction_data])
        X_feat = self.extract_features(df)
        
        # Anomaly score: 1 is normal, -1 is anomaly -> map to risk penalty
        anomaly_score = self.iso_forest.predict(X_feat)[0]
        anomaly_risk = 100 if anomaly_score == -1 else 10
        
        # XGBoost probability of fraud
        xgb_prob = self.xgb_model.predict_proba(X_feat)[0][1]
        xgb_risk = int(xgb_prob * 100)
        
        # Ensemble: 70% supervised, 30% unsupervised
        final_risk_score = int((xgb_risk * 0.7) + (anomaly_risk * 0.3))
        
        return {
            "risk_score": min(final_risk_score, 100),
            "xgb_probability": float(xgb_prob),
            "anomaly_detected": bool(anomaly_score == -1)
        }

if __name__ == "__main__":
    import pandas as pd
    
    print("Loading synthetic training data...")
    # Read the data created in Component 1
    train_df = pd.read_json("data/synthetic_train.json")
    
    # Assuming 'is_fraud' is your target column from Component 1
    X_train = train_df.drop(columns=["is_fraud"])
    y_train = train_df["is_fraud"]
    
    scorer = RiskScorer()
    print("Training Risk Scoring Engine (XGBoost + Isolation Forest)...")
    scorer.train(X_train, y_train)
    print("Training complete!")
    
    # Test a sample prediction
    sample_txn = X_train.iloc[0].to_dict()
    result = scorer.predict_risk(sample_txn)
    print("Sample Risk Score Result:", result)