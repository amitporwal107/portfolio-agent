import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

async function main() {
  const transport = new StdioClientTransport({
    command: "npx",
    args: ["-y", "cas-parser-node-mcp@latest"]
  });

  const client = new Client({
    name: "portfolio-agent",
    version: "1.0.0"
  });

  await client.connect(transport);

  const tools = await client.listTools();
  console.log("Available MCP Tools:\n", tools);
}

main();
