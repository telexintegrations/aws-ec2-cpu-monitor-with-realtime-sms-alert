import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
import boto3
import httpx
import asyncio
import requests
from twilio.rest import Client
import json
import re
app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Twilio Credentials

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
#AWS CREDENTIALS
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Async function to send SMS alert
async def send_sms_alert(to_phone_number: str, message_body: str):
    loop = asyncio.get_event_loop()
    try:
        message = await loop.run_in_executor(
            None, 
            lambda: twilio_client.messages.create(
                body=message_body,
                from_=TWILIO_PHONE_NUMBER,
                to=to_phone_number
            )
        )
        return {"sid": message.sid, "status": message.status}
    except Exception as e:
        return {"error": str(e)}


# Function to assume AWS IAM role
def assume_role(account_id: str, role_name: str):
    try:
        sts_client = boto3.client(
            'sts',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
        response = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName="CloudWatchAccessSession"
        )
        return response['Credentials']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error assuming role: {str(e)}")
@app.get("/integration.json")
def get_integration_json(request: Request):
    """
    Returns json metadata for the output integration.
    """
    base_url = str(request.base_url).rstrip("/")
    return {
  "data": {
    "date": {
      "created_at": "2025-02-19",
      "updated_at": "2025-02-19"
    },
"descriptions": {
  "app_name": "Telex CHANNEL MESSAGE TO SMS",
  "app_description": "Sends Telex channel messages as SMS to a specified number",
  "app_url": "BASE_URL",
  "app_logo": "https://res.cloudinary.com/naijaceo/image/upload/v1595027227/3d_logo_maker_bonus_ssqd0g.png",
  "background_color": "#fff"
},

    "integration_category": "Monitoring & Logging",
    "integration_type": "output",
    "is_active": True,
    
    "key_features": [
      "Sends SMS to a target in real time",
      "Real time notifications when message enters the channel",
      "Easy setup with pre-configured commit patterns"
    ],
     "website": "https://hng12-stage3-ec2-cpu-usage-monitoring.onrender.com/integration.json",
    "author": "YoungOH",
    "settings": [

    {
        "label": "slack_channel_url",
        "type": "text",
        "required": True,
        "description": "Slack Webhook URL",
        "default": ""
      },
      {
        "label": "Phone_number",
        "type": "text",
        "required": True,
        "default": ""
      }
    ],
    "target_url": "https://hng12-stage3-ec2-cpu-usage-monitoring.onrender.com/target"
  }
}

@app.get("/interval-integration.json")
def get_interval_integration_json(request: Request):
    """
    Returns integration metadata for the check_cpu function.
    """
    base_url = str(request.base_url).rstrip("/")
    return {

  "data": {
    "date": {
      "created_at": "2025-02-19",
      "updated_at": "2025-02-19"
    },
    "descriptions": {
      "app_name": "AWS EC2 INSTANCE CPU Monitor",
      "app_description": "Monitors EC2 CPU usage and sends alerts",
      "app_url": "https://hng12-stage3-ec2-cpu-usage-monitoring.onrender.com",
      "app_logo": "https://res.cloudinary.com/naijaceo/image/upload/v1595027227/3d_logo_maker_bonus_ssqd0g.png",
      "background_color": "#ffffff"
    },
    "integration_category": "Monitoring & Logging",
    "integration_type": "interval",
    "is_active": True,
 
    "key_features": [
      "Automated CPU monitoring for AWS EC2 instances",
      "Sends SMS alerts when CPU usage exceeds threshold",
      "Configurable monitoring interval",
      "Seamless AWS IAM role authentication"
    ],
    "permissions": {
      "monitoring_user": {
        "always_online": True,
        "display_name": "Performance Monitor"
      }
    },     
    "website": "https://hng12-stage3-ec2-cpu-usage-monitoring.onrender.com/interval-integration.json",
    "author": "YoungOH",
    "settings": [
      {
        "label": "AWS-Account-ID",
        "type": "text",
        "required": True,
        "default": ""
      },
      {
        "label": "IAM-Role-Name",
        "type": "text",
        "required": True,
        "default": ""
      },
      {
        "label": "EC2-Instance-ID",
        "type": "text",
        "required": True,
        "default": ""
      },
          {
        "label": "Return-URL",
        "type": "text",
        "required": True,
        "default": ""
      },
      {
        "label": "interval",
        "type": "text",
        "required": True,
        "default": "*/5 * * * *"
      }
    ],
    "tick_url": "https://hng12-stage3-ec2-cpu-usage-monitoring.onrender.com/tick",
    "target_url": ""
  }
}

