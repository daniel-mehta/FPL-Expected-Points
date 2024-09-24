# Fantasy Premier League Points Predictor

This repository contains two models designed to predict Fantasy Premier League (FPL) points for players. The models offer different approaches to forecasting player performance in FPL:

1. **ML_xP.py**: A Random Forest regression model that uses machine learning to predict player points based on various features.
2. **xP_FPL.py**: A custom statistical model that predicts points using simpler, manually defined rules and calculations.

## How to Use

1. Clone the repository and install any required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2. To run the **Machine Learning** model:
    ```bash
    python ML_xP.py
    ```

3. To run the **Statistical** model:
    ```bash
    python xP_FPL.py
    ```

Both models can be evaluated and compared by analyzing their predictions against actual FPL points.

## Gameweek 5 Comparison (2024/25 EPL Season)

For Gameweek 5 of the 2024/25 EPL season, I compared the performance of both models and found the following:

- The average absolute difference for each algorithm was:
  - **Machine Learning algorithm**: 1.82 points
  - **Statistical algorithm**: 1.89 points

- The average difference (signed) between expected and real points for each algorithm was:
  - **Machine Learning algorithm**: -0.20 points
  - **Statistical algorithm**: -0.06 points

### Overprediction and Underprediction:
- **Machine Learning algorithm**:
  - Overpredicted: 135 players
  - Underpredicted: 162 players

- **Statistical algorithm**:
  - Overpredicted: 80 players
  - Underpredicted: 113 players

You can view a chart comparing the predictions and actual points below:

![output (1)](https://github.com/user-attachments/assets/4dbb06f4-fadc-4242-bef0-e97aeaf58594)

