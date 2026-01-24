# content-management Specification

## Purpose
TBD - created by archiving change refactor-content-service. Update Purpose after archive.
## Requirements
### Requirement: Structured Content Retrieval
The system SHALL provide structured content retrieval across all supported platforms through a dedicated service layer.

#### Scenario: Retrieve content by hotspot ID
- **WHEN** an API client requests content for a specific hotspot ID via `GET /hotspots/{hotspot_id}/contents`
- **THEN** the system SHALL return a structured response containing:
  - Hotspot basic info (id, keyword)
  - Content grouped by platform
  - Each content item with normalized common fields (id, title, desc, user info, engagement metrics, timestamps)
  - Each content item with platform-specific fields in a `platform_specific` dict
  - Comments nested within each content item as structured objects

#### Scenario: Retrieve platform content with filters
- **WHEN** an API client requests content for a specific platform via `GET /contents/{platform}/notes`
- **THEN** the system SHALL return a paginated list of structured content items
- **AND** the system SHALL support filtering by keyword, hotspot_id, and date range
- **AND** each content item SHALL include the associated hotspot_keyword if hotspot_id is present

#### Scenario: Retrieve comments for specific content
- **WHEN** an API client requests comments via `GET /contents/{platform}/comments?note_id={id}`
- **THEN** the system SHALL return a paginated list of structured comment objects
- **AND** each comment SHALL have normalized fields (comment_id, content, user info, engagement, timestamps)
- **AND** platform-specific comment fields SHALL be preserved in `platform_specific` dict

### Requirement: Content Service Layer
The system SHALL implement a `ContentService` class in `app/services/content_service.py` to encapsulate all content retrieval business logic.

#### Scenario: Service retrieves content for hotspot
- **WHEN** `content_service.get_contents_by_hotspot_id(hotspot_id)` is called
- **THEN** the service SHALL query all platform content tables for matching hotspot_id
- **AND** the service SHALL query associated comments for each content item
- **AND** the service SHALL return a dict mapping platform names to lists of `StructuredContent` objects
- **AND** each `StructuredContent` SHALL have nested `StructuredComment` objects

#### Scenario: Service retrieves content by platform with filters
- **WHEN** `content_service.get_contents_by_platform(platform, filters)` is called with filters (keyword, hotspot_id, date_range, pagination)
- **THEN** the service SHALL query the appropriate platform content table
- **AND** the service SHALL apply all provided filters
- **AND** the service SHALL return a list of `StructuredContent` objects with pagination metadata

#### Scenario: Service retrieves comments for content
- **WHEN** `content_service.get_comments_by_note_id(platform, note_id, pagination)` is called
- **THEN** the service SHALL query the appropriate platform comment table
- **AND** the service SHALL return a list of `StructuredComment` objects with pagination metadata

### Requirement: Unified Data Models
The system SHALL define Pydantic models in `app/schemas/content.py` for structured content and comments.

#### Scenario: StructuredContent model includes all common fields
- **WHEN** a `StructuredContent` object is instantiated from raw database data
- **THEN** it SHALL include these normalized fields:
  - platform (str): Platform identifier (xhs, dy, etc.)
  - content_id (str): Primary content identifier
  - title (Optional[str]): Content title
  - desc (Optional[str]): Content description
  - content_text (Optional[str]): Main content text
  - user_id (str): Creator user ID
  - nickname (Optional[str]): Creator display name
  - avatar (Optional[str]): Creator avatar URL
  - ip_location (Optional[str]): IP location
  - liked_count (Optional[int]): Like/digg count
  - collected_count (Optional[int]): Collection/favorite count
  - comment_count (Optional[int]): Comment count
  - share_count (Optional[int]): Share count
  - time (Optional[str]): Formatted time string
  - create_time (Optional[datetime]): Creation timestamp
  - add_ts (Optional[int]): Timestamp added to database
  - last_modify_ts (Optional[int]): Last modification timestamp
  - platform_specific (dict): Platform-unique fields
  - comments (List[StructuredComment]): Associated comments
  - hotspot_id (Optional[int]): Associated hotspot ID
  - hotspot_keyword (Optional[str]): Associated hotspot keyword

