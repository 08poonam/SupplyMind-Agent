"""
SupplyMind Agent — Microsoft Foundry Reasoning Agent
=====================================================
This is the agent layer that wraps your existing ML models
into a Microsoft Foundry multi-step reasoning agent.

File: agent/supplymind_agent.py

Setup:
  pip install azure-ai-projects azure-ai-inference azure-identity flask requests python-dotenv

Usage:
  python agent/supplymind_agent.py
"""

import os
import json
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Azure / Foundry SDK imports
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    FunctionTool,
    ToolSet,
    AgentThread,
    MessageRole,
)
from azure.identity import DefaultAzureCredential

load_dotenv()

# ─────────────────────────────────────────────────────────
# CONFIG — fill these from your Azure AI Foundry project
# ─────────────────────────────────────────────────────────
FOUNDRY_CONNECTION_STRING = os.getenv("FOUNDRY_CONNECTION_STRING")  # from Azure portal
FLASK_ML_BASE_URL = os.getenv("FLASK_ML_BASE_URL", "http://localhost:5000/api/v1")
PORT = int(os.getenv("AGENT_PORT", 8000))

# ─────────────────────────────────────────────────────────
# TOOL FUNCTIONS — these call YOUR existing Flask ML APIs
# ─────────────────────────────────────────────────────────

def forecast_demand(product_id: str, periods: int = 30) -> str:
    """
    Forecast future demand for a product.
    Calls your /demand/forecast endpoint.
    Returns demand forecast with confidence intervals.
    """
    try:
        resp = requests.get(
            f"{FLASK_ML_BASE_URL}/demand/forecast",
            json={"product_id": product_id, "periods": periods},
            timeout=10
        )
        data = resp.json()
        return json.dumps({
            "product_id": product_id,
            "forecast_mean": data.get("mean", 0),
            "forecast_lower": data.get("lower", 0),
            "forecast_upper": data.get("upper", 0),
            "trend": data.get("trend", "stable"),
            "periods": periods,
            "model_used": data.get("model", "prophet"),
            "reasoning": f"Demand forecasted at {data.get('mean', 0):.1f} units over {periods} days "
                         f"(95% CI: [{data.get('lower', 0):.1f}, {data.get('upper', 0):.1f}]). "
                         f"Trend is {data.get('trend', 'stable')}."
        })
    except Exception as e:
        # Fallback mock if API not running yet — remove before demo
        return json.dumps({
            "product_id": product_id,
            "forecast_mean": 120.5,
            "forecast_lower": 95.0,
            "forecast_upper": 148.0,
            "trend": "increasing",
            "periods": periods,
            "model_used": "prophet",
            "reasoning": f"Demand forecast: 120.5 units over {periods} days (mock data — connect Flask API)."
        })


def check_inventory(product_id: str, warehouse_ids: list = None) -> str:
    """
    Check current inventory levels and calculate reorder recommendations.
    Calls your /inventory/status endpoint.
    """
    try:
        resp = requests.get(
            f"{FLASK_ML_BASE_URL}/inventory/status",
            json={"product_id": product_id, "warehouse_ids": warehouse_ids or []},
            timeout=10
        )
        data = resp.json()
        return json.dumps({
            "product_id": product_id,
            "current_stock": data.get("current_stock", 0),
            "safety_stock": data.get("safety_stock", 0),
            "reorder_point": data.get("reorder_point", 0),
            "eoq": data.get("eoq", 0),
            "needs_reorder": data.get("needs_reorder", False),
            "days_of_stock_remaining": data.get("days_remaining", 0),
            "reasoning": (
                f"Current stock: {data.get('current_stock', 0)} units. "
                f"Reorder point: {data.get('reorder_point', 0)}. "
                f"{'⚠️ Reorder recommended — stock below safety threshold.' if data.get('needs_reorder') else '✅ Stock levels sufficient.'}"
            )
        })
    except Exception as e:
        return json.dumps({
            "product_id": product_id,
            "current_stock": 85,
            "safety_stock": 30,
            "reorder_point": 50,
            "eoq": 200,
            "needs_reorder": False,
            "days_of_stock_remaining": 21,
            "reasoning": "Current stock: 85 units. Reorder point: 50. Stock levels sufficient for ~21 days. (mock data)"
        })


