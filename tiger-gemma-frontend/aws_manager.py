import boto3
import time
from typing import Optional
import streamlit as st

class AWSInstanceManager:
    def __init__(self, instance_id: str, region: str = "eu-central-1"):
        self.instance_id = instance_id
        self.region = region
        self.ec2_client = boto3.client('ec2', region_name=region)
        
    def get_status(self) -> str:
        """Get current instance status"""
        try:
            response = self.ec2_client.describe_instances(InstanceIds=[self.instance_id])
            instance = response['Reservations'][0]['Instances'][0]
            return instance['State']['Name']
        except Exception as e:
            st.error(f"Error getting instance status: {e}")
            return "unknown"
    
    def get_public_ip(self) -> Optional[str]:
        """Get public IP address"""
        try:
            response = self.ec2_client.describe_instances(InstanceIds=[self.instance_id])
            instance = response['Reservations'][0]['Instances'][0]
            return instance.get('PublicIpAddress')
        except Exception as e:
            st.error(f"Error getting IP address: {e}")
            return None
    
    def start_instance(self) -> str:
        """Start the instance and return public IP"""
        try:
            st.info("🚀 Starting GPU instance...")
            self.ec2_client.start_instances(InstanceIds=[self.instance_id])
            
            # Wait for running state
            st.info("⏳ Waiting for instance to start (this takes 2-3 minutes)...")
            waiter = self.ec2_client.get_waiter('instance_running')
            waiter.wait(
                InstanceIds=[self.instance_id],
                WaiterConfig={'Delay': 15, 'MaxAttempts': 40}
            )
            
            # Get public IP
            public_ip = self.get_public_ip()
            st.success(f"✅ Instance started! Public IP: {public_ip}")
            
            # Wait additional time for services to start
            st.info("⏳ Waiting for services to initialize (30 seconds)...")
            time.sleep(30)
            
            return public_ip
            
        except Exception as e:
            st.error(f"Failed to start instance: {e}")
            raise
    
    def stop_instance(self) -> bool:
        """Stop the instance"""
        try:
            st.info("⏹️ Stopping GPU instance...")
            self.ec2_client.stop_instances(InstanceIds=[self.instance_id])
            st.success("✅ Instance stop initiated!")
            return True
            
        except Exception as e:
            st.error(f"Failed to stop instance: {e}")
            return False
    
    def get_instance_info(self) -> dict:
        """Get detailed instance information"""
        try:
            response = self.ec2_client.describe_instances(InstanceIds=[self.instance_id])
            instance = response['Reservations'][0]['Instances'][0]
            
            return {
                "instance_id": instance['InstanceId'],
                "instance_type": instance['InstanceType'],
                "state": instance['State']['Name'],
                "public_ip": instance.get('PublicIpAddress', 'N/A'),
                "private_ip": instance.get('PrivateIpAddress', 'N/A'),
                "launch_time": instance.get('LaunchTime'),
                "availability_zone": instance['Placement']['AvailabilityZone']
            }
        except Exception as e:
            st.error(f"Error getting instance info: {e}")
            return {}
    
    def estimate_cost(self) -> dict:
        """Estimate running costs"""
        # g4dn.xlarge pricing in eu-central-1
        hourly_rate = 0.526
        
        try:
            info = self.get_instance_info()
            if info.get('state') == 'running' and info.get('launch_time'):
                # Calculate running time
                from datetime import datetime, timezone
                launch_time = info['launch_time'].replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                running_hours = (now - launch_time).total_seconds() / 3600
                
                current_cost = running_hours * hourly_rate
                daily_cost = 24 * hourly_rate
                monthly_cost = 30 * daily_cost
                
                return {
                    "hourly_rate": hourly_rate,
                    "running_hours": round(running_hours, 2),
                    "current_session_cost": round(current_cost, 2),
                    "daily_cost_if_24h": round(daily_cost, 2),
                    "monthly_cost_if_24h": round(monthly_cost, 2),
                    "status": "running"
                }
            else:
                return {
                    "hourly_rate": hourly_rate,
                    "running_hours": 0,
                    "current_session_cost": 0,
                    "daily_cost_if_24h": round(24 * hourly_rate, 2),
                    "monthly_cost_if_24h": round(30 * 24 * hourly_rate, 2),
                    "status": "stopped"
                }
        except Exception as e:
            st.error(f"Error calculating costs: {e}")
            return {"error": str(e)}