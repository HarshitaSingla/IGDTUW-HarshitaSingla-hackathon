import re
from typing import Dict, Any, List

CATEGORIES = [
    "Credit Event",
    "Macroeconomic",
    "Geopolitical",
    "Regulatory",
    "Earnings Performance",
    "Product Launch"
]

CATEGORY_TAXONOMY = {
    "Credit Event": ["default", "downgrade", "insolvency", "delinquency", "debt", "impairment", "npa", "bankruptcy", "distressed", "credit profile"],
    "Macroeconomic": ["rate hike", "inflation", "central bank", "yield", "gdp", "recession", "interest rate", "basis points", "repo rate", "monetary policy"],
    "Geopolitical": ["war", "sanction", "conflict", "border", "embargo", "tariff", "diplomatic", "standoff", "geopolitical"],
    "Regulatory": ["investigation", "fine", "penalty", "compliance", "probe", "antitrust", "lawsuit", "watchdog"],
    "Earnings Performance": ["revenue", "profit", "ebitda", "margin", "guidance", "quarterly", "earnings", "losses"],
    "Product Launch": ["launch", "unveil", "rollout", "innovation", "product", "platform", "release"]
}

KNOWN_ENTITIES = ["Alpha", "Beta", "Gamma", "Commercial Bank", "Global Tech Corp", "Central Bank", "Industrial Conglomerate"]


class RiskNLPEngine:
    def __init__(self) -> None:
        self.use_transformer: bool = False
        try:
            from transformers import pipeline  # type: ignore
            self.sentiment_pipe = pipeline("text-classification", model="ProsusAI/finbert", top_k=None)
            self.use_transformer = True
        except (ImportError, Exception):
            self.use_transformer = False

    def extract_entity(self, text: str) -> str:
        """Extracts the specific corporate entity or counterparty from text."""
        for ent in KNOWN_ENTITIES:
            if re.search(r'\b' + re.escape(ent) + r'\b', text, re.IGNORECASE):
                return ent
        # Regex search for capitalized corporate names
        matches = re.findall(r'([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)*\s+(?:Corp|Bank|Ltd|Inc|Group|Conglomerate))', text)
        if matches:
            return matches[0]
        return "Systemic"

    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Calculates normalized score from -1.0 to +1.0."""
        if self.use_transformer:
            preds = self.sentiment_pipe(text[:512])[0]
            scores = {item['label'].lower(): item['score'] for item in preds}
            score = scores.get('positive', 0.0) - scores.get('negative', 0.0)
            label = "negative" if score < -0.15 else ("positive" if score > 0.15 else "neutral")
            return {"score": round(score, 3), "label": label, "confidence": round(max(scores.values()), 3)}

        # Fallback lexicon
        lower = text.lower()
        neg_words = ["default", "drop", "surge", "shock", "inflation", "loss", "decline", "crisis", "tumble", "fine", "downgrade"]
        pos_words = ["growth", "gain", "profit", "surplus", "rebound", "boost", "positive", "strong"]
        neg_count = sum(1 for w in neg_words if w in lower)
        pos_count = sum(1 for w in pos_words if w in lower)

        if neg_count > pos_count:
            return {"score": -0.80, "label": "negative", "confidence": 0.88}
        elif pos_count > neg_count:
            return {"score": 0.70, "label": "positive", "confidence": 0.85}
        return {"score": 0.0, "label": "neutral", "confidence": 0.65}

    def classify_event(self, text: str) -> str:
        lower = text.lower()
        for cat, keywords in CATEGORY_TAXONOMY.items():
            if any(k in lower for k in keywords):
                return cat
        return "Macroeconomic"

    def extract_key_evidence(self, text: str) -> List[str]:
        """Extracts top risk trigger phrases for auditability and explainability."""
        lower = text.lower()
        evidence: List[str] = []
        for words in CATEGORY_TAXONOMY.values():
            for w in words:
                if w in lower and w not in evidence:
                    evidence.append(w)
        return evidence[:4]

    def calculate_impact_score(self, event_class: str, sentiment_score: float, source: str) -> int:
        base_severity = {
            "Credit Event": 9.0,
            "Geopolitical": 8.5,
            "Macroeconomic": 7.5,
            "Regulatory": 6.5,
            "Earnings Performance": 5.0,
            "Product Launch": 3.0
        }.get(event_class, 4.0)

        source_weight = 9.0 if source == "financial_news" else 6.5
        raw_score = (0.50 * base_severity) + (0.30 * (abs(sentiment_score) * 10)) + (0.20 * source_weight)
        return int(max(1, min(10, round(raw_score))))

    def process_text(self, item_id: str, title: str, text: str, source: str, timestamp: str) -> Dict[str, Any]:
        full_text = f"{title}. {text}"
        entity = self.extract_entity(full_text)
        sent = self.analyze_sentiment(full_text)
        category = self.classify_event(full_text)
        impact = self.calculate_impact_score(category, sent["score"], source)
        evidence = self.extract_key_evidence(full_text)

        return {
            "id": item_id,
            "source": source,
            "timestamp": timestamp,
            "title": title,
            "extracted_entity": entity,
            "sentiment_score": sent["score"],
            "sentiment_label": sent["label"],
            "event_classification": category,
            "impact_score": impact,
            "confidence": sent["confidence"],
            "evidence_triggers": evidence,
            "stress_test_triggered": (impact >= 7 and sent["score"] < -0.2)
        }