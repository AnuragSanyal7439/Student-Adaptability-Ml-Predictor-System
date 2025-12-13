"""
Installation Verification Script
Run this to check if all components are properly set up
"""

import os
import sys

def check_file(filepath, description):
    """Check if a file exists"""
    exists = os.path.exists(filepath)
    status = "✓" if exists else "✗"
    print(f"{status} {description}: {filepath}")
    return exists

def check_directory(dirpath, description):
    """Check if a directory exists"""
    exists = os.path.exists(dirpath) and os.path.isdir(dirpath)
    status = "✓" if exists else "✗"
    print(f"{status} {description}: {dirpath}")
    return exists

def check_python_package(package_name):
    """Check if a Python package is installed"""
    try:
        __import__(package_name)
        print(f"✓ Python package: {package_name}")
        return True
    except ImportError:
        print(f"✗ Python package: {package_name} (NOT INSTALLED)")
        return False

def main():
    print("="*60)
    print("Student Adaptability ML Predictor - Installation Verification")
    print("="*60)

    all_checks = []

    print("\n1. Checking Core Python Files...")
    all_checks.append(check_file("app.py", "Flask application"))
    all_checks.append(check_file("model_training.py", "Model training script"))

    print("\n2. Checking Frontend Files...")
    all_checks.append(check_file("templates/index.html", "HTML template"))
    all_checks.append(check_file("static/styles.css", "CSS stylesheet"))
    all_checks.append(check_file("static/script.js", "JavaScript"))

    print("\n3. Checking Documentation...")
    all_checks.append(check_file("README.md", "Main documentation"))
    all_checks.append(check_file("QUICKSTART.md", "Quick start guide"))
    all_checks.append(check_file("DEPLOYMENT.md", "Deployment guide"))

    print("\n4. Checking Testing Scripts...")
    all_checks.append(check_file("test_model.py", "Model tests"))
    all_checks.append(check_file("test_api.py", "API tests"))
    all_checks.append(check_file("generate_sample_csv.py", "Sample generator"))

    print("\n5. Checking Configuration Files...")
    all_checks.append(check_file("requirements.txt", "Python dependencies"))
    all_checks.append(check_file("setup.sh", "Setup script"))

    print("\n6. Checking Python Packages...")
    packages = [
        'flask',
        'flask_cors',
        'pandas',
        'numpy',
        'sklearn',
        'joblib',
        'matplotlib',
        'seaborn',
        'reportlab'
    ]

    packages_ok = []
    for package in packages:
        packages_ok.append(check_python_package(package))

    print("\n7. Checking Required Directories...")
    dirs_to_check = [
        ("templates", "Templates directory"),
        ("static", "Static files directory"),
    ]

    for dirpath, description in dirs_to_check:
        all_checks.append(check_directory(dirpath, description))

    print("\n8. Checking Runtime Directories (will be created on first run)...")
    runtime_dirs = [
        ("models", "Models directory"),
        ("data", "Data directory"),
    ]

    for dirpath, description in runtime_dirs:
        exists = check_directory(dirpath, description)
        if not exists:
            print(f"  ℹ This will be created automatically on first run")

    print("\n" + "="*60)
    print("Summary")
    print("="*60)

    core_files_ok = all(all_checks[:2])
    frontend_ok = all(all_checks[2:5])
    docs_ok = all(all_checks[5:8])
    tests_ok = all(all_checks[8:11])
    config_ok = all(all_checks[11:13])
    dirs_ok = all(all_checks[13:])
    python_packages_ok = all(packages_ok)

    print(f"\nCore Application: {'✓ OK' if core_files_ok else '✗ ISSUES'}")
    print(f"Frontend Files: {'✓ OK' if frontend_ok else '✗ ISSUES'}")
    print(f"Documentation: {'✓ OK' if docs_ok else '✗ ISSUES'}")
    print(f"Testing Scripts: {'✓ OK' if tests_ok else '✗ ISSUES'}")
    print(f"Configuration: {'✓ OK' if config_ok else '✗ ISSUES'}")
    print(f"Directories: {'✓ OK' if dirs_ok else '✗ ISSUES'}")
    print(f"Python Packages: {'✓ OK' if python_packages_ok else '✗ ISSUES'}")

    all_ok = (core_files_ok and frontend_ok and docs_ok and
              tests_ok and config_ok and dirs_ok)

    print("\n" + "="*60)

    if all_ok and python_packages_ok:
        print("✓ INSTALLATION COMPLETE!")
        print("\nYou're ready to run the application:")
        print("  python3 app.py")
        print("\nThen open: http://localhost:5000")
        return 0
    elif all_ok and not python_packages_ok:
        print("⚠ FILES OK - PACKAGES NEEDED")
        print("\nInstall Python packages:")
        print("  chmod +x setup.sh")
        print("  sudo ./setup.sh")
        print("\nOr manually:")
        print("  pip3 install -r requirements.txt")
        return 1
    else:
        print("✗ INSTALLATION INCOMPLETE")
        print("\nSome files are missing. Please check the errors above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
