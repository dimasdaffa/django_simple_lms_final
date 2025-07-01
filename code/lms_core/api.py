from datetime import timedelta

import jwt
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Count, F, Q
from django.utils import timezone
from lms_core.models import (
    Bookmark,
    Comment,
    CompletionTracking,
    Course,
    CourseContent,
    CourseMember,
)
from lms_core.schema import (
    BatchEnrollIn,
    BookmarkListOut,
    CompletionProgressOut,
    CourseAnalytics,
    CourseContentScheduleIn,
    SuccessResponse,
    UserActivityDashboard,
    UserOut,
    UserProfileOut,
    UserProfileUpdateIn,
    UserRegisterIn,
)
from ninja import NinjaAPI
from ninja.responses import Response
from ninja_simple_jwt.auth.ninja_auth import HttpJwtAuth
from ninja_simple_jwt.auth.views.api import mobile_auth_router

apiv1 = NinjaAPI()
apiv1.add_router("/auth/", mobile_auth_router)
apiAuth = HttpJwtAuth()


# FITUR 1: USER REGISTRATION (+1 Point)
@apiv1.post("/register", response=UserOut)
def register_user(request, user_data: UserRegisterIn):
    """Register a new user"""
    try:
        if User.objects.filter(username=user_data.username).exists():
            return Response({"error": "Username already exists"}, status=400)
        if User.objects.filter(email=user_data.email).exists():
            return Response({"error": "Email already exists"}, status=400)

        user = User.objects.create(
            username=user_data.username,
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            password=make_password(user_data.password),
        )
        return user
    except IntegrityError:
        return Response({"error": "Failed to create user"}, status=400)


# FITUR 8: PROFILE MANAGEMENT (+2 Points)
# Part 1: GET Profile (+1 Point)
@apiv1.get("/user/profile", response=UserProfileOut, auth=apiAuth)
def show_profile(request):
    """Show current user's profile with statistics"""
    user = None
    auth_header = request.headers.get("Authorization", "")

    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            decoded_token = jwt.decode(
                token,
                settings.NINJA_JWT["VERIFYING_KEY"],
                algorithms=[settings.NINJA_JWT["ALGORITHM"]],
            )
            user_id = decoded_token.get("user_id")

            if user_id:
                user = User.objects.get(id=user_id)

        except (jwt.InvalidTokenError, User.DoesNotExist):
            return Response({"error": "Invalid token or user not found"}, status=401)

    if not user:
        return Response({"error": "Authentication failed"}, status=401)

    try:
        courses_enrolled = CourseMember.objects.filter(
            user_id=user, roles="std"
        ).count()
        courses_teaching = Course.objects.filter(teacher=user).count()

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "date_joined": user.date_joined,
            "total_courses_enrolled": courses_enrolled,
            "total_courses_teaching": courses_teaching,
        }
    except Exception as e:
        return Response({"error": f"Profile retrieval failed: {str(e)}"}, status=500)


# Part 2: PUT Profile (+1 Point)
@apiv1.put("/user/profile", response=UserProfileOut, auth=apiAuth)
def edit_profile(request, profile_data: UserProfileUpdateIn):
    """Edit current user's profile with validation"""
    try:
        user = None
        auth_header = request.headers.get("Authorization", "")

        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                decoded_token = jwt.decode(
                    token,
                    settings.NINJA_JWT["VERIFYING_KEY"],
                    algorithms=[settings.NINJA_JWT["ALGORITHM"]],
                )
                user_id = decoded_token.get("user_id")
                if user_id:
                    user = User.objects.get(id=user_id)
            except Exception as e:
                return Response({"error": "Invalid token"}, status=401)

        if not user:
            return Response({"error": "Authentication failed"}, status=401)

        # Validate email duplication (exclude current user)
        if profile_data.email is not None:
            if (
                User.objects.filter(email=profile_data.email)
                .exclude(id=user.id)
                .exists()
            ):
                return Response({"error": "Email already exists"}, status=400)
            user.email = profile_data.email

        # Partial update - only update provided fields
        if profile_data.first_name is not None:
            user.first_name = profile_data.first_name
        if profile_data.last_name is not None:
            user.last_name = profile_data.last_name

        user.save()

        # Return updated profile with statistics
        courses_enrolled = CourseMember.objects.filter(
            user_id=user, roles="std"
        ).count()
        courses_teaching = Course.objects.filter(teacher=user).count()

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "date_joined": user.date_joined,
            "total_courses_enrolled": courses_enrolled,
            "total_courses_teaching": courses_teaching,
        }
    except Exception as e:
        return Response({"error": f"Profile update failed: {str(e)}"}, status=500)


