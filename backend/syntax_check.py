#!/usr/bin/env python3
"""
Simple syntax validation for models - without database connections
"""

import ast
import sys
from pathlib import Path


def validate_model_syntax():
    """Validate that all model files have correct Python syntax"""

    model_files = [
        "src/models/user.py",
        "src/models/patient.py",
        "src/models/doctor.py",
        "src/models/medical_record.py",
        "src/models/appointment.py",
        "src/models/message.py",
        "src/models/questionnaire.py",
    ]

    backend_path = Path(__file__).parent
    all_valid = True

    for model_file in model_files:
        file_path = backend_path / model_file
        try:
            with open(file_path, "r") as f:
                content = f.read()

            # Parse the AST to check syntax
            ast.parse(content)
            print(f"✅ {model_file} - syntax valid")

        except SyntaxError as e:
            print(f"❌ {model_file} - syntax error: {e}")
            all_valid = False
        except FileNotFoundError:
            print(f"❌ {model_file} - file not found")
            all_valid = False
        except Exception as e:
            print(f"❌ {model_file} - error: {e}")
            all_valid = False

    # Check __init__.py
    try:
        init_path = backend_path / "src/models/__init__.py"
        with open(init_path, "r") as f:
            content = f.read()
        ast.parse(content)
        print(f"✅ src/models/__init__.py - syntax valid")
    except Exception as e:
        print(f"❌ src/models/__init__.py - error: {e}")
        all_valid = False

    if all_valid:
        print("\n🎉 All model files have valid syntax!")
        print("\n📋 Model Summary:")
        print("- User (base authentication model)")
        print("- Patient (extends User)")
        print("- Doctor (extends User)")
        print("- MedicalRecord + MedicalRecordVersion (versioned medical data)")
        print("- Appointment (patient-doctor consultations)")
        print("- Message (secure messaging)")
        print("- QuestionnaireProgress (onboarding progress tracking)")
    else:
        print("\n❌ Some model files have syntax errors!")

    return all_valid


if __name__ == "__main__":
    success = validate_model_syntax()
    sys.exit(0 if success else 1)
