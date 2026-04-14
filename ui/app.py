import gradio as gr
import requests
import json

def investigate(phone_number, sample_text, ip_address):
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
                "destination": phone_number,
                "sample_text": sample_text,
                "ip_address": ip_address
            }
        }
        
        response = requests.post(run_url, json=payload)
        if response.status_code != 200:
            return f"Error running agent: {response.status_code} - {response.text}"
            
        events = response.json()
        
        report = f"Investigation Report for Phone Number: {phone_number}\n"
        report += "--------------------------------------------\n"
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

# Custom CSS for Sinch Branding
custom_css = """
body {
    background-color: #F7F9FA;
    font-family: 'Inter', sans-serif;
}
.container {
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
}
.sinch-header {
    background-color: #645DC2; /* Violet */
    color: white;
    padding: 20px;
    border-radius: 10px 10px 0 0;
    text-align: center;
}
.sinch-header h1 {
    margin: 0;
    font-size: 24px;
}
.sinch-header p {
    margin: 5px 0 0 0;
    opacity: 0.8;
}
.sinch-button {
    background-color: #D15CB4 !important; /* Sinch Pink */
    color: white !important;
    border: none !important;
    font-weight: bold !important;
}
.sinch-button:hover {
    background-color: #B54A9A !important;
}
.output-box {
    background-color: white;
    border: 1px solid #EBEEF0;
    border-radius: 0 0 10px 10px;
    padding: 20px;
}
"""

with gr.Blocks() as demo:
    with gr.Column(elem_classes="container"):
        # Replaced Div with Column and applied class
        with gr.Column(elem_classes="sinch-header"):
            gr.Markdown("# Sinch Real-Time Fraud Monitoring")
            gr.Markdown("Powered by ADK Multi-Agent AI")
            
        with gr.Row(elem_classes="output-box"):
            with gr.Column(scale=1):
                phone_input = gr.Textbox(label="Phone Number", placeholder="+263222222222")
                text_input = gr.Textbox(label="Sample Text", placeholder="Enter SMS text here...")
                ip_input = gr.Textbox(label="IP Address", placeholder="187.37.63.58")
                submit_btn = gr.Button("Run Investigation", elem_classes="sinch-button")
                
            with gr.Column(scale=2):
                report_output = gr.Textbox(label="Investigation Report", lines=20)
                
        submit_btn.click(
            fn=investigate,
            inputs=[phone_input, text_input, ip_input],
            outputs=report_output
        )

if __name__ == "__main__":
    # Moved css to launch() as per warning
    demo.launch(server_name="0.0.0.0", server_port=7860, css=custom_css)
