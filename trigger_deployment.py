#!/usr/bin/env python3
"""
AWS Infrastructure Deployment Trigger
Starts GitHub Actions workflow for ClinChat-RAG
"""

import subprocess
import webbrowser
import time

def trigger_github_deployment():
    """Open GitHub Actions page to manually trigger deployment"""
    
    print("🚀 TRIGGERING AWS INFRASTRUCTURE DEPLOYMENT")
    print("=" * 50)
    
    # Open GitHub Actions workflow page
    actions_url = "https://github.com/reddygautam98/clinchat-rag/actions"
    
    print("📍 Opening GitHub Actions page...")
    webbrowser.open(actions_url)
    
    print()
    print("🔧 MANUAL TRIGGER STEPS:")
    print("1. Look for 'Infrastructure Deployment' workflow")
    print("2. Click 'Run workflow' button")
    print("3. Select environment: 'staging'")
    print("4. Select action: 'apply'") 
    print("5. Click 'Run workflow' to start")
    print()
    
    print("⏱️  EXPECTED DEPLOYMENT TIME: 15-20 minutes")
    print()
    print("📊 MONITOR PROGRESS:")
    print(f"   {actions_url}")
    print()
    
    # Also provide git push option
    print("🔄 ALTERNATIVE - TRIGGER VIA CODE PUSH:")
    print("   Any push to main branch will trigger deployment")
    print("   Run: git add . && git commit -m 'trigger deployment' && git push")
    print()

if __name__ == "__main__":
    trigger_github_deployment()
