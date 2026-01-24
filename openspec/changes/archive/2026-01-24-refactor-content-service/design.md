# Design Document: Content Service Refactoring

## Context

The current codebase queries platform content tables (xhs_note, douyin_aweme, etc.) directly in API endpoints, returning raw database records. Each platform has different table schemas, making it difficult to build consistent client applications.

**Constraints**:
- Must maintain compatibility with existing MediaCrawlerPro-Python database schema (read-only, no schema changes)
- Seven different platforms with different table structures
- Need to preserve all platform-specific data while providing unified interface

**Stakeholders**:
- Frontend developers consuming the API
- Future mobile/integration clients
- Backend developers maintaining the service layer

## Goals / Non-Goals

**Goals**:
- Centralize content retrieval logic in a dedicated service layer
- Provide structured, typed responses with Pydantic models
- Support all seven platforms (xhs, dy, ks, bili, wb, tieba, zhihu) uniformly
- Preserve all platform-specific data in a flexible structure
- Simplify API endpoint implementations

**Non-Goals**:
- Modifying the underlying database schema
- Adding data transformation logic beyond normalization (e.g., no enrichment, aggregation)
- Implementing caching (can be added later)
- Creating a GraphQL API (REST only)

## Decisions

### 1. Service Layer Architecture

**Decision**: Create `ContentService` as a stateless class with async methods that abstract MySQL queries.

**Rationale**:
- Follows existing pattern used in `HotspotService`
- Keeps business logic separate from API routing
- Easier to test and reuse across endpoints
- Can inject dependencies (database connections) as needed

**Alternatives considered**:
- Repository pattern: Too heavyweight for simple CRUD operations
- Helper functions: Less organized, harder to maintain state/config

### 2. Structured Data Model Design

**Decision**: Create `StructuredContent` and `StructuredComment` models with:
- Common fields extracted from all platforms (id, title, desc, user info, metrics, timestamps)
- `platform_specific: dict` field for platform-unique data
- Use Pydantic `Field` with aliases to handle different field names across platforms

**Example structure**:
```python
class StructuredContent(BaseModel):
    platform: str
    content_id: str
    title: Optional[str]
    desc: Optional[str]
    content_text: Optional[str]

    # User info
    user_id: str
    nickname: Optional[str]
    avatar: Optional[str]
    ip_location: Optional[str]

    # Engagement metrics
    liked_count: Optional[int]
    collected_count: Optional[int]
    comment_count: Optional[int]
    share_count: Optional[int]

    # Timestamps
    time: Optional[str]
    create_time: Optional[datetime]
    add_ts: Optional[int]
    last_modify_ts: Optional[int]

    # Platform-specific fields
    platform_specific: dict = Field(default_factory=dict)

    # Related data
    comments: List[StructuredComment] = Field(default_factory=list)
    hotspot_id: Optional[int]
    hotspot_keyword: Optional[str]
```

**Rationale**:
- Provides predictable structure for frontend developers
- `platform_specific` allows preservation of unique fields without schema explosion
- Comments nested within content for convenience
- Type safety via Pydantic

**Alternatives considered**:
- Union types for each platform: Too verbose, harder to extend
- Fully dynamic dict: Loses type safety and documentation
- Separate models per platform: Code duplication, harder to maintain

### 3. Field Mapping Strategy

**Decision**: Create mapping dictionaries in `ContentService` to translate platform-specific field names to common fields.

**Example**:
```python
CONTENT_ID_FIELD_MAP = {
    "xhs": "note_id",
    "dy": "aweme_id",
    "ks": "video_id",
    # ...
}

ENGAGEMENT_FIELD_MAP = {
    "liked_count": ["liked_count", "like_count", "digg_count"],
    "comment_count": ["comment_count", "comments_count"],
    # ...
}
```

**Rationale**:
- Explicit mapping makes transformation logic clear
- Easy to update when platforms change
- Can handle field name variations (e.g., "liked_count" vs "like_count")

**Alternatives considered**:
- Hardcoded if/else per platform: Not scalable
- AI-based field matching: Over-engineered, unpredictable

## Risks / Trade-offs

**Risk**: Breaking change for existing API clients
- **Mitigation**: Document breaking changes clearly; provide migration guide; version API if necessary (future consideration)

**Risk**: Performance impact from additional data transformation
- **Mitigation**: Transformation is simple field mapping, minimal overhead; can add caching layer later if needed

**Trade-off**: Flexibility vs. type safety in `platform_specific` field
- Using dict loses type safety for platform-unique fields
- **Acceptable**: Platform-specific fields are secondary; common fields are type-safe

**Trade-off**: Nested comments vs. separate endpoint
- Nesting comments in content makes responses larger
- **Acceptable**: Matches existing API behavior; clients expect this structure

## Migration Plan

**Phase 1**: Create service and models (no breaking changes)
1. Add `ContentService` class with all methods
2. Add structured models to schemas
3. Deploy without using in endpoints yet

**Phase 2**: Refactor endpoints one by one
1. Update `get_hotspot_contents` first (most impacted)
2. Update `list_contents` and `list_comments`
3. Test each endpoint after refactoring

**Phase 3**: Cleanup
1. Remove unused code from hotspots.py
2. Update API documentation
3. Notify frontend team of changes

**Rollback**: If issues arise, revert to direct DB queries in endpoints (service remains unused but harmless).

## Open Questions

1. Should we add pagination to comments within content responses?
   - Current behavior returns all comments, which could be large for popular content
   - **Decision**: Keep existing behavior for now; add pagination later if needed

2. Should we add data validation/sanitization in the service layer?
   - E.g., ensure URLs are valid, timestamps are within reasonable range
   - **Decision**: No, trust database data; add validation in write operations if needed later

3. Should the service handle hotspot keyword enrichment (joining hotspots table)?
   - **Decision**: Yes, service should handle this join to keep API endpoints simple