class CPUMonitorPayload(BaseModel):
    account_id: str
    role_name: str
    instance_id: str
    return_url: str
    
class SMSPayload(BaseModel):
    message: str
    settings: list  

async def get_cpu_usage(account_id: str, role_name: str, instance_id: str) -> float:
    credentials = assume_role(account_id, role_name)
    cloudwatch_client = boto3.client(
        "cloudwatch",
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
        region_name=AWS_REGION
    )
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=5)
    
    response = cloudwatch_client.get_metric_statistics(
        Period=300,
        StartTime=start_time.isoformat(),
        EndTime=end_time.isoformat(),
        MetricName="CPUUtilization",
        Namespace="AWS/EC2",
        Statistics=["Average"],
        Dimensions=[{"Name": "InstanceId", "Value": instance_id}]
    )
    
    if "Datapoints" in response and response["Datapoints"]:
        return response["Datapoints"][0]["Average"]
    return 0.0


async def monitor_cpu_task(payload: CPUMonitorPayload):
    cpu_usage = await get_cpu_usage(payload.account_id, payload.role_name, payload.instance_id)
    end_time = datetime.utcnow()
    formatted_time = end_time.strftime("%H:%M:%S")
    message = f"CPU usage for instance {payload.instance_id} is {cpu_usage}% at {formatted_time}."
    data = {
        "event_name": "CPU Monitor",
        "message": message,
        "status": "success" ,#if not alert_sent else "error",
        "username": payload.instance_id
    }
    
    response = requests.post(
        payload.return_url,
        json=data,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    )

async def send_sms_alert(to_phone_number: str, message_body: str):
    loop = asyncio.get_event_loop()
    try:
        message = await loop.run_in_executor(
            None, 
            lambda: twilio_client.messages.create(
                body=message_body,
                from_=TWILIO_PHONE_NUMBER,
                to=to_phone_number
            )
        )
        return {"sid": message.sid, "status": message.status}
    except Exception as e:
        return {"error": str(e)}

async def send_sms_task(payload: SMSPayload):
    try:
        phone_number = None
        for setting in payload.settings:
            if setting.get("label") == "Phone_number":
                phone_number = setting.get("default")
                break
        message = payload.message  # Extract message
        if phone_number:
            await send_sms_alert(phone_number, message)  # Send SMS
        else:
            print("Error: No phone number found in settings.")
    except Exception as e:
        print(f"Error processing SMS task: {str(e)}")

@app.post("/tick", status_code=202)
async def monitor_cpu(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()    
    settings_dict = {s["label"]: s["default"] for s in payload["settings"]}
    required_keys = ["AWS-Account-ID", "IAM-Role-Name", "EC2-Instance-ID", "Return-URL"]
    if not all(key in settings_dict for key in required_keys):
        return {"status": "error", "message": "Missing required settings"}
    cpu_payload = CPUMonitorPayload(
        account_id=settings_dict["AWS-Account-ID"],
        role_name=settings_dict["IAM-Role-Name"],
        instance_id=settings_dict["EC2-Instance-ID"],
        return_url=settings_dict["Return-URL"]
    )
    background_tasks.add_task(monitor_cpu_task, cpu_payload)
    return {"status": "accepted"}
@app.post("/target", status_code=202)
async def send_alert(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        message = data.get("message", "")
        cpu_usage_match = re.search(r"CPU usage for instance .*? is ([\d.]+)%", message)
        cpu_usage = float(cpu_usage_match.group(1)) if cpu_usage_match else None
        if cpu_usage is not None and cpu_usage > 85:
            payload = SMSPayload(**data)
            background_tasks.add_task(send_sms_task, payload)
        else:
            print("CPU usage is normal. No SMS sent.")
        return {"status": "accepted"}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format"}, 400
@app.get("/health_check")
async def health_check():
    """Checks if server is active."""
    return {"status": "active"}