import gradio as gr
import requests
import json

def investigate(destination, sample_text, ip_address, customer_id):
    # Updated to port 8001
    base_url = "http://127.0.0.1:8001"
    
    try:
        # 1. Create Session
        create_session_url = f"{base_url}/apps/fraud_pipeline/users/user1/sessions"
        response = requests.post(create_session_url)
        if response.status_code != 200:
            return f"Error creating session: {response.status_code} - {response.text}"
        session_id = response.json().get("id")
        
        # 2. Run Agent
        run_url = f"{base_url}/run"
        payload = {
            "appName": "fraud_pipeline",
            "userId": "user1",
            "sessionId": session_id,
            "newMessage": {
                "parts": [{"text": "Start investigation"}]
            },
            "stateDelta": {
                "destination": destination,
                "sample_text": sample_text,
                "ip_address": ip_address,
                "customer_id": customer_id
            }
        }
        
        response = requests.post(run_url, json=payload)
        if response.status_code != 200:
            return f"Error running agent: {response.status_code} - {response.text}"
            
        events = response.json()
        
        report = f"Investigation Report for Destination: {destination}\n"
        report += "--------------------------------------------\n"
        report += f"Customer ID: {customer_id}\n"
        report += f"IP Address: {ip_address}\n"
        report += f"Sample Text: {sample_text}\n\n"
        
        for event in events:
            author = event.get("author")
            content = event.get("content", {})
            parts = content.get("parts", [])
            text = parts[0].get("text", "") if parts else ""
            
            report += f"[{author.capitalize()}]\n{text}\n\n"
            
        return report
        
    except Exception as e:
        return f"Error: {e}"

iface = gr.Interface(
    fn=investigate,
    inputs=[
        gr.Textbox(label="Destination"),
        gr.Textbox(label="Sample Text"),
        gr.Textbox(label="IP Address"),
        gr.Textbox(label="Customer ID")
    ],
    outputs=gr.Textbox(label="Report"),
    title="Fraud Investigation Agent (ADK Multi-Agent)",
    description="Enter alert details to trigger an automated investigation."
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=7860)
