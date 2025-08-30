import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input, decode_predictions
import numpy as np
from PIL import Image
import cv2
import os

class EnvironmentalAnalyzer:
    """
    AI Model using Transfer Learning with MobileNetV2 for Environmental Image Analysis
    
    Techniques Used:
    1. Transfer Learning - Using pre-trained MobileNetV2 CNN
    2. Computer Vision - Image preprocessing and feature extraction
    3. Multi-class Classification - Environmental vs Non-environmental content
    4. Image Feature Analysis - Color distribution, texture analysis
    5. Semantic Analysis - Object detection for environmental elements
    """
    
    def __init__(self):
        # Lazy loading - model will be loaded only when first used
        self.model = None
        self._model_loaded = False
        
    def _ensure_model_loaded(self):
        """Load model only when needed (lazy loading)"""
        if not self._model_loaded:
            try:
                import os
                # Suppress TensorFlow warnings for faster loading
                os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
                self.model = MobileNetV2(weights='imagenet', include_top=True)
                self._model_loaded = True
            except Exception as e:
                print(f"Failed to load AI model: {e}")
                self.model = None
                
        # Initialize environmental classes (moved from __init__ for lazy loading)
        if not hasattr(self, 'environmental_classes'):
            # Environmental keywords from ImageNet classes (expanded for better detection)
            self.environmental_classes = {
            # Nature and Wildlife - Animals
            'beaver', 'otter', 'zebra', 'elephant', 'lion', 'tiger', 'bear', 'panda',
            'eagle', 'hawk', 'owl', 'pelican', 'flamingo', 'ostrich', 'peacock',
            'turtle', 'frog', 'snake', 'lizard', 'crocodile', 'alligator',
            'fish', 'shark', 'whale', 'dolphin', 'seal', 'octopus',
            'butterfly', 'bee', 'spider', 'dragonfly', 'ladybug',
            
            # Plants and Trees
            'tree', 'oak', 'pine', 'palm', 'maple', 'willow', 'birch',
            'flower', 'rose', 'tulip', 'sunflower', 'daisy', 'orchid',
            'mushroom', 'coral', 'seaweed', 'moss', 'fern',
            
            # Landscapes and Natural Features
            'mountain', 'volcano', 'geyser', 'glacier', 'iceberg', 'cliff',
            'beach', 'lakeside', 'seashore', 'sandbar', 'promontory',
            'forest', 'rainforest', 'jungle', 'desert', 'canyon', 'valley',
            'river', 'stream', 'waterfall', 'lake', 'pond', 'ocean',
            'island', 'peninsula', 'reef', 'atoll',
            
            # Weather and Sky
            'thunderstorm', 'rainbow', 'aurora', 'sunset', 'sunrise',
            
            # Environmental Threats
            'wildfire', 'forest_fire', 'pollution', 'oil_spill', 'smog',
        }
        
        # Critical environmental threat indicators
        self.critical_indicators = {
            'wildfire', 'forest_fire', 'oil_spill', 'pollution', 'smog',
            'toxic_waste', 'deforestation', 'illegal_dumping'
        }
        
        # High-risk environmental indicators
        self.high_risk_indicators = {
            'drought', 'flood', 'erosion', 'bleaching', 'dying_coral',
            'overfishing', 'habitat_loss', 'endangered_species'
        }

    def preprocess_image(self, image_path):
        """Preprocess image for model prediction"""
        try:
            # Load and resize image
            img = image.load_img(image_path, target_size=(224, 224))
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)
            return img_array
        except Exception as e:
            print(f"Error preprocessing image: {e}")
            return None

    def analyze_color_distribution(self, image_path):
        """Analyze color distribution to detect environmental content"""
        try:
            img = cv2.imread(image_path)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Calculate color histograms
            hist_r = cv2.calcHist([img_rgb], [0], None, [256], [0, 256])
            hist_g = cv2.calcHist([img_rgb], [1], None, [256], [0, 256])
            hist_b = cv2.calcHist([img_rgb], [2], None, [256], [0, 256])
            
            # Analyze green dominance (vegetation indicator)
            green_dominance = np.sum(hist_g[50:200]) / np.sum(hist_g)
            
            # Analyze blue dominance (water/sky indicator)
            blue_dominance = np.sum(hist_b[100:255]) / np.sum(hist_b)
            
            # Analyze brown/earth tones (soil/desert indicator)
            brown_score = self._calculate_brown_score(img_rgb)
            
            return {
                'green_dominance': green_dominance,
                'blue_dominance': blue_dominance,
                'brown_score': brown_score
            }
        except Exception as e:
            print(f"Error analyzing colors: {e}")
            return {'green_dominance': 0, 'blue_dominance': 0, 'brown_score': 0}

    def _calculate_brown_score(self, img_rgb):
        """Calculate brown/earth tone score"""
        # Define brown color range in RGB
        brown_lower = np.array([50, 25, 0])
        brown_upper = np.array([150, 100, 50])
        
        # Create mask for brown colors
        brown_mask = cv2.inRange(img_rgb, brown_lower, brown_upper)
        brown_ratio = np.sum(brown_mask > 0) / (img_rgb.shape[0] * img_rgb.shape[1])
        
        return brown_ratio

    def detect_environmental_content(self, image_path):
        """Main function to analyze environmental content using Transfer Learning"""
        try:
            # Ensure model is loaded (lazy loading)
            self._ensure_model_loaded()
            
            # If model failed to load, use color analysis only
            if self.model is None:
                color_analysis = self.analyze_color_distribution(image_path)
                return self._fallback_analysis(color_analysis)
            
            # Preprocess image
            processed_img = self.preprocess_image(image_path)
            if processed_img is None:
                return self._create_default_result("Error processing image", image_path)
            
            # Get predictions from MobileNetV2
            predictions = self.model.predict(processed_img, verbose=0)
            decoded_predictions = decode_predictions(predictions, top=5)[0]
            
            # Analyze color distribution
            color_analysis = self.analyze_color_distribution(image_path)
            
            # Calculate environmental score
            environmental_score = self._calculate_environmental_score(
                decoded_predictions, color_analysis
            )
            
            # Determine risk level and confidence
            result = self._determine_risk_level(
                decoded_predictions, environmental_score, color_analysis
            )
            
            return result
            
        except Exception as e:
            print(f"Error in environmental detection: {e}")
            return self._create_default_result("Analysis failed", image_path)

    def _calculate_environmental_score(self, predictions, color_analysis):
        """Calculate how environmental the image is"""
        env_score = 0.0
        
        # Check predictions against environmental classes
        for class_name, confidence in predictions:
            class_lower = class_name.lower()
            for env_class in self.environmental_classes:
                if env_class in class_lower or class_lower in env_class:
                    env_score += confidence
                    break
        
        # Boost score based on color analysis
        if color_analysis['green_dominance'] > 0.3:  # High vegetation
            env_score += 0.2
        if color_analysis['blue_dominance'] > 0.25:  # Water/sky present
            env_score += 0.15
        if color_analysis['brown_score'] > 0.1:  # Earth tones
            env_score += 0.1
            
        return min(env_score, 1.0)

    def _determine_risk_level(self, predictions, env_score, color_analysis):
        """Determine risk level based on analysis"""
        
        # If not environmental content, return low risk
        if env_score < 0.15:
            return {
                'is_environmental': False,
                'risk_level': 'low',
                'confidence': int((1 - env_score) * 100),
                'analysis': 'Non-environmental content detected',
                'detected_objects': [pred[0] for pred in predictions[:3]]
            }
        
        # Check for critical environmental threats
        critical_score = 0.0
        high_risk_score = 0.0
        
        for class_name, confidence in predictions:
            class_lower = class_name.lower()
            
            # Check for critical threats
            for critical in self.critical_indicators:
                if critical in class_lower or any(word in class_lower for word in critical.split('_')):
                    critical_score += confidence
            
            # Check for high-risk indicators
            for high_risk in self.high_risk_indicators:
                if high_risk in class_lower or any(word in class_lower for word in high_risk.split('_')):
                    high_risk_score += confidence
        
        # Determine final risk level
        if critical_score > 0.3 or (env_score > 0.7 and 'fire' in str(predictions).lower()):
            risk_level = 'critical'
            confidence = int(min(90, (critical_score + env_score) * 100))
            analysis = 'Critical environmental threat detected'
        elif high_risk_score > 0.2 or (env_score > 0.5 and critical_score > 0.1):
            risk_level = 'high'
            confidence = int(min(85, (high_risk_score + env_score) * 80))
            analysis = 'High environmental risk detected'
        else:
            risk_level = 'low'
            confidence = int(min(95, env_score * 100))
            analysis = 'Environmental content with low risk'
        
        return {
            'is_environmental': True,
            'risk_level': risk_level,
            'confidence': confidence,
            'analysis': analysis,
            'detected_objects': [pred[0] for pred in predictions[:3]],
            'environmental_score': round(env_score, 2),
            'color_analysis': color_analysis
        }

    def _fallback_analysis(self, color_analysis):
        """Fallback analysis using only color analysis when AI model fails"""
        # Determine environmental likelihood based on colors only
        env_score = 0.0
        
        if color_analysis['green_dominance'] > 0.4:  # Strong vegetation
            env_score += 0.5
        elif color_analysis['green_dominance'] > 0.2:
            env_score += 0.3
            
        if color_analysis['blue_dominance'] > 0.3:  # Water/sky
            env_score += 0.4
        elif color_analysis['blue_dominance'] > 0.15:
            env_score += 0.2
            
        if color_analysis['brown_score'] > 0.15:  # Earth tones
            env_score += 0.3
        elif color_analysis['brown_score'] > 0.05:
            env_score += 0.15
            
        # Determine result based on color analysis
        if env_score > 0.4:
            return {
                'is_environmental': True,
                'risk_level': 'low',
                'confidence': min(int(env_score * 100), 85),
                'analysis': 'Environmental content detected (color analysis)',
                'detected_objects': ['Natural scene'],
                'environmental_score': round(env_score, 2),
                'color_analysis': color_analysis
            }
        else:
            return {
                'is_environmental': False,
                'risk_level': 'low',
                'confidence': max(60, int((1 - env_score) * 100)),
                'analysis': 'Non-environmental content (color analysis)',
                'detected_objects': ['Unknown'],
                'color_analysis': color_analysis
            }
    
    def _create_default_result(self, message, image_path=None):
        """Create default result for error cases with improved confidence calculation"""
        # Improved base confidence based on the type of error
        if "Error processing image" in message:
            # Image exists but can't be processed - medium confidence in "non-environmental"
            confidence = 65
        elif "Analysis failed" in message:
            # General analysis failure - still moderate confidence
            confidence = 60
        else:
            # Unknown error - base confidence
            confidence = 55
        
        # If we have image path, try color analysis for better confidence
        if image_path and os.path.exists(image_path):
            try:
                color_analysis = self.analyze_color_distribution(image_path)
                
                # Calculate environmental likelihood from colors
                env_score = 0.0
                if color_analysis['green_dominance'] > 0.3:
                    env_score += 0.4
                if color_analysis['blue_dominance'] > 0.25:
                    env_score += 0.3
                if color_analysis['brown_score'] > 0.1:
                    env_score += 0.2
                
                if env_score > 0.3:
                    # Looks environmental based on colors
                    confidence = max(60, min(85, int(env_score * 100)))
                    return {
                        'is_environmental': True,
                        'risk_level': 'low',
                        'confidence': confidence,
                        'analysis': 'Environmental content detected via color analysis',
                        'detected_objects': ['Natural scene'],
                        'color_analysis': color_analysis
                    }
                else:
                    # Doesn't look environmental based on colors
                    confidence = max(65, min(85, int((1 - env_score) * 90)))
            except:
                # If color analysis fails, stick with the message-based confidence
                pass
        elif image_path:
            # Image path provided but file doesn't exist - likely user error
            # Be more confident that this is a non-environmental situation
            confidence = 70
        
        return {
            'is_environmental': False,
            'risk_level': 'low',
            'confidence': confidence,
            'analysis': message,
            'detected_objects': []
        }

# Global instance
environmental_analyzer = EnvironmentalAnalyzer()
