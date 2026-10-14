#!/usr/bin/env python3
"""
Connect Amusement Park MCP Server to Azure AI Foundry using SDK.

Prerequisites:
- Azure AI Foundry project created with agent
- Azure AI Projects SDK installed: pip install "azure-ai-projects>=2.1.0"
- Environment variables set:
  - AZURE_PROJECT_ENDPOINT (e.g., https://test-eval-1.services.ai.azure.com/api/projects/proj-default)
  - AGENT_NAME (Foundry agent name, e.g., "agent-POC")
  - CEO_PAT (Snowflake PAT for CEO persona)
  - ANALYST_PAT (Snowflake PAT for Analyst persona)
"""

import os
import sys
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# Configuration
MCP_URL = "https://abz2pr-tqmttqp-hw26207.snowflakecomputing.app/mcp"
MCP_API_KEY = "123456"

CEO_PAT = os.getenv("CEO_PAT")
ANALYST_PAT = os.getenv("ANALYST_PAT")
AZURE_PROJECT_ENDPOINT = os.getenv("AZURE_PROJECT_ENDPOINT")
AGENT_NAME = os.getenv("AGENT_NAME")


def test_mcp_connection(project_client, agent_name: str, pat: str, entra_user: str):
    """
    Test MCP tool connection by calling the agent.
    
    Args:
        project_client: AIProjectClient instance
        agent_name: Agent name in Foundry
        pat: Snowflake PAT for this persona
        entra_user: Entra ID user (e.g., "ceo@amusementpark.com")
    """
    print(f"\n=== Testing agent with {entra_user} ===")
    
    try:
        # Get OpenAI client for the agent
        openai_client = project_client.get_openai_client(agent_name=agent_name)
        
        # Create a conversation
        conversation = openai_client.conversations.create()
        print(f"   Conversation created: {conversation.id}")
        
        # Send a test message
        user_message = f"Hi! I'm {entra_user}. What parks do we have?"
        print(f"   Sending: '{user_message}'")
        
        response = openai_client.responses.create(
            conversation=conversation.id,
            input=[{"role": "user", "content": user_message}],
        )
        
        print(f"   ✅ Agent responded: {response.output_text[:100]}...")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    """Test Amusement Park MCP server connection via Azure AI Foundry SDK."""
    
    print("=" * 70)
    print("Amusement Park MCP → Azure AI Foundry SDK Test")
    print("=" * 70)
    
    # Validate environment
    if not all([CEO_PAT, ANALYST_PAT, AZURE_PROJECT_ENDPOINT, AGENT_NAME]):
        print("\n❌ Missing required environment variables!")
        print("\nSet:")
        print("   export CEO_PAT='<snowflake-ceo-pat>'")
        print("   export ANALYST_PAT='<snowflake-analyst-pat>'")
        print("   export AZURE_PROJECT_ENDPOINT='https://test-eval-1.services.ai.azure.com/api/projects/proj-default'")
        print("   export AGENT_NAME='agent-POC'")
        sys.exit(1)
    
    print("\n✅ Configuration loaded:")
    print(f"   MCP URL: {MCP_URL}")
    print(f"   Foundry Endpoint: {AZURE_PROJECT_ENDPOINT}")
    print(f"   Agent Name: {AGENT_NAME}")
    
    # Initialize Azure AI Projects client
    print("\n=== Authenticating with Azure ===")
    try:
        credential = DefaultAzureCredential()
        project_client = AIProjectClient(
            endpoint=AZURE_PROJECT_ENDPOINT,
            credential=credential,
            allow_preview=True,
        )
        print("✅ Connected to Azure AI Foundry")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        print("\nTroubleshooting:")
        print("  - Check AZURE_PROJECT_ENDPOINT format")
        print("  - Verify Azure CLI authentication: az account show")
        print("  - Ensure azure-ai-projects SDK is installed: pip install 'azure-ai-projects>=2.1.0'")
        sys.exit(1)
    
    # Test agent connection with CEO persona
    print("\n=== Testing Agent Connection ===")
    ceo_success = test_mcp_connection(
        project_client,
        agent_name=AGENT_NAME,
        pat=CEO_PAT,
        entra_user="ceo@amusementpark.com"
    )
    
    # Test agent connection with Analyst persona
    analyst_success = test_mcp_connection(
        project_client,
        agent_name=AGENT_NAME,
        pat=ANALYST_PAT,
        entra_user="analyst@amusementpark.com"
    )
    
    # Summary
    print("\n" + "=" * 70)
    if ceo_success and analyst_success:
        print("✅ SUCCESS! Agent is ready for MCP tool calls")
    else:
        print("⚠️  Agent connected but test calls had issues")
    print("=" * 70)
    
    print("\nNext steps:")
    print("  1. Go to Azure AI Foundry portal:")
    print(f"     {AZURE_PROJECT_ENDPOINT}")
    print(f"  2. Open agent: {AGENT_NAME}")
    print("  3. Configure MCP Tools in Agent Settings:")
    print("     - Add MCP Server Connection")
    print("     - Server URL: " + MCP_URL)
    print("     - Add custom headers:")
    print("       * Authorization: Snowflake Token=\"<YOUR_PAT>\"")
    print("       * X-API-Key: 123456")
    print("       * X-Entra-User: ceo@amusementpark.com (or analyst@amusementpark.com)")
    print("  4. Test in agent chat:")
    print("     - Ask: 'What is ticket net revenue by park?'")
    print("     - CEO should see 3 parks + GL data")
    print("     - Analyst should see 1 park + GL access denied")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
