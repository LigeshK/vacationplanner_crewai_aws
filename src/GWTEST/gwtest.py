import os
import requests
import json
from dotenv import load_dotenv

# Settings come from the project's .env file.
load_dotenv()
MCP_PROTOCOL_VERSION = os.getenv("MCP_PROTOCOL_VERSION")
CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")
CLIENT_SECRET = os.getenv("COGNITO_CLIENT_SECRET")
TOKEN_URL = os.getenv("COGNITO_TOKEN_URL")

def fetch_access_token(client_id, client_secret, token_url):
  response = requests.post(
    token_url,
    data="grant_type=client_credentials&client_id={client_id}&client_secret={client_secret}".format(client_id=client_id, client_secret=client_secret),
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
  )
  print("Access Token Response:", response.json()['access_token'])
  return response.json()['access_token']

def list_tools(gateway_url, access_token):
  headers = {
      "Content-Type": "application/json",
      "Accept": "application/json, text/event-stream",
      "Authorization": f"Bearer {access_token}",
      "MCP-Protocol-Version": MCP_PROTOCOL_VERSION
  }

  payload = {
      "jsonrpc": "2.0",
      "id": "list-tools-request",
      "method": "tools/list"
  }

  response = requests.post(gateway_url, headers=headers, json=payload)
  print("This is List Tools Response:", response.json())
  return response.json()

# Call the vacation planner tool
def call_tool(gateway_url, access_token, tool_name, arguments):
  headers = {
      "Content-Type": "application/json",
      "Accept": "application/json, text/event-stream",
      "Authorization": f"Bearer {access_token}",
      "MCP-Protocol-Version": MCP_PROTOCOL_VERSION
  }

  payload = {
      "jsonrpc": "2.0",
      "id": "call-tool-request",
      "method": "tools/call",
      "params": {
          "tool_name": tool_name, # The name of the tool to call
          "arguments": arguments # The arguments to pass to the tool
      }
  }

  response_tool = requests.post(gateway_url, headers=headers, json=payload)
  print("This is Travel Packages detail response:", response_tool.json())
  return response_tool.json()


# Example usage
gateway_url = os.getenv("GATEWAY_URL")
access_token = fetch_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)
tools = list_tools(gateway_url, access_token)
print(json.dumps(tools, indent=2))

#call the vacation planner tool with the required arguments
tools_response = call_tool(gateway_url, access_token, os.getenv("GATEWAY_TOOL_NAME"), {"city": "Mumbai"})
print(json.dumps(tools_response, indent=2))