#!/usr/bin/env python3
"""
Comprehensive Test Suite for Fusion AI Technology
Tests Google Gemini + Groq Cloud intelligent combination
"""

import asyncio
import requests
import json
import time
from datetime import datetime
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test both engines
FUSION_API_URL = "http://localhost:8003"  # Fusion AI API

def test_fusion_api_health():
    """Test Fusion AI API health"""
    print("🔍 Testing Fusion AI API Health...")
    
    try:
        response = requests.get(f"{FUSION_API_URL}/health")
        if response.status_code == 200:
            health = response.json()
            print("✅ Fusion AI API Health Check Passed!")
            print(f"   Status: {health['status']}")
            print(f"   Version: {health['version']}")
            print(f"   Fusion AI Enabled: {health['fusion_ai_enabled']}")
            
            print("   🤖 Providers Available:")
            for provider, status in health['providers_available'].items():
                icon = "✅" if status else "❌"
                print(f"     {icon} {provider}")
            
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_fusion_capabilities():
    """Test Fusion AI capabilities endpoint"""
    print("\n🔮 Testing Fusion AI Capabilities...")
    
    try:
        response = requests.get(f"{FUSION_API_URL}/fusion/capabilities")
        if response.status_code == 200:
            caps = response.json()
            print("✅ Fusion AI Capabilities Retrieved!")
            
            print(f"   📊 Providers:")
            for provider, info in caps['providers'].items():
                print(f"     • {provider.upper()}: {info['model']}")
                print(f"       Optimal for: {', '.join(info['optimal_for'])}")
            
            print(f"   🎯 Analysis Types: {len(caps['analysis_types'])}")
            print(f"   ⚡ Fusion Strategies: {len(caps['fusion_strategies'])}")
            
            return True
        else:
            print(f"❌ Capabilities test failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Capabilities error: {e}")
        return False

def test_fusion_analysis_types():
    """Test different Fusion AI analysis types"""
    print("\n🏥 Testing Fusion AI Analysis Types...")
    
    # Clinical test case
    clinical_text = """
    Patient: 72-year-old female with history of CAD, diabetes, hypertension
    Chief Complaint: Acute onset severe chest pain, 3 hours duration
    Present Illness: Sharp, substernal chest pain radiating to left arm and jaw
    Vitals: BP 200/110, HR 120, RR 24, O2Sat 88% on RA, Temp 98.6°F
    Physical: Diaphoretic, anxious, JVD present, bilateral crackles
    ECG: ST elevations in V1-V6, new LBBB
    Labs: Troponin I 25.8 ng/mL, BNP 2,800 pg/mL, Cr 1.8 mg/dL
    Assessment: STEMI with cardiogenic shock
    """
    
    # Test cases with different analysis types
    test_cases = [
        {
            "name": "Quick Triage",
            "analysis_type": "quick_triage",
            "urgency": "normal",
            "endpoint": "/fusion/quick-triage"
        },
        {
            "name": "Emergency Assessment", 
            "analysis_type": "emergency_assessment",
            "urgency": "emergency",
            "endpoint": "/fusion/emergency"
        },
        {
            "name": "Diagnostic Reasoning",
            "analysis_type": "diagnostic_reasoning", 
            "urgency": "normal",
            "endpoint": "/fusion/analyze"
        },
        {
            "name": "Treatment Planning",
            "analysis_type": "treatment_planning",
            "urgency": "normal", 
            "endpoint": "/fusion/analyze"
        }
    ]
    
    results = {}
    
    for test_case in test_cases:
        print(f"\n   🔬 Testing: {test_case['name']}")
        
        payload = {
            "text": clinical_text,
            "analysis_type": test_case["analysis_type"],
            "urgency": test_case["urgency"],
            "include_entities": True
        }
        
        try:
            start_time = time.time()
            response = requests.post(f"{FUSION_API_URL}{test_case['endpoint']}", json=payload)
            total_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"     ✅ Success! ({total_time:.2f}s total)")
                
                if 'fusion_strategy' in result:
                    print(f"     Strategy: {result['fusion_strategy']}")
                    print(f"     Primary: {result['primary_provider']}")
                    if result.get('secondary_provider'):
                        print(f"     Secondary: {result['secondary_provider']}")
                    print(f"     Confidence: {result['confidence_score']:.1%}")
                    print(f"     Processing: {result['processing_time']:.2f}s")
                
                # Show analysis preview
                analysis_key = 'consensus_analysis' if 'consensus_analysis' in result else 'analysis'
                if analysis_key in result:
                    preview = result[analysis_key][:150]
                    print(f"     Preview: {preview}...")
                
                results[test_case['name']] = {
                    "success": True,
                    "time": total_time,
                    "strategy": result.get('fusion_strategy', 'N/A'),
                    "confidence": result.get('confidence_score', 0)
                }
                
            else:
                print(f"     ❌ Failed: {response.status_code}")
                results[test_case['name']] = {"success": False, "error": response.status_code}
                
        except Exception as e:
            print(f"     ❌ Error: {e}")
            results[test_case['name']] = {"success": False, "error": str(e)}
    
    return results