# FITUR 6: USER ACTIVITY DASHBOARD (+1 Point)
@apiv1.get("/user/dashboard", response=UserActivityDashboard, auth=apiAuth)
def get_user_activity_dashboard(request):
    """Get user activity dashboard with statistics"""
    user = request.auth

    courses_enrolled = CourseMember.objects.filter(user_id=user, roles="std").count()
    courses_teaching = Course.objects.filter(teacher=user).count()
    comments_posted = Comment.objects.filter(member_id__user_id=user).count()

    recent_activities = []
    recent_enrollments = CourseMember.objects.filter(
        user_id=user, roles="std"
    ).order_by("-created_at")[:3]

    for enrollment in recent_enrollments:
        recent_activities.append(f"Enrolled in {enrollment.course_id.name}")

    recent_comments = Comment.objects.filter(member_id__user_id=user).order_by(
        "-created_at"
    )[:3]

    for comment in recent_comments:
        recent_activities.append(f"Commented on {comment.content_id.name}")

    return {
        "total_courses_enrolled": courses_enrolled,
        "total_courses_teaching": courses_teaching,
        "total_comments_posted": comments_posted,
        "recent_activities": recent_activities[:5],
    }


# FITUR 4: COURSE ENROLLMENT (+1 Point)
@apiv1.post("/courses/{course_id}/enroll", response=SuccessResponse, auth=apiAuth)
def enroll_in_course(request, course_id: int):
    """Enroll current user in a course with enrollment limit check"""
    try:
        course = Course.objects.get(id=course_id)

        user = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                decoded_token = jwt.decode(
                    token,
                    settings.NINJA_JWT["VERIFYING_KEY"],
                    algorithms=[settings.NINJA_JWT["ALGORITHM"]],
                )
                user_id = decoded_token.get("user_id")
                if user_id:
                    user = User.objects.get(id=user_id)
            except (
                jwt.ExpiredSignatureError,
                jwt.InvalidTokenError,
                User.DoesNotExist,
            ):
                return Response(
                    {"error": "Invalid token or user not found"}, status=401
                )

        if not user:
            return Response({"error": "Authentication failed"}, status=401)

        if CourseMember.objects.filter(course_id=course, user_id=user).exists():
            return Response(
                {"error": "User already enrolled in this course"}, status=400
            )

        if course.is_enrollment_full():
            return Response({"error": "Course enrollment is full"}, status=400)

        CourseMember.objects.create(course_id=course, user_id=user, roles="std")
        return {"message": "Successfully enrolled in course"}
    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)


# FITUR 5: BATCH ENROLLMENT (+1 Point)
@apiv1.post("/courses/{course_id}/batch-enroll", response=SuccessResponse, auth=apiAuth)
def batch_enroll_students(request, course_id: int, enrollment_data: BatchEnrollIn):
    """Batch enroll multiple students in a course"""
    try:
        course = Course.objects.get(id=course_id)

        valid_students = User.objects.filter(id__in=enrollment_data.student_ids)
        valid_student_ids = list(valid_students.values_list("id", flat=True))

        already_enrolled = CourseMember.objects.filter(
            course_id=course, user_id__in=valid_student_ids
        ).values_list("user_id", flat=True)

        students_to_enroll = [
            sid for sid in valid_student_ids if sid not in already_enrolled
        ]

        if course.max_students:
            current_count = course.current_student_count()
            available_slots = course.max_students - current_count
            if len(students_to_enroll) > available_slots:
                return Response(
                    {
                        "error": f"Cannot enroll {len(students_to_enroll)} students. Only {available_slots} slots available."
                    },
                    status=400,
                )

        memberships = [
            CourseMember(course_id=course, user_id_id=student_id, roles="std")
            for student_id in students_to_enroll
        ]

        CourseMember.objects.bulk_create(memberships)
        return {"message": f"Successfully enrolled {len(students_to_enroll)} students"}
    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)


