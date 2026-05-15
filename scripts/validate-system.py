import os
import sys
import subprocess
import socket
from loguru import logger

def check_command(cmd):
    try:
        subprocess.run([cmd, "--version"], capture_output=True, check=True)
        return True
    except:
        return False

def check_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

def validate_system():
    logger.info("🔍 Initiating QueryBridge Platform Validation...")
    
    # 1. Toolchain Check
    tools = ["docker", "docker-compose", "python", "node", "npm"]
    for tool in tools:
        if check_command(tool):
            logger.success(f"Tool found: {tool}")
        else:
            logger.error(f"Missing required tool: {tool}")

    # 2. Port Check
    critical_ports = [3000, 8000, 5432, 6379]
    for port in critical_ports:
        if check_port(port):
            logger.success(f"Port available: {port}")
        else:
            logger.warning(f"Port conflict detected: {port}")

    # 3. Environment Check
    if os.path.exists(".env"):
        logger.success("Environment file (.env) exists")
    else:
        logger.error("Missing .env file. Copy from .env.example")

    logger.info("Validation complete.")

if __name__ == "__main__":
    validate_system()
