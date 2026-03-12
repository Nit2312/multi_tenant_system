"""
Quick Evaluation Script
Run a quick smoke test to check if the system is working properly
"""

import requests
import time


def test_system(base_url="http://localhost:5001"):
    """Run quick smoke tests"""
    print("🔍 Quick System Evaluation")
    print("=" * 60)
    print()
    
    # Test 1: System Status
    print("1. Checking system status...")
    try:
        response = requests.get(f"{base_url}/api/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ System is {'initialized' if data.get('initialized') else 'not initialized'}")
            print(f"   ✓ Model: {data.get('model', 'Unknown')}")
        else:
            print(f"   ✗ Failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    print()
    
    # Test 2: Initialize system
    print("2. Initializing system...")
    try:
        response = requests.post(f"{base_url}/api/initialize", timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✓ {data.get('message', 'Initialized successfully')}")
            else:
                print(f"   ✗ Initialization failed: {data.get('message', 'Unknown error')}")
                return False
        else:
            print(f"   ✗ Failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    print()
    
    # Test 3: Simple query
    print("3. Testing simple query...")
    test_query = "What is value investing?"
    try:
        start = time.time()
        response = requests.post(
            f"{base_url}/api/chat",
            json={"message": test_query},
            timeout=30
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                print(f"   ✗ Error: {data['error']}")
                return False
            
            response_text = data.get('response', '')
            sources = data.get('sources', [])
            metrics = data.get('retrieval_metrics', {})
            
            print(f"   ✓ Response received ({elapsed:.2f}s)")
            print(f"   ✓ Response length: {len(response_text)} characters")
            print(f"   ✓ Sources retrieved: {metrics.get('retrieved', 0)}")
            print(f"   ✓ Sources cited: {metrics.get('cited_in_answer', 0)}")
            print(f"   ✓ Precision@k: {metrics.get('precision_at_k', 0):.2f}")
            
            if response_text:
                print(f"\n   Preview: {response_text[:150]}...")
            
            # Basic checks
            if len(response_text) < 50:
                print(f"   ⚠️  Warning: Response is very short")
            if metrics.get('retrieved', 0) == 0:
                print(f"   ⚠️  Warning: No sources retrieved")
            
        else:
            print(f"   ✗ Failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    print()
    
    # Test 4: Financial expert agent
    print("4. Testing financial expert agent...")
    test_query = "Give me advice on long-term investing"
    try:
        start = time.time()
        response = requests.post(
            f"{base_url}/api/financial-expert",
            json={"message": test_query},
            timeout=30
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                print(f"   ⚠️  Agent not available: {data['error']}")
            else:
                response_text = data.get('response', '')
                print(f"   ✓ Agent response received ({elapsed:.2f}s)")
                print(f"   ✓ Response length: {len(response_text)} characters")
                if response_text:
                    print(f"\n   Preview: {response_text[:150]}...")
        else:
            print(f"   ⚠️  Agent endpoint returned HTTP {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Agent test failed: {e}")
    
    print()
    print("=" * 60)
    print("✓ Quick evaluation completed successfully!")
    print()
    print("💡 Tips:")
    print("   - Run full evaluation: python evaluate_system.py")
    print("   - Check logs: cat query_logs.json | tail -n 50")
    print("   - Monitor dashboard: http://localhost:5001/dashboard")
    
    return True


if __name__ == "__main__":
    import sys
    success = test_system()
    sys.exit(0 if success else 1)
