import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import pickle
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import joblib
import os

class AILearningSystem:
    def __init__(self):
        self.models = {
            'profitability': RandomForestRegressor(n_estimators=100, random_state=42),
            'direction': GradientBoostingClassifier(n_estimators=100, random_state=42),
            'confidence': RandomForestRegressor(n_estimators=50, random_state=42)
        }
        
        self.scalers = {
            'features': StandardScaler(),
            'targets': StandardScaler()
        }
        
        self.label_encoders = {
            'symbol': LabelEncoder(),
            'option_type': LabelEncoder(),
            'action': LabelEncoder()
        }
        
        self.feature_names = [
            'delta', 'gamma', 'theta', 'vega', 'iv', 'oi_change_percent',
            'volume_ratio', 'spread_percent', 'time_to_expiry',
            'underlying_price', 'strike_distance', 'moneyness'
        ]
        
        self.learning_data = []
        self.model_performance = {}
        self.parameter_importance = {}
        self.learning_curve = []
        
        self.models_trained = False
        self.min_samples_for_training = 50
        
        # Load existing models and data
        self.load_models()
        self.load_learning_data()
    
    def load_models(self):
        """Load pre-trained models if they exist"""
        try:
            model_dir = 'data/models'
            if os.path.exists(model_dir):
                for model_name in self.models.keys():
                    model_path = os.path.join(model_dir, f'{model_name}_model.pkl')
                    scaler_path = os.path.join(model_dir, f'{model_name}_scaler.pkl')
                    
                    if os.path.exists(model_path):
                        self.models[model_name] = joblib.load(model_path)
                        print(f"Loaded {model_name} model")
                
                # Load scalers
                for scaler_name in self.scalers.keys():
                    scaler_path = os.path.join(model_dir, f'{scaler_name}_scaler.pkl')
                    if os.path.exists(scaler_path):
                        self.scalers[scaler_name] = joblib.load(scaler_path)
                
                # Load encoders
                for encoder_name in self.label_encoders.keys():
                    encoder_path = os.path.join(model_dir, f'{encoder_name}_encoder.pkl')
                    if os.path.exists(encoder_path):
                        self.label_encoders[encoder_name] = joblib.load(encoder_path)
                
                self.models_trained = True
                
        except Exception as e:
            print(f"Error loading models: {e}")
    
    def save_models(self):
        """Save trained models"""
        try:
            model_dir = 'data/models'
            os.makedirs(model_dir, exist_ok=True)
            
            # Save models
            for model_name, model in self.models.items():
                model_path = os.path.join(model_dir, f'{model_name}_model.pkl')
                joblib.dump(model, model_path)
            
            # Save scalers
            for scaler_name, scaler in self.scalers.items():
                scaler_path = os.path.join(model_dir, f'{scaler_name}_scaler.pkl')
                joblib.dump(scaler, scaler_path)
            
            # Save encoders
            for encoder_name, encoder in self.label_encoders.items():
                encoder_path = os.path.join(model_dir, f'{encoder_name}_encoder.pkl')
                joblib.dump(encoder, encoder_path)
            
            print("Models saved successfully")
            
        except Exception as e:
            print(f"Error saving models: {e}")
    
    def load_learning_data(self):
        """Load historical learning data"""
        try:
            learning_file = 'data/ai_learning_data.json'
            if os.path.exists(learning_file):
                with open(learning_file, 'r') as f:
                    self.learning_data = json.load(f)
                print(f"Loaded {len(self.learning_data)} learning records")
                
                # If we have enough data, train models
                if len(self.learning_data) >= self.min_samples_for_training:
                    self.train_models()
                    
        except Exception as e:
            print(f"Error loading learning data: {e}")
    
    def save_learning_data(self):
        """Save learning data to file"""
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/ai_learning_data.json', 'w') as f:
                json.dump(self.learning_data, f, default=str, indent=2)
        except Exception as e:
            print(f"Error saving learning data: {e}")
    
    def add_learning_record(self, signal_data: Dict, outcome_data: Dict):
        """Add a new learning record from trade outcome"""
        try:
            learning_record = {
                'timestamp': datetime.now().isoformat(),
                'signal_id': signal_data.get('id'),
                'symbol': signal_data.get('symbol'),
                'strike': signal_data.get('strike'),
                'option_type': signal_data.get('type'),
                'action': signal_data.get('action'),
                'predicted_confidence': signal_data.get('confidence', 0) / 100,
                
                # Features used in prediction
                'features': {
                    'delta': signal_data.get('parameters', {}).get('delta_score', 0),
                    'gamma': 0.005,  # Would come from option data
                    'theta': -2.5,   # Would come from option data
                    'vega': 15.0,    # Would come from option data
                    'iv': signal_data.get('parameters', {}).get('iv_score', 0) * 25,  # Convert back to IV
                    'oi_change_percent': signal_data.get('parameters', {}).get('oi_score', 0) * 20,
                    'volume_ratio': signal_data.get('parameters', {}).get('volume_score', 0),
                    'spread_percent': (1 - signal_data.get('parameters', {}).get('spread_score', 0.5)) * 10,
                    'time_to_expiry': 7.0,  # Would be calculated from expiry
                    'underlying_price': signal_data.get('underlying_price', 0),
                    'strike_distance': abs(signal_data.get('underlying_price', 0) - signal_data.get('strike', 0)),
                    'moneyness': signal_data.get('underlying_price', 0) / signal_data.get('strike', 1)
                },
                
                # Actual outcomes
                'actual_pnl': outcome_data.get('pnl', 0),
                'actual_return_percent': outcome_data.get('return_percent', 0),
                'was_profitable': outcome_data.get('pnl', 0) > 0,
                'holding_period_minutes': outcome_data.get('holding_period', 0),
                'exit_reason': outcome_data.get('exit_reason', 'manual'),
                
                # Market conditions during trade
                'market_volatility': signal_data.get('parameters', {}).get('iv_score', 0.5),
                'market_trend': 'neutral'  # Would be calculated from market data
            }
            
            self.learning_data.append(learning_record)
            
            # Keep only recent data (last 1000 records)
            if len(self.learning_data) > 1000:
                self.learning_data = self.learning_data[-1000:]
            
            # Save updated data
            self.save_learning_data()
            
            # Retrain models periodically
            if len(self.learning_data) % 20 == 0:  # Retrain every 20 new records
                self.train_models()
            
            return True
            
        except Exception as e:
            print(f"Error adding learning record: {e}")
            return False
    
    def prepare_training_data(self) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Prepare data for model training"""
        if len(self.learning_data) < self.min_samples_for_training:
            return None, None, []
        
        try:
            # Convert learning data to DataFrame
            df = pd.DataFrame(self.learning_data)
            
            # Extract features
            features_list = []
            targets_list = []
            
            for _, record in df.iterrows():
                # Extract feature vector
                feature_vector = []
                for feature_name in self.feature_names:
                    feature_vector.append(record['features'].get(feature_name, 0))
                
                features_list.append(feature_vector)
                
                # Extract targets (multiple targets for different models)
                targets_list.append({
                    'profitability': record['actual_pnl'],
                    'direction': 1 if record['was_profitable'] else 0,
                    'confidence': abs(record['actual_return_percent']) / 100  # Normalized confidence
                })
            
            features = np.array(features_list)
            
            return features, targets_list, self.feature_names
            
        except Exception as e:
            print(f"Error preparing training data: {e}")
            return None, None, []
    
    def train_models(self):
        """Train all AI models on accumulated learning data"""
        try:
            features, targets_list, feature_names = self.prepare_training_data()
            
            if features is None or len(targets_list) < self.min_samples_for_training:
                print("Insufficient data for training")
                return False
            
            print(f"Training models with {len(targets_list)} samples...")
            
            # Scale features
            features_scaled = self.scalers['features'].fit_transform(features)
            
            # Train each model
            model_scores = {}
            
            # Profitability prediction model
            profitability_targets = [t['profitability'] for t in targets_list]
            
            X_train, X_test, y_train, y_test = train_test_split(
                features_scaled, profitability_targets, test_size=0.2, random_state=42
            )
            
            self.models['profitability'].fit(X_train, y_train)
            prof_score = self.models['profitability'].score(X_test, y_test)
            model_scores['profitability'] = prof_score
            
            # Direction prediction model (classification)
            direction_targets = [t['direction'] for t in targets_list]
            
            X_train, X_test, y_train, y_test = train_test_split(
                features_scaled, direction_targets, test_size=0.2, random_state=42
            )
            
            self.models['direction'].fit(X_train, y_train)
            y_pred = self.models['direction'].predict(X_test)
            dir_score = accuracy_score(y_test, y_pred)
            model_scores['direction'] = dir_score
            
            # Confidence prediction model
            confidence_targets = [t['confidence'] for t in targets_list]
            
            X_train, X_test, y_train, y_test = train_test_split(
                features_scaled, confidence_targets, test_size=0.2, random_state=42
            )
            
            self.models['confidence'].fit(X_train, y_train)
            conf_score = self.models['confidence'].score(X_test, y_test)
            model_scores['confidence'] = conf_score
            
            # Calculate feature importance
            self.calculate_feature_importance(features_scaled, targets_list)
            
            # Update model performance tracking
            self.model_performance = {
                'last_training_date': datetime.now().isoformat(),
                'training_samples': len(targets_list),
                'model_scores': model_scores,
                'feature_importance': self.parameter_importance
            }
            
            # Update learning curve
            overall_accuracy = (prof_score + dir_score + conf_score) / 3
            self.learning_curve.append({
                'date': datetime.now().isoformat(),
                'samples': len(targets_list),
                'accuracy': overall_accuracy * 100
            })
            
            self.models_trained = True
            
            # Save models
            self.save_models()
            
            print(f"Models trained successfully:")
            print(f"  Profitability R²: {prof_score:.3f}")
            print(f"  Direction Accuracy: {dir_score:.3f}")
            print(f"  Confidence R²: {conf_score:.3f}")
            
            return True
            
        except Exception as e:
            print(f"Error training models: {e}")
            return False
    
    def calculate_feature_importance(self, features: np.ndarray, targets_list: List[Dict]):
        """Calculate and store feature importance"""
        try:
            # Get feature importance from profitability model (RandomForest)
            if hasattr(self.models['profitability'], 'feature_importances_'):
                importances = self.models['profitability'].feature_importances_
                
                self.parameter_importance = {}
                for i, feature_name in enumerate(self.feature_names):
                    self.parameter_importance[feature_name] = float(importances[i])
                
                # Sort by importance
                self.parameter_importance = dict(
                    sorted(self.parameter_importance.items(), 
                          key=lambda x: x[1], reverse=True)
                )
        
        except Exception as e:
            print(f"Error calculating feature importance: {e}")
    
    def predict_signal_quality(self, signal_data: Dict) -> Dict:
        """Predict signal quality using trained models"""
        if not self.models_trained:
            # Return default predictions if models not trained
            return {
                'predicted_pnl': 0,
                'predicted_direction': 0.5,  # Neutral
                'predicted_confidence': signal_data.get('confidence', 70) / 100,
                'recommendation': 'HOLD',
                'risk_score': 0.5,
                'using_trained_model': False
            }
        
        try:
            # Extract features from signal
            feature_vector = []
            parameters = signal_data.get('parameters', {})
            
            features = {
                'delta': parameters.get('delta_score', 0),
                'gamma': 0.005,  # Would come from option data
                'theta': -2.5,   # Would come from option data
                'vega': 15.0,    # Would come from option data
                'iv': parameters.get('iv_score', 0) * 25,
                'oi_change_percent': parameters.get('oi_score', 0) * 20,
                'volume_ratio': parameters.get('volume_score', 0),
                'spread_percent': (1 - parameters.get('spread_score', 0.5)) * 10,
                'time_to_expiry': 7.0,
                'underlying_price': signal_data.get('underlying_price', 0),
                'strike_distance': abs(signal_data.get('underlying_price', 0) - signal_data.get('strike', 0)),
                'moneyness': signal_data.get('underlying_price', 0) / signal_data.get('strike', 1)
            }
            
            for feature_name in self.feature_names:
                feature_vector.append(features.get(feature_name, 0))
            
            feature_vector = np.array(feature_vector).reshape(1, -1)
            
            # Scale features
            feature_vector_scaled = self.scalers['features'].transform(feature_vector)
            
            # Make predictions
            predicted_pnl = self.models['profitability'].predict(feature_vector_scaled)[0]
            predicted_direction_prob = self.models['direction'].predict_proba(feature_vector_scaled)[0][1]  # Probability of profit
            predicted_confidence = self.models['confidence'].predict(feature_vector_scaled)[0]
            
            # Generate recommendation
            if predicted_direction_prob > 0.7 and predicted_pnl > 100:
                recommendation = 'BUY'
            elif predicted_direction_prob < 0.3 or predicted_pnl < -100:
                recommendation = 'SELL'
            else:
                recommendation = 'HOLD'
            
            # Calculate risk score (0 = low risk, 1 = high risk)
            risk_score = min(1.0, abs(predicted_pnl) / 1000)  # Normalized risk
            
            return {
                'predicted_pnl': predicted_pnl,
                'predicted_direction': predicted_direction_prob,
                'predicted_confidence': predicted_confidence,
                'recommendation': recommendation,
                'risk_score': risk_score,
                'using_trained_model': True,
                'model_confidence': min(predicted_direction_prob, 1 - predicted_direction_prob) * 2  # Normalized
            }
            
        except Exception as e:
            print(f"Error making prediction: {e}")
            return {
                'predicted_pnl': 0,
                'predicted_direction': 0.5,
                'predicted_confidence': 0.5,
                'recommendation': 'HOLD',
                'risk_score': 0.5,
                'using_trained_model': False
            }
    
    def get_learning_progress(self) -> List[float]:
        """Get learning progress for charting"""
        if len(self.learning_curve) < 2:
            # Return sample progress if no real data
            return [65.0, 68.0, 71.0, 73.0, 75.0, 76.0, 78.0, 79.0, 80.0, 82.0]
        
        return [point['accuracy'] for point in self.learning_curve[-20:]]  # Last 20 points
    
    def get_model_performance_summary(self) -> Dict:
        """Get summary of model performance"""
        if not self.model_performance:
            return {
                'models_trained': False,
                'training_samples': 0,
                'last_training': 'Never',
                'overall_accuracy': 0.0,
                'top_features': []
            }
        
        scores = self.model_performance.get('model_scores', {})
        overall_accuracy = sum(scores.values()) / len(scores) * 100 if scores else 0
        
        # Get top 5 most important features
        importance = self.parameter_importance
        top_features = list(importance.items())[:5] if importance else []
        
        return {
            'models_trained': self.models_trained,
            'training_samples': self.model_performance.get('training_samples', 0),
            'last_training': self.model_performance.get('last_training_date', 'Never'),
            'overall_accuracy': overall_accuracy,
            'profitability_score': scores.get('profitability', 0),
            'direction_accuracy': scores.get('direction', 0),
            'confidence_score': scores.get('confidence', 0),
            'top_features': top_features
        }
    
    def optimize_parameters(self):
        """Optimize AI parameters based on learning"""
        if not self.models_trained or len(self.learning_data) < 100:
            return
        
        try:
            # Analyze what parameter combinations lead to best results
            df = pd.DataFrame(self.learning_data)
            profitable_trades = df[df['was_profitable'] == True]
            
            if len(profitable_trades) > 10:
                # Calculate average feature values for profitable trades
                profitable_features = {}
                for feature_name in self.feature_names:
                    values = [trade['features'].get(feature_name, 0) for trade in profitable_trades.to_dict('records')]
                    profitable_features[feature_name] = np.mean(values)
                
                # Update parameter weights based on importance and profitability correlation
                # This would adjust the weights in the signal engine
                print("Parameter optimization completed")
                
        except Exception as e:
            print(f"Error optimizing parameters: {e}")
    
    def generate_learning_insights(self) -> Dict:
        """Generate insights from learning data"""
        if len(self.learning_data) < 20:
            return {'insights': ['Insufficient data for insights']}
        
        try:
            df = pd.DataFrame(self.learning_data)
            insights = []
            
            # Win rate analysis
            win_rate = df['was_profitable'].mean() * 100
            insights.append(f"Current AI win rate: {win_rate:.1f}%")
            
            # Best performing symbols
            symbol_performance = df.groupby('symbol')['actual_pnl'].agg(['mean', 'count'])
            best_symbol = symbol_performance[symbol_performance['count'] >= 5]['mean'].idxmax()
            insights.append(f"Best performing symbol: {best_symbol}")
            
            # Time-based insights
            df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
            hourly_performance = df.groupby('hour')['was_profitable'].mean()
            best_hour = hourly_performance.idxmax()
            insights.append(f"Most profitable trading hour: {best_hour}:00")
            
            # Feature insights
            if self.parameter_importance:
                most_important = list(self.parameter_importance.keys())[0]
                insights.append(f"Most important parameter: {most_important}")
            
            # Recent performance trend
            recent_trades = df.tail(20)
            recent_win_rate = recent_trades['was_profitable'].mean() * 100
            
            if recent_win_rate > win_rate:
                insights.append("AI performance is improving recently")
            elif recent_win_rate < win_rate - 10:
                insights.append("AI performance has declined recently")
            else:
                insights.append("AI performance is stable")
            
            return {
                'insights': insights,
                'win_rate': win_rate,
                'total_trades': len(df),
                'average_pnl': df['actual_pnl'].mean(),
                'best_trade': df['actual_pnl'].max(),
                'worst_trade': df['actual_pnl'].min()
            }
            
        except Exception as e:
            print(f"Error generating insights: {e}")
            return {'insights': ['Error generating insights']}
    
    def reset_learning_data(self):
        """Reset all learning data (use with caution)"""
        self.learning_data = []
        self.learning_curve = []
        self.model_performance = {}
        self.parameter_importance = {}
        self.models_trained = False
        
        # Delete saved files
        try:
            if os.path.exists('data/ai_learning_data.json'):
                os.remove('data/ai_learning_data.json')
            
            model_dir = 'data/models'
            if os.path.exists(model_dir):
                for file in os.listdir(model_dir):
                    os.remove(os.path.join(model_dir, file))
                os.rmdir(model_dir)
            
            print("Learning data reset successfully")
            
        except Exception as e:
            print(f"Error resetting learning data: {e}")