def test_fusion_performance():
    """Test Fusion AI performance across different scenarios"""
    print("\n⚡ Testing Fusion AI Performance...")
    
    test_scenarios = [
        {
            "name": "Emergency Speed Test",
            "text": "Patient unconscious, no pulse, CPR in progress",
            "analysis_type": "emergency_assessment",
            "urgency": "emergency"
        },
        {
            "name": "Complex Diagnostic Case",
            "text": """
            45-year-old male with 6-month history of progressive fatigue, weight loss (20 lbs), 
            night sweats, and intermittent fever. Physical exam reveals splenomegaly, 
            lymphadenopathy, and pallor. CBC shows WBC 150,000, Hgb 7.2, platelets 50,000.
            Flow cytometry pending. Considering hematologic malignancy.
            """,
            "analysis_type": "diagnostic_reasoning",
            "urgency": "normal"
        },
        {
            "name": "Quick Triage Scenario",
            "text": "Patient with minor ankle sprain, stable vitals, ambulating",
            "analysis_type": "quick_triage",
            "urgency": "normal"
        }
    ]
    
    performance_results = []
    
    for scenario in test_scenarios:
        print(f"\n   📊 {scenario['name']}:")
        
        payload = {
            "text": scenario["text"],
            "analysis_type": scenario["analysis_type"],
            "urgency": scenario["urgency"],
            "include_entities": False  # Skip entities for speed test
        }
        
        try:
            start_time = time.time()
            response = requests.post(f"{FUSION_API_URL}/fusion/analyze", json=payload)
            total_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                performance_results.append({
                    "scenario": scenario['name'],
                    "total_time": total_time,
                    "processing_time": result.get('processing_time', 0),
                    "strategy": result.get('fusion_strategy', 'unknown'),
                    "primary": result.get('primary_provider', 'unknown'),
                    "confidence": result.get('confidence_score', 0)
                })
                
                print(f"     ⏱️ Total Time: {total_time:.3f}s")
                print(f"     🔮 Strategy: {result.get('fusion_strategy')}")
                print(f"     🎯 Confidence: {result.get('confidence_score', 0):.1%}")
                
            else:
                print(f"     ❌ Failed: {response.status_code}")
                
        except Exception as e:
            print(f"     ❌ Error: {e}")
    
    # Performance summary
    if performance_results:
        print(f"\n   📈 Performance Summary:")
        avg_time = sum(r['total_time'] for r in performance_results) / len(performance_results)
        avg_confidence = sum(r['confidence'] for r in performance_results) / len(performance_results)
        
        print(f"     Average Response Time: {avg_time:.3f}s")
        print(f"     Average Confidence: {avg_confidence:.1%}")
        
        fastest = min(performance_results, key=lambda x: x['total_time'])
        print(f"     Fastest: {fastest['scenario']} ({fastest['total_time']:.3f}s)")
    
    return performance_results

