#!/usr/bin/env python3
"""
Conflict Zero - ML Model Training v1.5
Entrena el modelo predictivo de riesgo usando datos históricos
Fase 2 - Pipeline ML completo

Uso:
    cd backend && python scripts/train_ml_model.py [--dataset ml_dataset.json] [--output models/]
"""

import json
import os
import sys
import argparse
import pickle
import joblib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.pipeline import Pipeline

# Añadir parent al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def load_dataset(dataset_path: str = 'ml_dataset.json') -> List[Dict]:
    """Carga el dataset de entrenamiento."""
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset no encontrado: {dataset_path}")
        print("   Ejecuta primero: python scripts/generate_ml_dataset.py")
        sys.exit(1)
    
    with open(dataset_path, 'r') as f:
        data = json.load(f)
    
    print(f"📊 Dataset cargado: {len(data)} registros")
    return data


def extract_features(record: Dict) -> np.ndarray:
    """
    Extrae características de un snapshot para el modelo.
    
    Features:
        - risk_score: Score actual del proveedor
        - debt_ratio: Ratio de deuda vs umbral
        - sanction_count: Total de sanciones
        - compliance_changes: Cambios detectados
        - days_since_last_change: Días desde último cambio
        - volatility_score: Volatilidad histórica
        - trend_direction: Dirección de tendencia (1=up, -1=down, 0=stable)
    """
    raw = record.get('raw_data', {})
    
    # Características numéricas
    risk_score = raw.get('score', 50)
    debt = raw.get('deuda_tributaria', 0)
    debt_ratio = min(debt / 100000, 10.0)  # Normalizado a 0-10
    
    sanctions = raw.get('osce_sanciones', 0) + raw.get('tce_sanciones', 0)
    
    # Volatilidad basada en score
    volatility = raw.get('volatility_score', 0.5)
    
    # Features derivados
    features = [
        risk_score / 100.0,           # Normalizado 0-1
        debt_ratio / 10.0,            # Normalizado 0-1
        min(sanctions / 10.0, 1.0),   # Normalizado 0-1
        volatility,                    # 0-1
        1.0 if raw.get('verified') else 0.0,  # Booleano
        raw.get('consultation_count', 0) / 100.0,  # Frecuencia de consulta
    ]
    
    return np.array(features)


