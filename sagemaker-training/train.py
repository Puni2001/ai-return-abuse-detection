"""
SageMaker Training Script for Return Abuse Detection
Uses XGBoost for binary classification with SHAP explainability
"""

import argparse
import json
import os
import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_auc_score, 
    precision_recall_curve, 
    classification_report,
    confusion_matrix
)
import shap
import joblib
from typing import Tuple, Dict


def load_data(data_path: str) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Load and prepare training data from S3
    
    Args:
        data_path: Path to training data CSV
        
    Returns:
        X: Feature DataFrame
        y: Target Series (1 = fraud, 0 = legitimate)
    """
    print(f"Loading data from {data_path}")
    
    # Load data
    df = pd.read_csv(os.path.join(data_path, 'training_data.csv'))
    
    print(f"Loaded {len(df)} records")
    print(f"Columns: {df.columns.tolist()}")
    
    # Define features
    feature_columns = [
        'customer_return_rate',
        'total_orders',
        'is_cod',
        'amount',
        'product_return_rate',
        'is_festival_season',
        'customer_age_days',
        'avg_order_value',
        'return_frequency_30d',
        'high_value_order_flag',
        'new_customer_flag'
    ]
    
    # Prepare features and target
    X = df[feature_columns]
    y = df['is_fraud']  # 1 = fraud, 0 = legitimate
    
    print(f"Features shape: {X.shape}")
    print(f"Target distribution: {y.value_counts().to_dict()}")
    
    return X, y


def engineer_features(X: pd.DataFrame) -> pd.DataFrame:
    """
    Create additional engineered features
    
    Args:
        X: Input feature DataFrame
        
    Returns:
        Enhanced feature DataFrame
    """
    X = X.copy()
    
    # Interaction features
    X['return_rate_x_cod'] = X['customer_return_rate'] * X['is_cod']
    X['amount_x_return_rate'] = X['amount'] * X['customer_return_rate']
    X['festival_x_cod'] = X['is_festival_season'] * X['is_cod']
    
    # Risk score components
    X['customer_risk_score'] = (
        X['customer_return_rate'] * 0.4 +
        X['new_customer_flag'] * 0.1
    )
    
    X['order_risk_score'] = (
        X['is_cod'] * 0.15 +
        X['high_value_order_flag'] * 0.2 +
        X['product_return_rate'] * 0.1
    )
    
    return X


def train_model(
    X_train: pd.DataFrame, 
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    hyperparameters: Dict
) -> xgb.XGBClassifier:
    """
    Train XGBoost model with early stopping
    
    Args:
        X_train: Training features
        y_train: Training labels
        X_val: Validation features
        y_val: Validation labels
        hyperparameters: Model hyperparameters
        
    Returns:
        Trained XGBoost model
    """
    print("Training XGBoost model...")
    
    # Initialize model
    model = xgb.XGBClassifier(
        max_depth=hyperparameters.get('max_depth', 6),
        learning_rate=hyperparameters.get('learning_rate', 0.1),
        n_estimators=hyperparameters.get('n_estimators', 100),
        min_child_weight=hyperparameters.get('min_child_weight', 1),
        gamma=hyperparameters.get('gamma', 0),
        subsample=hyperparameters.get('subsample', 0.8),
        colsample_bytree=hyperparameters.get('colsample_bytree', 0.8),
        objective='binary:logistic',
        eval_metric='auc',
        use_label_encoder=False,
        random_state=42
    )
    
    # Train with early stopping
    model.fit(
        X_train, 
        y_train,
        eval_set=[(X_val, y_val)],
        early_stopping_rounds=10,
        verbose=True
    )
    
    print(f"Best iteration: {model.best_iteration}")
    print(f"Best score: {model.best_score:.4f}")
    
    return model


def evaluate_model(
    model: xgb.XGBClassifier,
    X_test: pd.DataFrame,
    y_test: pd.Series
) -> Dict:
    """
    Evaluate model performance
    
    Args:
        model: Trained model
        X_test: Test features
        y_test: Test labels
        
    Returns:
        Dictionary of evaluation metrics
    """
    print("\nEvaluating model...")
    
    # Predictions
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    # Calculate metrics
    auc_score = roc_auc_score(y_test, y_pred_proba)
    
    # Precision-Recall at different thresholds
    precision, recall, thresholds = precision_recall_curve(y_test, y_pred_proba)
    
    # Find optimal threshold (maximize F1)
    f1_scores = 2 * (precision * recall) / (precision + recall + 1e-10)
    optimal_idx = np.argmax(f1_scores)
    optimal_threshold = thresholds[optimal_idx] if optimal_idx < len(thresholds) else 0.5
    
    # Classification report
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    print("\nConfusion Matrix:")
    print(cm)
    
    metrics = {
        'auc': float(auc_score),
        'optimal_threshold': float(optimal_threshold),
        'optimal_precision': float(precision[optimal_idx]),
        'optimal_recall': float(recall[optimal_idx]),
        'optimal_f1': float(f1_scores[optimal_idx]),
        'confusion_matrix': cm.tolist()
    }
    
    print(f"\nAUC Score: {auc_score:.4f}")
    print(f"Optimal Threshold: {optimal_threshold:.4f}")
    print(f"Optimal F1 Score: {f1_scores[optimal_idx]:.4f}")
    
    return metrics


def generate_shap_values(
    model: xgb.XGBClassifier,
    X_sample: pd.DataFrame,
    output_path: str
) -> None:
    """
    Generate SHAP values for model explainability
    
    Args:
        model: Trained model
        X_sample: Sample data for SHAP calculation
        output_path: Path to save SHAP values
    """
    print("\nGenerating SHAP values for explainability...")
    
    # Create SHAP explainer
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_sample)
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X_sample.columns,
        'importance': np.abs(shap_values).mean(axis=0)
    }).sort_values('importance', ascending=False)
    
    print("\nTop 10 Most Important Features:")
    print(feature_importance.head(10))
    
    # Save SHAP values
    shap_output = {
        'feature_importance': feature_importance.to_dict('records'),
        'base_value': float(explainer.expected_value),
        'sample_shap_values': shap_values[:100].tolist()  # Save first 100 samples
    }
    
    with open(os.path.join(output_path, 'shap_values.json'), 'w') as f:
        json.dump(shap_output, f, indent=2)
    
    print(f"SHAP values saved to {output_path}/shap_values.json")


def save_model(model: xgb.XGBClassifier, output_path: str) -> None:
    """
    Save trained model and metadata
    
    Args:
        model: Trained model
        output_path: Path to save model
    """
    print(f"\nSaving model to {output_path}")
    
    # Save model
    model_path = os.path.join(output_path, 'model.joblib')
    joblib.dump(model, model_path)
    
    # Save model metadata
    metadata = {
        'model_type': 'XGBoost',
        'version': '1.0',
        'features': model.feature_names_in_.tolist() if hasattr(model, 'feature_names_in_') else [],
        'n_features': model.n_features_in_,
        'best_iteration': int(model.best_iteration),
        'best_score': float(model.best_score)
    }
    
    with open(os.path.join(output_path, 'model_metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("Model saved successfully")


def main():
    """
    Main training function
    """
    parser = argparse.ArgumentParser()
    
    # Hyperparameters
    parser.add_argument('--max-depth', type=int, default=6)
    parser.add_argument('--learning-rate', type=float, default=0.1)
    parser.add_argument('--n-estimators', type=int, default=100)
    parser.add_argument('--min-child-weight', type=int, default=1)
    parser.add_argument('--gamma', type=float, default=0)
    parser.add_argument('--subsample', type=float, default=0.8)
    parser.add_argument('--colsample-bytree', type=float, default=0.8)
    
    # SageMaker paths
    parser.add_argument('--model-dir', type=str, default=os.environ.get('SM_MODEL_DIR', './model'))
    parser.add_argument('--train', type=str, default=os.environ.get('SM_CHANNEL_TRAIN', './data'))
    parser.add_argument('--output-data-dir', type=str, default=os.environ.get('SM_OUTPUT_DATA_DIR', './output'))
    
    args = parser.parse_args()
    
    # Load data
    X, y = load_data(args.train)
    
    # Engineer features
    X = engineer_features(X)
    
    # Split data
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
    )
    
    print(f"\nTrain size: {len(X_train)}")
    print(f"Validation size: {len(X_val)}")
    print(f"Test size: {len(X_test)}")
    
    # Hyperparameters
    hyperparameters = {
        'max_depth': args.max_depth,
        'learning_rate': args.learning_rate,
        'n_estimators': args.n_estimators,
        'min_child_weight': args.min_child_weight,
        'gamma': args.gamma,
        'subsample': args.subsample,
        'colsample_bytree': args.colsample_bytree
    }
    
    # Train model
    model = train_model(X_train, y_train, X_val, y_val, hyperparameters)
    
    # Evaluate model
    metrics = evaluate_model(model, X_test, y_test)
    
    # Save metrics
    with open(os.path.join(args.output_data_dir, 'metrics.json'), 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Generate SHAP values
    generate_shap_values(model, X_test.head(100), args.output_data_dir)
    
    # Save model
    save_model(model, args.model_dir)
    
    print("\n✅ Training completed successfully!")


if __name__ == '__main__':
    main()
