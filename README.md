# SupplyMind 🧠
### AI Reasoning Agent for Intelligent Supply Chain Management
> Microsoft Agents League Hackathon 2026 · Reasoning Agents Track

---

## 🚀 What is SupplyMind?

SupplyMind is a multi-step reasoning agent built on **Microsoft Foundry** that automates intelligent decision-making across the supply chain.

Given a logistics query, it reasons step-by-step:

1. 📊 **Forecast Demand** — ARIMA / Prophet / LSTM models
2. 📦 **Check Inventory** — EOQ, safety stock, reorder alerts
3. 🏭 **Select Warehouse** — cost, distance, capacity scoring
4. 🗺️ **Optimize Route** — VRP solver for multi-stop delivery
5. 🧾 **Explain Decision** — full plain-language reasoning trace

---

## 🏗️ Architecture

![Architecture](architecture_diagram.html)

**Stack:** Microsoft Foundry · GPT-4o · Python · Flask · scikit-learn · Prophet · TensorFlow · PostgreSQL · Docker

---

## ⚡ Quick Start

```bash
git clone https://github.com/08poonam/SupplyMind-Agent
cd SupplyMind-Agent
pip install -r requirements.txt
cp .env.example .env   # add your Foundry connection string
python supplymind_agent.py
```

Test it:
```bash
curl -X POST http://localhost:8000/api/v1/agent/decide \
  -H "Content-Type: application/json" \
  -d '{"query": "Fulfill 50 units of PROD001 to New York", "product_id": "PROD001", "quantity": 50}'
```

---

## 🎯 Impact

| Metric | Improvement |
|---|---|
| Operational cost reduction | 15–20% |
| Delivery time improvement | 25% |
| Inventory holding cost reduction | 30% |
| Manual decision dependency | Near zero |

---

## 👩‍💻 Developer

**Poonam** · Final-year MScIT Student  
GitHub: [@08poonam](https://github.com/08poonam)  
Hackathon: Microsoft Agents League @ AI Skills Fest 2026