def prepare_training_data(data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Prepara datos de entrenamiento X, y.
    
    Target (y):
        0 = Bajo riesgo (score >= 70)
        1 = Riesgo moderado (score 50-69)
        2 = Riesgo alto (score 30-49)
        3 = Crítico (score < 30)
    """
    X = []
    y = []
    
    for record in data:
        features = extract_features(record)
        X.append(features)
        
        # Clasificación del riesgo
        score = record.get('raw_data', {}).get('score', 50)
        if score >= 70:
            y.append(0)  # Bajo
        elif score >= 50:
            y.append(1)  # Moderado
        elif score >= 30:
            y.append(2)  # Alto
        else:
            y.append(3)  # Crítico
    
    return np.array(X), np.array(y)


def train_model_v1_5(X: np.ndarray, y: np.ndarray, 
                      model_type: str = 'gradient_boosting') -> Pipeline:
    """
    Entrena el modelo ML v1.5.
    
    Args:
        X: Features de entrenamiento
        y: Labels (0-3)
        model_type: 'random_forest' | 'gradient_boosting'
    
    Returns:
        Pipeline entrenado (scaler + classifier)
    """
    print(f"\n🤖 Entrenando modelo v1.5 ({model_type})...")
    
    # Split train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"   Train: {len(X_train)} muestras")
    print(f"   Test: {len(X_test)} muestras")
    
    # Seleccionar clasificador
    if model_type == 'random_forest':
        classifier = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'
        )
    else:  # gradient_boosting
        classifier = GradientBoostingClassifier(
            n_estimators=150,
            max_depth=8,
            learning_rate=0.1,
            random_state=42
        )
    
    # Pipeline: scaling + clasificación
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', classifier)
    ])
    
    # Entrenamiento
    print("   Entrenando...")
    pipeline.fit(X_train, y_train)
    
    # Evaluación
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)
    
    print(f"\n📈 Resultados:")
    print(f"   Accuracy: {pipeline.score(X_test, y_test):.3f}")
    
    try:
        auc = roc_auc_score(y_test, y_proba, multi_class='ovr', average='weighted')
        print(f"   ROC-AUC (weighted): {auc:.3f}")
    except:
        pass
    
    # Cross-validation
    cv_scores = cross_val_score(pipeline, X, y, cv=5, scoring='accuracy')
    print(f"   CV Accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
    
    # Feature importance (solo para RandomForest/GB)
    if hasattr(classifier, 'feature_importances_'):
        feature_names = [
            'risk_score', 'debt_ratio', 'sanctions', 'volatility', 
            'verified', 'consultation_freq'
        ]
        importances = classifier.feature_importances_
        print(f"\n🔍 Feature Importance:")
        for name, imp in sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True):
            print(f"   {name}: {imp:.3f}")
    
    return pipeline


def save_model(pipeline: Pipeline, output_dir: str = 'models') -> str:
    """Guarda el modelo entrenado."""
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    model_path = os.path.join(output_dir, f'conflictzero_ml_v15_{timestamp}.joblib')
    
    joblib.dump(pipeline, model_path)
    
    # Guardar también metadata
    metadata = {
        'version': '1.5',
        'trained_at': datetime.now().isoformat(),
        'model_path': model_path,
        'features': [
            'risk_score', 'debt_ratio', 'sanctions', 'volatility', 
            'verified', 'consultation_freq'
        ],
        'classes': ['bajo', 'moderado', 'alto', 'critico']
    }
    
    meta_path = os.path.join(output_dir, f'conflictzero_ml_v15_{timestamp}_meta.json')
    with open(meta_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n💾 Modelo guardado en: {model_path}")
    print(f"📋 Metadata guardada en: {meta_path}")
    
    # Crear symlink al modelo más reciente
    latest_link = os.path.join(output_dir, 'latest.joblib')
    if os.path.exists(latest_link) or os.path.islink(latest_link):
        os.remove(latest_link)
    os.symlink(model_path, latest_link)
    print(f"🔗 Symlink creado: {latest_link}")
    
    return model_path


def run_hyperparameter_tuning(X: np.ndarray, y: np.ndarray) -> Dict:
    """Ejecuta búsqueda de hiperparámetros (opcional, más lento)."""
    print("\n🔬 Hyperparameter Tuning (esto puede tomar varios minutos)...")
    
    param_grid = {
        'classifier__n_estimators': [100, 200, 300],
        'classifier__max_depth': [5, 10, 15],
        'classifier__min_samples_split': [2, 5, 10]
    }
    
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', RandomForestClassifier(random_state=42, class_weight='balanced'))
    ])
    
    grid_search = GridSearchCV(
        pipeline, param_grid, cv=3, scoring='accuracy', n_jobs=-1, verbose=1
    )
    grid_search.fit(X, y)
    
    print(f"   Mejor score: {grid_search.best_score_:.3f}")
    print(f"   Mejores params: {grid_search.best_params_}")
    
    return {
        'best_params': grid_search.best_params_,
        'best_score': grid_search.best_score_,
        'best_model': grid_search.best_estimator_
    }


def main():
    parser = argparse.ArgumentParser(description='Conflict Zero ML Model Training v1.5')
    parser.add_argument('--dataset', default='ml_dataset.json', help='Path al dataset JSON')
    parser.add_argument('--output', default='models', help='Directorio de salida')
    parser.add_argument('--model-type', default='gradient_boosting', 
                        choices=['random_forest', 'gradient_boosting'],
                        help='Tipo de modelo')
    parser.add_argument('--tune', action='store_true', help='Ejecutar hyperparameter tuning')
    parser.add_argument('--seed-db', action='store_true', help='Generar dataset desde DB si no existe')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Conflict Zero - ML Model Training v1.5")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Dataset: {args.dataset}")
    print(f"Modelo: {args.model_type}")
    print("=" * 60)
    
    # 1. Cargar dataset
    data = load_dataset(args.dataset)
    
    # 2. Preparar datos
    X, y = prepare_training_data(data)
    print(f"\n📐 Features shape: {X.shape}")
    print(f"📐 Labels distribution: {dict(zip(*np.unique(y, return_counts=True)))}")
    
    # 3. Entrenar modelo
    if args.tune:
        results = run_hyperparameter_tuning(X, y)
        model = results['best_model']
    else:
        model = train_model_v1_5(X, y, model_type=args.model_type)
    
    # 4. Guardar modelo
    model_path = save_model(model, output_dir=args.output)
    
    # 5. Reporte final
    print("\n" + "=" * 60)
    print("✅ Entrenamiento completado")
    print("=" * 60)
    print(f"Modelo: {model_path}")
    print(f"\nPróximos pasos:")
    print("  1. Evaluar modelo en datos de producción")
    print("  2. Actualizar ML_SCORING_VERSION en app/routers/ml_scoring.py")
    print("  3. Desplegar modelo a producción")
    print("=" * 60)


if __name__ == '__main__':
    main()