def test_real_world_scenarios():
    """Test real-world clinical scenarios"""
    print("\n🌟 Testing Real-World Clinical Scenarios...")
    
    scenarios = [
        {
            "name": "Pediatric Emergency",
            "text": """
            3-year-old brought by parents for high fever (104°F), difficulty breathing,
            and decreased activity for 2 days. Child appears toxic, lethargic.
            Vitals: HR 180, RR 40, O2Sat 92%. Retractions present.
            Possible sepsis vs pneumonia vs meningitis.
            """,
            "expected_urgency": "emergency"
        },
        {
            "name": "Psychiatric Crisis",
            "text": """
            28-year-old male brought by police, agitated and confused.
            History of bipolar disorder, medication non-compliance.
            Threatening self-harm, paranoid delusions present.
            Vitals stable but requires immediate psychiatric evaluation.
            """,
            "expected_urgency": "urgent"
        },
        {
            "name": "Chronic Disease Management",
            "text": """
            65-year-old with diabetes, hypertension, and CKD for routine follow-up.
            HbA1c 7.2%, BP 135/85, eGFR 45. Medication adherence good.
            Discussing insulin adjustment and nephrology referral.
            """,
            "expected_urgency": "routine"
        }
    ]
    
    scenario_results = []
    
    for scenario in scenarios:
        print(f"\n   🏥 {scenario['name']}:")
        
        # Test with automatic strategy selection
        payload = {
            "text": scenario["text"],
            "analysis_type": "detailed_analysis",
            "urgency": "normal",
            "include_entities": True
        }
        
        try:
            response = requests.post(f"{FUSION_API_URL}/fusion/analyze", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"     ✅ Analysis Complete")
                print(f"     🔮 Strategy: {result.get('fusion_strategy')}")
                print(f"     🤖 Providers: {result.get('primary_provider')}")
                if result.get('secondary_provider'):
                    print(f"        + {result.get('secondary_provider')}")
                
                # Show key recommendations
                if 'recommendations' in result and result['recommendations']:
                    print(f"     💡 Key Insights:")
                    for rec in result['recommendations'][:3]:
                        print(f"        • {rec}")
                
                scenario_results.append({
                    "name": scenario['name'],
                    "success": True,
                    "strategy": result.get('fusion_strategy'),
                    "confidence": result.get('confidence_score', 0)
                })
                
            else:
                print(f"     ❌ Failed: {response.status_code}")
                scenario_results.append({"name": scenario['name'], "success": False})
                
        except Exception as e:
            print(f"     ❌ Error: {e}")
            scenario_results.append({"name": scenario['name'], "success": False})
    
    return scenario_results

async def test_fusion_engine_direct():
    """Test Fusion AI engine directly (if available)"""
    print("\n🔬 Testing Fusion AI Engine Directly...")
    
    try:
        from fusion_ai_engine import FusionAIEngine, AnalysisType
        
        engine = FusionAIEngine()
        
        # Test case
        clinical_text = """
        Patient with acute MI, cardiogenic shock, requires immediate intervention.
        BP 70/40, HR 130, cold and clammy. Needs emergent cardiac catheterization.
        """
        
        # Test emergency assessment
        result = await engine.fusion_analyze(
            text=clinical_text,
            analysis_type=AnalysisType.EMERGENCY_ASSESSMENT,
            urgency="emergency"
        )
        
        print("✅ Direct Fusion Engine Test Passed!")
        print(f"   Strategy: {result.fusion_strategy}")
        print(f"   Processing Time: {result.total_processing_time:.3f}s")
        print(f"   Confidence: {result.confidence_score:.1%}")
        
        if result.primary_result:
            print(f"   Primary: {result.primary_result.provider} ({result.primary_result.processing_time:.3f}s)")
        if result.secondary_result:
            print(f"   Secondary: {result.secondary_result.provider} ({result.secondary_result.processing_time:.3f}s)")
        
        return True
        
    except ImportError:
        print("⚠️ Fusion AI Engine not available for direct testing")
        return False
    except Exception as e:
        print(f"❌ Direct engine test failed: {e}")
        return False

