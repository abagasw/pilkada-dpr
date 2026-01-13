
import joblib
import numpy as np
from datetime import datetime
import json

class SentimentPredictor:
    """Production-ready sentiment prediction service"""

    def __init__(self, model_path, metadata_path):
        self.model = joblib.load(model_path)
        with open(metadata_path, 'r') as f:
            self.metadata = json.load(f)
        self.feature_names = self.metadata['feature_names']
        self.version = self.metadata['version']

    def predict(self, features_dict):
        """Make prediction from feature dictionary"""
        features = np.array([features_dict[col] for col in self.feature_names]).reshape(1, -1)
        prediction = self.model.predict(features)[0]
        proba = self.model.predict_proba(features)[0]

        return {
            'sentiment': prediction,
            'confidence': float(max(proba)),
            'probabilities': dict(zip(self.model.classes_, [float(p) for p in proba])),
            'model_version': self.version,
            'timestamp': datetime.now().isoformat()
        }

    def batch_predict(self, features_df):
        """Make predictions for batch of samples"""
        predictions = self.model.predict(features_df[self.feature_names])
        probas = self.model.predict_proba(features_df[self.feature_names])

        results = []
        for i, (pred, proba) in enumerate(zip(predictions, probas)):
            results.append({
                'index': i,
                'sentiment': pred,
                'confidence': float(max(proba)),
                'probabilities': dict(zip(self.model.classes_, [float(p) for p in proba]))
            })
        return results

# Usage:
# predictor = SentimentPredictor('model_path.pkl', 'metadata_path.json')
# result = predictor.predict(feature_dict)
# batch_results = predictor.batch_predict(df)
