from datetime import datetime
from typing import Optional

from django.contrib.auth.models import User
from ninja import Schema


class UserOut(Schema):
    id: int
    email: str
    first_name: str
    last_name: str


class UserRegisterIn(Schema):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str


class SuccessResponse(Schema):
    message: str


class CourseSchemaOut(Schema):
    id: int
    name: str
    description: str
    price: int
    image: Optional[str]
    teacher: UserOut
    max_students: Optional[int]
    created_at: datetime
    updated_at: datetime


class CourseMemberOut(Schema):
    id: int
    course_id: CourseSchemaOut
    user_id: UserOut
    roles: str
    # created_at: datetime


class CourseSchemaIn(Schema):
    name: str
    description: str
    price: int


class CourseContentMini(Schema):
    id: int
    name: str
    description: str
    course_id: CourseSchemaOut
    release_time: Optional[datetime]
    is_published: bool
    created_at: datetime
    updated_at: datetime


class CourseContentFull(Schema):
    id: int
    name: str
    description: str
    video_url: Optional[str]
    file_attachment: Optional[str]
    course_id: CourseSchemaOut
    release_time: Optional[datetime]
    is_published: bool
    created_at: datetime
    updated_at: datetime


class CourseContentScheduleIn(Schema):
    release_time: datetime


class BatchEnrollIn(Schema):
    student_ids: list[int]


class UserActivityDashboard(Schema):
    total_courses_enrolled: int
    total_courses_teaching: int
    total_comments_posted: int
    recent_activities: list[str]


class CourseCommentOut(Schema):
    id: int
    content_id: CourseContentMini
    member_id: CourseMemberOut
    comment: str
    created_at: datetime
    updated_at: datetime


class CourseCommentIn(Schema):
    comment: str


class CourseAnalytics(Schema):
    course_id: int
    course_name: str
    total_students: int
    total_contents: int
    total_comments: int
    engagement_score: float
    recent_enrollments: int


class UserProfileOut(Schema):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    date_joined: datetime
    total_courses_enrolled: int
    total_courses_teaching: int


class UserProfileUpdateIn(Schema):
    email: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class CompletionTrackingOut(Schema):
    id: int
    user: UserOut
    content: CourseContentMini
    completed_at: datetime


class CompletionProgressOut(Schema):
    course_id: int
    course_name: str
    total_contents: int
    completed_contents: int
    completion_percentage: float
    completed_content_ids: list[int]


class BookmarkOut(Schema):
    id: int
    user: UserOut
    content: CourseContentMini
    created_at: datetime


class BookmarkListOut(Schema):
    bookmarks: list[BookmarkOut]
    total_count: int


class CourseCertificate(Schema):
    course_id: int
    course_name: str
    student_name: str
    teacher_name: str
    completion_date: datetime
    completion_percentage: float
    certificate_html: str


class CategoryOut(Schema):
    id: int
    name: str
    description: Optional[str]
    color: str
    created_at: datetime


class CategoryIn(Schema):
    name: str
    description: Optional[str] = None
    color: str = "#007bff"


class TagOut(Schema):
    id: int
    name: str
    created_at: datetime


class TagIn(Schema):
    name: str


class CourseWithCategoriesOut(Schema):
    id: int
    name: str
    description: str
    price: int
    image: Optional[str]
    teacher: UserOut
    max_students: Optional[int]
    categories: list[CategoryOut]
    created_at: datetime
    updated_at: datetime


class ContentWithTagsOut(Schema):
    id: int
    name: str
    description: str
    video_url: Optional[str]
    file_attachment: Optional[str]
    course_id: CourseSchemaOut
    release_time: Optional[datetime]
    is_published: bool
    tags: list[TagOut]
    created_at: datetime
    updated_at: datetime


class SearchFilters(Schema):
    query: Optional[str] = None
    category_ids: Optional[list[int]] = None
    tag_ids: Optional[list[int]] = None
    min_price: Optional[int] = None
    max_price: Optional[int] = None
    teacher_id: Optional[int] = None
    is_published: Optional[bool] = None
    has_available_slots: Optional[bool] = None


class SearchResultsOut(Schema):
    courses: list[CourseWithCategoriesOut]
    contents: list[ContentWithTagsOut]
    total_courses: int
    total_contents: int
    filters_applied: dict


class DiscussionThreadOut(Schema):
    id: int
    title: str
    description: str
    course: CourseSchemaOut
    author: UserOut
    is_pinned: bool
    is_locked: bool
    reply_count: int
    last_reply_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class DiscussionThreadIn(Schema):
    title: str
    description: str


class DiscussionReplyOut(Schema):
    id: int
    thread_id: int
    author: UserOut
    content: str
    parent_reply_id: Optional[int]
    is_solution: bool
    created_at: datetime
    updated_at: datetime


class DiscussionReplyIn(Schema):
    content: str
    parent_reply_id: Optional[int] = None


class ForumStatsOut(Schema):
    total_threads: int
    total_replies: int
    active_discussions: int
    recent_activity: list[str]


class NotificationOut(Schema):
    id: int
    recipient: UserOut
    sender: Optional[UserOut]
    title: str
    message: str
    notification_type: str
    is_read: bool
    related_course: Optional[CourseSchemaOut]
    related_content: Optional[CourseContentMini]
    action_url: Optional[str]
    created_at: datetime


class NotificationIn(Schema):
    title: str
    message: str
    notification_type: str = "announcement"
    action_url: Optional[str] = None


class NotificationPreferenceOut(Schema):
    email_notifications: bool
    enrollment_notifications: bool
    content_notifications: bool
    discussion_notifications: bool
    comment_notifications: bool
    completion_notifications: bool
    announcement_notifications: bool


class NotificationPreferenceIn(Schema):
    email_notifications: Optional[bool] = None
    enrollment_notifications: Optional[bool] = None
    content_notifications: Optional[bool] = None
    discussion_notifications: Optional[bool] = None
    comment_notifications: Optional[bool] = None
    completion_notifications: Optional[bool] = None
    announcement_notifications: Optional[bool] = None


class NotificationStatsOut(Schema):
    total_notifications: int
    unread_notifications: int
    notifications_by_type: dict
