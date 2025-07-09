API_DOCS = """
## EHR Integration API

### `GET /integrations/api/ehr/patients/?patient_id=<ID>`
- Fetches patient data from hospital EHR.

### `POST /integrations/api/ehr/webhook/`
- Accepts JSON payload:
  ```json
  {"sample_id": "123", "values": {"glucose": "95mg/dL"}}