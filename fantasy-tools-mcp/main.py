import os

from dotenv import load_dotenv
from fastmcp import FastMCP
from supabase import create_client

from helpers.tool_analytics import ToolAnalyticsMiddleware
from tools.registry import register_tools

load_dotenv()  # Loads variables from .env

# Initialize OpenTelemetry tracing for Arize Phoenix (if endpoint configured)
PHOENIX_ENDPOINT = os.getenv("PHOENIX_COLLECTOR_ENDPOINT")
if PHOENIX_ENDPOINT:
    try:
        from openinference.instrumentation.anthropic import AnthropicInstrumentor
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import SimpleSpanProcessor

        tracer_provider = TracerProvider()
        tracer_provider.add_span_processor(
            SimpleSpanProcessor(OTLPSpanExporter(endpoint=PHOENIX_ENDPOINT))
        )
        AnthropicInstrumentor().instrument(tracer_provider=tracer_provider)
        print(f"[Tracing] Phoenix tracing initialized → {PHOENIX_ENDPOINT}")
    except ImportError:
        print("[Tracing] OTel packages not installed — tracing disabled")
else:
    print("[Tracing] PHOENIX_COLLECTOR_ENDPOINT not set — tracing disabled")

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Initialize FastMCP
mcp = FastMCP("Gridiron Tools MCP")

# Register analytics middleware (instruments every tool call)
mcp.add_middleware(ToolAnalyticsMiddleware())

# Register all tools
register_tools(mcp, supabase)

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)

# Add a simple health check (if FastMCP supports it)
