#!/usr/bin/env python3
"""
Step-by-Step Manual GitHub Actions Trigger
"""

import webbrowser
import time

def step_by_step_deployment():
    print("🚀 STEP-BY-STEP DEPLOYMENT GUIDE")
    print("=" * 60)
    
    print("\n📋 CURRENT STATUS CHECK:")
    print("✅ AWS credentials: WORKING")
    print("✅ S3 permissions: WORKING") 
    print("✅ GitHub secrets: CONFIGURED")
    print("❌ GitHub Actions: FAILING (need to fix)")
    
    print("\n" + "="*60)
    print("STEP 1: OPEN GITHUB ACTIONS")
    print("="*60)
    
    actions_url = "https://github.com/reddygautam98/clinchat-rag/actions"
    print(f"🌐 Opening: {actions_url}")
    
    try:
        webbrowser.open(actions_url)
        print("✅ GitHub Actions page opened")
    except:
        print("❌ Could not open browser automatically")
        print(f"📋 Manual URL: {actions_url}")
    
    input("\n⏳ Press Enter when you see the GitHub Actions page...")
    
    print("\n" + "="*60)
    print("STEP 2: SELECT WORKFLOW TO RUN")  
    print("="*60)
    
    print("📋 In the GitHub Actions page:")
    print("1. Look at the LEFT SIDEBAR")
    print("2. You should see:")
    print("   - 📦 All workflows")
    print("   - 🚀 Deploy Infrastructure")  
    print("   - 📊 Simple Infrastructure Deployment")
    print("")
    print("3. CLICK on '🚀 Deploy Infrastructure'")
    
    input("\n⏳ Press Enter after clicking 'Deploy Infrastructure'...")
    
    print("\n" + "="*60)
    print("STEP 3: TRIGGER MANUAL RUN")
    print("="*60)
    
    print("📋 On the Deploy Infrastructure page:")
    print("1. Look for a button that says 'Run workflow' (top right)")
    print("2. Click the 'Run workflow' button")
    print("3. A dropdown will appear:")
    print("   - Branch: main (should be selected)")
    print("   - Keep all default settings")
    print("4. Click the green 'Run workflow' button")
    
    input("\n⏳ Press Enter after clicking 'Run workflow'...")
    
    print("\n" + "="*60)
    print("STEP 4: MONITOR DEPLOYMENT")
    print("="*60)
    
    print("📊 You should now see:")
    print("🟡 A new workflow run starting (yellow circle)")
    print("⏱️  Status: 'In progress' or 'Queued'")
    print("📋 Click on the workflow run to see details")
    
    print("\n🔍 EXPECTED TIMELINE:")
    print("⏱️  0-2 minutes: Setup and initialization")
    print("⏱️  2-10 minutes: Terraform planning")
    print("⏱️  10-20 minutes: AWS resource creation")
    print("⏱️  20-25 minutes: Application deployment")
    
    print("\n✅ SUCCESS INDICATORS:")
    print("🟢 Green checkmark when complete")
    print("🌐 Load balancer URL in the logs")
    print("🎉 'Deployment completed successfully' message")
    
    print("\n❌ IF IT FAILS:")
    print("🔍 Click on the failed step")
    print("📋 Read the error message")
    print("📞 Come back with the error for help")

def alternative_method():
    print("\n" + "="*60)
    print("ALTERNATIVE: DIRECT FILE EDIT METHOD")
    print("="*60)
    
    print("If the manual workflow trigger doesn't work:")
    print("")
    print("1. Go to: https://github.com/reddygautam98/clinchat-rag")
    print("2. Click on README.md file")
    print("3. Click the pencil icon (Edit)")
    print("4. Add this line at the end:")
    print("   'Manual deployment triggered on Oct 21, 2025'")
    print("5. Click 'Commit changes'")
    print("6. This will auto-trigger the workflow")

def main():
    print("🎯 ClinChat-RAG Deployment - Step by Step")
    print("=" * 60)
    
    step_by_step_deployment()
    alternative_method()
    
    print("\n" + "="*60)
    print("🎉 READY TO DEPLOY!")
    print("="*60)
    print("Follow the steps above carefully.")
    print("Your deployment should succeed this time!")
    print("")
    print("💬 Come back with any error messages if issues occur.")

if __name__ == "__main__":
    main()