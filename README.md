# OpenGreenMetric

Product-level life cycle assessment from free-text descriptions.

## What This Is

I built this to answer a straightforward question: given nothing but a product description (say, "organic cotton t-shirt, 180g, made in Bangladesh"), can you estimate its environmental footprint from first principles?

It turns out you can. The engine classifies the product into one of 44 NAICS categories, looks up emission factors from six public databases, and runs a cradle-to-grave impact calculation covering CO$_2$e, water, energy, and fossil resource depletion. Everything gets normalized into a single 0-to-100 score with a letter grade. The whole pipeline is deterministic, reproducible, and runs in under 200ms.

The data science layer on top handles uncertainty quantification (Monte Carlo), sensitivity analysis (OAT), clustering, regression, and geospatial visualization. Every figure and animation in this repo is generated from the same codebase.

<p align="center">
  <img src="animations/gif_waterfall.gif" width="750" />
</p>

## Quick Start

```bash
git clone https://github.com/alanknguyen/OpenGreenMetric.git
cd OpenGreenMetric
pip install -e ".[all]"
make test        # 43 tests
make gifs        # regenerate all animations
make figures     # regenerate all static figures
```

## How It Works

The pipeline has four stages: **classify** the product, **calculate** raw impacts, **validate** against benchmarks, and **score**.

```python
from openmetric import analyze
result = analyze("organic cotton t-shirt 180g made in Bangladesh", destination="US")
print(result.scores.letter_grade)  # "B"
print(result.impacts.climate_change)  # ~7.5 kg CO2e
```

### Scoring

Each impact metric $v_i$ gets normalized against category benchmarks into a 0-to-100 sub-score:

$$S_i = 100 \times \left(1 - \frac{v_i - v_{\min}}{v_{\max} - v_{\min}}\right)$$

The overall score is a weighted sum. The weights come from inverse-variance weighting across the benchmark dataset, which naturally upweights the most discriminating metric (climate) and downweights noisier ones:

$$S_{\text{overall}} = 0.5558 \, S_{\text{climate}} + 0.2246 \, S_{\text{water}} + 0.2196 \, S_{\text{fossils}}$$

Letter grades map linearly: $A^+ \geq 90$, $A \geq 80$, $B^+ \geq 70$, $B \geq 60$, $C^+ \geq 50$, $C \geq 40$, $D \geq 30$, $F < 30$.

### Uncertainty Quantification

I model factor uncertainty with a **lognormal distribution**, which is standard for emission factors (they are strictly positive and right-skewed). Given a central estimate $c$ and relative standard deviation $\text{RSD}$:

$$\sigma = \sqrt{\ln(1 + \text{RSD}^2)}, \qquad \mu = \ln(c) - \frac{\sigma^2}{2}$$

The moments of the resulting distribution are:

$$\mathbb{E}[X] = \exp\!\left(\mu + \frac{\sigma^2}{2}\right), \qquad \text{Var}[X] = \left(e^{\sigma^2} - 1\right) \cdot e^{2\mu + \sigma^2}$$

For textile emission factors I use $\text{RSD} = 0.30$, giving $\sigma = 0.294$. Monte Carlo sampling with 1,000 to 10,000 draws produces the empirical distribution and confidence intervals you see in the animations.

### Energy and Fossil Resources

Grid electricity converts to fossil resource depletion via the **Primary Energy Factor**:

$$\text{PEF} = 3.6 \; \frac{\text{MJ}}{\text{kWh}} \times 1.8 \; \text{(grid loss factor)} = 6.48 \; \frac{\text{MJ}}{\text{kWh}}$$

The 3.6 is the thermodynamic conversion (1 kWh = 3.6 MJ), and the 1.8 accounts for generation, transmission, and distribution losses in a typical fossil-dominated grid.

### Clustering

Product categories are clustered in impact space using **K-means** on standardized features (via `StandardScaler`). Optimal $k$ is selected by maximizing the **silhouette coefficient**:

$$s(i) = \frac{b(i) - a(i)}{\max\{a(i), \, b(i)\}}$$

where $a(i)$ is the mean intra-cluster distance and $b(i)$ is the mean nearest-cluster distance. Dimensionality reduction for visualization uses PCA (linear, preserving variance) and t-SNE (nonlinear, Barnes-Hut approximation, perplexity = 15).

### Regression