def select_warehouse(product_id: str, quantity: int, destination_lat: float, destination_lon: float) -> str:
    """
    Select the optimal warehouse for order fulfillment.
    Calls your /warehouse/select endpoint.
    """
    try:
        resp = requests.post(
            f"{FLASK_ML_BASE_URL}/warehouse/select",
            json={
                "product_id": product_id,
                "quantity": quantity,
                "location": {"lat": destination_lat, "lon": destination_lon}
            },
            timeout=10
        )
        data = resp.json()
        best = data.get("best_warehouse", {})
        return json.dumps({
            "warehouse_id": best.get("id", "WH-001"),
            "warehouse_name": best.get("name", "Central Warehouse"),
            "distance_km": best.get("distance_km", 45.2),
            "estimated_cost": best.get("cost", 320.0),
            "estimated_delivery_hours": best.get("delivery_hours", 6),
            "inventory_available": best.get("inventory", 500),
            "score": best.get("score", 0.92),
            "alternatives": data.get("alternatives", []),
            "reasoning": (
                f"Best warehouse: {best.get('name', 'WH-001')} "
                f"(score: {best.get('score', 0.92):.2f}). "
                f"Distance: {best.get('distance_km', 45.2)} km. "
                f"Estimated delivery: {best.get('delivery_hours', 6)}h. "
                f"Cost: ${best.get('cost', 320.0):.2f}. "
                f"Inventory available: {best.get('inventory', 500)} units."
            )
        })
    except Exception as e:
        return json.dumps({
            "warehouse_id": "WH-002",
            "warehouse_name": "North Distribution Centre",
            "distance_km": 38.5,
            "estimated_cost": 285.0,
            "estimated_delivery_hours": 5,
            "inventory_available": 340,
            "score": 0.94,
            "reasoning": "Best warehouse: North DC (score: 0.94). Distance: 38.5km. ETA: 5h. Cost: $285. (mock data)"
        })


def optimize_route(warehouse_id: str, delivery_points: list) -> str:
    """
    Optimize the delivery route using VRP solver.
    Calls your /route/optimize endpoint.
    """
    try:
        resp = requests.post(
            f"{FLASK_ML_BASE_URL}/route/optimize",
            json={
                "warehouse_id": warehouse_id,
                "delivery_points": delivery_points
            },
            timeout=10
        )
        data = resp.json()
        return json.dumps({
            "route": data.get("route", []),
            "total_distance_km": data.get("total_distance_km", 0),
            "estimated_duration_hours": data.get("duration_hours", 0),
            "vehicle_count": data.get("vehicle_count", 1),
            "total_cost": data.get("total_cost", 0),
            "reasoning": (
                f"Optimized route covers {data.get('total_distance_km', 0)} km "
                f"in {data.get('duration_hours', 0):.1f}h using {data.get('vehicle_count', 1)} vehicle(s). "
                f"Total delivery cost: ${data.get('total_cost', 0):.2f}."
            )
        })
    except Exception as e:
        return json.dumps({
            "route": [{"stop": 1, "location": "Warehouse"}, {"stop": 2, "location": "Customer"}],
            "total_distance_km": 76.3,
            "estimated_duration_hours": 2.5,
            "vehicle_count": 1,
            "total_cost": 142.0,
            "reasoning": "Optimized route: 76.3 km, 2.5h, 1 vehicle. Total cost: $142. (mock data)"
        })


# ─────────────────────────────────────────────────────────
# FOUNDRY AGENT SETUP
# ─────────────────────────────────────────────────────────

def build_toolset() -> ToolSet:
    """Register all ML model functions as Foundry agent tools."""
    functions = FunctionTool(functions={
        forecast_demand,
        check_inventory,
        select_warehouse,
        optimize_route,
    })
    toolset = ToolSet()
    toolset.add(functions)
    return toolset


