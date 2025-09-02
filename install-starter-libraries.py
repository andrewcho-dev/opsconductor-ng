#!/usr/bin/env python3
"""
OpsConductor Starter Libraries Installer
Automatically installs the basic step libraries for OpsConductor
"""

import os
import sys
import requests
import time
from pathlib import Path

# Configuration
STEP_LIBRARIES_URL = "http://localhost:3011/api/v1/libraries/install"
STARTER_LIBRARIES_DIR = Path(__file__).parent / "starter-libraries"

# Library packages to install
STARTER_PACKAGES = [
    {
        'name': 'Windows Core Operations',
        'file': 'windows-core-v1.0.0.zip',
        'description': 'Essential Windows system operations including file management, registry, services, and process control'
    },
    {
        'name': 'Network Tools',
        'file': 'network-tools-v1.0.0.zip',
        'description': 'Network connectivity testing, monitoring, and troubleshooting tools'
    },
    {
        'name': 'Automation Basics',
        'file': 'automation-basics-v1.0.0.zip',
        'description': 'Essential automation steps including delays, conditions, loops, and data manipulation'
    },
    {
        'name': 'Web & HTTP Tools',
        'file': 'web-http-v1.0.0.zip',
        'description': 'HTTP requests, web scraping, API testing, and web service interactions'
    }
]


def wait_for_service():
    """Wait for the step-libraries service to be ready"""
    print("⏳ Waiting for Step Libraries Service to be ready...")
    
    for attempt in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get("http://localhost:3011/health", timeout=5)
            if response.status_code == 200:
                print("✅ Step Libraries Service is ready")
                return True
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(1)
        print(f"   Attempt {attempt + 1}/30...")
    
    print("❌ Step Libraries Service is not responding")
    return False


def install_library(package_info):
    """Install a single library package"""
    package_file = STARTER_LIBRARIES_DIR / package_info['file']
    
    if not package_file.exists():
        print(f"❌ Package file not found: {package_file}")
        return False
    
    print(f"📦 Installing {package_info['name']}...")
    print(f"   {package_info['description']}")
    
    try:
        with open(package_file, 'rb') as f:
            files = {'file': (package_info['file'], f, 'application/zip')}
            
            response = requests.post(
                STEP_LIBRARIES_URL,
                files=files,
                timeout=60
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully installed: {result.get('display_name', package_info['name'])}")
            print(f"   Version: {result.get('version', 'Unknown')}")
            print(f"   Steps: {result.get('steps_count', 0)}")
            return True
        else:
            error_msg = response.json().get('detail', 'Unknown error') if response.headers.get('content-type', '').startswith('application/json') else response.text
            print(f"❌ Failed to install {package_info['name']}: {error_msg}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error installing {package_info['name']}: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Error installing {package_info['name']}: {str(e)}")
        return False


def check_existing_libraries():
    """Check what libraries are already installed"""
    try:
        response = requests.get("http://localhost:3011/api/v1/libraries", timeout=10)
        if response.status_code == 200:
            libraries = response.json()
            if libraries:
                print(f"📋 Found {len(libraries)} existing libraries:")
                for lib in libraries:
                    print(f"   - {lib.get('display_name', lib.get('name', 'Unknown'))}")
                return [lib.get('name', '') for lib in libraries]
            else:
                print("📋 No existing libraries found")
                return []
        else:
            print("⚠️  Could not check existing libraries")
            return []
    except Exception as e:
        print(f"⚠️  Error checking existing libraries: {str(e)}")
        return []


def main():
    """Main installation process"""
    print("🚀 OpsConductor Starter Libraries Installer")
    print("=" * 50)
    
    # Wait for service
    if not wait_for_service():
        print("❌ Cannot proceed without Step Libraries Service")
        sys.exit(1)
    
    # Check existing libraries
    existing_libraries = check_existing_libraries()
    
    # Install starter packages
    print(f"\\n📦 Installing {len(STARTER_PACKAGES)} starter library packages...")
    
    installed_count = 0
    skipped_count = 0
    failed_count = 0
    
    for package in STARTER_PACKAGES:
        # Extract library name from filename (remove version and extension)
        lib_name = package['file'].split('-v')[0].replace('-', '_')
        
        if lib_name in existing_libraries:
            print(f"⏭️  Skipping {package['name']} (already installed)")
            skipped_count += 1
            continue
        
        if install_library(package):
            installed_count += 1
        else:
            failed_count += 1
        
        print()  # Add spacing between installations
    
    # Summary
    print("=" * 50)
    print("📊 Installation Summary:")
    print(f"   ✅ Installed: {installed_count}")
    print(f"   ⏭️  Skipped: {skipped_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📦 Total packages: {len(STARTER_PACKAGES)}")
    
    if failed_count == 0:
        print("\\n🎉 All starter libraries installed successfully!")
        print("\\n🔧 Next steps:")
        print("   1. Open http://localhost in your browser")
        print("   2. Navigate to Visual Job Builder")
        print("   3. Start building jobs with the new step libraries!")
    else:
        print(f"\\n⚠️  {failed_count} packages failed to install")
        print("   Check the error messages above for details")
    
    # Show available steps
    try:
        response = requests.get("http://localhost:3011/api/v1/steps", timeout=10)
        if response.status_code == 200:
            steps_data = response.json()
            steps = steps_data.get('steps', [])
            if steps:
                print(f"\\n📋 Available Steps ({len(steps)} total):")
                
                # Group by category
                categories = {}
                for step in steps:
                    category = step.get('category', 'Other')
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(step.get('display_name', step.get('name', 'Unknown')))
                
                for category, step_names in sorted(categories.items()):
                    print(f"   {category}:")
                    for step_name in sorted(step_names):
                        print(f"     - {step_name}")
    except:
        pass  # Don't fail if we can't show steps


if __name__ == "__main__":
    main()