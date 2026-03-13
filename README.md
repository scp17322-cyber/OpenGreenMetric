<p align="center">
  <img src="assets/banner.png" width="750" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue?style=flat-square" />
  <img src="https://img.shields.io/badge/matplotlib-3.8+-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/scikit--learn-1.4+-green?style=flat-square" />
  <img src="https://img.shields.io/badge/FastAPI-0.109+-teal?style=flat-square" />
  <img src="https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square" />
</p>

## What This Is

I built this to answer a straightforward question: given nothing but a product description (say, "organic cotton t-shirt, 180g, made in Bangladesh"), can you estimate its environmental footprint from first principles?

It turns out you can. The engine classifies the product into one of 44 NAICS categories, looks up emission factors from six public databases, and runs a cradle-to-grave impact calculation covering $\text{CO}_2\text{e}$, water, energy, and fossil resource depletion. Everything gets normalized into a single 0-to-100 score with a letter grade. The whole pipeline is deterministic, reproducible, and runs in under 200ms.

The data science layer on top handles uncertainty quantification (Monte Carlo), sensitivity analysis (OAT), clustering, regression, and geospatial visualization. Every figure and animation in this repo is generated from the same codebase.

## Relationship to GreenMetric.AI

This repo is the open-source foundation behind [GreenMetric.AI](https://greenmetric.ai), a fully functional SaaS product that provides environmental scoring as an API for e-commerce platforms. GreenMetric.AI has been live since early 2026 and serves around 20 users, handling real product assessments for EU Digital Product Passport compliance and sustainability reporting.

OpenGreenMetric contains the core LCA engine, scoring logic, and the full data science analysis pipeline. The production API adds authentication, caching, webhook integrations, and embeddable widgets on top of this same `analyze()` function. If you are evaluating the technical work behind GreenMetric.AI, this is the codebase to look at.

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

Price-to-$\text{CO}_2\text{e}$ relationship is fit with OLS:

$$\hat{y} = \beta_0 + \beta_1 x + \varepsilon, \qquad \varepsilon \sim \mathcal{N}(0, \sigma^2)$$

Feature importance is estimated via a Random Forest (100 trees, max depth 5) with permutation importance over 20 repeats.

## Key Constants

| Constant | Value | Notes |
|---|---|---|
| Climate weight | 55.58% | Inverse-variance derived |
| Water weight | 22.46% | Inverse-variance derived |
| Fossils weight | 21.96% | Inverse-variance derived |
| Primary Energy Factor | 6.48 MJ/kWh | $3.6 \times 1.8$ |
| Sea freight factor | 0.016 kg $\text{CO}_2\text{e}$/tonne-km | DEFRA 2024 container |
| Road freight factor | 0.107 kg $\text{CO}_2\text{e}$/tonne-km | DEFRA 2024 HGV |
| Clothing emission factor | 2.5 kg $\text{CO}_2\text{e}$/kg | Generic fallback |
| Electronics emission factor | 5.0 kg $\text{CO}_2\text{e}$/kg | Generic fallback |
| Furniture emission factor | 3.5 kg $\text{CO}_2\text{e}$/kg | Generic fallback |
| Appliances emission factor | 4.0 kg $\text{CO}_2\text{e}$/kg | Generic fallback |
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

One-at-a-time perturbation of 8 input parameters by $\pm 20\%$ (or categorical swap for materials and origin). Bars grow left/right from the base case of 7.5 kg $\text{CO}_2\text{e}$. The final frame shows the total swing and identifies the most sensitive parameter, which is almost always the material emission factor.

### Score Decomposition (Waterfall)

<p align="center"><img src="animations/gif_waterfall.gif" width="750" /></p>

Starting from a perfect score of 100, each lifecycle stage contributes a deduction proportional to its normalized impact. The weighted formula $S = 0.5558 \cdot S_c + 0.2246 \cdot S_w + 0.2196 \cdot S_f$ drives the final grade. For a cotton t-shirt, the result is typically a B (around 64/100), with raw materials and manufacturing as the biggest drivers.

### Material Substitution

<p align="center"><img src="animations/gif_material_swap.gif" width="750" /></p>

Radar chart cycling through four materials (cotton, organic cotton, recycled polyester, hemp) across five impact dimensions. Each transition shows the delta in average score. Organic cotton and hemp tend to dominate on climate and water, while recycled polyester wins on fossil resource depletion.

### Global Grid Intensity

<p align="center"><img src="animations/gif_world_map.gif" width="750" /></p>

Countries appear one at a time, sorted from highest to lowest grid carbon intensity (kg $\text{CO}_2\text{e}$/kWh). A dashed line marks the global average. The color gradient (red to green) makes it immediately clear which grids are clean and which are coal-heavy. The PEF annotation ($6.48$ MJ/kWh) links grid intensity to fossil resource depletion.

### Supply Chain Sankey

<p align="center"><img src="animations/gif_sankey.gif" width="750" /></p>

Carbon flow through the five lifecycle stages of a cotton t-shirt (total: 6.3 kg $\text{CO}_2\text{e}$). Raw materials account for roughly half, manufacturing about 29%, and the three transport/use/EOL stages split the remainder. Emission factors for cotton (2.5 kg $\text{CO}_2\text{e}$/kg), sea freight (0.016 kg $\text{CO}_2\text{e}$/tonne-km), and road freight (0.107 kg $\text{CO}_2\text{e}$/tonne-km) are annotated.

### Lifecycle Stage Comparison

<p align="center"><img src="animations/gif_lifecycle.gif" width="750" /></p>

Stacked bar chart building up four products (smartphone, t-shirt, chair, laptop) across five lifecycle stages. Electronics are dominated by the use phase (charging over a multi-year lifespan), while clothing is dominated by raw materials. The generic emission factors (electronics: 5.0, clothing: 2.5, furniture: 3.5 kg $\text{CO}_2\text{e}$/kg) are shown for reference.

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

## Data Science Techniques

The analysis layer applies standard statistical and machine learning methods to the LCA outputs. Here is what each technique does and the math behind it.

| Technique | Module | What It Does |
|---|---|---|
| **Gaussian KDE** | `analysis/eda.py` | Estimates continuous probability densities from the discrete impact samples. Uses `scipy.stats.gaussian_kde` with automatic bandwidth selection (Scott's rule). The kernel is a standard normal centered on each data point, evaluated over 200 linearly spaced values. |
| **Pearson Correlation** | `analysis/eda.py` | Computes pairwise linear correlation $r_{xy} = \frac{\sum (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum(x_i - \bar{x})^2 \sum(y_i - \bar{y})^2}}$ across all impact metrics. Each pair is tested with `scipy.stats.pearsonr` for significance: $^{**}$ if $p < 0.01$, $^{*}$ if $p < 0.05$. |
| **Tukey IQR Fences** | `analysis/eda.py` | Flags outliers using $\text{threshold} = Q_3 + 1.5 \times \text{IQR}$ where $\text{IQR} = Q_3 - Q_1$. This is the classical Tukey fence; anything above the threshold is counted as an outlier per category. |
| **K-Means Clustering** | `analysis/clustering.py` | Lloyd's algorithm with `n_init=10` random restarts and seed 42. Clusters product categories in 5D impact space (standardized via `StandardScaler`). Optimal $k$ is chosen by maximizing the silhouette score $s(i) = \frac{b(i) - a(i)}{\max(a(i), b(i))}$ over $k \in [2, 10]$. |
| **PCA** | `analysis/clustering.py` | Eigendecomposition of the covariance matrix after z-score normalization. Retains up to 5 components; the explained variance plot marks 80% and 95% cumulative thresholds. Cluster centroids are projected into the first two PCs for the scatter plot. |
| **t-SNE** | `analysis/clustering.py` | Barnes-Hut approximation with perplexity $= \min(15, n-1)$ and 1,000 iterations. Preserves local neighborhood structure in 2D. Points are colored by their K-means labels; the silhouette score is annotated to show how well the nonlinear embedding respects cluster assignments. |
| **OLS Regression** | `analysis/regression.py` | Fits $\hat{y} = \beta_0 + \beta_1 x$ via `sklearn.linear_model.LinearRegression`. The 95% prediction interval uses $\hat{y} \pm t_{0.025} \cdot s_e \sqrt{1 + \frac{1}{n} + \frac{(x - \bar{x})^2}{S_{xx}}}$ with $s_e^2 = \frac{\sum(y_i - \hat{y}_i)^2}{n - 2}$ and $t \approx 2.02$. |
| **Random Forest** | `analysis/regression.py` | 100 trees, max depth 5, seed 42. Feature importance is estimated via `permutation_importance` with 20 repeats: for each feature, the model's $R^2$ is measured after randomly shuffling that feature's values. The drop in $R^2$ is the importance. Cross-validated with $k = \min(5, n)$ folds. |
| **Lognormal Monte Carlo** | `analysis/uncertainty.py` | Draws $n = 10{,}000$ samples from $X \sim \text{LogNormal}(\mu, \sigma)$ where $\sigma = \sqrt{\ln(1 + \text{RSD}^2)}$ and $\mu = \ln(c) - \sigma^2/2$. Percentiles $P_5$ through $P_{95}$ are computed directly from the empirical distribution. Seed 42 via `numpy.random.default_rng`. |
| **Bootstrap CI** | `analysis/uncertainty.py` | 5,000 bootstrap resamples (sampling with replacement from the Monte Carlo draws). The 90% CI at each resample size is the $[5^{\text{th}}, 95^{\text{th}}]$ percentile of the bootstrap means. CI width is plotted against a theoretical $1/\sqrt{n}$ decay curve to verify convergence. |
| **OAT Sensitivity** | `analysis/sensitivity.py` | Perturbs each input parameter by $\pm 20\%$ (continuous) or swaps category (material, origin). The absolute delta $\Delta = f(x + \delta) - f(x_0)$ and percentage change $\Delta / f(x_0) \times 100$ are computed for each parameter. Results are sorted by $|\Delta|$ descending for the tornado chart. |
| **Geospatial Mapping** | `analysis/geospatial.py` | Grid carbon intensities (kg $\text{CO}_2\text{e}$/kWh) are loaded from EPA data and mapped with `RdYlGn_r` (red = dirty, green = clean). Sea freight emissions per route are estimated as $\text{distance (km)} \times 0.016 / 1000$ using the DEFRA 2024 container freight factor. |

## Notebooks

The `notebooks/` directory has five Jupyter walkthroughs that mirror the analysis modules. Each notebook is self-contained: load the data, run the analysis, and produce the figures inline. They are meant to be read top-to-bottom as a narrative.

| Notebook | What It Covers |
|---|---|
| `01_data_exploration.ipynb` | Loading the benchmark dataset, plotting distributions, computing correlation matrices, and flagging outliers with Tukey fences. |
| `02_clustering_analysis.ipynb` | Silhouette sweep for optimal $k$, PCA explained variance, K-means cluster assignments, and t-SNE 2D embedding. |
| `03_regression_models.ipynb` | Price vs. $\text{CO}_2\text{e}$ linear fit with prediction intervals, Random Forest feature importance, and cross-validated $R^2$. |
| `04_uncertainty_analysis.ipynb` | Lognormal Monte Carlo sampling (10k draws), percentile tables, bootstrap CI convergence, and OAT sensitivity tornado. |
| `05_geospatial_analysis.ipynb` | Country-level grid intensities, supply chain freight routes, and per-route emission estimates. |

## Datasets

All emission factor data lives in `data/` as JSON files. These are public-domain or openly licensed factors compiled from government and academic sources.

| File | What It Contains |
|---|---|
| `product-category-benchmarks.json` | 40+ product categories with benchmark ranges for $\text{CO}_2\text{e}$, water, energy, price, weight, and lifespan. |
| `defra-conversion-factors.json` | Material-level emission factors (kg $\text{CO}_2\text{e}$/kg) for 61 materials, from DEFRA/BEIS 2024. |
| `epa-ghg-emission-factors.json` | Grid carbon intensities for 60+ countries and US regions (kg $\text{CO}_2\text{e}$/kWh). |
| `epa-supply-chain-factors.json` | Spend-based sector intensities (kg $\text{CO}_2\text{e}$/USD) for 86 NAICS codes. |
| `emission-factor-uncertainties.json` | Relative standard deviations (RSD) per factor, used to parameterize Monte Carlo sampling. |
| `emission-profiles.json` | Lifecycle emission profiles broken down by material and product type. |
| `ef31-characterization-factors.json` | EU EF 3.1 midpoint characterization factors for 16 impact categories. |
| `ef31-normalization-weighting.json` | EF 3.1 normalization references and weighting set. |
| `lifecycle-templates.json` | Use-phase and end-of-life templates for 36 product archetypes. |
| `gwp100-factors.json` | IPCC AR6 100-year Global Warming Potentials for 30 greenhouse gases. |

## Data Sources

This project pulls emission factors from six public databases: **EPA Supply Chain EEIO v1.3** (86 NAICS sectors), **UK DEFRA/BEIS 2024** (61 materials, 8 transport modes), **EPA GHG Emission Factors Hub** (60+ electricity grids), **IPCC AR6 GWP100** (100-year global warming potentials), **EU EF 3.1** (16 impact categories), and a set of compiled lifecycle templates for use-phase and end-of-life modeling.

## License

MIT
