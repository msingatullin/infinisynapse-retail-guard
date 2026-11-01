import os
import json
import requests
import pandas as pd
import numpy as np

class InfiniSynapseAgent:
    """
    InfiniSynapse Vibe Coding Agent for Retail Stockout Prevention & Automated Reordering.
    Combines quantitative depletion modelling with LLM-guided executive decision-making.
    """
    def __init__(self, api_key: str = None, base_url: str = "https://app.infinisynapse.com/api/v1"):
        self.api_key = api_key or os.getenv("INFINISYNAPSE_API_KEY", "")
        self.base_url = base_url.rstrip("/")
        self.has_remote_api = bool(self.api_key and self.api_key != "mock_key")

    def analyze_inventory(self, df: pd.DataFrame, service_level: float = 0.95):
        """
        Calculates runout velocity, safety stock, reorder point (ROP), and risk classifications.
        """
        results = []
        # z-score for 95% service level is ~1.645
        z = 1.65 if service_level >= 0.95 else 1.28
        
        for _, row in df.iterrows():
            stock = float(row.get("current_stock", 0))
            velocity = max(float(row.get("daily_velocity", 1.0)), 0.1)
            lead_time = float(row.get("lead_time_days", 3.0))
            moq = int(row.get("moq", 10))
            cost = float(row.get("unit_cost", 10.0))
            
            days_to_stockout = stock / velocity
            lead_time_demand = velocity * lead_time
            # Standard deviation of demand estimated as 30% of daily mean
            sigma_d = velocity * 0.35
            safety_stock = z * np.sqrt(lead_time) * sigma_d
            rop = lead_time_demand + safety_stock
            
            # Risk Scoring
            if stock <= 0:
                risk_tier = "CRITICAL_OUT"
                urgency_score = 100.0
                action = "EMERGENCY_REORDER"
            elif days_to_stockout < lead_time:
                risk_tier = "HIGH_STOCKOUT_RISK"
                urgency_score = 85.0 + (lead_time - days_to_stockout) * 3
                action = "IMMEDIATE_REORDER"
            elif days_to_stockout < (lead_time + 4):
                risk_tier = "REORDER_WINDOW"
                urgency_score = 60.0 + (lead_time + 4 - days_to_stockout) * 5
                action = "PREPARE_PO"
            else:
                risk_tier = "HEALTHY"
                urgency_score = max(10.0, 50.0 - days_to_stockout)
                action = "MONITOR"
                
            # Suggested reorder quantity (round up to MOQ)
            if action in ["EMERGENCY_REORDER", "IMMEDIATE_REORDER", "PREPARE_PO"]:
                target_stock = rop + (velocity * 14) # 14 days target cycle
                deficit = max(0, target_stock - stock)
                reorder_units = int(np.ceil(deficit / moq) * moq)
            else:
                reorder_units = 0
                
            total_cost = round(reorder_units * cost, 2)
            
            results.append({
                "sku_id": str(row.get("sku_id")),
                "product_name": str(row.get("product_name")),
                "category": str(row.get("category")),
                "supplier": str(row.get("supplier")),
                "current_stock": int(stock),
                "daily_velocity": round(velocity, 1),
                "lead_time_days": int(lead_time),
                "days_to_stockout": round(days_to_stockout, 1),
                "reorder_point": int(np.ceil(rop)),
                "risk_tier": risk_tier,
                "urgency_score": min(100.0, round(urgency_score, 1)),
                "suggested_reorder_qty": reorder_units,
                "unit_cost": cost,
                "estimated_po_cost": total_cost,
                "recommended_action": action
            })
            
        res_df = pd.DataFrame(results)
        res_df = res_df.sort_values(by="urgency_score", ascending=False).reset_index(drop=True)
        return res_df

    def generate_executive_action_plan(self, analyzed_df: pd.DataFrame) -> dict:
        """
        Generates an executive purchase order summary and natural language AI narrative.
        Calls InfiniSynapse API if configured, otherwise executes local decision heuristic.
        """
        critical_items = analyzed_df[analyzed_df["risk_tier"].isin(["CRITICAL_OUT", "HIGH_STOCKOUT_RISK"])]
        reorder_items = analyzed_df[analyzed_df["suggested_reorder_qty"] > 0]
        
        total_po_cost = float(reorder_items["estimated_po_cost"].sum())
        total_skus_at_risk = len(critical_items)
        suppliers_involved = reorder_items["supplier"].nunique()
        
        # Build prompt for InfiniSynapse LLM
        prompt = f"""
        Act as InfiniSynapse Supply Chain Optimization Agent.
        Analyze this retail replenishment status:
        - Total SKUs Audited: {len(analyzed_df)}
        - SKUs At Immediate Stockout Risk: {total_skus_at_risk}
        - Total Proposed Purchase Order Value: ${total_po_cost:,.2f} across {suppliers_involved} suppliers.
        Top 3 Most Urgent Items:
        {critical_items.head(3)[['sku_id', 'product_name', 'days_to_stockout', 'suggested_reorder_qty', 'supplier']].to_dict(orient='records')}
        Provide a concise 3-paragraph executive operational directive for the Store Operations Manager.
        """
        
        ai_narrative = ""
        if self.has_remote_api:
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "infinisynapse-reasoning-v1",
                    "messages": [
                        {"role": "system", "content": "You are InfiniSynapse Retail Replenishment AI Agent."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2
                }
                res = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload, timeout=8)
                if res.status_code == 200:
                    ai_narrative = res.json()["choices"][0]["message"]["content"]
            except Exception:
                pass
                
        if not ai_narrative:
            # High-fidelity deterministic decision report
            ai_narrative = (
                f"OPERATIONAL DIRECTIVE - IMMEDIATE ACTION REQUIRED:\n"
                f"1. RISK MITIGATION: {total_skus_at_risk} SKUs have breached critical runout safety thresholds (< lead time). "
                f"Top stockout vulnerabilities include {', '.join(critical_items['product_name'].head(3).tolist()) if len(critical_items) else 'none'}. "
                f"Immediate PO dispatch is required to prevent customer churn.\n\n"
                f"2. CAPITAL ALLOCATION: Consolidated purchase orders total ${total_po_cost:,.2f} spanning {suppliers_involved} primary suppliers. "
                f"Order quantities have been optimized against Minimum Order Quantity (MOQ) and 14-day cycle requirements.\n\n"
                f"3. EXECUTION DISPATCH: Recommended action is to approve batch PO generation for Supplier-A through Supplier-F to lock in lead-time slots."
            )
            
        return {
            "total_skus": len(analyzed_df),
            "critical_skus": total_skus_at_risk,
            "reorder_skus": len(reorder_items),
            "total_po_cost": round(total_po_cost, 2),
            "suppliers_count": suppliers_involved,
            "executive_narrative": ai_narrative,
            "reorder_items": reorder_items.to_dict(orient="records"),
            "all_items": analyzed_df.to_dict(orient="records")
        }