Price-to-CO$_2$e relationship is fit with OLS:

$$\hat{y} = \beta_0 + \beta_1 x + \varepsilon, \qquad \varepsilon \sim \mathcal{N}(0, \sigma^2)$$

Feature importance is estimated via a Random Forest (100 trees, max depth 5) with permutation importance over 20 repeats.

## Key Constants

| Constant | Value | Notes |
|---|---|---|
| Climate weight | 55.58% | Inverse-variance derived |
| Water weight | 22.46% | Inverse-variance derived |
| Fossils weight | 21.96% | Inverse-variance derived |
| Primary Energy Factor | 6.48 MJ/kWh | $3.6 \times 1.8$ |
| Sea freight factor | 0.016 kg CO$_2$e/tonne-km | DEFRA 2024 container |
| Road freight factor | 0.107 kg CO$_2$e/tonne-km | DEFRA 2024 HGV |
| Clothing emission factor | 2.5 kg CO$_2$e/kg | Generic fallback |
| Electronics emission factor | 5.0 kg CO$_2$e/kg | Generic fallback |
| Furniture emission factor | 3.5 kg CO$_2$e/kg | Generic fallback |
| Appliances emission factor | 4.0 kg CO$_2$e/kg | Generic fallback |
| Monte Carlo RSD (textiles) | 30% | $\sigma = 0.294$ |

## Animations

### Monte Carlo Convergence

<p align="center"><img src="animations/gif_monte_carlo.gif" width="750" /></p>

1,000 draws from a lognormal distribution with $\mu = \ln(7.5) - \sigma^2/2$ and $\sigma = 0.294$. The left panel shows the empirical PDF building up sample by sample, while the right panel tracks the 90% confidence interval width as it shrinks roughly as $1/\sqrt{n}$. By around 500 draws the CI has stabilized to within a few percent of the median.

### K-Means Clustering

<p align="center"><img src="animations/gif_clustering.gif" width="750" /></p>

K-means iteration on PCA-projected product data ($k = 4$). Each frame is one E-M step: assign points to nearest centroid, then recompute centroids. The silhouette score and inertia update live. You can watch the centroids migrate and the cluster boundaries settle over about 15 iterations.

### Sensitivity Analysis (Tornado)

<p align="center"><img src="animations/gif_tornado.gif" width="750" /></p>

One-at-a-time perturbation of 8 input parameters by $\pm 20\%$ (or categorical swap for materials and origin). Bars grow left/right from the base case of 7.5 kg CO$_2$e. The final frame shows the total swing and identifies the most sensitive parameter, which is almost always the material emission factor.

### Score Decomposition (Waterfall)

<p align="center"><img src="animations/gif_waterfall.gif" width="750" /></p>

Starting from a perfect score of 100, each lifecycle stage contributes a deduction proportional to its normalized impact. The weighted formula $S = 0.5558 \cdot S_c + 0.2246 \cdot S_w + 0.2196 \cdot S_f$ drives the final grade. For a cotton t-shirt, the result is typically a B (around 64/100), with raw materials and manufacturing as the biggest drivers.

### Material Substitution

<p align="center"><img src="animations/gif_material_swap.gif" width="750" /></p>

Radar chart cycling through four materials (cotton, organic cotton, recycled polyester, hemp) across five impact dimensions. Each transition shows the delta in average score. Organic cotton and hemp tend to dominate on climate and water, while recycled polyester wins on fossil resource depletion.

### Global Grid Intensity

<p align="center"><img src="animations/gif_world_map.gif" width="750" /></p>

Countries appear one at a time, sorted from highest to lowest grid carbon intensity (kg CO$_2$e/kWh). A dashed line marks the global average. The color gradient (red to green) makes it immediately clear which grids are clean and which are coal-heavy. The PEF annotation ($6.48$ MJ/kWh) links grid intensity to fossil resource depletion.

### Supply Chain Sankey

<p align="center"><img src="animations/gif_sankey.gif" width="750" /></p>

Carbon flow through the five lifecycle stages of a cotton t-shirt (total: 6.3 kg CO$_2$e). Raw materials account for roughly half, manufacturing about 29%, and the three transport/use/EOL stages split the remainder. Emission factors for cotton (2.5 kg CO$_2$e/kg), sea freight (0.016 kg CO$_2$e/tonne-km), and road freight (0.107 kg CO$_2$e/tonne-km) are annotated.

