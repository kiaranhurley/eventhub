# EventHub

```powershell
docker compose up --build
```

- UI: http://localhost:8080  
- Booking API: http://localhost:5000  

```powershell
docker compose build
kubectl apply -k k8s/
```

- UI (cluster): http://localhost:30080  
- Uses `imagePullPolicy: Never` — build images locally first so the cluster can see them.  

```powershell
pip install -r requirements-dev.txt
pytest -m unit
```

`pytest` runs the full suite. Booking unit tests: `services/booking-service/booking_service_tests/`.

Written submission: `docs/EventHub_Submission_Document.docx`.
