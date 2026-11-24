<p align="center">
  <picture>
    <img src="https://github.com/aryaanay/aryaanay/raw/refs/heads/main/lorenz-attractor.svg" width="286" height="158" alt="Dotted Lorenz attractor with a moving highlight.">
  </picture>
</p>

<h1 align="center">Anay Arya</h1>
<p align="center">University of Washington, Seattle<br>AI research, quantitative modeling, and developer tools</p>

## About me

I’m interested in how people make decisions under uncertainty, especially in finance and technology. I like thinking about what data can tell us and where judgment still matters.

[Published skills](#published-skills) | [Featured work](#featured-work) | [Recent activity](#recent-public-activity) | [LinkedIn](https://www.linkedin.com/in/anay-arya/)

## Published skills

**[Build, Review, and Release](https://github.com/aryaanay/build-review-release#readme)** is a reusable Codex skill for planning a project, testing it, and checking that it’s ready to publish. It uses the tools already in your workspace. The repository includes setup instructions for using it across projects or sharing it with a team.

## Featured work

### Can a market maker manage inventory while quoting both sides?

My limit order book notebook models bids, asks, and trades in a synthetic market. It then puts an inventory-aware market maker into that market and tests a case the initial version missed: fills that happen between strategy steps.

<picture>
  <img src="order-book-simulation.svg" alt="Simulated order book showing the best bid, best ask, and executed trades over time.">
</picture>

[Open the order book notebook](https://github.com/aryaanay/Quantitative-Finance-Model-Development-Portfolio/blob/main/OrderBookSimulator_InventoryAwareMarketMaking.ipynb)

<details>
<summary>What broke in the first version?</summary>

The simulator only checked for fills right after it posted a quote. A fill between strategy steps could leave its inventory count wrong. The fix tracks the order IDs the strategy has placed and checks every new trade for a match. The notebook verifies this by filling a quote between steps and checking that the next step picks it up.

</details>

<details>
<summary>More quant notebooks</summary>

- [Implied vs. realized volatility forecasting](https://github.com/aryaanay/Quantitative-Finance-Model-Development-Portfolio/blob/main/OptionsVolatility_ImpliedVsRealizedForecasting.ipynb)
- [Pairs trading and statistical arbitrage](https://github.com/aryaanay/Quantitative-Finance-Model-Development-Portfolio/blob/main/PairsTradingSystem_StatisticalArbitrage.ipynb)
- [Market regime detection with a hidden Markov model](https://github.com/aryaanay/Quantitative-Finance-Model-Development-Portfolio/blob/main/RegimeDetection_HMMBasedMarketRegimeStrategy.ipynb)
- [Hybrid cryptocurrency price prediction](https://github.com/aryaanay/Quantitative-Finance-Model-Development-Portfolio/blob/main/CryptoPricePredictionHybridModel.ipynb)

</details>

### What do corporate AI claims tell us about future returns?

[AI Narrative Reality Gap](https://github.com/aryaanay/ai-narrative-reality-gap#readme) lays out a study of S&P 100 companies. The plan compares a score based on evidence behind AI claims with a baseline that counts AI keywords. Data collection is next.

```mermaid
flowchart LR
    A[Public filings] --> B[Extract AI claims]
    B --> C[Score supporting evidence]
    B --> D[Count AI keywords]
    C --> E[Compare against later returns]
    D --> E
```

[Read the research plan](https://github.com/aryaanay/ai-narrative-reality-gap#plan) | [See the data sources](https://github.com/aryaanay/ai-narrative-reality-gap#data)

### CommUHub

[CommUHub](https://github.com/aryaanay/commhub) is a Next.js project built to make local resources and events easier to find in one place.

## Recent public activity

<!-- activity:start -->
- **Nov 24, 2026** — Opened repository in [careerops-public-feed](https://github.com/aryaanay/careerops-public-feed)
- **Nov 24, 2026** — Updated code in [build-review-release](https://github.com/aryaanay/build-review-release/commits)
- **Nov 24, 2026** — Opened repository in [build-review-release](https://github.com/aryaanay/build-review-release)
- **Nov 19, 2026** — Updated code in [ai-narrative-reality-gap](https://github.com/aryaanay/ai-narrative-reality-gap/commits)
- **Nov 19, 2026** — Opened repository in [ai-narrative-reality-gap](https://github.com/aryaanay/ai-narrative-reality-gap)
<!-- activity:end -->

## Get in touch

If you find a bug or want to discuss a method, open an issue in the relevant repository. [Browse all repositories](https://github.com/aryaanay?tab=repositories).
