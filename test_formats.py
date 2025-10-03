#!/usr/bin/env python3
"""
Test script demonstrating different video format options for the Veo3 API
"""

import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_video_format(prompt, aspect_ratio, description):
    """Test video generation with specific format"""
    
    payload = {
        "prompt": prompt,
        "duration": 8,
        "resolution": "1080p",
        "quality": "high",
        "aspect_ratio": aspect_ratio,
        "fps": 30,
        "format": "mp4"
    }
    
    print(f"\n🎬 Testing {description}")
    print(f"   Aspect Ratio: {aspect_ratio}")
    print(f"   Prompt: {prompt}")
    
    # Generate video
    response = requests.post(f"{API_BASE}/generate", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        task_id = result["task_id"]
        print(f"   ✅ Task ID: {task_id}")
        
        # Wait and check status
        time.sleep(6)
        status_response = requests.get(f"{API_BASE}/status/{task_id}")
        
        if status_response.status_code == 200:
            status = status_response.json()
            print(f"   📊 Status: {status['status']}")
            if status.get('video_url'):
                print(f"   🎥 Video URL: {status['video_url']}")
        else:
            print(f"   ❌ Error checking status: {status_response.text}")
    else:
        print(f"   ❌ Error: {response.text}")

def main():
    print("🚀 Veo3 Video Format Testing")
    print("=" * 50)
    
    # Test different formats
    formats_to_test = [
        {
            "prompt": "A cat playing with a ball", 
            "aspect_ratio": "9:16", 
            "description": "Mobile/TikTok Format (9:16)"
        },
        {
            "prompt": "Food preparation in a kitchen", 
            "aspect_ratio": "1:1", 
            "description": "Instagram Square (1:1)"
        },
        {
            "prompt": "Landscape nature scenery", 
            "aspect_ratio": "16:9", 
            "description": "Standard Landscape (16:9)"
        },
        {
            "prompt": "Cinematic car chase scene", 
            "aspect_ratio": "21:9", 
            "description": "Cinematic Widescreen (21:9)"
        }
    ]
    
    for test_case in formats_to_test:
        test_video_format(
            test_case["prompt"], 
            test_case["aspect_ratio"], 
            test_case["description"]
        )
        time.sleep(1)  # Small delay between requests
    
    print("\n✨ Testing completed!")
    print(f"\n📖 View API documentation at: {API_BASE}/docs")

if __name__ == "__main__":
    main()