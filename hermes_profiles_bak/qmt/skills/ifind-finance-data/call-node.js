const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

const CONFIG = JSON.parse(fs.readFileSync(path.join(__dirname, 'mcp_config.json'), 'utf-8'));
const AUTH_TOKEN = CONFIG.auth_token;

const BASE = "https://api-mcp.51ifind.com:8643/ds-mcp-servers";
const SERVERS = {
    stock: `${BASE}/hexin-ifind-ds-stock-mcp`,
    fund: `${BASE}/hexin-ifind-ds-fund-mcp`,
    edb: `${BASE}/hexin-ifind-ds-edb-mcp`,
    news: `${BASE}/hexin-ifind-ds-news-mcp`,
    bond: `${BASE}/hexin-ifind-ds-bond-mcp`,
    global_stock: `${BASE}/hexin-ifind-ds-global-stock-mcp`,
    index: `${BASE}/hexin-ifind-ds-index-mcp`,
    future: `${BASE}/hexin-ifind-ds-futures-mcp`,
};

const _sessions = {};
const _req_ids = {};
const _tool_sets = {};
const BLOCKED_KEYS = new Set(['__proto__', 'prototype', 'constructor']);

function nextId(t) {
    _req_ids[t] = (_req_ids[t] || 0) + 1;
    return _req_ids[t];
}

function headers(t = null) {
    const h = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
        'Authorization': AUTH_TOKEN,
    };
    if (t && _sessions[t]) {
        h['Mcp-Session-Id'] = _sessions[t];
    }
    return h;
}

function post(t, payload, timeout = 60) {
    return new Promise((resolve, reject) => {
        const url = new URL(SERVERS[t]);
        const options = {
            hostname: url.hostname,
            port: url.port,
            path: url.pathname,
            method: 'POST',
            headers: headers(t),
            timeout: timeout * 1000,
        };

        const req = (url.protocol === 'https:' ? https : http).request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                let parsed = null;
                if (data.trim()) {
                    try {
                        parsed = JSON.parse(data);
                    } catch (e) {
                        parsed = data;
                    }
                }
                resolve({ response: res, data: parsed });
            });
        });

        req.on('error', reject);
        req.on('timeout', () => {
            req.destroy();
            reject(new Error(`Request timeout after ${timeout}s`));
        });

        req.write(JSON.stringify(payload));
        req.end();
    });
}

function validateParams(params) {
    if (params === null || typeof params !== 'object' || Array.isArray(params)) {
        throw new TypeError('input must be a JSON object');
    }

    function walk(value) {
        if (value === null) {
            return;
        }
        if (Array.isArray(value)) {
            for (const item of value) {
                walk(item);
            }
            return;
        }
        if (typeof value === 'object') {
            for (const key of Object.keys(value)) {
                if (BLOCKED_KEYS.has(key)) {
                    throw new TypeError('input contains blocked field');
                }
                walk(value[key]);
            }
            return;
        }
        if (typeof value === 'number' && !Number.isFinite(value)) {
            throw new TypeError('input contains invalid number');
        }
        if (typeof value === 'bigint' || typeof value === 'function' || typeof value === 'symbol' || typeof value === 'undefined') {
            throw new TypeError('input contains unsupported value type');
        }
    }
    walk(params);

    JSON.stringify(params);
}

async function loadToolSet(serverType) {
    if (_tool_sets[serverType]) {
        return _tool_sets[serverType];
    }

    await init(serverType);

    const payload = {
        jsonrpc: "2.0",
        id: nextId(serverType),
        method: "tools/list",
        params: {},
    };

    const { response, data } = await post(serverType, payload);
    if (response.statusCode >= 400) {
        throw new Error(`HTTP Error: ${response.statusCode}`);
    }
    if (!data || typeof data !== 'object' || !data.result || !Array.isArray(data.result.tools)) {
        throw new Error('Invalid tools/list response');
    }

    const set = new Set();
    for (const tool of data.result.tools) {
        if (tool && typeof tool.name === 'string' && tool.name) {
            set.add(tool.name);
        }
    }
    _tool_sets[serverType] = set;
    return set;
}

async function init(t) {
    if (_sessions[t]) {
        return;
    }

    const payload = {
        jsonrpc: "2.0",
        id: nextId(t),
        method: "initialize",
        params: {
            protocolVersion: "2025-03-26",
            capabilities: {},
            clientInfo: { name: "http-client", version: "1.0.0" },
        },
    };

    const { response } = await post(t, payload, 30);

    const sessionId = response.headers['mcp-session-id'] || response.headers.get?.('mcp-session-id');
    if (!sessionId) {
        throw new Error(`initialize 成功但未返回 Mcp-Session-Id`);
    }

    _sessions[t] = sessionId;

    const notify = { jsonrpc: "2.0", method: "notifications/initialized" };
    await post(t, notify, 10);
}

async function call(serverType, toolName, params) {
    if (!SERVERS[serverType]) {
        throw new Error(`unknown server_type: ${serverType}`);
    }
    validateParams(params);
    const allowedTools = await loadToolSet(serverType);
    if (!allowedTools.has(toolName)) {
        throw new Error(`toolName not allowed for server_type ${serverType}: ${toolName}`);
    }

    await init(serverType);

    const payload = {
        jsonrpc: "2.0",
        id: nextId(serverType),
        method: "tools/call",
        params: {
            name: toolName,
            arguments: params,
        },
    };

    const { response, data } = await post(serverType, payload);

    if (data && typeof data === 'object' && 'error' in data) {
        return {
            ok: false,
            status_code: response.statusCode,
            error: data.error,
            raw: data,
        };
    }

    if (response.statusCode >= 400) {
        throw new Error(`HTTP Error: ${response.statusCode}`);
    }

    return {
        ok: true,
        status_code: response.statusCode,
        data: data,
    };
}

async function listTools(serverType) {
    if (!SERVERS[serverType]) {
        throw new Error(`unknown server_type: ${serverType}`);
    }

    await init(serverType);

    const payload = {
        jsonrpc: "2.0",
        id: nextId(serverType),
        method: "tools/list",
        params: {},
    };

    const { response, data } = await post(serverType, payload);

    if (data && typeof data === 'object' && 'error' in data) {
        return {
            ok: false,
            status_code: response.statusCode,
            error: data.error,
            raw: data,
        };
    }

    if (response.statusCode >= 400) {
        throw new Error(`HTTP Error: ${response.statusCode}`);
    }

    return {
        ok: true,
        status_code: response.statusCode,
        data: data,
    };
}

async function main() {
    console.log("请按skill说明书发起明确的工具调用与参数请求，不要直接执行请求脚本");
}

module.exports = { call, listTools };

if (require.main === module) {
    main().catch(console.error);
}
