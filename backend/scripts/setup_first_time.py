"""
First-time setup script for SakhiBot
Run from backend folder: python setup_first_time.py
"""
import os
import sys

print("=" * 60)
print("  🔧 SakhiBot First-Time Setup")
print("=" * 60)

# Check if we're in the right directory
if not os.path.exists("main.py"):
    print("\n❌ Error: Run this script from the backend directory")
    print("   cd backend")
    print("   python setup_first_time.py")
    sys.exit(1)

# Check for .env file
if not os.path.exists(".env"):
    print("\n⚠️  No .env file found!")
    print("   Creating .env from .env.example...")
    
    if os.path.exists(".env.example"):
        import shutil
        shutil.copy(".env.example", ".env")
        print("   ✅ Created .env file")
        print("   📝 Please edit .env and add your GROQ_API_KEY")
        print()
        response = input("   Have you added GROQ_API_KEY to .env? (y/n): ")
        if response.lower() != 'y':
            print("\n   Please add GROQ_API_KEY to .env and run this script again")
            sys.exit(1)
    else:
        print("\n❌ .env.example not found!")
        print("   Create a .env file with:")
        print("   GROQ_API_KEY=your_api_key_here")
        sys.exit(1)
else:
    print("\n✅ Step 0: .env file exists")

print("\n📚 Step 1: Checking ChromaDB setup...")

run_ingest = False

# Check if chroma_db exists
if os.path.exists("chroma_db"):
    print("   ✅ ChromaDB directory exists")
    
    # Check if collection exists
    try:
        import chromadb
        from core.config import CHROMA_PATH
        
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        try:
            collection = client.get_collection("sakhibot_legal")
            print("   ✅ Legal collection exists")
        except:
            print("   ⚠️  Legal collection not found - need to run ingest")
            run_ingest = True
    except Exception as e:
        print(f"   ⚠️  Could not check collection: {e}")
        run_ingest = True
else:
    print("   ⚠️  ChromaDB not initialized")
    run_ingest = True

# Run ingest if needed
if run_ingest:
    print("\n📥 Step 2: Running document ingestion...")
    print("   This will take 1-2 minutes...")
    
    try:
        # Run ingest script
        import subprocess
        result = subprocess.run(
            [sys.executable, "ingest.py"],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            print("   ✅ Document ingestion complete!")
            print(result.stdout)
        else:
            print(f"   ❌ Ingestion failed:")
            print(result.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"   ❌ Error running ingest: {e}")
        print("\n   Try running manually:")
        print("   python ingest.py")
        sys.exit(1)
else:
    print("\n✅ Step 2: Document ingestion already complete")

print("\n🧪 Step 3: Testing emergency features...")
print("   Testing imports...")

try:
    from routes.emergency import router as emergency_router
    print("   ✅ Emergency routes OK")
except Exception as e:
    print(f"   ❌ Emergency routes error: {e}")
    sys.exit(1)

try:
    from routes.consent import router as consent_router
    print("   ✅ Consent routes OK")
except Exception as e:
    print(f"   ❌ Consent routes error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("  ✅ SETUP COMPLETE!")
print("=" * 60)
print("\n🚀 Ready to start the server!")
print("\n   Start server:")
print("   python start_server.py")
print("\n   OR")
print("   uvicorn main:app --reload")
print("\n📝 Then run tests in another terminal:")
print("   python test_emergency.py")
print("\n" + "=" * 60)