def create_agent(client: AIProjectClient):
    """Create the SupplyMind reasoning agent in Microsoft Foundry."""
    toolset = build_toolset()

    agent = client.agents.create_agent(
        model="gpt-4o",
        name="SupplyMind",
        instructions="""
You are SupplyMind, an expert AI reasoning agent for intelligent supply chain management.

When given a logistics query or order request, you MUST reason through it step-by-step:

STEP 1 — UNDERSTAND: Parse the request. Identify product ID, quantity, destination, and urgency.

STEP 2 — FORECAST DEMAND: Call forecast_demand() to understand future demand trends.
  - Always explain what the forecast means for the decision.

STEP 3 — CHECK INVENTORY: Call check_inventory() to assess current stock levels.
  - Flag if reorder is needed. Note days of stock remaining.

STEP 4 — SELECT WAREHOUSE: Call select_warehouse() with the destination coordinates.
  - Explain WHY this warehouse was chosen (score, distance, cost, inventory).

STEP 5 — OPTIMIZE ROUTE: Call optimize_route() to find the most efficient delivery path.
  - Report distance, duration, vehicle count, and total cost.

STEP 6 — SYNTHESIZE DECISION: Provide a clear, structured final decision:
  - Recommended warehouse
  - Delivery route summary
  - Inventory/reorder action (if needed)
  - Total estimated cost and time
  - Confidence level (0–1)
  - Plain-language reasoning summary (3–5 sentences)

Always be specific. Always show your reasoning. Never skip steps.
If data seems anomalous, flag it and explain your concern.
Your goal: minimize cost, maximize delivery speed, ensure inventory sufficiency.
        """,
        toolset=toolset,
    )
    return agent


# ─────────────────────────────────────────────────────────
# AGENT RUNNER
# ─────────────────────────────────────────────────────────

def run_agent_query(client: AIProjectClient, agent_id: str, user_query: str) -> dict:
    """
    Run a supply chain query through the SupplyMind agent.
    Returns the full reasoning trace + final decision.
    """
    # Create a new thread for this conversation
    thread: AgentThread = client.agents.create_thread()

    # Send the user's query
    client.agents.create_message(
        thread_id=thread.id,
        role=MessageRole.USER,
        content=user_query
    )

    # Run the agent (this triggers multi-step reasoning + tool calls)
    run = client.agents.create_and_process_run(
        thread_id=thread.id,
        agent_id=agent_id
    )

    # Collect all messages (reasoning trace)
    messages = client.agents.list_messages(thread_id=thread.id)

    reasoning_steps = []
    final_answer = ""

    for msg in messages.data:
        if msg.role == MessageRole.ASSISTANT:
            for content_block in msg.content:
                if hasattr(content_block, "text"):
                    final_answer = content_block.text.value
        if msg.role == MessageRole.TOOL:
            reasoning_steps.append({
                "tool": msg.name if hasattr(msg, "name") else "tool_call",
                "result": msg.content[0].text.value if msg.content else ""
            })

    return {
        "query": user_query,
        "agent_id": agent_id,
        "thread_id": thread.id,
        "run_status": run.status,
        "reasoning_steps": reasoning_steps,
        "final_decision": final_answer,
        "timestamp": datetime.utcnow().isoformat()
    }


# ─────────────────────────────────────────────────────────
# FLASK API — expose agent as REST endpoint
# ─────────────────────────────────────────────────────────

app = Flask(__name__)

# Initialize Foundry client once at startup
try:
    foundry_client = AIProjectClient.from_connection_string(
        credential=DefaultAzureCredential(),
        conn_str=FOUNDRY_CONNECTION_STRING
    )
    agent = create_agent(foundry_client)
    AGENT_ID = agent.id
    print(f"✅ SupplyMind agent created: {AGENT_ID}")
