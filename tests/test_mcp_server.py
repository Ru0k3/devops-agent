import asyncio
from fastmcp import Client
from tools.mcp_tools import mcp

async def main():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        names = {tool.name for tool in tools}
        expected = {"fetch_logs", "list_recent_commits", "get_commit_diff", "sandbox_run_tests", "deploy_to_sandbox", "post_slack_report", "escalate_to_oncall"}
        assert expected <= names
        result = await client.call_tool("fetch_logs", {"service": "payment-service", "time_range": "last_15m"})
        assert result
        print("mcp tools", sorted(names))

if __name__ == "__main__": asyncio.run(main())
