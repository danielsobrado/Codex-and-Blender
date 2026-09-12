"""Probe the installed server via MCP, without mutating the live scene."""
import asyncio
import json
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]

async def main():
    server = StdioServerParameters(command=str(ROOT / '.venv/Scripts/blender-mcp.exe'))
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            results = {'tools': [t.name for t in tools.tools]}
            for name in ('get_blendfile_summary_path_info', 'get_objects_summary'):
                result = await session.call_tool(name, {})
                results[name] = result.model_dump(mode='json')
                if result.isError:
                    raise RuntimeError(str(result))
            (ROOT/'output/mcp_check.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
            print(json.dumps(results,indent=2))

if __name__ == '__main__':
    asyncio.run(main())
