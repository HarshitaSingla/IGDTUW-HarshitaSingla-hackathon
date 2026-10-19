import matplotlib.pyplot as plt
import matplotlib.patches as patches

fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
ax.set_xlim(0, 14)
ax.set_ylim(0, 8)
ax.axis("off")

# Visual Styling
box_style = dict(boxstyle="round,pad=0.5", facecolor="#f8fafc", edgecolor="#334155", linewidth=1.5)
header_style = dict(color="#0f172a", fontsize=11, fontweight="bold", ha="center", va="center")
desc_style = dict(color="#475569", fontsize=8.5, ha="center", va="center")

# Architecture Nodes
nodes = [
    (1.8, 6.2, "1. INGESTION LAYER", "Financial News APIs\nSocial Media Streams\n(data/sample_feed.json)"),
    (5.4, 6.2, "2. AI/NLP RISK ENGINE", "ProsusAI/FinBERT Sentiment\nEntity Extraction (NER)\nTaxonomy Event Classifier\nExplainable Impact Scorer (1-10)"),
    (9.2, 6.2, "3. STRUCTURED SIGNALS", "Normalized JSON Bus\nSignal Persistence\n(/analyze, /signals API)"),
    (9.2, 2.2, "4. MODULE B: STRESS ENGINE", "Basel III Expected Credit Loss (ECL)\nModified Duration Bond Repricing\nCapital Adequacy (CRAR) Impact"),
    (3.6, 2.2, "5. PRESENTATION LAYER", "Streamlit Real-Time Dashboard\nPlotly Asset Breakdown\nFastAPI Interactive Docs")
]

for x, y, title, desc in nodes:
    ax.text(x, y + 0.35, title, **header_style)
    ax.text(x, y - 0.25, desc, **desc_style)
    rect = patches.FancyBboxPatch((x - 1.6, y - 0.8), 3.2, 1.6, **box_style)
    ax.add_patch(rect)

# Connecting Arrows
arrow_props = dict(arrowstyle="->", color="#2563eb", linewidth=2, shrinkA=8, shrinkB=8)
ax.annotate("", xy=(3.8, 6.2), xytext=(3.4, 6.2), arrowprops=arrow_props)
ax.annotate("", xy=(7.6, 6.2), xytext=(7.0, 6.2), arrowprops=arrow_props)
ax.annotate("", xy=(9.2, 3.0), xytext=(9.2, 5.4), arrowprops=arrow_props)
ax.annotate("", xy=(5.2, 2.2), xytext=(7.6, 2.2), arrowprops=arrow_props)
ax.annotate("", xy=(1.8, 5.4), xytext=(2.0, 3.0), arrowprops=dict(arrowstyle="<-", color="#94a3b8", linewidth=1.5, linestyle="dashed"))

plt.title("FinRisk AI — System Architecture & Data Flow", fontsize=15, fontweight="bold", pad=20, color="#0f172a")
plt.tight_layout()
plt.savefig("docs/architecture.png", dpi=300, bbox_inches="tight")
print("✅ Saved docs/architecture.png successfully!")