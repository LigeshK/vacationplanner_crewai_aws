import os
import requests
import json

MCP_PROTOCOL_VERSION = "2025-11-25"
# Set these in your environment before running:
#   export CLIENT_ID="your-client-id"
#   export CLIENT_SECRET="your-client-secret"
CLIENT_ID = "48bo6mupddn9lbjc17ueibi9d4"
CLIENT_SECRET = "1t2fhf6dc7bvm2igqkkli1c7nq9suckok0tolm2b7tes54npgebu"
TOKEN_URL = "https://ap-southeast-2czkmt0kb9.auth.ap-southeast-2.amazoncognito.com/oauth2/token"

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
gateway_url = "https://gateway-vacation-planner-lknfwclwfa.gateway.bedrock-agentcore.ap-southeast-2.amazonaws.com/mcp"
access_token = fetch_access_token(CLIENT_ID, CLIENT_SECRET, TOKEN_URL)
tools = list_tools(gateway_url, access_token)
print(json.dumps(tools, indent=2))

#call the vacation planner tool with the required arguments
tools_response = call_tool(gateway_url, access_token, "target-travel-agent-tool__get_travel_packages", {"city": "Mumbai"})
print(json.dumps(tools_response, indent=2))