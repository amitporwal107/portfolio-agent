import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  ListToolsRequestSchema,
  CallToolRequestSchema
} from "@modelcontextprotocol/sdk/types.js";
import fetch from "node-fetch";

// ==============================
// CONFIG
// ==============================
const API_KEY = process.env.CAS_PARSER_API_KEY;
const BASE_URL = "https://portfolio-parser.api.casparser.in";

// ==============================
// SERVER INIT
// ==============================
const server = new Server(
  {
    name: "cas-parser-mcp",
    version: "1.0.0"
  },
  {
    capabilities: {
      tools: {}
    }
  }
);

// ==============================
// API HELPER
// ==============================
async function callAPI(path, method = "POST", body = {}, headers = {}) {
  console.log("📡 Calling:", path);

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: {
      "x-api-key": API_KEY,
      "Content-Type": "application/json",
      ...headers
    },
    body: method !== "GET" ? JSON.stringify(body) : undefined
  });

  const data = await res.json();

  if (!res.ok) {
    console.error("❌ API Error:", data);
  }

  return data;
}

// ==============================
// TOOL DEFINITIONS
// ==============================
const tools = [
  {
    name: "smart_parse",
    description: "Auto-detect CAS type and parse PDF",
    inputSchema: {
      type: "object",
      properties: {
        pdf_url: { type: "string" },
        pdf_file: { type: "string" },
        password: { type: "string" }
      }
    }
  },
  {
    name: "cdsl_parse",
    description: "Parse CDSL CAS",
    inputSchema: { type: "object", properties: {} }
  },
  {
    name: "nsdl_parse",
    description: "Parse NSDL CAS",
    inputSchema: { type: "object", properties: {} }
  },
  {
    name: "cams_kfintech_parse",
    description: "Parse CAMS/KFintech CAS",
    inputSchema: { type: "object", properties: {} }
  },
  {
    name: "contract_note_parse",
    description: "Parse broker contract note",
    inputSchema: { type: "object", properties: {} }
  },
  {
    name: "kfintech_generate",
    description: "Generate CAS via KFintech",
    inputSchema: { type: "object", properties: {} }
  },
  {
    name: "cdsl_fetch",
    description: "Request OTP for CDSL CAS",
    inputSchema: { type: "object", properties: {} }
  },
  {
    name: "cdsl_fetch_verify",
    description: "Verify OTP and fetch CAS",
    inputSchema: { type: "object", properties: {} }
  },
  {
    name: "inbox_connect",
    description: "Connect Gmail inbox",
    inputSchema: { type: "object", properties: {} }
  },
  {
    name: "inbox_cas",
    description: "List CAS from inbox",
    inputSchema: { type: "object", properties: {} }
  },
  {
    name: "inbox_disconnect",
    description: "Disconnect inbox",
    inputSchema: { type: "object", properties: {} }
  },
  {
    name: "credits",
    description: "Check API credits",
    inputSchema: { type: "object", properties: {} }
  },
  {
    name: "token_generate",
    description: "Generate access token",
    inputSchema: { type: "object", properties: {} }
  }
];

// ==============================
// LIST TOOLS
// ==============================
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return { tools };
});

// ==============================
// CALL TOOL
// ==============================
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args = {} } = request.params;

  switch (name) {
    case "smart_parse":
      return callAPI("/v4/smart/parse", "POST", args);

    case "cdsl_parse":
      return callAPI("/v4/cdsl/parse", "POST", args);

    case "nsdl_parse":
      return callAPI("/v4/nsdl/parse", "POST", args);

    case "cams_kfintech_parse":
      return callAPI("/v4/cams_kfintech/parse", "POST", args);

    case "contract_note_parse":
      return callAPI("/v4/contract_note/parse", "POST", args);

    case "kfintech_generate":
      return callAPI("/v4/kfintech/generate", "POST", args);

    case "cdsl_fetch":
      return callAPI("/v4/cdsl/fetch", "POST", args);

    case "cdsl_fetch_verify":
      return callAPI(
        `/v4/cdsl/fetch/${args.session_id}/verify`,
        "POST",
        args
      );

    case "inbox_connect":
      return callAPI("/v4/inbox/connect", "POST", args);

    case "inbox_cas":
      return callAPI("/v4/inbox/cas", "POST", args, {
        "x-inbox-token": args.inbox_token
      });

    case "inbox_disconnect":
      return callAPI("/v4/inbox/disconnect", "POST", {}, {
        "x-inbox-token": args.inbox_token
      });

    case "credits":
      return callAPI("/v1/credits", "POST");

    case "token_generate":
      return callAPI("/v1/token", "POST", args);

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
});

// ==============================
// START SERVER
// ==============================
const transport = new StdioServerTransport();
await server.connect(transport);

console.log("✅ MCP CAS Parser server running (NEW SDK)");