### Lifecycle Stage Comparison

<p align="center"><img src="animations/gif_lifecycle.gif" width="750" /></p>

Stacked bar chart building up four products (smartphone, t-shirt, chair, laptop) across five lifecycle stages. Electronics are dominated by the use phase (charging over a multi-year lifespan), while clothing is dominated by raw materials. The generic emission factors (electronics: 5.0, clothing: 2.5, furniture: 3.5 kg CO$_2$e/kg) are shown for reference.

## Figures

<table>
<tr>
<td width="50%"><img src="figures/fig_eda_distributions.png" width="100%"><br><em>Impact distributions with KDE overlays and per-metric skewness.</em></td>
<td width="50%"><img src="figures/fig_eda_correlations.png" width="100%"><br><em>Pearson correlation matrix with significance markers.</em></td>
</tr>
<tr>
<td width="50%"><img src="figures/fig_eda_outliers.png" width="100%"><br><em>Tukey IQR outlier detection (threshold = Q3 + 1.5 x IQR).</em></td>
<td width="50%"><img src="figures/fig_silhouette.png" width="100%"><br><em>Silhouette analysis for optimal cluster count.</em></td>
</tr>
<tr>
<td width="50%"><img src="figures/fig_pca_variance.png" width="100%"><br><em>PCA explained variance with 80%/95% thresholds and 2D cluster projection.</em></td>
<td width="50%"><img src="figures/fig_tsne.png" width="100%"><br><em>t-SNE embedding (perplexity = 15, Barnes-Hut).</em></td>
</tr>
<tr>
<td width="50%"><img src="figures/fig_price_vs_co2.png" width="100%"><br><em>OLS regression with 95% prediction interval band.</em></td>
<td width="50%"><img src="figures/fig_feature_importance.png" width="100%"><br><em>Random Forest permutation importance (100 trees, depth 5).</em></td>
</tr>
<tr>
<td width="50%"><img src="figures/fig_mc_distribution.png" width="100%"><br><em>Monte Carlo empirical distribution (10k samples, lognormal).</em></td>
<td width="50%"><img src="figures/fig_bootstrap_ci.png" width="100%"><br><em>Bootstrap CI convergence with theoretical 1/sqrt(n) decay.</em></td>
</tr>
<tr>
<td width="50%"><img src="figures/fig_tornado.png" width="100%"><br><em>OAT sensitivity tornado with percentage change labels.</em></td>
<td width="50%"><img src="figures/fig_world_grid_intensity.png" width="100%"><br><em>Grid carbon intensity by country with global mean line.</em></td>
</tr>
<tr>
<td width="50%"><img src="figures/fig_supply_chain_routes.png" width="100%"><br><em>Sea freight routes with per-leg CO2e estimates.</em></td>
<td></td>
</tr>
</table>

## API

The project includes a FastAPI server for programmatic access:

```bash
make api                  # starts on localhost:8000
curl -X POST localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"description": "organic cotton t-shirt 180g", "destination": "US"}'
```

```json
{
  "scores": {"overall": 64, "letter_grade": "B", "climate": 58, "water": 71, "resource_use_fossils": 66},
  "impacts": {"climate_change": 7.5, "water_use": 8420, "energy_use": 12.3, "resource_use_fossils": 79.7},
  "product": {"product_category": "clothing_cotton", "country_of_origin": "BD", "total_weight_kg": 0.18}
}
```

Other endpoints: `GET /benchmarks`, `POST /compare`, `GET /factors/{type}`.

## Dashboard

An interactive Streamlit dashboard lets you analyze products and compare alternatives without writing code:

```bash
streamlit run streamlit_app.py
```

The dashboard uses the same `analyze()` function under the hood. The production version of this project is deployed at [greenmetric.ai](https://greenmetric.ai).

## Data Sources

This project pulls emission factors from six public databases: **EPA Supply Chain EEIO v1.3** (86 NAICS sectors), **UK DEFRA/BEIS 2024** (61 materials, 8 transport modes), **EPA GHG Emission Factors Hub** (60+ electricity grids), **IPCC AR6 GWP100** (100-year global warming potentials), **EU EF 3.1** (16 impact categories), and a set of compiled lifecycle templates for use-phase and end-of-life modeling.

## License

MIT