# FITUR 7: COURSE ANALYTICS (+1 Point)
@apiv1.get("/courses/{course_id}/analytics", response=CourseAnalytics, auth=apiAuth)
def get_course_analytics(request, course_id: int):
    """Get course analytics and statistics"""
    try:
        course = Course.objects.get(id=course_id)

        total_students = CourseMember.objects.filter(
            course_id=course, roles="std"
        ).count()
        total_contents = CourseContent.objects.filter(course_id=course).count()
        total_comments = Comment.objects.filter(content_id__course_id=course).count()

        engagement_score = (
            (total_comments / total_students) if total_students > 0 else 0.0
        )

        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_enrollments = CourseMember.objects.filter(
            course_id=course, roles="std", created_at__gte=thirty_days_ago
        ).count()

        return {
            "course_id": course.id,
            "course_name": course.name,
            "total_students": total_students,
            "total_contents": total_contents,
            "total_comments": total_comments,
            "engagement_score": round(engagement_score, 2),
            "recent_enrollments": recent_enrollments,
        }
    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)


# FITUR 3: CONTENT SCHEDULING (+1 Point)
@apiv1.put("/contents/{content_id}/schedule", response=SuccessResponse, auth=apiAuth)
def schedule_content(request, content_id: int, schedule_data: CourseContentScheduleIn):
    """Schedule content release time"""
    try:
        content = CourseContent.objects.get(id=content_id)
        content.release_time = schedule_data.release_time
        content.save()
        return {"message": "Content scheduled successfully"}
    except CourseContent.DoesNotExist:
        return Response({"error": "Content not found"}, status=404)


# FITUR 9: CONTENT APPROVAL WORKFLOW (+2 Points)
# Part 1: Publish Content (+1 Point)
@apiv1.put("/contents/{content_id}/publish", response=SuccessResponse, auth=apiAuth)
def publish_content(request, content_id: int):
    """Publish content"""
    try:
        content = CourseContent.objects.get(id=content_id)
        content.is_published = True
        content.save()
        return {"message": "Content published successfully"}
    except CourseContent.DoesNotExist:
        return Response({"error": "Content not found"}, status=404)


# Part 2: Unpublish Content (+1 Point)
@apiv1.put("/contents/{content_id}/unpublish", response=SuccessResponse, auth=apiAuth)
def unpublish_content(request, content_id: int):
    """Unpublish content"""
    try:
        content = CourseContent.objects.get(id=content_id)
        content.is_published = False
        content.save()
        return {"message": "Content unpublished successfully"}
    except CourseContent.DoesNotExist:
        return Response({"error": "Content not found"}, status=404)


# FITUR 2: COMMENT MODERATION (+1 Point)
@apiv1.put("/comments/{comment_id}/moderate", response=SuccessResponse, auth=apiAuth)
def moderate_comment(request, comment_id: int, approved: bool = True):
    """Moderate a comment (approve/reject)"""
    try:
        comment = Comment.objects.get(id=comment_id)
        comment.is_approved = approved
        comment.save()

        status = "approved" if approved else "rejected"
        return {"message": f"Comment {status} successfully"}
    except Comment.DoesNotExist:
        return Response({"error": "Comment not found"}, status=404)


