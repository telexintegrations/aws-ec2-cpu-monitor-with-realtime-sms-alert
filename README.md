EC2 CPU Usage Monitoring and SMS Alert Integration
Overview
This API monitors the CPU usage of an AWS EC2 instance using CloudWatch and sends alerts via Twilio SMS and a specified channel. It integrates with Telex, requiring two JSON integrations:

integration.json – Sends messages to a channel.
interval-integration.json – Sends channel messages to SMS.
The service uses an AWS IAM role to retrieve CloudWatch metrics, assume necessary permissions, and trigger alerts when CPU usage exceeds 85%.

Features
✅ EC2 CPU Usage Monitoring – Fetches CPU utilization using AWS CloudWatch.
✅ AWS IAM Role Assumption – Uses STS to assume roles for cross-account access.
✅ Telex Integration – Supports dual integrations for both channel and SMS notifications.
✅ Twilio SMS Alerts – Sends SMS when CPU usage exceeds 85%.
✅ CORS Handling – Allows requests from any domain for seamless API usage.

Technology Stack
FastAPI – Web framework for API development.
AWS CloudWatch – Fetches EC2 instance CPU metrics.
AWS STS (Security Token Service) – Assumes IAM roles.
Twilio API – Sends SMS notifications.
Python – Core programming language.
IAM Role Setup
Before integrating with AWS, configure an IAM role with the required permissions:

Go to AWS IAM Console → Roles → Create Role.
Select Another AWS account and enter your AWS Account ID.
Add the following trust policy to allow the necessary AWS user to assume the role:


{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::277707100860:user/assume-role-user"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}

Attach the CloudWatchReadOnlyAccess policy to the role.
Save the Role ARN.
API Endpoint
GET /tick/{account_id}/{role_name}/{instance_id}
Retrieves CPU usage and sends an alert if usage exceeds 85%.

Parameter	Type	Description
account_id	string	AWS Account ID
role_name	string	IAM Role Name
instance_id	string	EC2 Instance ID

Response Examples
✅ Normal Response (200 OK)


{
 "CPU usage for instance i-03f21cd8e811c7936 is 3.834224304675515% at 20:    12:22."
}
🚨 Alert Triggered (202 OK)


{
  "detail": "Error retrieving CPU usage: <error message>"
}
Telex Integration Activation
To activate integrations in Telex, follow these steps:

1️⃣ Activate interval-integration.json (Channel Messaging Integration)
Upload the interval-integration.json file and ensure all required fields are provided.

2️⃣ Activate integration.json (SMS Forwarding Integration)
Upload the integration.json file and configure it to forward channel messages to SMS.

Once both integrations are active, the system will notify the channel and forward messages as SMS.

Setup Instructions
Requirements
Python 3.7+
AWS account with CloudWatch permissions
Twilio account for SMS alerts
Install Dependencies
Clone the repository and install dependencies:


git clone https://github.com/telexintegrations/aws-ec2-cpu-monitor-with-realtime-sms-alert.git
pip install -r requirements.txt
Run Locally
Start the FastAPI server using Uvicorn:

uvicorn main:app --reload
API will be available at http://127.0.0.1:8000.

Example Request:

curl "http://127.0.0.1:8000/tick/123456789012/MyRole/i-0abcd1234ef567890"


Notes:
✔ Ensure IAM Role permissions allow CloudWatch Read Access.
✔ Modify the CPU alert threshold in the code if needed.
✔ Set Twilio credentials correctly for SMS alerts.


🔥 Now your service is fully integrated with AWS, Telex, and Twilio for real-time EC2 monitoring and SMS alerts! 🚀