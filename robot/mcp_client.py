# -*- coding: utf-8 -*-
"""
robot/mcp_client.py ? ?? MCP ???? stock-trading-mcp ??
??????????????????????? MySQL??
"""
import asyncio
import json
import os
import sys
import time

_PROJECT_ROOT = r"D:/workspace_gitee/ai_agent_qmt"
_MCP_SERVER_PY = r"D:/workspace_gitee/ai_agent_qmt/mcp_server/run_mcp_server.py"
_MCP_PYTHON = r"D:/workspace_gitee/ai_agent_qmt/mcp_server/.venv/Scripts/python.exe"


def _parse_result(res):
    """?? MCP call_tool ?????? JSON?? dict?"""
    text = res.content[0].text if res.content else ""
    try:
        return json.loads(text)
    except Exception:
        return {"success": False, "message": text or "empty result"}


class TradingMCP(object):
    """stock-trading-mcp ?????????????? asyncio ?????"""

    def __init__(self, python=None, server_py=None):
        self._python = python or _MCP_PYTHON
        self._server_py = server_py or _MCP_SERVER_PY
        self._session = None
        self._stack = None

    # ---- ??????? ----
    def _ensure_imports(self):
        if "mcp" not in sys.modules:
            sys.path.insert(0, _PROJECT_ROOT)
        from mcp import ClientSession, StdioServerParameters  # noqa
        from mcp.client.stdio import stdio_client  # noqa
        return ClientSession, StdioServerParameters, stdio_client

    def _run(self, coro):
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            # ????????? jupyter/?????????????
            new_loop = asyncio.new_event_loop()
            try:
                return new_loop.run_until_complete(coro)
            finally:
                new_loop.close()
        else:
            return asyncio.run(coro)

    def connect(self):
        ClientSession, StdioServerParameters, stdio_client = self._ensure_imports()

        async def _connect():
            params = StdioServerParameters(
                command=self._python,
                args=[self._server_py],
            )
            stack = asyncio.ExitStack()
            read, write = await stack.enter_async_context(stdio_client(params))
            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            return session, stack

        self._session, self._stack = self._run(_connect())
        return self

    def close(self):
        if self._stack is not None:
            try:
                self._run(self._stack.aclose())
            except Exception:
                pass
            self._stack = None
            self._session = None

    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    # ---- ?? ----
    def query_account(self):
        return self._run(self._session.call_tool("query_account", {}))

    def query_positions(self):
        return self._run(self._session.call_tool("query_positions", {}))

    def query_orders(self):
        return self._run(self._session.call_tool("query_orders", {}))

    def query_deals(self):
        return self._run(self._session.call_tool("query_deals", {}))

    def query_stock_selection(self):
        return self._run(self._session.call_tool("query_stock_selection", {}))

    # ---- ?? ----
    def place_order(self, order_type, order_code, volume, remark=""):
        return self._run(
            self._session.call_tool(
                "place_order",
                {
                    "order_type": order_type,
                    "order_code": order_code,
                    "volume": int(volume),
                    "remark": remark or "",
                },
            )
        )

    def cancel_order(self, order_sys_id):
        return self._run(
            self._session.call_tool("cancel_order", {"order_sys_id": str(order_sys_id)})
        )

    # ---- ???? ----
    def account_dict(self):
        r = _parse_result(self.query_account())
        rows = r.get("data") or []
        return rows[0] if rows else {}

    def positions_list(self):
        r = _parse_result(self.query_positions())
        return r.get("data") or []

    def watchlist_list(self):
        r = _parse_result(self.query_stock_selection())
        return r.get("data") or []

    def orders_list(self):
        r = _parse_result(self.query_orders())
        return r.get("data") or []

    def deals_list(self):
        r = _parse_result(self.query_deals())
        return r.get("data") or []
