# Change: Refactor Content Retrieval to Dedicated Service with Structured Data Models

## Why

Currently, the `get_hotspot_contents` endpoint in `hotspots.py` (lines 563-681) directly queries MySQL platform content tables and returns raw database dictionaries. This creates several issues:

1. **Business logic in API layer**: Database query logic is embedded in the API endpoint instead of a service layer
2. **Code duplication**: Similar content retrieval patterns exist in both `hotspots.py` and `contents.py` without sharing logic
3. **Unstructured responses**: APIs return raw database records instead of well-defined data structures, making it harder for clients to consume and maintain
4. **Poor separation of concerns**: Content management logic is scattered across multiple API files

## What Changes

- Create a new `ContentService` class in `app/services/content_service.py` to centralize all content and comment retrieval logic
- Define structured Pydantic models for content and comment responses that unify data from different platforms
- Refactor `get_hotspot_contents` endpoint in `hotspots.py` to use the new service
- Update `contents.py` endpoints to use the new service instead of direct database queries
- Create a unified `StructuredContent` model that represents content across all platforms with:
  - Common fields (id, title, desc, user info, engagement metrics, timestamps)
  - Platform-specific fields in a flexible structure
  - Nested comments with the same structured approach

## Impact

- Affected specs: content-management (new capability)
- Affected code:
  - `app/api/v1/hotspots.py` - refactor `get_hotspot_contents` endpoint
  - `app/api/v1/contents.py` - refactor `list_contents`, `list_comments` endpoints
  - `app/services/content_service.py` - new service file
  - `app/schemas/content.py` - add structured data models
  - `app/schemas/hotspot.py` - update `GetHotspotContentsResponse` to use structured models

**Breaking Changes**: The response structure of `GET /hotspots/{hotspot_id}/contents` will change from raw database records to structured models. Clients will need to update their response parsing logic.
