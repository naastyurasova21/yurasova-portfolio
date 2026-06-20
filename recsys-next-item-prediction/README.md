# Next Item Prediction — Recommendation System

A simple recommendation system for predicting the next product in an e-commerce session based on a transition graph.

## Project Description

The model analyzes a user's view history and predicts which product they will view next. It is based on a transition graph between products built from training data.

### Key Features

- Data analysis: session length distribution, top popular products, anomaly detection
- Train/test split preserving temporal structure (last product in session goes to test)
- Building transition graph and computing transition probabilities P(j|i)
- Top-10 product recommendations based on the last viewed product
- Fallback based on incoming popularity for handling unknown/cold start products
- Quality evaluation using Hit@10 metric
- Comparison with baseline (top-10 most popular products)

## Technologies

- Python 3
- NumPy — mathematical calculations
- Matplotlib — visualization
- JSON — data handling
- Standard libraries (collections, defaultdict, Counter)

Prohibited libraries (implicit, LightFM, RecBole) are not used.

### Install dependencies

```bash
pip install -r requirements.txt



