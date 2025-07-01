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
    Category,
    Comment,
    CompletionTracking,
    ContentTag,
    Course,
    CourseCategory,
    CourseContent,
    CourseMember,
    DiscussionReply,
    DiscussionThread,
    Notification,
    NotificationPreference,
    Tag,
)
from lms_core.schema import (
    BatchEnrollIn,
    BookmarkListOut,
    BookmarkOut,
    CategoryIn,
    CategoryOut,
    CompletionProgressOut,
    CompletionTrackingOut,
    ContentWithTagsOut,
    CourseAnalytics,
    CourseCertificate,
    CourseCommentIn,
    CourseCommentOut,
    CourseContentFull,
    CourseContentMini,
    CourseContentScheduleIn,
    CourseMemberOut,
    CourseSchemaIn,
    CourseSchemaOut,
    CourseWithCategoriesOut,
    DiscussionReplyIn,
    DiscussionReplyOut,
    DiscussionThreadIn,
    DiscussionThreadOut,
    ForumStatsOut,
    NotificationIn,
    NotificationOut,
    NotificationPreferenceIn,
    NotificationPreferenceOut,
    NotificationStatsOut,
    SearchFilters,
    SearchResultsOut,
    SuccessResponse,
    TagIn,
    TagOut,
    UserActivityDashboard,
    UserOut,
    UserProfileOut,
    UserProfileUpdateIn,
    UserRegisterIn,
)
from ninja import File, Form, NinjaAPI, UploadedFile
from ninja.pagination import PageNumberPagination, paginate
from ninja.responses import Response
from ninja_simple_jwt.auth.ninja_auth import HttpJwtAuth
from ninja_simple_jwt.auth.views.api import mobile_auth_router
from .models import CourseContent, CourseMember, Bookmark

apiv1 = NinjaAPI()
apiv1.add_router("/auth/", mobile_auth_router)
apiAuth = HttpJwtAuth()


# === USER MANAGEMENT ===
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


# FITUR 8: MANAJEMEN PROFIL PENGGUNA (+2 Poin) - COMPLETELY FIXED VERSION
# Implementasi GET profile - menampilkan profil user dengan statistik
@apiv1.get("/user/profile", response=UserProfileOut, auth=apiAuth)
def show_profile(request):
    """Show current user's profile - FITUR 8 Part 1 (+1 Poin) - COMPLETELY FIXED"""
    try:
        # Get user from JWT token payload directly
        user = None

        # Method 1: Check if request has user attribute (Django standard)
        if hasattr(request, "user") and hasattr(request.user, "id"):
            user = request.user

        # Method 2: If request.auth has user info, extract user ID from token
        elif hasattr(request, "auth") and request.auth:
            # Try to get user_id from JWT payload
            try:
                # Get the raw token from Authorization header
                auth_header = request.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]

                    # Decode token to get user_id
                    import jwt
                    from django.conf import settings

                    decoded_token = jwt.decode(
                        token,
                        settings.NINJA_JWT["VERIFYING_KEY"],
                        algorithms=[settings.NINJA_JWT["ALGORITHM"]],
                    )

                    user_id = decoded_token.get("user_id")
                    if user_id:
                        user = User.objects.get(id=user_id)

            except Exception as e:
                print(f"JWT decode error: {e}")
                pass

        # Method 3: Fallback - if nothing works, return error
        if not user or not hasattr(user, "id"):
            return Response(
                {"error": "Authentication failed - unable to identify user"}, status=401
            )

        # Hitung statistik user untuk dashboard insight dengan error handling
        try:
            courses_enrolled = CourseMember.objects.filter(
                user_id=user, roles="std"
            ).count()
        except Exception:
            courses_enrolled = 0

        try:
            courses_teaching = Course.objects.filter(teacher=user).count()
        except Exception:
            courses_teaching = 0

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
        return Response({"error": f"Profile retrieval failed: {str(e)}"}, status=500)


