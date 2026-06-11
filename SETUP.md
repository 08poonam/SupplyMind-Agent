# SupplyMind Agent — Quick Setup

## Step 1: Install dependencies
```bash
pip install azure-ai-projects azure-ai-inference azure-identity flask requests python-dotenv
```

## Step 2: Copy env template and fill values
```bash
cp .env.example .env
```

## Step 3: Run the agent
```bash
python supplymind_agent.py
```

## Step 4: Test it
```bash
curl -X POST http://localhost:8000/api/v1/agent/decide \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Fulfill order for 50 units of PROD001 to New York",
    "product_id": "PROD001",
    "quantity": 50,
    "destination": {"lat": 40.71, "lon": -74.00}
  }'
```

---

# .env.example contents below — copy to .env and fill in

FOUNDRY_CONNECTION_STRING=your_azure_ai_foundry_connection_string_here
FLASK_ML_BASE_URL=http://localhost:5000/api/v1
AGENT_PORT=8000

# How to get FOUNDRY_CONNECTION_STRING:
# 1. Go to https://ai.azure.com
# 2. Create a new project (free tier works)
# 3. Go to Settings > Connection string
# 4. Copy and paste here

# ─────────────────────────────────────────────────
# IMPORTANT FOR HACKATHON DEMO:
# If you don't have Foundry credentials yet,
# the agent runs in MOCK MODE automatically —
# perfect for building the dashboard first.
# ─────────────────────────────────────────────────
