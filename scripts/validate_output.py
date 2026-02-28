#!/usr/bin/env python3
"""
Validate enriched EPG output
Checks that enrichment was applied correctly to XMLTV data
"""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def validate_xmltv(xml_path):
    """Validate XMLTV structure and content."""
    if not Path(xml_path).exists():
        print(f"❌ File not found: {xml_path}")
        return False
    
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        if root.tag != "tv":
            print(f"❌ Invalid root element: {root.tag} (expected 'tv')")
            return False
        
        programmes = root.findall("programme")
        print(f"✅ Valid XMLTV with {len(programmes)} programmes")
        
        # Check programme structure
        for idx, prog in enumerate(programmes, 1):
            title = prog.find("title")
            if title is None or not title.text:
                print(f"⚠️  Programme {idx} missing title")
            
            category = prog.find("category")
            if category is None:
                print(f"⚠️  Programme {idx} missing category")
            
            # Check for enrichment indicators
            has_episode = prog.find("episode-num") is not None
            has_credits = prog.find("credits") is not None
            
            if idx == 1:
                if has_episode:
                    print("✅ Episode metadata detected")
                if has_credits:
                    print("✅ Cast/crew metadata detected")
        
        return True
    
    except ET.ParseError as e:
        print(f"❌ XML parse error: {e}")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_output.py <xmltv-file>")
        sys.exit(1)
    
    success = validate_xmltv(sys.argv[1])
    sys.exit(0 if success else 1)