# FITUR 8: MANAJEMEN PROFIL PENGGUNA (+2 Poin) - COMPLETELY FIXED VERSION
# Implementasi PUT profile - edit profil user dengan validasi
@apiv1.put("/user/profile", response=UserProfileOut, auth=apiAuth)
def edit_profile(request, profile_data: UserProfileUpdateIn):
    """Edit current user's profile - FITUR 8 Part 2 (+1 Poin) - COMPLETELY FIXED"""
    try:
        # Get user from JWT token payload directly (same method as above)
        user = None

        # Method 1: Check if request has user attribute (Django standard)
        if hasattr(request, "user") and hasattr(request.user, "id"):
            user = request.user

        # Method 2: If request.auth has user info, extract user ID from token
        elif hasattr(request, "auth") and request.auth:
            # Try to get user_id from JWT payload
            try:
                # Get the raw token from Authorization header
                auth_header = request.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]

                    # Decode token to get user_id
                    import jwt
                    from django.conf import settings

                    decoded_token = jwt.decode(
                        token,
                        settings.NINJA_JWT["VERIFYING_KEY"],
                        algorithms=[settings.NINJA_JWT["ALGORITHM"]],
                    )

                    user_id = decoded_token.get("user_id")
                    if user_id:
                        user = User.objects.get(id=user_id)

            except Exception as e:
                print(f"JWT decode error: {e}")
                pass

        # Method 3: Fallback - if nothing works, return error
        if not user or not hasattr(user, "id"):
            return Response(
                {"error": "Authentication failed - unable to identify user"}, status=401
            )

        # Validasi email duplikasi saat update (exclude user saat ini)
        if profile_data.email is not None:
            if (
                User.objects.filter(email=profile_data.email)
                .exclude(id=user.id)
                .exists()
            ):
                return Response({"error": "Email already exists"}, status=400)
            user.email = profile_data.email

        # Partial update - hanya update field yang disediakan
        if profile_data.first_name is not None:
            user.first_name = profile_data.first_name
        if profile_data.last_name is not None:
            user.last_name = profile_data.last_name

        user.save()

        # Return updated profile dengan statistik terbaru dengan error handling
        try:
            courses_enrolled = CourseMember.objects.filter(
                user_id=user, roles="std"
            ).count()
        except Exception:
            courses_enrolled = 0

        try:
            courses_teaching = Course.objects.filter(teacher=user).count()
        except Exception:
            courses_teaching = 0

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


# === COURSE MANAGEMENT ===
@apiv1.post("/courses/{course_id}/enroll", response=SuccessResponse, auth=apiAuth)
def enroll_in_course(request, course_id: int):
    """Enroll current user in a course with enrollment limit check"""
    try:
        course = Course.objects.get(id=course_id)
        
        # AWAL PERBAIKAN: Dapatkan user dari token JWT
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
            except jwt.ExpiredSignatureError:
                return Response({"error": "Token has expired"}, status=401)
            except jwt.InvalidTokenError:
                return Response({"error": "Invalid token"}, status=401)
            except User.DoesNotExist:
                 return Response({"error": "User not found"}, status=404)

        if not user:
            return Response({"error": "Authentication failed"}, status=401)
        # AKHIR PERBAIKAN

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


# === CONTENT MANAGEMENT ===
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


# === COMMENT MODERATION ===
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


# === COMPLETION TRACKING ===
@apiv1.post("/contents/{content_id}/complete", response=SuccessResponse, auth=apiAuth)
def mark_content_complete(request, content_id: int):
    """Mark content as completed by current user"""
    # ... (logika untuk mendapatkan user dari token sama seperti di atas) ...
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
        
        # === PERBAIKAN LOGIKA UTAMA ===
        course = content.course_id
        # =============================

        if not CourseMember.objects.filter(
            course_id=course, user_id=user
        ).exists():
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


@apiv1.delete("/contents/{content_id}/complete", response=SuccessResponse, auth=apiAuth)
def unmark_content_complete(request, content_id: int):
    """Remove completion mark from content"""
    # === AWAL PERBAIKAN ===
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
    # === AKHIR PERBAIKAN ===

    try:
        content = CourseContent.objects.get(id=content_id)

        # Sekarang pengecekan ini akan berhasil karena `user` adalah objek yang benar
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


# === BOOKMARKING ===
@apiv1.post("/contents/{content_id}/bookmark", response=SuccessResponse, auth=apiAuth)
def bookmark_content(request, content_id: int):
    """Bookmark a content for the current user"""
    # 1. Dapatkan user dari token (logika ini sudah benar)
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
        # 2. Ambil objek KONTEN menggunakan ID dari URL
        content = CourseContent.objects.get(id=content_id)

        # 3. KUNCI UTAMA: Dapatkan objek KURSUS dari relasi di model konten
        # Model CourseContent memiliki foreign key 'course_id' ke model Course
        course_object = content.course_id

        # 4. Periksa apakah user terdaftar di KURSUS yang benar
        is_member = CourseMember.objects.filter(course_id=course_object, user_id=user).exists()
        if not is_member:
            return Response({"error": "User not enrolled in this course"}, status=403)

        # 5. Logika untuk membuat atau menghapus bookmark
        bookmark, created = Bookmark.objects.get_or_create(content=content, user=user)
        if not created:
            bookmark.delete()
            return {"message": "Bookmark removed"}

        return {"message": "Successfully bookmarked"}

    except CourseContent.DoesNotExist:
        return Response({"error": "Content not found"}, status=404)


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


@apiv1.delete("/contents/{content_id}/bookmark", response=SuccessResponse, auth=apiAuth)
def remove_bookmark(request, content_id: int):
    """Remove content from bookmarks"""
    # === AWAL PERBAIKAN ===
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
    # === AKHIR PERBAIKAN ===

    try:
        content = CourseContent.objects.get(id=content_id)

        # Sekarang `user` adalah objek User yang benar
        bookmark = Bookmark.objects.filter(user=user, content=content).first()
        
        if bookmark:
            bookmark.delete()
            return {"message": "Bookmark removed successfully"}
        else:
            return Response({"error": "Content not bookmarked"}, status=404)
            
    except CourseContent.DoesNotExist:
        return Response({"error": "Content not found"}, status=404)


