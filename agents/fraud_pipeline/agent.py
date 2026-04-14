import os
from typing import AsyncGenerator
from google.adk.agents import BaseAgent, SequentialAgent
from google.adk.events import Event
from google.adk.agents.invocation_context import InvocationContext
from google.cloud import bigquery
import vertexai
from vertexai.generative_models import GenerativeModel, Part

PROJECT_ID = "fraud-prevention-demo"
vertexai.init(project=PROJECT_ID, location="us-central1")

class ProfilerAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        destination = ctx.session.state.get("destination")
        
        client = bigquery.Client(project=PROJECT_ID)
        query = """
            SELECT
                COUNT(*) as msg_count,
                AVG(cost) as avg_cost,
                ARRAY_AGG(ip_address ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)] as last_ip,
                ARRAY_AGG(unstructured_ref IGNORE NULLS ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)] as last_ref
            FROM `fraud-prevention-demo.fraud_data.historical_transactions`
            WHERE CAST(destination AS STRING) = @destination
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("destination", "STRING", destination)
            ]
        )
        
        try:
            query_job = client.query(query, job_config=job_config)
            results = query_job.result()
            
            msg_count = 0
            avg_cost = 0.0
            last_ip = None
            last_ref = None
            for row in results:
                msg_count = row.msg_count
                avg_cost = row.avg_cost or 0.0
                last_ip = row.last_ip
                last_ref = row.last_ref
                
            result = f"Profiler: Destination {destination} has {msg_count} historical messages with average cost {avg_cost:.4f}."
            
            if last_ip:
                ctx.session.state["ip_address"] = last_ip
                result += f" Found last known IP: {last_ip}."
            
            if last_ref:
                ctx.session.state["unstructured_ref"] = last_ref
                result += f" Found associated asset: {last_ref}."
            else:
                result += " No associated asset found in history."
                
        except Exception as e:
            result = f"Profiler Error: Could not query BigQuery. {e}"
            
        ctx.session.state["customer_history"] = result
        yield Event(author=self.name, content={"parts": [{"text": result}]})

class InspectorAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        ip_address = ctx.session.state.get("ip_address")
        
        if not ip_address:
            result = "Inspector: No IP address available to check."
            yield Event(author=self.name, content={"parts": [{"text": result}]})
            return
            
        client = bigquery.Client(project=PROJECT_ID)
        query = """
            SELECT
                COUNT(*) as count,
                AVG(cost) as avg_cost
            FROM `fraud-prevention-demo.fraud_data.historical_transactions`
            WHERE ip_address = @ip_address
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("ip_address", "STRING", ip_address)
            ]
        )
        
        try:
            query_job = client.query(query, job_config=job_config)
            results = query_job.result()
            
            count = 0
            avg_cost = 0.0
            for row in results:
                count = row.count
                avg_cost = row.avg_cost or 0.0
                
            result = f"Inspector: IP {ip_address} found in {count} historical records with average cost {avg_cost:.4f}."
        except Exception as e:
            result = f"Inspector Error: Could not query BigQuery. {e}"
            
        ctx.session.state["ip_reputation"] = result
        yield Event(author=self.name, content={"parts": [{"text": result}]})

class AnalystAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        sample_text = ctx.session.state.get("sample_text")
        unstructured_ref = ctx.session.state.get("unstructured_ref")
        
        contents = []
        prompt = "Analyze the following message text and/or associated media for potential fraud, phishing, or SMS pumping patterns. Return a risk score between 0.0 and 1.0 and a brief reason."
        contents.append(prompt)
        
        if sample_text:
            contents.append(f"Sample Text: {sample_text}")
            
        if unstructured_ref:
            try:
                mime_type = "image/png"
                if unstructured_ref.endswith(".wav"):
                    mime_type = "audio/wav"
                
                contents.append(Part.from_uri(uri=unstructured_ref, mime_type=mime_type))
                contents.append(f"Analyze the attached asset: {unstructured_ref}")
            except Exception as e:
                print(f"Warning: Could not attach GCS asset: {e}")
                
        if len(contents) == 1:
            result = "Analyst: No text or asset provided for analysis."
            ctx.session.state["message_analysis"] = result
            yield Event(author=self.name, content={"parts": [{"text": result}]})
            return
            
        try:
            # Switched to gemini-2.5-pro as per user's update
            model = GenerativeModel("gemini-2.5-pro")
            response = model.generate_content(contents)
            result = f"Analyst: {response.text}"
        except Exception as e:
            result = f"Analyst Error: Could not call Gemini API. {e}"
            
        ctx.session.state["message_analysis"] = result
        yield Event(author=self.name, content={"parts": [{"text": result}]})

class DecisionAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        cust_history = ctx.session.state.get("customer_history")
        content_analysis = ctx.session.state.get("message_analysis")
        ip_rep = ctx.session.state.get("ip_reputation")
        
        decision = "ALLOW"
        reasoning = "Traffic appears normal based on historical volume."
        
        if "Profiler Error" not in cust_history and "Profiler:" in cust_history:
             if "has 0 historical messages" not in cust_history:
                  decision = "ALLOW"
                  
        if "Risk Score:" in content_analysis:
             try:
                  score_str = content_analysis.split("Risk Score:")[1].split()[0]
                  score = float(score_str)
                  if score > 0.5:
                       decision = "QUARANTINE"
                       reasoning = f"Flagged due to high content risk score: {score}."
             except:
                  if "fraud" in content_analysis.lower() or "phishing" in content_analysis.lower():
                       decision = "QUARANTINE"
                       reasoning = "Flagged due to suspicious content analysis."
            
        result = f"Decision: {decision}\nReasoning: {reasoning}\nInputs used:\n- History: {cust_history}\n- Analysis: {content_analysis}\n- IP: {ip_rep}"
        
        yield Event(author=self.name, content={"parts": [{"text": result}]})

# Orchestrator
root_agent = SequentialAgent(
    name="fraud_pipeline",
    sub_agents=[
        ProfilerAgent(name="profiler"),
        InspectorAgent(name="inspector"),
        AnalystAgent(name="analyst"),
        DecisionAgent(name="decision")
    ]
)
