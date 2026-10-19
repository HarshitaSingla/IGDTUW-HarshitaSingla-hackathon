from typing import Dict, Any, List
import pandas as pd


class PortfolioStressTester:
    def __init__(self, portfolio_path: str = "data/synthetic_portfolio.csv") -> None:
        self.portfolio_path = portfolio_path
        self.portfolio_df = pd.read_csv(portfolio_path)
        # Bank-level regulatory capital parameters (RBI / Basel III Framework)
        self.tier1_capital_lakhs = 15.0  # ₹15L capital base
        self.baseline_rwa = 85.0         # ₹85L Risk-Weighted Assets

    def run_stress_test(
        self,
        event_type: str,
        impact_score: int,
        detected_entity: str = "Systemic"
    ) -> Dict[str, Any]:
        """
        Calculates loss rates using quantitative risk formulas:
        - Corporate Loans: Basel Expected Loss dLoss = EAD * dPD * LGD (LGD = 45%)
        - Fixed Income: Modified Duration Repricing dP = -D_mod * dy * P
        - Derivatives: Net Mark-to-Market (MTM) Sensitivity
        - Equities: Systemic Beta Drawdown
        """
        df = self.portfolio_df.copy()
        severity = impact_score / 10.0

        loss_amounts: List[float] = []
        shock_explanations: List[str] = []

        for _, row in df.iterrows():
            a_type = row["asset_type"]
            val = float(row["initial_value_inr_lakhs"])
            dur = float(row.get("duration_years", 1.0))
            asset_name = str(row.get("asset_name", ""))

            # Target specific entity if identified, otherwise treat as systemic
            is_targeted = (detected_entity.lower() in asset_name.lower()) or (detected_entity == "Systemic")

            if event_type == "Macroeconomic":
                # Interest rate yield curve shock (up to 200 bps)
                delta_yield = 0.02 * severity
                if a_type == "Bond":
                    # Duration formula: dP = -ModDuration * dy * P
                    loss = dur * delta_yield * val
                    expl = f"Duration repricing: -{round(dur * delta_yield * 100, 2)}% from +{int(delta_yield * 10000)} bps yield surge"
                elif a_type == "Derivative":
                    loss = dur * delta_yield * 1.5 * val
                    expl = "MTM swap rate divergence"
                elif a_type == "Loan":
                    loss = val * 0.025 * severity
                    expl = "Macro borrowing cost compression"
                else:
                    loss = val * 0.05 * severity
                    expl = "Macro equity valuation discount"

            elif event_type == "Credit Event":
                # Basel Expected Loss: dLoss = EAD * dPD * LGD (assume LGD = 45%)
                lgd = 0.45
                if a_type == "Loan":
                    delta_pd = (0.05 + (0.30 * severity)) if is_targeted else (0.02 + (0.08 * severity))
                    loss = val * delta_pd * lgd
                    expl = f"Basel ECL: PD surged +{round(delta_pd * 100, 1)}% at 45% LGD"
                elif a_type == "Bond":
                    spread_shock_bps = (280 * severity) if is_targeted else (120 * severity)
                    loss = (spread_shock_bps / 10000.0) * dur * val
                    expl = f"Credit spread widened by +{int(spread_shock_bps)} bps (ModDur {dur}y)"
                else:
                    loss = val * 0.04 * severity
                    expl = "Secondary market discount"

            elif event_type == "Geopolitical":
                if a_type == "Equity":
                    loss = val * (0.15 * severity)
                    expl = "Systemic beta sell-off"
                elif a_type == "Derivative":
                    loss = val * (0.20 * severity)
                    expl = "Cross-border settlement volatility"
                else:
                    loss = val * (0.04 * severity)
                    expl = "Sovereign risk premium increase"

            else:
                loss = val * 0.01 * severity
                expl = "Idiosyncratic operational variance"

            loss = min(val, max(0.0, loss))
            loss_amounts.append(round(loss, 3))
            shock_explanations.append(expl)

        df["loss_amount_inr_lakhs"] = loss_amounts
        df["stressed_value_inr_lakhs"] = (df["initial_value_inr_lakhs"] - df["loss_amount_inr_lakhs"]).round(3)
        df["stress_mechanic"] = shock_explanations

        total_initial = round(float(df["initial_value_inr_lakhs"].sum()), 2)
        total_loss = round(float(df["loss_amount_inr_lakhs"].sum()), 2)
        total_stressed = round(total_initial - total_loss, 2)
        loss_pct = round((total_loss / total_initial) * 100.0, 2)

        # Regulatory Capital Impact (CRAR calculation)
        post_tier1 = max(0.0, self.tier1_capital_lakhs - total_loss)
        pre_crar = round((self.tier1_capital_lakhs / self.baseline_rwa) * 100, 2)
        post_crar = round((post_tier1 / self.baseline_rwa) * 100, 2)

        return {
            "total_initial_lakhs": total_initial,
            "total_stressed_lakhs": total_stressed,
            "total_loss_lakhs": total_loss,
            "portfolio_loss_pct": loss_pct,
            "pre_crar_pct": pre_crar,
            "post_crar_pct": post_crar,
            "capital_adequacy_breached": post_crar < 11.5,  # RBI/Basel minimum benchmark
            "detected_entity": detected_entity,
            "asset_breakdown": df.to_dict(orient="records"),
        }