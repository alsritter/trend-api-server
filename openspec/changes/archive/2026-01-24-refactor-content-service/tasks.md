# Implementation Tasks

## 1. Define Structured Data Models
- [x] 1.1 Create `StructuredContent` model in `app/schemas/content.py` with common fields (id, title, desc, user_id, nickname, avatar, engagement metrics, timestamps)
- [x] 1.2 Create `StructuredComment` model in `app/schemas/content.py` with common fields (comment_id, content, user info, engagement, timestamps)
- [x] 1.3 Add `platform_specific` field to both models for platform-unique data
- [x] 1.4 Update `GetHotspotContentsResponse` in `app/schemas/hotspot.py` to use structured models instead of raw dicts

## 2. Create Content Service
- [x] 2.1 Create `app/services/content_service.py` with `ContentService` class
- [x] 2.2 Implement `get_contents_by_hotspot_id(hotspot_id: int) -> Dict[str, List[StructuredContent]]` method
- [x] 2.3 Implement `get_contents_by_platform(platform: str, filters: dict) -> List[StructuredContent]` method
- [x] 2.4 Implement `get_comments_by_note_id(platform: str, note_id: str) -> List[StructuredComment]` method
- [x] 2.5 Add helper method `_map_raw_to_structured_content(raw_dict: dict, platform: str) -> StructuredContent` to normalize raw DB records
- [x] 2.6 Add helper method `_map_raw_to_structured_comment(raw_dict: dict, platform: str) -> StructuredComment` to normalize comments
- [x] 2.7 Create global `content_service` instance

## 3. Refactor Hotspots API
- [x] 3.1 Update `get_hotspot_contents` in `app/api/v1/hotspots.py` to use `content_service.get_contents_by_hotspot_id()`
- [x] 3.2 Remove direct database query logic from the endpoint
- [x] 3.3 Update response to return structured data instead of raw dicts
- [x] 3.4 Update docstring to reflect the new structured response format

## 4. Refactor Contents API
- [x] 4.1 Update `list_contents` in `app/api/v1/contents.py` to use `content_service.get_contents_by_platform()`
- [x] 4.2 Update `list_comments` in `app/api/v1/contents.py` to use `content_service.get_comments_by_note_id()`
- [x] 4.3 Remove direct database query logic from both endpoints
- [x] 4.4 Update response models to use structured data

## 5. Testing & Validation
- [x] 5.1 Verify all modules import successfully without errors
- [x] 5.2 Verify ContentService imports correctly
- [x] 5.3 Verify StructuredContent and StructuredComment models import correctly
- [x] 5.4 Verify API endpoint imports work correctly
- [ ] 5.5 Manual testing should be performed with actual database connections and hotspot data