# FITUR 10: CONTENT COMPLETION TRACKING (+3 Points)
# Part 1: Mark Complete (+1 Point)
@apiv1.post("/contents/{content_id}/complete", response=SuccessResponse, auth=apiAuth)
def mark_content_complete(request, content_id: int):
    """Mark content as completed by current user"""
    user = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            decoded_token = jwt.decode(
                token,
                settings.NINJA_JWT["VERIFYING_KEY"],
                algorithms=[settings.NINJA_JWT["ALGORITHM"]],
            )
            user_id = decoded_token.get("user_id")
            if user_id:
                user = User.objects.get(id=user_id)
        except (jwt.InvalidTokenError, User.DoesNotExist):
            return Response({"error": "Invalid token or user not found"}, status=401)
    if not user:
        return Response({"error": "Authentication failed"}, status=401)

    try:
        content = CourseContent.objects.get(id=content_id)
        course = content.course_id

        if not CourseMember.objects.filter(course_id=course, user_id=user).exists():
            return Response({"error": "User not enrolled in this course"}, status=403)

        completion, created = CompletionTracking.objects.get_or_create(
            user=user, content=content
        )

        if created:
            return {"message": "Content marked as completed"}
        else:
            return {"message": "Content already completed"}
    except CourseContent.DoesNotExist:
        return Response({"error": "Content not found"}, status=404)


# Part 2: Progress Tracking (+1 Point)
@apiv1.get(
    "/courses/{course_id}/progress", response=CompletionProgressOut, auth=apiAuth
)
def get_course_progress(request, course_id: int):
    """Get current user's progress in a course"""
    try:
        course = Course.objects.get(id=course_id)
        user = request.auth

        if not CourseMember.objects.filter(course_id=course, user_id=user).exists():
            return Response({"error": "User not enrolled in this course"}, status=403)

        total_contents = CourseContent.objects.filter(
            course_id=course, is_published=True
        ).count()
        completed_contents = CompletionTracking.objects.filter(
            user=user, content__course_id=course, content__is_published=True
        )

        completed_count = completed_contents.count()
        completed_content_ids = list(
            completed_contents.values_list("content_id", flat=True)
        )
        completion_percentage = (
            (completed_count / total_contents * 100) if total_contents > 0 else 0.0
        )

        return {
            "course_id": course.id,
            "course_name": course.name,
            "total_contents": total_contents,
            "completed_contents": completed_count,
            "completion_percentage": round(completion_percentage, 2),
            "completed_content_ids": completed_content_ids,
        }
    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)


# Part 3: Unmark Complete (+1 Point)
@apiv1.delete("/contents/{content_id}/complete", response=SuccessResponse, auth=apiAuth)
def unmark_content_complete(request, content_id: int):
    """Remove completion mark from content"""
    user = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            decoded_token = jwt.decode(
                token,
                settings.NINJA_JWT["VERIFYING_KEY"],
                algorithms=[settings.NINJA_JWT["ALGORITHM"]],
            )
            user_id = decoded_token.get("user_id")
            if user_id:
                user = User.objects.get(id=user_id)
        except (jwt.InvalidTokenError, User.DoesNotExist):
            return Response({"error": "Invalid token or user not found"}, status=401)

    if not user:
        return Response({"error": "Authentication failed"}, status=401)

    try:
        content = CourseContent.objects.get(id=content_id)

        if not CourseMember.objects.filter(
            course_id=content.course_id, user_id=user
        ).exists():
            return Response({"error": "User not enrolled in this course"}, status=403)

        completion = CompletionTracking.objects.filter(
            user=user, content=content
        ).first()

        if completion:
            completion.delete()
            return {"message": "Completion mark removed"}
        else:
            return Response({"error": "Content not marked as completed"}, status=404)

    except CourseContent.DoesNotExist:
        return Response({"error": "Content not found"}, status=404)


