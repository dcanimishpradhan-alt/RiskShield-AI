import os
from google import genai

class NarrativeGenerator:
    def __init__(self):
        if not os.environ.get("GEMINI_API_KEY"):
            raise RuntimeError("Set GEMINI_API_KEY before creating NarrativeGenerator")
        self.client = genai.Client()

    def generate_narrative(self, reason_code: str, reason_desc: str, evidence: dict) -> str:
        prompt = f"""
        You are a professional dispute resolution specialist for a merchant.
        Write a formal, compelling evidence narrative for a chargeback dispute.
        
        Chargeback Reason Code: {reason_code} - {reason_desc}
        
        Evidence available:
        {evidence}
        
        Format the response as a concise, formal letter to the acquiring bank. 
        Be authoritative and base all claims strictly on the provided evidence.
        """
        
        # Updated to use the required gemini-3.6-flash model
        response = self.client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt
        )
        return response.text

if __name__ == "__main__":
    print("Initializing LLM Narrative Generator...")
    
    generator = NarrativeGenerator()
    
    # Mock evidence mimicking the data from Component 1
    mock_evidence = {
        "authentication": {
            "3ds_status": "Y (Fully Authenticated)",
            "avs_match": "Y",
            "cvv_verified": True
        },
        "delivery": {
            "tracking_number": "AWB123456789",
            "delivery_date": "2023-10-15T14:30:00Z"
        },
        "customer_history": {
            "total_orders": 12,
            "dispute_rate": 0.0
        }
    }
    
    print("Generating evidence narrative via Gemini LLM...\n")
    narrative = generator.generate_narrative(
        reason_code="13.1", 
        reason_desc="Merchandise Not Received", 
        evidence=mock_evidence
    )
    
    print("--- GENERATED NARRATIVE ---")
    print(narrative)
    print("---------------------------")
