"""
Sponsor management system for newsletter sponsor rotation
"""

import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class SponsorManager:
    """Manages sponsor rotation and tracking"""
    
    def __init__(self, sponsors: List[Dict], state_file: str = "data/sponsor_state.json"):
        self.sponsors = sponsors
        self.state_file = state_file
        self.current_index = 0
        self.rotation_history = []
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        
        # Load existing state
        self.load_state()
    
    def load_state(self):
        """Load sponsor rotation state from file"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                self.current_index = state.get('current_index', 0)
                self.rotation_history = state.get('rotation_history', [])
                
                # Validate index bounds
                if self.sponsors and self.current_index >= len(self.sponsors):
                    self.current_index = 0
                
                logger.info(f"Loaded sponsor state: index {self.current_index}")
            else:
                logger.info("No existing sponsor state found, starting fresh")
        except Exception as e:
            logger.error(f"Failed to load sponsor state: {e}")
            self.current_index = 0
            self.rotation_history = []
    
    def save_state(self):
        """Save sponsor rotation state to file"""
        try:
            state = {
                'current_index': self.current_index,
                'rotation_history': self.rotation_history,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            logger.debug("Sponsor state saved")
        except Exception as e:
            logger.error(f"Failed to save sponsor state: {e}")
    
    def get_current_sponsor(self) -> Optional[Dict]:
        """
        Get the current sponsor
        
        Returns:
            Dictionary with sponsor information or None if no sponsors
        """
        try:
            if not self.sponsors:
                logger.warning("No sponsors configured")
                return None
            
            if self.current_index >= len(self.sponsors):
                logger.warning(f"Invalid sponsor index {self.current_index}, resetting to 0")
                self.current_index = 0
                self.save_state()
            
            current_sponsor = self.sponsors[self.current_index].copy()
            
            # Add rotation metadata
            current_sponsor['_rotation_info'] = {
                'index': self.current_index,
                'total_sponsors': len(self.sponsors),
                'last_rotated': self.rotation_history[-1] if self.rotation_history else None
            }
            
            logger.debug(f"Current sponsor: {current_sponsor.get('name', 'Unknown')}")
            return current_sponsor
            
        except Exception as e:
            logger.error(f"Failed to get current sponsor: {e}")
            return None
    
    def rotate_sponsor(self) -> Optional[Dict]:
        """
        Rotate to the next sponsor
        
        Returns:
            New current sponsor or None if no sponsors
        """
        try:
            if not self.sponsors:
                logger.warning("No sponsors to rotate")
                return None
            
            # Record current rotation
            old_index = self.current_index
            old_sponsor = self.sponsors[old_index] if old_index < len(self.sponsors) else None
            
            # Move to next sponsor
            self.current_index = (self.current_index + 1) % len(self.sponsors)
            
            # Record rotation in history
            rotation_record = {
                'timestamp': datetime.now().isoformat(),
                'from_index': old_index,
                'to_index': self.current_index,
                'from_sponsor': old_sponsor.get('name', 'Unknown') if old_sponsor else None,
                'to_sponsor': self.sponsors[self.current_index].get('name', 'Unknown')
            }
            
            self.rotation_history.append(rotation_record)
            
            # Keep only last 100 rotations
            if len(self.rotation_history) > 100:
                self.rotation_history = self.rotation_history[-100:]
            
            # Save state
            self.save_state()
            
            new_sponsor = self.get_current_sponsor()
            logger.info(f"Rotated sponsor: {rotation_record['from_sponsor']} -> {rotation_record['to_sponsor']}")
            
            return new_sponsor
            
        except Exception as e:
            logger.error(f"Failed to rotate sponsor: {e}")
            return None
    
    def get_sponsor_by_name(self, name: str) -> Optional[Dict]:
        """
        Get sponsor by name
        
        Args:
            name: Sponsor name to search for
        
        Returns:
            Sponsor dictionary or None if not found
        """
        try:
            for sponsor in self.sponsors:
                if sponsor.get('name', '').lower() == name.lower():
                    return sponsor.copy()
            
            logger.warning(f"Sponsor not found: {name}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get sponsor by name: {e}")
            return None
    
    def set_current_sponsor(self, name: str) -> bool:
        """
        Set current sponsor by name
        
        Args:
            name: Sponsor name to set as current
        
        Returns:
            True if successful, False otherwise
        """
        try:
            for i, sponsor in enumerate(self.sponsors):
                if sponsor.get('name', '').lower() == name.lower():
                    old_index = self.current_index
                    self.current_index = i
                    
                    # Record manual change
                    rotation_record = {
                        'timestamp': datetime.now().isoformat(),
                        'from_index': old_index,
                        'to_index': self.current_index,
                        'from_sponsor': self.sponsors[old_index].get('name', 'Unknown') if old_index < len(self.sponsors) else None,
                        'to_sponsor': sponsor.get('name', 'Unknown'),
                        'manual': True
                    }
                    
                    self.rotation_history.append(rotation_record)
                    self.save_state()
                    
                    logger.info(f"Manually set current sponsor to: {name}")
                    return True
            
            logger.warning(f"Sponsor not found for manual setting: {name}")
            return False
            
        except Exception as e:
            logger.error(f"Failed to set current sponsor: {e}")
            return False
    
    def get_rotation_stats(self) -> Dict:
        """Get sponsor rotation statistics"""
        try:
            if not self.sponsors:
                return {'error': 'No sponsors configured'}
            
            # Count rotations per sponsor
            sponsor_counts = {}
            for record in self.rotation_history:
                sponsor_name = record.get('to_sponsor', 'Unknown')
                sponsor_counts[sponsor_name] = sponsor_counts.get(sponsor_name, 0) + 1
            
            # Get last rotation
            last_rotation = self.rotation_history[-1] if self.rotation_history else None
            
            return {
                'total_sponsors': len(self.sponsors),
                'current_sponsor_index': self.current_index,
                'current_sponsor_name': self.sponsors[self.current_index].get('name', 'Unknown'),
                'total_rotations': len(self.rotation_history),
                'sponsor_usage_counts': sponsor_counts,
                'last_rotation': last_rotation
            }
            
        except Exception as e:
            logger.error(f"Failed to get rotation stats: {e}")
            return {'error': str(e)}
    
    def validate_sponsors(self) -> List[str]:
        """
        Validate sponsor configuration
        
        Returns:
            List of validation errors
        """
        errors = []
        
        if not self.sponsors:
            errors.append("No sponsors configured")
            return errors
        
        required_fields = ['name', 'message']
        
        for i, sponsor in enumerate(self.sponsors):
            for field in required_fields:
                if not sponsor.get(field):
                    errors.append(f"Sponsor {i+1}: Missing required field '{field}'")
            
            # Validate optional fields
            if 'link' in sponsor and not sponsor['link'].startswith(('http://', 'https://')):
                errors.append(f"Sponsor {i+1}: Invalid link format")
        
        return errors

# Default sponsors for testing
DEFAULT_SPONSORS = [
    {
        "name": "Visit St. Pete Clearwater",
        "message": "This issue is sponsored by Visit St. Pete Clearwater — where sunshine meets sophistication. Learn more about hosting your next meeting in paradise.",
        "link": "https://www.visitstpeteclearwater.com/meetings"
    },
    {
        "name": "Meet Boston",
        "message": "Discover why Boston is the perfect destination for your next meeting or event. Rich history, world-class venues, and unmatched hospitality await.",
        "link": "https://www.meetboston.com"
    },
    {
        "name": "Visit Orlando",
        "message": "Orlando offers more than theme parks — discover world-class meeting facilities, diverse dining, and endless entertainment options.",
        "link": "https://www.visitorlando.com/meetings"
    }
]

if __name__ == "__main__":
    # Test the sponsor manager
    logging.basicConfig(level=logging.INFO)
    
    manager = SponsorManager(DEFAULT_SPONSORS, "data/test_sponsor_state.json")
    
    print("Testing sponsor rotation...")
    
    # Get current sponsor
    current = manager.get_current_sponsor()
    print(f"Current sponsor: {current.get('name') if current else 'None'}")
    
    # Rotate through sponsors
    for i in range(5):
        next_sponsor = manager.rotate_sponsor()
        print(f"Rotation {i+1}: {next_sponsor.get('name') if next_sponsor else 'None'}")
    
    # Get stats
    stats = manager.get_rotation_stats()
    print(f"Stats: {json.dumps(stats, indent=2)}")
    
    # Validate sponsors
    errors = manager.validate_sponsors()
    print(f"Validation errors: {errors}")
