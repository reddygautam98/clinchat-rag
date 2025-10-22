#!/usr/bin/env python3
"""
AWS Policy Usage Check Guide
Step-by-step instructions to check policy usage in AWS Console
"""

import webbrowser

def show_policy_check_guide():
    print("🔍 AWS Policy Usage Check Guide")
    print("=" * 60)
    
    print("\n📋 MULTIPLE METHODS TO CHECK POLICY USAGE:")
    
    print("\n" + "="*60)
    print("METHOD 1: CHECK SPECIFIC USER POLICIES")
    print("="*60)
    
    print("1. Go to AWS Console: https://console.aws.amazon.com/")
    print("2. Search for 'IAM' and click on IAM service")
    print("3. In left sidebar, click 'Users'")
    print("4. Find and click your user: 'clinchat-github-actions'")
    print("5. Click 'Permissions' tab")
    print("6. You'll see:")
    print("   - 'Permissions policies (9)' section")
    print("   - All attached policies listed")
    print("   - Policy names, types, and attachment method")
    
    print("\n" + "="*60)
    print("METHOD 2: POLICY USAGE ANALYZER")
    print("="*60)
    
    print("1. In IAM Console, click 'Policies' (left sidebar)")
    print("2. Search for a specific policy (e.g., 'AmazonS3FullAccess')")
    print("3. Click on the policy name")
    print("4. Click 'Policy usage' tab")
    print("5. You'll see:")
    print("   - Which users have this policy")
    print("   - Which roles have this policy") 
    print("   - Which groups have this policy")
    print("   - Last activity information")
    
    print("\n" + "="*60)
    print("METHOD 3: ACCESS ANALYZER")
    print("="*60)
    
    print("1. In IAM Console, click 'Access analyzer' (left sidebar)")
    print("2. Click 'Policy validation'")
    print("3. This shows:")
    print("   - Policy usage warnings")
    print("   - Unused permissions")
    print("   - Security recommendations")
    
    print("\n" + "="*60)
    print("METHOD 4: CREDENTIAL REPORT")
    print("="*60)
    
    print("1. In IAM Console, click 'Credential report' (left sidebar)")
    print("2. Click 'Generate report' if needed")
    print("3. Download the CSV report")
    print("4. Shows:")
    print("   - All users and their access keys")
    print("   - Last used information")
    print("   - MFA status")
    
    print("\n" + "="*60)
    print("METHOD 5: CLOUDTRAIL (ADVANCED)")
    print("="*60)
    
    print("1. Search for 'CloudTrail' in AWS Console")
    print("2. Go to 'Event history'")
    print("3. Filter by:")
    print("   - User name: clinchat-github-actions")
    print("   - Time range: Last 30 days")
    print("4. See actual API calls and permissions used")

def open_iam_console():
    """Open IAM console for hands-on checking."""
    
    print("\n" + "="*60)
    print("🚀 HANDS-ON DEMONSTRATION")
    print("="*60)
    
    iam_url = "https://console.aws.amazon.com/iam/home#/users/clinchat-github-actions"
    
    print(f"🌐 Opening your user's permissions page...")
    print(f"   URL: {iam_url}")
    
    try:
        webbrowser.open(iam_url)
        print("✅ IAM Console opened - you should see your user's permissions")
    except Exception as e:
        print(f"❌ Could not open browser: {e}")
        print(f"📋 Manual URL: {iam_url}")
    
    print("\n📋 WHAT YOU'LL SEE:")
    print("1. User summary at the top")
    print("2. 'Permissions' tab (should be selected)")
    print("3. 'Permissions policies (9)' section")
    print("4. List of all your 9 attached policies")
    print("5. Each policy shows:")
    print("   - Policy name (clickable)")
    print("   - Type (AWS managed)")
    print("   - Attached via (Directly)")

def show_specific_checks():
    """Show how to check specific policy details."""
    
    print("\n" + "="*60)
    print("🔍 CHECK SPECIFIC POLICY USAGE")
    print("="*60)
    
    print("To see WHO is using a specific policy:")
    print("")
    print("1. Go to IAM > Policies")
    print("2. Search for policy name (e.g., 'AmazonS3FullAccess')")
    print("3. Click on the policy name")
    print("4. Click 'Policy usage' tab")
    print("5. You'll see:")
    print("   📊 Usage summary")
    print("   👥 Users with this policy")
    print("   🏷️  Groups with this policy")
    print("   🎭 Roles with this policy")
    
    print("\n📋 EXAMPLE: Check S3 Policy Usage")
    s3_policy_url = "https://console.aws.amazon.com/iam/home#/policies/arn:aws:iam::aws:policy/AmazonS3FullAccess"
    print(f"🔗 Direct link: {s3_policy_url}")

def main():
    print("🎯 AWS Policy Usage Check - Complete Guide")
    print("=" * 60)
    
    show_policy_check_guide()
    open_iam_console()
    show_specific_checks()
    
    print("\n" + "="*60)
    print("🎯 QUICK SUMMARY FOR YOUR ACCOUNT")
    print("="*60)
    print("👤 User: clinchat-github-actions")
    print("📊 Policies: 9 attached")
    print("🔗 Direct link to your permissions:")
    print("   https://console.aws.amazon.com/iam/home#/users/clinchat-github-actions")
    
    print("\n💡 PRO TIPS:")
    print("• Click any policy name to see its JSON document")
    print("• Use 'Policy usage' tab to see who else has the policy")  
    print("• Check 'Access advisor' tab to see unused permissions")
    print("• Generate credential reports for account-wide overview")

if __name__ == "__main__":
    main()