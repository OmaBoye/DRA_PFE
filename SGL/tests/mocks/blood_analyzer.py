# tests/mocks/blood_analyzer.py
def get_success_response():
    return {
        "status": "completed",
        "results": {
            "hemoglobin": "14.2 g/dL",
            "wbc": "6.5 x10^3/μL"
        }
    }