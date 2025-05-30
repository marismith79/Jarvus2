# Availity MCP Server

A FastAPI-based MCP server that wraps Availity's REST API, providing a clean interface for claim status and configuration management.

## Project Structure

```
mcp_server/
├── __init__.py
├── app.py                 # Main FastAPI application
├── config.py             # Configuration and environment settings
├── auth/
│   ├── __init__.py
│   └── token_manager.py  # OAuth2 token management
├── routers/
│   ├── __init__.py
│   ├── auth.py          # Authentication endpoints
│   ├── claim_status.py  # Claim status endpoints
│   └── configurations.py # Configuration endpoints
├── schemas/
│   ├── __init__.py
│   ├── claim_status.py  # Claim status data models
│   └── configurations.py # Configuration data models
└── services/
    ├── __init__.py
    └── availity.py      # Availity API tools / service wrapper 
```

## Components

### Configuration (`config.py`)
- Manages environment variables and application settings
- Defines default values for development
- Handles API URLs and credentials

### Authentication (`auth/token_manager.py`)
- Manages OAuth2 token lifecycle
- Handles token refresh and caching
- Provides token validation

### Routers
- `auth.py`: OAuth2 token endpoint
- `claim_status.py`: Claim status list and detail endpoints
- `configurations.py`: Payer configuration endpoints

### Schemas
- `claim_status.py`: Data models for claim status responses
- `configurations.py`: Data models for configuration responses

### Services (`services/availity.py`)
- Wraps Availity API calls
- Handles authentication and request formatting
- Manages error handling and response parsing

## API Endpoints

### 1. Get Access Token
```bash
curl -X POST "http://localhost:8000/availity/v1/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET&scope=hipaa"
```

Response:
```json
{
  "access_token": "YOUR_ACCESS_TOKEN",
  "expires_in": 300,
  "token_type": "Bearer"
}
```

### 2. List Claim Statuses
```bash
curl "http://localhost:8000/availity/v1/claim-statuses?payer_id=12345&claim_number=ABC123456" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response:
```json
{
  "totalCount": 1,
  "count": 1,
  "offset": 0,
  "limit": 1,
  "links": {
    "self": {
      "href": "https://api.availity.com/demo/v1/claim-statuses?payer.id=BCBSF&..."
    }
  },
  "claimStatuses": [
    {
      "id": "123",
      "status": "Complete",
      "statusCode": "4",
      "createdDate": "2015-06-25T17:26:19.000+0000",
      "updatedDate": "2015-06-25T17:26:19.000+0000",
      "payer": {
        "id": "BCBSF",
        "name": "FLORIDA BLUE"
      },
      "submitter": {
        "lastName": "SUBMITLAST",
        "firstName": "SUBMITFIRST",
        "id": "H8747"
      },
      "providers": [
        {
          "lastName": "PRVLAST",
          "firstName": "PRVFIRST",
          "npi": "1619978434"
        }
      ],
      "subscriber": {
        "lastName": "KENNEY",
        "memberId": "CNDXZ7980219"
      },
      "patient": {
        "lastName": "KENNEY",
        "birthDate": "1960-04-20",
        "gender": "Female",
        "genderCode": "F",
        "accountNumber": "unknown",
        "subscriberRelationship": "Self",
        "subscriberRelationshipCode": "18"
      },
      "claimStatuses": [
        {
          "traceId": "36777",
          "fromDate": "2014-07-26",
          "toDate": "2014-07-26",
          "statusDetails": [
            {
              "category": "Acknowledgement/Forwarded",
              "categoryCode": "A0",
              "status": "Business Application Currently Not Available",
              "statusCode": "484",
              "effectiveDate": "2015-06-25",
              "claimAmount": "0",
              "claimAmountUnits": "USD",
              "paymentAmount": "0",
              "paymentAmountUnits": "USD"
            }
          ]
        }
      ],
      "claimCount": "1"
    }
  ]
}
```

### 3. Get Specific Claim Status
```bash
curl "http://localhost:8000/availity/v1/claim-statuses/123" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response: Same as individual claim status object from list response.

### 4. Get Payer Configurations
```bash
curl "http://localhost:8000/availity/v1/configurations?type=claim-status&subtype_id=276&payer_id=BCBSF" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response:
```json
{
  "totalCount": 1,
  "count": 1,
  "offset": 0,
  "limit": 50,
  "links": {
    "self": {
      "href": "https://api.availity.com/demo/v1/configurations?payerId=BCBSF&type=270"
    }
  },
  "configurations": [
    {
      "type": "270",
      "categoryId": "admin",
      "categoryValue": "Administrative Transactions",
      "payerId": "BCBSF",
      "version": "5010A1",
      "elements": {
        "providerLastName": {
          "type": "Text",
          "label": "Provider Last Name",
          "order": 0,
          "allowed": true,
          "required": false,
          "errorMessage": "Please enter a valid Provider Last Name.",
          "pattern": "^[a-zA-Z0-9\\s!&,()+'\\-./;?=#\\\\]{1,60}$",
          "maxLength": 60
        },
        // ... more elements ...
      },
      "requiredFieldCombinations": {
        "patient": [
          ["memberId", "patientLastName", "patientBirthDate"],
          ["memberId", "patientLastName", "patientFirstName"],
          ["patientLastName", "patientFirstName", "patientBirthDate"],
          ["memberId", "patientFirstName", "patientBirthDate"]
        ]
      }
    }
  ]
}
```

## Setup and Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```env
AVAILITY_CLIENT_ID=your_client_id
AVAILITY_CLIENT_SECRET=your_client_secret
AVAILITY_PAYER_ID=your_payer_id
AVAILITY_TOKEN_URL=https://api.availity.com/availity/v1/token
AVAILITY_API_BASE_URL=https://api.availity.com/availity/development-partner/v1
```

3. Run the server:
```bash
uvicorn mcp_server.app:app --reload
```

## Error Handling

The server includes comprehensive error handling:
- Invalid token responses
- API errors
- Validation errors
- Network errors

All errors are returned with appropriate HTTP status codes and descriptive messages.

## Development

To add new features:
1. Create appropriate schemas in `schemas/`
2. Add service methods in `services/availity.py`
3. Create router endpoints in `routers/`
4. Update documentation

## Testing

Use the curl commands above to test each endpoint. The server includes debug logging to help troubleshoot issues.

## Security

- OAuth2 authentication
- Token refresh handling
- Secure credential management
- Environment variable configuration 