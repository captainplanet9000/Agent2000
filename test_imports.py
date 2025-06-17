"""
Test script to verify that all required imports are working correctly.
"""
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

def test_imports():
    """Test importing the required modules."""
    print("Testing imports...")
    
    # Test importing from python.helpers
    try:
        from python.helpers import dotenv, runtime
        from python.helpers.rate_limiter import RateLimiter
        from python.helpers.dotenv import load_dotenv
        
        print("✅ Successfully imported all required modules from python.helpers")
        
        # Test creating a RateLimiter instance
        limiter = RateLimiter(max_requests=10, per_seconds=60)
        print(f"✅ Successfully created RateLimiter: {limiter}")
        
        # Test dotenv functionality
        print(f"✅ dotenv module: {dotenv}")
        print(f"✅ load_dotenv function: {load_dotenv}")
        
        # Test runtime functionality
        print(f"✅ runtime module: {runtime}")
        print(f"✅ Platform info: {runtime.PLATFORM}")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(f"Python path: {sys.path}")
    print(f"Current working directory: {os.getcwd()}")
    
    if test_imports():
        print("\n✅ All imports are working correctly!")
        sys.exit(0)
    else:
        print("\n❌ There were issues with the imports.")
        sys.exit(1)