# === CERTIFICATES ===
@apiv1.get("/courses/{course_id}/certificate", response=CourseCertificate, auth=apiAuth)
def generate_course_certificate(request, course_id: int):
    """Generate course completion certificate"""
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
        completion_percentage = (
            (completed_count / total_contents * 100) if total_contents > 0 else 0.0
        )

        latest_completion = completed_contents.order_by("-completed_at").first()
        completion_date = (
            latest_completion.completed_at if latest_completion else timezone.now()
        )

        certificate_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Certificate of Completion</title>
            <style>
                body {{
                    font-family: 'Times New Roman', serif;
                    margin: 0;
                    padding: 40px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }}
                .certificate {{
                    background: white;
                    padding: 60px;
                    border: 10px solid #gold;
                    border-radius: 20px;
                    box-shadow: 0 0 30px rgba(0,0,0,0.3);
                    text-align: center;
                    max-width: 800px;
                    width: 100%;
                }}
                .header {{ font-size: 48px; color: #2c3e50; margin-bottom: 20px; font-weight: bold; }}
                .subtitle {{ font-size: 24px; color: #7f8c8d; margin-bottom: 40px; }}
                .recipient {{ font-size: 36px; color: #e74c3c; margin: 30px 0; font-weight: bold; }}
                .course-name {{ font-size: 28px; color: #3498db; margin: 30px 0; font-style: italic; }}
                .completion-info {{ font-size: 18px; color: #2c3e50; margin: 20px 0; }}
                .signatures {{ display: flex; justify-content: space-between; margin-top: 60px; padding-top: 30px; border-top: 2px solid #ecf0f1; }}
                .signature {{ text-align: center; }}
                .signature-line {{ border-bottom: 2px solid #2c3e50; width: 200px; margin-bottom: 10px; }}
                .date {{ font-size: 16px; color: #7f8c8d; margin-top: 40px; }}
            </style>
        </head>
        <body>
            <div class="certificate">
                <div class="header">CERTIFICATE OF COMPLETION</div>
                <div class="subtitle">This is to certify that</div>
                <div class="recipient">{user.first_name} {user.last_name}</div>
                <div class="subtitle">has successfully completed the course</div>
                <div class="course-name">"{course.name}"</div>
                <div class="completion-info">
                    Course Completion: {completion_percentage:.1f}%<br>
                    Contents Completed: {completed_count} of {total_contents}
                </div>
                <div class="signatures">
                    <div class="signature">
                        <div class="signature-line"></div>
                        <div>Instructor</div>
                        <div>{course.teacher.first_name} {course.teacher.last_name}</div>
                    </div>
                    <div class="signature">
                        <div class="signature-line"></div>
                        <div>Date of Completion</div>
                        <div>{completion_date.strftime('%B %d, %Y')}</div>
                    </div>
                </div>
                <div class="date">Certificate generated on {timezone.now().strftime('%B %d, %Y')}</div>
            </div>
        </body>
        </html>
        """

        return {
            "course_id": course.id,
            "course_name": course.name,
            "student_name": f"{user.first_name} {user.last_name}",
            "teacher_name": f"{course.teacher.first_name} {course.teacher.last_name}",
            "completion_date": completion_date,
            "completion_percentage": round(completion_percentage, 2),
            "certificate_html": certificate_html,
        }
    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)


# === CATEGORIES & TAGS SYSTEM ===
@apiv1.get("/categories", response=list[CategoryOut])
def get_all_categories(request):
    """Get all categories"""
    categories = Category.objects.all()
    return categories


@apiv1.post("/categories", response=CategoryOut, auth=apiAuth)
def create_category(request, category_data: CategoryIn):
    """Create a new category"""
    try:
        category = Category.objects.create(
            name=category_data.name,
            description=category_data.description,
            color=category_data.color,
        )
        return category
    except IntegrityError:
        return Response({"error": "Category with this name already exists"}, status=400)


@apiv1.get("/tags", response=list[TagOut])
def get_all_tags(request):
    """Get all tags"""
    tags = Tag.objects.all()
    return tags


@apiv1.post("/tags", response=TagOut, auth=apiAuth)
def create_tag(request, tag_data: TagIn):
    """Create a new tag"""
    try:
        tag = Tag.objects.create(name=tag_data.name)
        return tag
    except IntegrityError:
        return Response({"error": "Tag with this name already exists"}, status=400)


@apiv1.post(
    "/courses/{course_id}/categories/{category_id}",
    response=SuccessResponse,
    auth=apiAuth,
)
def assign_category_to_course(request, course_id: int, category_id: int):
    """Assign category to course"""
    try:
        course = Course.objects.get(id=course_id)
        category = Category.objects.get(id=category_id)

        course_category, created = CourseCategory.objects.get_or_create(
            course=course, category=category
        )

        if created:
            return {"message": "Category assigned to course successfully"}
        else:
            return {"message": "Category already assigned to this course"}
    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)
    except Category.DoesNotExist:
        return Response({"error": "Category not found"}, status=404)


@apiv1.post(
    "/contents/{content_id}/tags/{tag_id}", response=SuccessResponse, auth=apiAuth
)
def assign_tag_to_content(request, content_id: int, tag_id: int):
    """Assign tag to content"""
    try:
        content = CourseContent.objects.get(id=content_id)
        tag = Tag.objects.get(id=tag_id)

        content_tag, created = ContentTag.objects.get_or_create(
            content=content, tag=tag
        )

        if created:
            return {"message": "Tag assigned to content successfully"}
        else:
            return {"message": "Tag already assigned to this content"}
    except CourseContent.DoesNotExist:
        return Response({"error": "Content not found"}, status=404)
    except Tag.DoesNotExist:
        return Response({"error": "Tag not found"}, status=404)


# === ADVANCED SEARCH & FILTERING ===
@apiv1.post("/search", response=SearchResultsOut)
def advanced_search(request, filters: SearchFilters):
    """Advanced search with multiple filters"""
    courses_query = Course.objects.all()
    contents_query = CourseContent.objects.all()
    filters_applied = {}

    # Text search
    if filters.query:
        filters_applied["query"] = filters.query
        courses_query = courses_query.filter(
            Q(name__icontains=filters.query)
            | Q(description__icontains=filters.query)
            | Q(teacher__first_name__icontains=filters.query)
            | Q(teacher__last_name__icontains=filters.query)
        )
        contents_query = contents_query.filter(
            Q(name__icontains=filters.query)
            | Q(description__icontains=filters.query)
            | Q(course_id__name__icontains=filters.query)
        )

    # Category filter for courses
    if filters.category_ids:
        filters_applied["category_ids"] = filters.category_ids
        courses_query = courses_query.filter(
            coursecategory__category_id__in=filters.category_ids
        ).distinct()

    # Tag filter for contents
    if filters.tag_ids:
        filters_applied["tag_ids"] = filters.tag_ids
        contents_query = contents_query.filter(
            contenttag__tag_id__in=filters.tag_ids
        ).distinct()

    # Price range filter
    if filters.min_price is not None:
        filters_applied["min_price"] = filters.min_price
        courses_query = courses_query.filter(price__gte=filters.min_price)

    if filters.max_price is not None:
        filters_applied["max_price"] = filters.max_price
        courses_query = courses_query.filter(price__lte=filters.max_price)

    # Teacher filter
    if filters.teacher_id:
        filters_applied["teacher_id"] = filters.teacher_id
        courses_query = courses_query.filter(teacher_id=filters.teacher_id)

    # Published filter
    if filters.is_published is not None:
        filters_applied["is_published"] = filters.is_published
        contents_query = contents_query.filter(is_published=filters.is_published)

    # Available slots filter
    if filters.has_available_slots is not None:
        filters_applied["has_available_slots"] = filters.has_available_slots
        if filters.has_available_slots:
            courses_query = courses_query.annotate(
                current_students=Count(
                    "coursemember", filter=Q(coursemember__roles="std")
                )
            ).filter(
                Q(max_students__isnull=True) | Q(current_students__lt=F("max_students"))
            )
        else:
            courses_query = courses_query.annotate(
                current_students=Count(
                    "coursemember", filter=Q(coursemember__roles="std")
                )
            ).filter(
                max_students__isnull=False, current_students__gte=F("max_students")
            )

    # Build results
    courses = courses_query.prefetch_related("coursecategory_set__category")
    contents = contents_query.prefetch_related("contenttag_set__tag")

    course_results = []
    for course in courses:
        categories = []
        for course_category in course.coursecategory_set.all():
            categories.append(
                {
                    "id": course_category.category.id,
                    "name": course_category.category.name,
                    "description": course_category.category.description,
                    "color": course_category.category.color,
                    "created_at": course_category.category.created_at,
                }
            )

        course_results.append(
            {
                "id": course.id,
                "name": course.name,
                "description": course.description,
                "price": course.price,
                "image": course.image.url if course.image else None,
                "teacher": {
                    "id": course.teacher.id,
                    "email": course.teacher.email,
                    "first_name": course.teacher.first_name,
                    "last_name": course.teacher.last_name,
                },
                "max_students": course.max_students,
                "categories": categories,
                "created_at": course.created_at,
                "updated_at": course.updated_at,
            }
        )

    content_results = []
    for content in contents:
        tags = []
        for content_tag in content.contenttag_set.all():
            tags.append(
                {
                    "id": content_tag.tag.id,
                    "name": content_tag.tag.name,
                    "created_at": content_tag.tag.created_at,
                }
            )

        content_results.append(
            {
                "id": content.id,
                "name": content.name,
                "description": content.description,
                "video_url": content.video_url,
                "file_attachment": (
                    content.file_attachment.url if content.file_attachment else None
                ),
                "course_id": {
                    "id": content.course_id.id,
                    "name": content.course_id.name,
                    "description": content.course_id.description,
                    "price": content.course_id.price,
                    "image": (
                        content.course_id.image.url if content.course_id.image else None
                    ),
                    "teacher": {
                        "id": content.course_id.teacher.id,
                        "email": content.course_id.teacher.email,
                        "first_name": content.course_id.teacher.first_name,
                        "last_name": content.course_id.teacher.last_name,
                    },
                    "max_students": content.course_id.max_students,
                    "created_at": content.course_id.created_at,
                    "updated_at": content.course_id.updated_at,
                },
                "release_time": content.release_time,
                "is_published": content.is_published,
                "tags": tags,
                "created_at": content.created_at,
                "updated_at": content.updated_at,
            }
        )

    return {
        "courses": course_results,
        "contents": content_results,
        "total_courses": len(course_results),
        "total_contents": len(content_results),
        "filters_applied": filters_applied,
    }


# === DISCUSSION FORUMS ===
@apiv1.get(
    "/courses/{course_id}/discussions", response=list[DiscussionThreadOut], auth=apiAuth
)
def get_course_discussions(request, course_id: int):
    """Get all discussion threads for a course"""
    try:
        course = Course.objects.get(id=course_id)

        if not CourseMember.objects.filter(
            course_id=course, user_id=request.auth
        ).exists():
            return Response({"error": "User not enrolled in this course"}, status=403)

        threads = DiscussionThread.objects.filter(course=course).select_related(
            "author", "course"
        )

        result = []
        for thread in threads:
            last_reply = thread.last_reply()
            result.append(
                {
                    "id": thread.id,
                    "title": thread.title,
                    "description": thread.description,
                    "course": {
                        "id": course.id,
                        "name": course.name,
                        "description": course.description,
                        "price": course.price,
                        "image": course.image.url if course.image else None,
                        "teacher": {
                            "id": course.teacher.id,
                            "email": course.teacher.email,
                            "first_name": course.teacher.first_name,
                            "last_name": course.teacher.last_name,
                        },
                        "max_students": course.max_students,
                        "created_at": course.created_at,
                        "updated_at": course.updated_at,
                    },
                    "author": {
                        "id": thread.author.id,
                        "email": thread.author.email,
                        "first_name": thread.author.first_name,
                        "last_name": thread.author.last_name,
                    },
                    "is_pinned": thread.is_pinned,
                    "is_locked": thread.is_locked,
                    "reply_count": thread.reply_count(),
                    "last_reply_at": last_reply.created_at if last_reply else None,
                    "created_at": thread.created_at,
                    "updated_at": thread.updated_at,
                }
            )

        return result
    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)


@apiv1.post(
    "/courses/{course_id}/discussions", response=DiscussionThreadOut, auth=apiAuth
)
def create_discussion_thread(request, course_id: int, thread_data: DiscussionThreadIn):
    """Create a new discussion thread"""
    try:
        course = Course.objects.get(id=course_id)

        if not CourseMember.objects.filter(
            course_id=course, user_id=request.auth
        ).exists():
            return Response({"error": "User not enrolled in this course"}, status=403)

        thread = DiscussionThread.objects.create(
            title=thread_data.title,
            description=thread_data.description,
            course=course,
            author=request.auth,
        )

        return {
            "id": thread.id,
            "title": thread.title,
            "description": thread.description,
            "course": {
                "id": course.id,
                "name": course.name,
                "description": course.description,
                "price": course.price,
                "image": course.image.url if course.image else None,
                "teacher": {
                    "id": course.teacher.id,
                    "email": course.teacher.email,
                    "first_name": course.teacher.first_name,
                    "last_name": course.teacher.last_name,
                },
                "max_students": course.max_students,
                "created_at": course.created_at,
                "updated_at": course.updated_at,
            },
            "author": {
                "id": thread.author.id,
                "email": thread.author.email,
                "first_name": thread.author.first_name,
                "last_name": thread.author.last_name,
            },
            "is_pinned": thread.is_pinned,
            "is_locked": thread.is_locked,
            "reply_count": 0,
            "last_reply_at": None,
            "created_at": thread.created_at,
            "updated_at": thread.updated_at,
        }
    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)


@apiv1.get(
    "/discussions/{thread_id}/replies", response=list[DiscussionReplyOut], auth=apiAuth
)
def get_discussion_replies(request, thread_id: int):
    """Get all replies for a discussion thread"""
    try:
        thread = DiscussionThread.objects.get(id=thread_id)

        if not CourseMember.objects.filter(
            course_id=thread.course, user_id=request.auth
        ).exists():
            return Response({"error": "User not enrolled in this course"}, status=403)

        replies = DiscussionReply.objects.filter(thread=thread).select_related("author")

        result = []
        for reply in replies:
            result.append(
                {
                    "id": reply.id,
                    "thread_id": thread.id,
                    "author": {
                        "id": reply.author.id,
                        "email": reply.author.email,
                        "first_name": reply.author.first_name,
                        "last_name": reply.author.last_name,
                    },
                    "content": reply.content,
                    "parent_reply_id": (
                        reply.parent_reply.id if reply.parent_reply else None
                    ),
                    "is_solution": reply.is_solution,
                    "created_at": reply.created_at,
                    "updated_at": reply.updated_at,
                }
            )

        return result
    except DiscussionThread.DoesNotExist:
        return Response({"error": "Discussion thread not found"}, status=404)


@apiv1.post(
    "/discussions/{thread_id}/replies", response=DiscussionReplyOut, auth=apiAuth
)
def create_discussion_reply(request, thread_id: int, reply_data: DiscussionReplyIn):
    """Create a reply to a discussion thread"""
    try:
        thread = DiscussionThread.objects.get(id=thread_id)

        if not CourseMember.objects.filter(
            course_id=thread.course, user_id=request.auth
        ).exists():
            return Response({"error": "User not enrolled in this course"}, status=403)

        if thread.is_locked:
            return Response({"error": "Cannot reply to locked thread"}, status=403)

        parent_reply = None
        if reply_data.parent_reply_id:
            try:
                parent_reply = DiscussionReply.objects.get(
                    id=reply_data.parent_reply_id, thread=thread
                )
            except DiscussionReply.DoesNotExist:
                return Response({"error": "Parent reply not found"}, status=404)

        reply = DiscussionReply.objects.create(
            thread=thread,
            author=request.auth,
            content=reply_data.content,
            parent_reply=parent_reply,
        )

        thread.save()  # Update thread's updated_at timestamp

        return {
            "id": reply.id,
            "thread_id": thread.id,
            "author": {
                "id": reply.author.id,
                "email": reply.author.email,
                "first_name": reply.author.first_name,
                "last_name": reply.author.last_name,
            },
            "content": reply.content,
            "parent_reply_id": reply.parent_reply.id if reply.parent_reply else None,
            "is_solution": reply.is_solution,
            "created_at": reply.created_at,
            "updated_at": reply.updated_at,
        }
    except DiscussionThread.DoesNotExist:
        return Response({"error": "Discussion thread not found"}, status=404)


@apiv1.put("/discussions/{thread_id}/pin", response=SuccessResponse, auth=apiAuth)
def pin_discussion_thread(request, thread_id: int):
    """Pin/unpin a discussion thread (teacher only)"""
    try:
        thread = DiscussionThread.objects.get(id=thread_id)

        if thread.course.teacher != request.auth:
            return Response(
                {"error": "Only course teacher can pin threads"}, status=403
            )

        thread.is_pinned = not thread.is_pinned
        thread.save()

        action = "pinned" if thread.is_pinned else "unpinned"
        return {"message": f"Thread {action} successfully"}
    except DiscussionThread.DoesNotExist:
        return Response({"error": "Discussion thread not found"}, status=404)


@apiv1.put("/discussions/{thread_id}/lock", response=SuccessResponse, auth=apiAuth)
def lock_discussion_thread(request, thread_id: int):
    """Lock/unlock a discussion thread (teacher only)"""
    try:
        thread = DiscussionThread.objects.get(id=thread_id)

        if thread.course.teacher != request.auth:
            return Response(
                {"error": "Only course teacher can lock threads"}, status=403
            )

        thread.is_locked = not thread.is_locked
        thread.save()

        action = "locked" if thread.is_locked else "unlocked"
        return {"message": f"Thread {action} successfully"}
    except DiscussionThread.DoesNotExist:
        return Response({"error": "Discussion thread not found"}, status=404)


@apiv1.put("/replies/{reply_id}/mark-solution", response=SuccessResponse, auth=apiAuth)
def mark_reply_as_solution(request, reply_id: int):
    """Mark a reply as solution (thread author or teacher only)"""
    try:
        reply = DiscussionReply.objects.get(id=reply_id)
        thread = reply.thread

        if thread.author != request.auth and thread.course.teacher != request.auth:
            return Response(
                {"error": "Only thread author or course teacher can mark solutions"},
                status=403,
            )

        # Unmark any existing solution in this thread
        DiscussionReply.objects.filter(thread=thread, is_solution=True).update(
            is_solution=False
        )

        # Mark this reply as solution
        reply.is_solution = True
        reply.save()

        return {"message": "Reply marked as solution successfully"}
    except DiscussionReply.DoesNotExist:
        return Response({"error": "Reply not found"}, status=404)


@apiv1.get("/courses/{course_id}/forum-stats", response=ForumStatsOut, auth=apiAuth)
def get_forum_stats(request, course_id: int):
    """Get forum statistics for a course"""
    try:
        course = Course.objects.get(id=course_id)

        if not CourseMember.objects.filter(
            course_id=course, user_id=request.auth
        ).exists():
            return Response({"error": "User not enrolled in this course"}, status=403)

        total_threads = DiscussionThread.objects.filter(course=course).count()
        total_replies = DiscussionReply.objects.filter(thread__course=course).count()

        seven_days_ago = timezone.now() - timedelta(days=7)
        active_discussions = DiscussionThread.objects.filter(
            course=course, updated_at__gte=seven_days_ago
        ).count()

        recent_activities = []
        recent_threads = DiscussionThread.objects.filter(course=course).order_by(
            "-created_at"
        )[:3]
        for thread in recent_threads:
            recent_activities.append(f"New thread: {thread.title}")

        recent_replies = DiscussionReply.objects.filter(thread__course=course).order_by(
            "-created_at"
        )[:3]
        for reply in recent_replies:
            recent_activities.append(f"New reply in: {reply.thread.title}")

        return {
            "total_threads": total_threads,
            "total_replies": total_replies,
            "active_discussions": active_discussions,
            "recent_activity": recent_activities[:5],
        }
    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)


# === NOTIFICATION SYSTEM ===
@apiv1.get("/notifications", response=list[NotificationOut], auth=apiAuth)
def get_user_notifications(request):
    """Get current user's notifications"""
    user = request.auth

    notifications = (
        Notification.objects.filter(recipient=user)
        .select_related("sender", "related_course", "related_content")
        .order_by("-created_at")
    )

    result = []
    for notification in notifications:
        # Build sender info
        sender_info = None
        if notification.sender:
            sender_info = {
                "id": notification.sender.id,
                "email": notification.sender.email,
                "first_name": notification.sender.first_name,
                "last_name": notification.sender.last_name,
            }

        # Build related course info
        course_info = None
        if notification.related_course:
            course_info = {
                "id": notification.related_course.id,
                "name": notification.related_course.name,
                "description": notification.related_course.description,
                "price": notification.related_course.price,
                "image": (
                    notification.related_course.image.url
                    if notification.related_course.image
                    else None
                ),
                "teacher": {
                    "id": notification.related_course.teacher.id,
                    "email": notification.related_course.teacher.email,
                    "first_name": notification.related_course.teacher.first_name,
                    "last_name": notification.related_course.teacher.last_name,
                },
                "max_students": notification.related_course.max_students,
                "created_at": notification.related_course.created_at,
                "updated_at": notification.related_course.updated_at,
            }

        # Build related content info
        content_info = None
        if notification.related_content:
            content_info = {
                "id": notification.related_content.id,
                "name": notification.related_content.name,
                "description": notification.related_content.description,
                "course_id": course_info,
                "release_time": notification.related_content.release_time,
                "is_published": notification.related_content.is_published,
                "created_at": notification.related_content.created_at,
                "updated_at": notification.related_content.updated_at,
            }

        result.append(
            {
                "id": notification.id,
                "recipient": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "sender": sender_info,
                "title": notification.title,
                "message": notification.message,
                "notification_type": notification.notification_type,
                "is_read": notification.is_read,
                "related_course": course_info,
                "related_content": content_info,
                "action_url": notification.action_url,
                "created_at": notification.created_at,
            }
        )

    return result


@apiv1.put(
    "/notifications/{notification_id}/read", response=SuccessResponse, auth=apiAuth
)
def mark_notification_read(request, notification_id: int):
    """Mark a notification as read"""
    try:
        notification = Notification.objects.get(
            id=notification_id, recipient=request.auth
        )
        notification.is_read = True
        notification.save()

        return {"message": "Notification marked as read"}
    except Notification.DoesNotExist:
        return Response({"error": "Notification not found"}, status=404)


@apiv1.put("/notifications/mark-all-read", response=SuccessResponse, auth=apiAuth)
def mark_all_notifications_read(request):
    """Mark all notifications as read for current user"""
    user = request.auth

    updated_count = Notification.objects.filter(recipient=user, is_read=False).update(
        is_read=True
    )

    return {"message": f"Marked {updated_count} notifications as read"}


@apiv1.get("/notifications/stats", response=NotificationStatsOut, auth=apiAuth)
def get_notification_stats(request):
    """Get notification statistics for current user"""
    user = request.auth

    total_notifications = Notification.objects.filter(recipient=user).count()
    unread_notifications = Notification.objects.filter(
        recipient=user, is_read=False
    ).count()

    # Count notifications by type
    notifications_by_type = dict(
        Notification.objects.filter(recipient=user)
        .values("notification_type")
        .annotate(count=Count("id"))
        .values_list("notification_type", "count")
    )

    return {
        "total_notifications": total_notifications,
        "unread_notifications": unread_notifications,
        "notifications_by_type": notifications_by_type,
    }


@apiv1.get(
    "/notifications/preferences", response=NotificationPreferenceOut, auth=apiAuth
)
def get_notification_preferences(request):
    """Get current user's notification preferences"""
    user = request.auth

    preferences, created = NotificationPreference.objects.get_or_create(
        user=user,
        defaults={
            "email_notifications": True,
            "enrollment_notifications": True,
            "content_notifications": True,
            "discussion_notifications": True,
            "comment_notifications": True,
            "completion_notifications": True,
            "announcement_notifications": True,
        },
    )

    return {
        "email_notifications": preferences.email_notifications,
        "enrollment_notifications": preferences.enrollment_notifications,
        "content_notifications": preferences.content_notifications,
        "discussion_notifications": preferences.discussion_notifications,
        "comment_notifications": preferences.comment_notifications,
        "completion_notifications": preferences.completion_notifications,
        "announcement_notifications": preferences.announcement_notifications,
    }


@apiv1.put(
    "/notifications/preferences", response=NotificationPreferenceOut, auth=apiAuth
)
def update_notification_preferences(request, preference_data: NotificationPreferenceIn):
    """Update current user's notification preferences"""
    user = request.auth

    preferences, created = NotificationPreference.objects.get_or_create(user=user)

    # Update only provided fields
    if preference_data.email_notifications is not None:
        preferences.email_notifications = preference_data.email_notifications
    if preference_data.enrollment_notifications is not None:
        preferences.enrollment_notifications = preference_data.enrollment_notifications
    if preference_data.content_notifications is not None:
        preferences.content_notifications = preference_data.content_notifications
    if preference_data.discussion_notifications is not None:
        preferences.discussion_notifications = preference_data.discussion_notifications
    if preference_data.comment_notifications is not None:
        preferences.comment_notifications = preference_data.comment_notifications
    if preference_data.completion_notifications is not None:
        preferences.completion_notifications = preference_data.completion_notifications
    if preference_data.announcement_notifications is not None:
        preferences.announcement_notifications = (
            preference_data.announcement_notifications
        )

    preferences.save()

    return {
        "email_notifications": preferences.email_notifications,
        "enrollment_notifications": preferences.enrollment_notifications,
        "content_notifications": preferences.content_notifications,
        "discussion_notifications": preferences.discussion_notifications,
        "comment_notifications": preferences.comment_notifications,
        "completion_notifications": preferences.completion_notifications,
        "announcement_notifications": preferences.announcement_notifications,
    }


@apiv1.post("/notifications/send", response=SuccessResponse, auth=apiAuth)
def send_notification(request, notification_data: NotificationIn):
    """Send a notification (teachers can send to their course students)"""
    sender = request.auth

    # For this example, we'll send to all users (admin feature)
    # In real implementation, you'd restrict this based on user roles
    recipients = User.objects.all()

    notifications = []
    for recipient in recipients:
        notifications.append(
            Notification(
                recipient=recipient,
                sender=sender,
                title=notification_data.title,
                message=notification_data.message,
                notification_type=notification_data.notification_type,
                action_url=notification_data.action_url,
            )
        )

    Notification.objects.bulk_create(notifications)

    return {"message": f"Notification sent to {len(recipients)} users"}


# === UTILITY FUNCTIONS FOR AUTOMATIC NOTIFICATIONS ===
def create_enrollment_notification(user, course):
    """Create notification when user enrolls in a course"""
    Notification.objects.create(
        recipient=user,
        sender=course.teacher,
        title=f"Welcome to {course.name}",
        message=f"You have successfully enrolled in {course.name}. Start learning now!",
        notification_type="enrollment",
        related_course=course,
        action_url=f"/courses/{course.id}",
    )


def create_new_content_notification(content):
    """Create notification when new content is published"""
    # Get all students enrolled in the course
    students = User.objects.filter(
        coursemember__course_id=content.course_id, coursemember__roles="std"
    )

    notifications = []
    for student in students:
        notifications.append(
            Notification(
                recipient=student,
                sender=content.course_id.teacher,
                title=f"New content: {content.name}",
                message=f"New content '{content.name}' has been published in {content.course_id.name}",
                notification_type="new_content",
                related_course=content.course_id,
                related_content=content,
                action_url=f"/courses/{content.course_id.id}/contents/{content.id}",
            )
        )

    Notification.objects.bulk_create(notifications)


def create_discussion_notification(reply):
    """Create notification when someone replies to a discussion"""
    thread = reply.thread

    # Notify thread author if someone else replied
    if reply.author != thread.author:
        Notification.objects.create(
            recipient=thread.author,
            sender=reply.author,
            title=f"New reply in: {thread.title}",
            message=f"{reply.author.first_name} replied to your discussion thread",
            notification_type="discussion",
            related_course=thread.course,
            action_url=f"/courses/{thread.course.id}/discussions/{thread.id}",
        )

    # Notify course teacher if not the author
    if reply.author != thread.course.teacher and thread.author != thread.course.teacher:
        Notification.objects.create(
            recipient=thread.course.teacher,
            sender=reply.author,
            title=f"New discussion activity in {thread.course.name}",
            message=f"New reply in discussion: {thread.title}",
            notification_type="discussion",
            related_course=thread.course,
            action_url=f"/courses/{thread.course.id}/discussions/{thread.id}",
        )
