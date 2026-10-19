import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from typing import Dict, Any, Optional
from fastapi import FastAPI
from pydantic import BaseModel
from src.engine.nlp_engine import RiskNLPEngine
from src.stress_testing.portfolio import PortfolioStressTester

app = FastAPI(
    title="FinRisk AI - NLP Risk & Basel Capital Stress Engine",
    description="Transforms unstructured market feeds into quantitative portfolio stress triggers.",
    version="1.0.0"
)

nlp_engine = RiskNLPEngine()
stress_tester = PortfolioStressTester()


class TextAnalysisRequest(BaseModel):
    title: str
    text: str
    source: str = "financial_news"


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "healthy", "service": "FinRisk AI Engine", "framework": "Basel III + FinBERT"}


@app.post("/analyze")
def analyze_and_simulate(req: TextAnalysisRequest) -> Dict[str, Any]:
    signal = nlp_engine.process_text(
        item_id="API-CALL",
        title=req.title,
        text=req.text,
        source=req.source,
        timestamp="2026-10-18T21:30:00Z"
    )

    stress_simulation: Optional[Dict[str, Any]] = None
    if signal["stress_test_triggered"]:
        stress_simulation = stress_tester.run_stress_test(
            event_type=signal["event_classification"],
            impact_score=signal["impact_score"],
            detected_entity=signal["extracted_entity"]
        )

    return {
        "risk_signal": signal,
        "stress_simulation": stress_simulation
    }  