# Clara_BE API Documentation

This document provides detailed information about the available API endpoints, including request/response formats and HTTP status codes.

## Authentication
All endpoints use JWT authentication where required. Obtain tokens via the login or registration endpoints.

---

## Endpoints

### 1. Register a New User
- **URL:** `/accounts/register/`
- **Method:** POST
- **Description:** Register a new user account.

#### Request Body (JSON)
```
{
  "username": "string",
  "password": "string",
  "first_name": "string",   // optional
  "last_name": "string"     // optional
}
```

#### Success Response
- **Code:** 201 CREATED
- **Content:**
```
{
  "message": "User registered successfully",
  "user": {
    "id": int,
    "username": "string",
    "first_name": "string",
    "last_name": "string"
  },
  "tokens": {
    "refresh": "string",
    "access": "string"
  }
}
```

#### Error Response
- **Code:** 400 BAD REQUEST
- **Content:**
```
{
  "field_name": ["error message"]
}
```

---

### 2. User Login
- **URL:** `/accounts/login/`
- **Method:** POST
- **Description:** Authenticate a user and obtain JWT tokens.

#### Request Body (JSON)
```
{
  "username": "string",
  "password": "string"
}
```

#### Success Response
- **Code:** 200 OK
- **Content:**
```
{
  "message": "Login successful",
  "user": {
    "id": int,
    "username": "string",
    "first_name": "string",
    "last_name": "string"
  },
  "tokens": {
    "refresh": "string",
    "access": "string"
  }
}
```

#### Error Responses
- **Code:** 400 BAD REQUEST
- **Content:**
```
{
  "field_name": ["error message"]
}
```
- **Code:** 401 UNAUTHORIZED
- **Content:**
```
{
  "error": "Invalid credentials"
}
```

---

### 3. Refresh Token
- **URL:** `/accounts/token/refresh/`
- **Method:** POST
- **Description:** Obtain a new access token using a refresh token.

#### Request Body (JSON)
```
{
  "refresh": "string"
}
```

#### Success Response
- **Code:** 200 OK
- **Content:**
```
{
  "access": "string"
}
```

#### Error Response
- **Code:** 401 UNAUTHORIZED
- **Content:**
```
{
  "detail": "Token is invalid or expired"
}
```

---

# Research API Endpoint Details

## `/api/research/<name>/` (GET, POST)

### Description
Research a politician by name. Returns cached research if available and recent, or triggers new research. POST forces new research.

### Query Parameters
- `position` (string, optional): Filter by position
- `max_age` (int, optional): Max age of cached results in days (default: 7)
- `include_sources` (bool, optional): Include sources in response (default: false)
- `detailed` (bool, optional): Return detailed results (default: false)

### GET Request Example
`/api/research/Jane%20Doe/?position=Senator&include_sources=true`

### POST Request Example
`/api/research/Jane%20Doe/` (with JSON body or empty)

### Success Response (200)
```
{
  "politician": { ... },
  "background": "...",
  "accomplishments": "...",
  "criticisms": "...",
  "summary": "...",
  "sources": { ... },
  "created_at": "...",
  "updated_at": "...",
  "metadata": {
    "is_fresh": true,
    "age_days": 0,
    "request_method": "GET"
  }
}
```

### Error Response (400, 500)
```
{
  "success": false,
  "error": "Error message",
  "name": "Jane Doe",
  "position": "Senator"
}
```

### Notes
- If research is in progress or partial, a `content_list` may be returned.
- All responses are JSON.

---

# Chat API Endpoint Details

## 1. Create a New Chat
- **URL:** `/api/chat/chats/`
- **Method:** POST
- **Authentication:** Optional (JWT Refresh Token)
- **Description:** Create a new chat about a politician. If authenticated, the chat will be associated with the user. If not, it will be a temporary chat.

### Request Body (JSON)
```
{
  "politician": "string",
  "position": "string"  // optional
}
```

### Success Response
- **Code:** 201 CREATED
- **Content:**
```
{
  "id": int,
  "politician": "string",
  "user": int or null,
  "created_at": "datetime string",
  "research_report": int or null,
  "qanda_set": []
}
```

### Error Response
- **Code:** 400 BAD REQUEST
- **Content:**
```
{
  "error": "Politician name is required"
}
```

---

## 2. Get All Chats (Authenticated Users Only)
- **URL:** `/api/chat/chats/`
- **Method:** GET
- **Authentication:** Required (JWT Refresh Token)
- **Description:** Retrieve all chats associated with the authenticated user.

### Success Response
- **Code:** 200 OK
- **Content:**
```
[
  {
    "id": int,
    "politician": "string",
    "user": int,
    "created_at": "datetime string",
    "research_report": int or null,
    "qanda_set": [
      {
        "id": int,
        "chat": int,
        "question": "string",
        "answer": "string",
        "created_at": "datetime string"
      }
    ]
  }
]
```

### Error Response
- **Code:** 401 UNAUTHORIZED
- **Content:**
```
{
  "error": "Authentication required to view chats"
}
```

---

## 3. Get Temporary Chat
- **URL:** `/api/chat/temporary-chats/<chat_id>/`
- **Method:** GET
- **Authentication:** None
- **Description:** Retrieve a temporary chat (no user association) by its ID.

### Success Response
- **Code:** 200 OK
- **Content:**
```
{
  "id": int,
  "politician": "string",
  "user": null,
  "created_at": "datetime string",
  "research_report": int or null,
  "qanda_set": [
    {
      "id": int,
      "chat": int,
      "question": "string",
      "answer": "string",
      "created_at": "datetime string"
    }
  ]
}
```

### Error Response
- **Code:** 404 NOT FOUND
- **Content:**
```
{
  "error": "Temporary chat not found"
}
```

---

## 4. Delete Chat
- **URL:** `/api/chat/chats/<chat_id>/`
- **Method:** DELETE
- **Authentication:** Optional (JWT Refresh Token)
- **Description:** Delete a chat. Authenticated users can only delete their own chats. Unauthenticated users can only delete temporary chats.

### Success Response
- **Code:** 204 NO CONTENT

### Error Responses
- **Code:** 404 NOT FOUND
- **Content:**
```
{
  "error": "Chat not found"
}
```
- **Code:** 403 FORBIDDEN
- **Content:**
```
{
  "error": "You can only delete your own chats"
}
```
- **Code:** 401 UNAUTHORIZED
- **Content:**
```
{
  "error": "Authentication required to delete this chat"
}
```

---

## 5. Create Question and Answer
- **URL:** `/api/chat/questions/`
- **Method:** POST
- **Authentication:** None
- **Description:** Create a new question and get an answer for a specific chat.

### Request Body (JSON)
```
{
  "chat_id": int,
  "question": "string"
}
```

### Success Response
- **Code:** 201 CREATED
- **Content:**
```
{
  "id": int,
  "chat": int,
  "question": "string",
  "answer": "string",
  "created_at": "datetime string"
}
```

### Error Responses
- **Code:** 400 BAD REQUEST
- **Content:**
```
{
  "error": "Chat ID and question are required"
}
```
- **Code:** 404 NOT FOUND
- **Content:**
```
{
  "error": "Chat not found"
}
```

---

## Notes
- All endpoints return JSON responses.
- Use the `Authorization: Bearer <access_token>` header for authenticated requests where required.
