#!/bin/bash

set -e

echo "🚀 Setting up CAS Parser MCP Server..."

PROJECT_DIR="cas-mcp-server"

# 1. Create project

mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

echo "📦 Initializing Node project..."
npm init -y >/dev/null 2>&1

# 2. Install dependencies

echo "📥 Installing dependencies..."
npm install @modelcontextprotocol/sdk zod node-fetch >/dev/null 2>&1

# 3. Create server.js

echo "🛠️ Creating MCP server..."

cat > server.js << 'EOF'
import { MCPServer } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import fetch from "node-fetch";
import { z } from "zod";

const server = new MCPServer({
name: "cas-parser-mcp",
version: "1.0.0"
});

const API_KEY = process.env.CAS_PARSER_API_KEY;
const BASE_URL = "https://portfolio-parser.api.casparser.in";

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

return await res.json();
}

// ==============================
// CAS PARSERS
// ==============================
server.tool("smart_parse", {
pdf_url: z.string().optional(),
pdf_file: z.string().optional(),
password: z.string().optional()
}, (args) => callAPI("/v4/smart/parse", "POST", args));

server.tool("cdsl_parse", {
pdf_url: z.string().optional(),
pdf_file: z.string().optional(),
password: z.string().optional()
}, (args) => callAPI("/v4/cdsl/parse", "POST", args));

server.tool("nsdl_parse", {
pdf_url: z.string().optional(),
pdf_file: z.string().optional(),
password: z.string().optional()
}, (args) => callAPI("/v4/nsdl/parse", "POST", args));

server.tool("cams_kfintech_parse", {
pdf_url: z.string().optional(),
pdf_file: z.string().optional(),
password: z.string().optional()
}, (args) => callAPI("/v4/cams_kfintech/parse", "POST", args));

// ==============================
// CONTRACT NOTE
// ==============================
server.tool("contract_note_parse", {
pdf_url: z.string().optional(),
pdf_file: z.string().optional(),
password: z.string(),
broker_type: z.enum(["zerodha","groww","upstox","icici"]).optional()
}, (args) => callAPI("/v4/contract_note/parse", "POST", args));

// ==============================
// KFINTECH
// ==============================
server.tool("kfintech_generate", {
email: z.string(),
from_date: z.string(),
to_date: z.string(),
password: z.string(),
pan_no: z.string().optional()
}, (args) => callAPI("/v4/kfintech/generate", "POST", args));

// ==============================
// CDSL FETCH
// ==============================
server.tool("cdsl_fetch", {
pan: z.string(),
bo_id: z.string(),
dob: z.string()
}, (args) => callAPI("/v4/cdsl/fetch", "POST", args));

server.tool("cdsl_fetch_verify", {
session_id: z.string(),
otp: z.string(),
num_periods: z.number().optional()
}, ({ session_id, ...body }) =>
callAPI(`/v4/cdsl/fetch/${session_id}/verify`, "POST", body)
);

// ==============================
// INBOX
// ==============================
server.tool("inbox_connect", {
redirect_uri: z.string(),
state: z.string().optional()
}, (args) => callAPI("/v4/inbox/connect", "POST", args));

server.tool("inbox_cas", {
start_date: z.string().optional(),
end_date: z.string().optional(),
cas_types: z.array(z.enum(["cdsl","nsdl","cams","kfintech"])).optional(),
inbox_token: z.string()
}, ({ inbox_token, ...body }) =>
callAPI("/v4/inbox/cas", "POST", body, {
"x-inbox-token": inbox_token
})
);

server.tool("inbox_disconnect", {
inbox_token: z.string()
}, ({ inbox_token }) =>
callAPI("/v4/inbox/disconnect", "POST", {}, {
"x-inbox-token": inbox_token
})
);

// ==============================
// AUTH
// ==============================
server.tool("credits", {}, () =>
callAPI("/v1/credits", "POST")
);

server.tool("token_generate", {
expiry_minutes: z.number().optional()
}, (args) => callAPI("/v1/token", "POST", args));

// ==============================
// START SERVER
// ==============================
const transport = new StdioServerTransport();
await server.connect(transport);

console.log("✅ MCP CAS Parser server running...");
EOF

# 4. Fix package.json for ES modules

echo "⚙️ Updating package.json..."
node -e "
let pkg = require('./package.json');
pkg.type = 'module';
pkg.scripts = { start: 'node server.js' };
require('fs').writeFileSync('package.json', JSON.stringify(pkg, null, 2));
"

echo ""
echo "✅ DONE!"
echo ""
echo "👉 Next steps:"
echo "cd cas-mcp-server"
echo "CAS_PARSER_API_KEY=sandbox-with-json-responses npm start"
echo ""
echo "🔥 MCP server ready!"