def main():
    """Main test suite"""
    print("🚀 ClinChat-RAG Fusion AI Technology Test Suite")
    print("=" * 60)
    print(f"Testing Fusion API at: {FUSION_API_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test results tracking
    test_results = {}
    
    # Run API tests
    print(f"\n{'='*60}")
    print("🔧 API INFRASTRUCTURE TESTS")
    print(f"{'='*60}")
    
    test_results['health'] = test_fusion_api_health()
    test_results['capabilities'] = test_fusion_capabilities()
    
    # Run functional tests
    print(f"\n{'='*60}")
    print("🧠 FUSION AI FUNCTIONALITY TESTS")
    print(f"{'='*60}")
    
    analysis_results = test_fusion_analysis_types()
    test_results['analysis_types'] = analysis_results
    
    # Run performance tests
    print(f"\n{'='*60}")
    print("⚡ PERFORMANCE & OPTIMIZATION TESTS")
    print(f"{'='*60}")
    
    performance_results = test_fusion_performance()
    test_results['performance'] = performance_results
    
    # Run real-world tests
    print(f"\n{'='*60}")
    print("🌍 REAL-WORLD SCENARIO TESTS") 
    print(f"{'='*60}")
    
    scenario_results = test_real_world_scenarios()
    test_results['scenarios'] = scenario_results
    
    # Test direct engine if available
    print(f"\n{'='*60}")
    print("🔬 DIRECT ENGINE TESTS")
    print(f"{'='*60}")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    test_results['direct_engine'] = loop.run_until_complete(test_fusion_engine_direct())
    loop.close()
    
    # Final summary
    print(f"\n{'='*60}")
    print("🎯 FUSION AI TEST SUMMARY")
    print(f"{'='*60}")
    
    # Count successes
    total_tests = 0
    passed_tests = 0
    
    # API tests
    api_tests = ['health', 'capabilities']
    for test in api_tests:
        total_tests += 1
        if test_results.get(test):
            passed_tests += 1
    
    # Analysis type tests
    if isinstance(test_results.get('analysis_types'), dict):
        for test_name, result in test_results['analysis_types'].items():
            total_tests += 1
            if result.get('success'):
                passed_tests += 1
    
    # Scenario tests
    if isinstance(test_results.get('scenarios'), list):
        for result in test_results['scenarios']:
            total_tests += 1
            if result.get('success'):
                passed_tests += 1
    
    # Direct engine test
    total_tests += 1
    if test_results.get('direct_engine'):
        passed_tests += 1
    
    print(f"📊 Test Results: {passed_tests}/{total_tests} passed ({passed_tests/total_tests*100:.1f}%)")
    
    if passed_tests == total_tests:
        print("🎉 ALL FUSION AI TESTS PASSED!")
        print("✅ Your Fusion AI system is fully operational!")
    else:
        print(f"⚠️ {total_tests - passed_tests} tests need attention")
    
    print(f"\n🔮 Fusion AI Technology Status:")
    print(f"   • Google Gemini: Advanced reasoning & diagnostic capabilities")
    print(f"   • Groq Cloud: High-speed inference & emergency processing")
    print(f"   • Intelligent Routing: Optimal provider selection per use case")
    print(f"   • Clinical Optimization: Specialized medical analysis workflows")
    
    print(f"\n🚀 Ready for Clinical Operations!")
    print(f"   Interactive API: {FUSION_API_URL}/docs")

if __name__ == "__main__":
    main()