#### Scenario: StructuredComment model includes all common fields
- **WHEN** a `StructuredComment` object is instantiated from raw database data
- **THEN** it SHALL include these normalized fields:
  - platform (str): Platform identifier
  - comment_id (str): Unique comment identifier
  - content (str): Comment text content
  - user_id (str): Commenter user ID
  - nickname (Optional[str]): Commenter display name
  - avatar (Optional[str]): Commenter avatar URL
  - ip_location (Optional[str]): IP location
  - like_count (Optional[int]): Like count
  - sub_comment_count (Optional[int]): Reply count
  - create_time (Optional[datetime]): Creation timestamp
  - add_ts (Optional[int]): Timestamp added to database
  - parent_comment_id (Optional[str]): Parent comment ID for replies
  - platform_specific (dict): Platform-unique fields

#### Scenario: Platform-specific fields are preserved
- **WHEN** raw database content has fields not in the common schema (e.g., dy's "aweme_type", xhs's "note_url")
- **THEN** these fields SHALL be stored in the `platform_specific` dict
- **AND** field names SHALL be preserved exactly as they appear in the database

### Requirement: Field Mapping and Normalization
The `ContentService` SHALL normalize platform-specific field names to common field names using explicit mapping dictionaries.

#### Scenario: Map content ID fields across platforms
- **WHEN** querying content from different platforms
- **THEN** the service SHALL map platform-specific ID fields to `content_id`:
  - xhs: note_id → content_id
  - dy: aweme_id → content_id
  - ks: video_id → content_id
  - bili: video_id → content_id
  - zhihu: content_id → content_id
  - wb: note_id → content_id
  - tieba: note_id → content_id

#### Scenario: Map engagement metric fields across platforms
- **WHEN** mapping engagement metrics
- **THEN** the service SHALL check multiple possible field names for each metric:
  - liked_count: ["liked_count", "like_count", "digg_count"]
  - collected_count: ["collected_count", "collect_count", "favorite_count"]
  - comment_count: ["comment_count", "comments_count", "comment_num"]
  - share_count: ["share_count", "shares_count", "forward_count"]

#### Scenario: Preserve timestamp fields
- **WHEN** mapping timestamp fields
- **THEN** the service SHALL preserve all available timestamp formats:
  - time (string format)
  - create_time (datetime)
  - add_ts (unix timestamp)
  - last_modify_ts (unix timestamp)

### Requirement: Hotspot Keyword Enrichment
The `ContentService` SHALL enrich content items with associated hotspot keywords when hotspot_id is present.

#### Scenario: Add hotspot keyword to content
- **WHEN** content items have a non-null hotspot_id field
- **THEN** the service SHALL batch-query the hotspots table in PostgreSQL to retrieve keywords
- **AND** the service SHALL add the `hotspot_keyword` field to each content item
- **AND** if hotspot_id does not match any hotspot record, hotspot_keyword SHALL be None

### Requirement: Error Handling
The service SHALL handle database errors and invalid inputs gracefully.

#### Scenario: Handle invalid platform identifier
- **WHEN** an invalid platform identifier is provided (not in PLATFORM_CONTENT_TABLES)
- **THEN** the service SHALL raise a ValueError with message "Unsupported platform: {platform}"

#### Scenario: Handle missing hotspot
- **WHEN** get_contents_by_hotspot_id is called with a non-existent hotspot_id
- **THEN** the service SHALL return empty results grouped by platform
- **AND** no exception SHALL be raised

#### Scenario: Handle database connection errors
- **WHEN** a database query fails due to connection issues
- **THEN** the service SHALL propagate the exception to the API layer
- **AND** the API layer SHALL return HTTP 500 with an error message

