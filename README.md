# SAF_Challenge_MYM
Repositori del grup MYM per el repte del SAF a la UAB The Hack

## Backend API

Install the backend dependencies and start the API with:

```text
pip install -r requirements.txt
uvicorn backendapi:app --reload
```

The API is available under `/api/v1`. Recommendation and SAFi responses
currently use clearly labelled simulated fitness occupancy data. Admin
reservation statistics read from SQLite; admin occupancy remains empty until
processed SAF occupancy data is connected.