except Exception as e:
    print(f"⚠️  Foundry not connected — running in mock mode. Error: {e}")
    foundry_client = None
    AGENT_ID = None


@app.route("/api/v1/agent/decide", methods=["POST"])
def agent_decide():
    """
    Main agent endpoint.

    Request body:
    {
        "query": "Fulfill order for 50 units of PROD001 to location lat=40.71, lon=-74.00",
        "product_id": "PROD001",
        "quantity": 50,
        "destination": {"lat": 40.71, "lon": -74.00}
    }

    Response:
    {
        "query": "...",
        "reasoning_steps": [...],
        "final_decision": "...",
        "timestamp": "..."
    }
    """
    data = request.get_json()
    if not data or "query" not in data:
        return jsonify({"error": "Missing 'query' field"}), 400

    query = data["query"]

    # Enrich query with structured params if provided
    if "product_id" in data:
        query += f" [product_id={data['product_id']}]"
    if "quantity" in data:
        query += f" [quantity={data['quantity']}]"
    if "destination" in data:
        d = data["destination"]
        query += f" [destination lat={d.get('lat')}, lon={d.get('lon')}]"

    if foundry_client and AGENT_ID:
        result = run_agent_query(foundry_client, AGENT_ID, query)
    else:
        # Mock response for development without Foundry credentials
        result = mock_agent_response(query)

    return jsonify(result)


@app.route("/api/v1/agent/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "agent_id": AGENT_ID,
        "foundry_connected": foundry_client is not None,
        "timestamp": datetime.utcnow().isoformat()
    })


# ─────────────────────────────────────────────────────────
# MOCK RESPONSE (for local dev without Azure credentials)
# ─────────────────────────────────────────────────────────

def mock_agent_response(query: str) -> dict:
    """Returns a simulated multi-step agent response for UI development."""
    return {
        "query": query,
        "agent_id": "mock-agent",
        "thread_id": "mock-thread-001",
        "run_status": "completed",
        "reasoning_steps": [
            {"step": 1, "action": "parse_query", "result": "Product: PROD001 | Qty: 50 | Destination identified"},
            {"step": 2, "action": "forecast_demand", "result": "Demand forecast: 120.5 units/30d (trend: increasing)"},
            {"step": 3, "action": "check_inventory", "result": "Current stock: 85 units. Stock sufficient for 21 days. No reorder needed."},
            {"step": 4, "action": "select_warehouse", "result": "Best: North Distribution Centre (score: 0.94). Distance: 38.5km. Cost: $285. ETA: 5h."},
            {"step": 5, "action": "optimize_route", "result": "Optimized route: 76.3 km | 2.5h | 1 vehicle | $142 total"},
        ],
        "final_decision": (
            "**SupplyMind Decision Summary**\n\n"
            "✅ **Warehouse**: North Distribution Centre (WH-002)\n"
            "🗺️ **Route**: Optimized — 76.3 km, estimated 2.5 hours\n"
            "📦 **Inventory**: Sufficient (85 units in stock, 21 days remaining)\n"
            "📈 **Demand Trend**: Increasing — consider restocking within 2 weeks\n"
            "💰 **Total Cost Estimate**: $427 (warehouse: $285 + delivery: $142)\n"
            "🎯 **Confidence**: 0.94\n\n"
            "**Reasoning**: North DC is optimal due to its proximity (38.5km vs 62km for alternatives) "
            "and higher inventory availability. Current stock covers demand for 21 days; "
            "with an increasing trend, a reorder of 200 units (EOQ) is recommended within 14 days "
            "to maintain safety stock. The VRP-optimized route reduces delivery cost by 18% vs naive routing."
        ),
        "timestamp": datetime.utcnow().isoformat()
    }


# ─────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🧠 SupplyMind Agent starting...")
    print(f"   Agent API: http://localhost:{PORT}/api/v1/agent/decide")
    print(f"   Health:    http://localhost:{PORT}/api/v1/agent/health")
    app.run(host="0.0.0.0", port=PORT, debug=True)