# FITUR 11: CONTENT BOOKMARKING (+3 Points)
# Part 1: Add Bookmark (+1 Point)
@apiv1.post("/contents/{content_id}/bookmark", response=SuccessResponse, auth=apiAuth)
def bookmark_content(request, content_id: int):
    """Bookmark a content for the current user"""
    user = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            decoded_token = jwt.decode(
                token,
                settings.NINJA_JWT["VERIFYING_KEY"],
                algorithms=[settings.NINJA_JWT["ALGORITHM"]],
            )
            user_id = decoded_token.get("user_id")
            if user_id:
                user = User.objects.get(id=user_id)
        except (jwt.InvalidTokenError, User.DoesNotExist):
            return Response({"error": "Invalid token or user not found"}, status=401)

    if not user:
        return Response({"error": "Authentication failed"}, status=401)

    try:
        content = CourseContent.objects.get(id=content_id)
        course_object = content.course_id

        # Check if user is enrolled in the course
        is_member = CourseMember.objects.filter(
            course_id=course_object, user_id=user
        ).exists()
        if not is_member:
            return Response({"error": "User not enrolled in this course"}, status=403)

        # Create or remove bookmark
        bookmark, created = Bookmark.objects.get_or_create(content=content, user=user)
        if not created:
            bookmark.delete()
            return {"message": "Bookmark removed"}

        return {"message": "Successfully bookmarked"}

    except CourseContent.DoesNotExist:
        return Response({"error": "Content not found"}, status=404)


# Part 2: Get Bookmarks (+1 Point)
@apiv1.get("/user/bookmarks", response=BookmarkListOut, auth=apiAuth)
def get_user_bookmarks(request):
    """Get current user's bookmarked contents"""
    user = request.auth

    bookmarks = (
        Bookmark.objects.filter(user=user)
        .select_related("content", "content__course_id", "content__course_id__teacher")
        .order_by("-created_at")
    )

    bookmark_list = []
    for bookmark in bookmarks:
        bookmark_list.append(
            {
                "id": bookmark.id,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "content": {
                    "id": bookmark.content.id,
                    "name": bookmark.content.name,
                    "description": bookmark.content.description,
                    "course_id": {
                        "id": bookmark.content.course_id.id,
                        "name": bookmark.content.course_id.name,
                        "description": bookmark.content.course_id.description,
                        "price": bookmark.content.course_id.price,
                        "image": (
                            bookmark.content.course_id.image.url
                            if bookmark.content.course_id.image
                            else None
                        ),
                        "teacher": {
                            "id": bookmark.content.course_id.teacher.id,
                            "email": bookmark.content.course_id.teacher.email,
                            "first_name": bookmark.content.course_id.teacher.first_name,
                            "last_name": bookmark.content.course_id.teacher.last_name,
                        },
                        "max_students": bookmark.content.course_id.max_students,
                        "created_at": bookmark.content.course_id.created_at,
                        "updated_at": bookmark.content.course_id.updated_at,
                    },
                    "release_time": bookmark.content.release_time,
                    "is_published": bookmark.content.is_published,
                    "created_at": bookmark.content.created_at,
                    "updated_at": bookmark.content.updated_at,
                },
                "created_at": bookmark.created_at,
            }
        )

    return {"bookmarks": bookmark_list, "total_count": len(bookmark_list)}


# Part 3: Remove Bookmark (+1 Point)
@apiv1.delete("/contents/{content_id}/bookmark", response=SuccessResponse, auth=apiAuth)
def remove_bookmark(request, content_id: int):
    """Remove content from bookmarks"""
    user = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            decoded_token = jwt.decode(
                token,
                settings.NINJA_JWT["VERIFYING_KEY"],
                algorithms=[settings.NINJA_JWT["ALGORITHM"]],
            )
            user_id = decoded_token.get("user_id")
            if user_id:
                user = User.objects.get(id=user_id)
        except (jwt.InvalidTokenError, User.DoesNotExist):
            return Response({"error": "Invalid token or user not found"}, status=401)

    if not user:
        return Response({"error": "Authentication failed"}, status=401)

    try:
        content = CourseContent.objects.get(id=content_id)
        bookmark = Bookmark.objects.filter(user=user, content=content).first()

        if bookmark:
            bookmark.delete()
            return {"message": "Bookmark removed successfully"}
        else:
            return Response({"error": "Content not bookmarked"}, status=404)

    except CourseContent.DoesNotExist:
        return Response({"error": "Content not found"}, status=404)
