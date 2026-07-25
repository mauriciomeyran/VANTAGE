"""
Facial Analyzer Module

This module provides functionality for analyzing facial geometry and classifying face shapes
based on landmark proportions using MediaPipe face mesh data.
"""

import numpy as np
from typing import Tuple, Optional
from scipy.spatial.distance import euclidean


class FacialAnalyzer:
    """
    Analyzes facial geometry from MediaPipe face mesh landmarks to classify face shapes.
    
    This class calculates various geometric ratios from facial landmarks to determine
    the face shape category (Heart, Square, Round, or Oval).
    """
    
    def __init__(self):
        """Initialize the FacialAnalyzer with default thresholds."""
        # Thresholds for face shape classification
        self.cheek_to_jaw_threshold = 0.85
        self.forehead_to_chin_threshold = 0.9
        
    def analyze_shape(self, landmarks: np.ndarray, image_width: int, image_height: int) -> str:
        """
        Analyze face shape from normalized landmarks.
        
        Args:
            landmarks: numpy array of shape (478, 3) containing normalized landmark coordinates
            image_width: width of the image in pixels
            image_height: height of the image in pixels
            
        Returns:
            str: Face shape classification ("Heart", "Square", "Round", or "Oval")
            
        Raises:
            ValueError: If landmarks array is invalid or insufficient
        """
        if landmarks is None or len(landmarks) < 478:
            raise ValueError("Invalid or insufficient landmarks provided")
            
        # Convert normalized landmarks to pixel coordinates
        pixel_landmarks = self._normalize_to_pixel(landmarks, image_width, image_height)
        
        # Calculate key geometric ratios
        cheek_to_jaw_ratio = self._calculate_cheek_to_jaw_ratio(pixel_landmarks)
        forehead_to_chin_ratio = self._calculate_forehead_to_chin_ratio(pixel_landmarks)
        
        # Classify face shape based on ratios
        return self._classify_face_shape(cheek_to_jaw_ratio, forehead_to_chin_ratio)
    
    def _normalize_to_pixel(self, landmarks: np.ndarray, width: int, height: int) -> np.ndarray:
        """
        Convert normalized landmark coordinates to pixel coordinates.
        
        Args:
            landmarks: normalized landmark coordinates (0-1 range)
            width: image width in pixels
            height: image height in pixels
            
        Returns:
            numpy array with pixel coordinates
        """
        pixel_landmarks = landmarks.copy()
        pixel_landmarks[:, 0] *= width
        pixel_landmarks[:, 1] *= height
        return pixel_landmarks
    
    def _calculate_cheek_to_jaw_ratio(self, landmarks: np.ndarray) -> float:
        """
        Calculate the ratio between cheek width and jaw width.
        
        Uses landmark indices:
        - Cheek: 234 (left cheek), 454 (right cheek)
        - Jaw: 172 (left jaw), 396 (right jaw)
        
        Args:
            landmarks: pixel coordinate landmarks
            
        Returns:
            float: cheek to jaw width ratio
        """
        # Left and right cheek points
        left_cheek = landmarks[234][:2]  # x, y coordinates
        right_cheek = landmarks[454][:2]
        
        # Left and right jaw points
        left_jaw = landmarks[172][:2]
        right_jaw = landmarks[396][:2]
        
        # Calculate widths using Euclidean distance
        cheek_width = euclidean(left_cheek, right_cheek)
        jaw_width = euclidean(left_jaw, right_jaw)
        
        if jaw_width == 0:
            return 1.0
            
        return cheek_width / jaw_width
    
    def _calculate_forehead_to_chin_ratio(self, landmarks: np.ndarray) -> float:
        """
        Calculate the ratio between forehead width and chin width.
        
        Uses landmark indices:
        - Forehead: 10 (top center), 338 (right forehead), 109 (left forehead)
        - Chin: 152 (chin tip), 377 (right chin), 148 (left chin)
        
        Args:
            landmarks: pixel coordinate landmarks
            
        Returns:
            float: forehead to chin width ratio
        """
        # Forehead width (using outer points)
        left_forehead = landmarks[109][:2]
        right_forehead = landmarks[338][:2]
        
        # Chin width (using outer points)
        left_chin = landmarks[148][:2]
        right_chin = landmarks[377][:2]
        
        # Calculate widths
        forehead_width = euclidean(left_forehead, right_forehead)
        chin_width = euclidean(left_chin, right_chin)
        
        if chin_width == 0:
            return 1.0
            
        return forehead_width / chin_width
    
    def _classify_face_shape(self, cheek_to_jaw: float, forehead_to_chin: float) -> str:
        """
        Classify face shape based on calculated ratios.
        
        Classification logic:
        - Heart: High forehead_to_chin ratio, moderate cheek_to_jaw
        - Square: Low cheek_to_jaw ratio, low forehead_to_chin ratio
        - Round: High cheek_to_jaw ratio, moderate forehead_to_chin ratio
        - Oval: Balanced ratios (default)
        
        Args:
            cheek_to_jaw: cheek to jaw width ratio
            forehead_to_chin: forehead to chin width ratio
            
        Returns:
            str: Face shape classification
        """
        # Heart shape: wider forehead than chin
        if forehead_to_chin > self.forehead_to_chin_threshold:
            if cheek_to_jaw > self.cheek_to_jaw_threshold:
                return "Heart"
        
        # Square shape: similar forehead and chin width, strong jaw
        if cheek_to_jaw < self.cheek_to_jaw_threshold and forehead_to_chin < self.forehead_to_chin_threshold:
            return "Square"
        
        # Round shape: wider cheeks relative to jaw
        if cheek_to_jaw > self.cheek_to_jaw_threshold:
            return "Round"
        
        # Default to Oval for balanced proportions
        return "Oval"