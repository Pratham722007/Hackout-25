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
        # Load pre-trained MobileNetV2 model
        self.model = MobileNetV2(weights='imagenet', include_top=True)
        
        # Environmental keywords from ImageNet classes
        self.environmental_classes = {
            # Nature and Wildlife
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
            # Preprocess image
            processed_img = self.preprocess_image(image_path)
            if processed_img is None:
                return self._create_default_result("Error processing image")
            
            # Get predictions from MobileNetV2
            predictions = self.model.predict(processed_img)
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
            return self._create_default_result("Analysis failed")

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

    def _create_default_result(self, message):
        """Create default result for error cases"""
        return {
            'is_environmental': False,
            'risk_level': 'low',
            'confidence': 0,
            'analysis': message,
            'detected_objects': []
        }

# Global instance
environmental_analyzer = EnvironmentalAnalyzer()
