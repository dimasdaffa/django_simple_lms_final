from django.contrib.auth.models import User
from django.db import models


# Create your models here.
class Course(models.Model):
    name = models.CharField("Nama Kursus", max_length=255)
    description = models.TextField("Deskripsi")
    price = models.IntegerField("Harga")
    image = models.ImageField("Gambar", upload_to="course", blank=True, null=True)
    teacher = models.ForeignKey(
        User, verbose_name="Pengajar", on_delete=models.RESTRICT
    )
    max_students = models.IntegerField("Maksimal Siswa", null=True, blank=True)
    created_at = models.DateTimeField("Dibuat pada", auto_now_add=True)
    updated_at = models.DateTimeField("Diperbarui pada", auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Mata Kuliah"
        verbose_name_plural = "Data Mata Kuliah"
        ordering = ["-created_at"]

    def is_member(self, user):
        return CourseMember.objects.filter(course_id=self, user_id=user).exists()

    def current_student_count(self):
        return CourseMember.objects.filter(course_id=self, roles="std").count()

    def is_enrollment_full(self):
        if self.max_students is None:
            return False
        return self.current_student_count() >= self.max_students


ROLE_OPTIONS = [("std", "Siswa"), ("ast", "Asisten")]


class CourseMember(models.Model):
    course_id = models.ForeignKey(
        Course, verbose_name="matkul", on_delete=models.RESTRICT
    )
    user_id = models.ForeignKey(User, verbose_name="siswa", on_delete=models.RESTRICT)
    roles = models.CharField("peran", max_length=3, choices=ROLE_OPTIONS, default="std")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Subscriber Matkul"
        verbose_name_plural = "Subscriber Matkul"

    def __str__(self) -> str:
        return f"{self.id} {self.course_id} : {self.user_id}"


class CourseContent(models.Model):
    name = models.CharField("judul konten", max_length=200)
    description = models.TextField("deskripsi", default="-")
    video_url = models.CharField("URL Video", max_length=200, null=True, blank=True)
    file_attachment = models.FileField("File", null=True, blank=True)
    course_id = models.ForeignKey(
        Course, verbose_name="matkul", on_delete=models.RESTRICT
    )
    parent_id = models.ForeignKey(
        "self", verbose_name="induk", on_delete=models.RESTRICT, null=True, blank=True
    )
    release_time = models.DateTimeField("waktu rilis", null=True, blank=True)
    is_published = models.BooleanField("dipublikasi", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Konten Matkul"
        verbose_name_plural = "Konten Matkul"

    def __str__(self) -> str:
        return f"{self.course_id} {self.name}"


class Comment(models.Model):
    content_id = models.ForeignKey(
        CourseContent, verbose_name="konten", on_delete=models.CASCADE
    )
    member_id = models.ForeignKey(
        CourseMember, verbose_name="pengguna", on_delete=models.CASCADE
    )
    comment = models.TextField("komentar")
    is_approved = models.BooleanField("disetujui", default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Komentar"
        verbose_name_plural = "Komentar"

    def __str__(self) -> str:
        return "Komen: " + str(self.member_id.user_id) + "-" + self.comment


class CompletionTracking(models.Model):
    user = models.ForeignKey(User, verbose_name="pengguna", on_delete=models.CASCADE)
    content = models.ForeignKey(
        CourseContent, verbose_name="konten", on_delete=models.CASCADE
    )
    completed_at = models.DateTimeField("diselesaikan pada", auto_now_add=True)

    class Meta:
        verbose_name = "Tracking Penyelesaian"
        verbose_name_plural = "Tracking Penyelesaian"
        unique_together = ("user", "content")  # Prevent duplicate completions

    def __str__(self) -> str:
        return f"{self.user.username} completed {self.content.name}"


class Bookmark(models.Model):
    user = models.ForeignKey(User, verbose_name="pengguna", on_delete=models.CASCADE)
    content = models.ForeignKey(
        CourseContent, verbose_name="konten", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField("dibuat pada", auto_now_add=True)

    class Meta:
        verbose_name = "Bookmark"
        verbose_name_plural = "Bookmarks"
        unique_together = ("user", "content")  # Prevent duplicate bookmarks

    def __str__(self) -> str:
        return f"{self.user.username} bookmarked {self.content.name}"


class Category(models.Model):
    name = models.CharField("nama kategori", max_length=100, unique=True)
    description = models.TextField("deskripsi", blank=True, null=True)
    color = models.CharField("warna", max_length=7, default="#007bff")  # hex color
    created_at = models.DateTimeField("dibuat pada", auto_now_add=True)

    class Meta:
        verbose_name = "Kategori"
        verbose_name_plural = "Kategori"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tag(models.Model):
    name = models.CharField("nama tag", max_length=50, unique=True)
    created_at = models.DateTimeField("dibuat pada", auto_now_add=True)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        ordering = ["name"]

    def __str__(self):
        return self.name


class CourseCategory(models.Model):
    course = models.ForeignKey(Course, verbose_name="kursus", on_delete=models.CASCADE)
    category = models.ForeignKey(
        Category, verbose_name="kategori", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField("dibuat pada", auto_now_add=True)

    class Meta:
        verbose_name = "Kategori Kursus"
        verbose_name_plural = "Kategori Kursus"
        unique_together = ("course", "category")

    def __str__(self):
        return f"{self.course.name} - {self.category.name}"


class ContentTag(models.Model):
    content = models.ForeignKey(
        CourseContent, verbose_name="konten", on_delete=models.CASCADE
    )
    tag = models.ForeignKey(Tag, verbose_name="tag", on_delete=models.CASCADE)
    created_at = models.DateTimeField("dibuat pada", auto_now_add=True)

    class Meta:
        verbose_name = "Tag Konten"
        verbose_name_plural = "Tag Konten"
        unique_together = ("content", "tag")

    def __str__(self):
        return f"{self.content.name} - {self.tag.name}"


class DiscussionThread(models.Model):
    title = models.CharField("judul diskusi", max_length=200)
    description = models.TextField("deskripsi")
    course = models.ForeignKey(Course, verbose_name="kursus", on_delete=models.CASCADE)
    author = models.ForeignKey(User, verbose_name="penulis", on_delete=models.CASCADE)
    is_pinned = models.BooleanField("disematkan", default=False)
    is_locked = models.BooleanField("dikunci", default=False)
    created_at = models.DateTimeField("dibuat pada", auto_now_add=True)
    updated_at = models.DateTimeField("diperbarui pada", auto_now=True)

    class Meta:
        verbose_name = "Thread Diskusi"
        verbose_name_plural = "Thread Diskusi"
        ordering = ["-is_pinned", "-updated_at"]

    def __str__(self):
        return f"{self.course.name} - {self.title}"

    def reply_count(self):
        return self.discussionreply_set.count()

    def last_reply(self):
        return self.discussionreply_set.order_by("-created_at").first()


class DiscussionReply(models.Model):
    thread = models.ForeignKey(
        DiscussionThread, verbose_name="thread", on_delete=models.CASCADE
    )
    author = models.ForeignKey(User, verbose_name="penulis", on_delete=models.CASCADE)
    content = models.TextField("konten")
    parent_reply = models.ForeignKey(
        "self",
        verbose_name="balasan induk",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    is_solution = models.BooleanField("solusi", default=False)
    created_at = models.DateTimeField("dibuat pada", auto_now_add=True)
    updated_at = models.DateTimeField("diperbarui pada", auto_now=True)

    class Meta:
        verbose_name = "Balasan Diskusi"
        verbose_name_plural = "Balasan Diskusi"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.thread.title} - {self.author.username}"


NOTIFICATION_TYPES = [
    ("enrollment", "Enrollment"),
    ("new_content", "New Content"),
    ("assignment", "Assignment"),
    ("discussion", "Discussion"),
    ("comment", "Comment"),
    ("completion", "Completion"),
    ("certificate", "Certificate"),
    ("announcement", "Announcement"),
]


class Notification(models.Model):
    recipient = models.ForeignKey(
        User,
        verbose_name="penerima",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    sender = models.ForeignKey(
        User,
        verbose_name="pengirim",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sent_notifications",
    )
    title = models.CharField("judul", max_length=200)
    message = models.TextField("pesan")
    notification_type = models.CharField(
        "tipe", max_length=20, choices=NOTIFICATION_TYPES, default="announcement"
    )
    is_read = models.BooleanField("sudah dibaca", default=False)
    related_course = models.ForeignKey(
        Course,
        verbose_name="kursus terkait",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    related_content = models.ForeignKey(
        CourseContent,
        verbose_name="konten terkait",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    action_url = models.CharField("URL aksi", max_length=500, null=True, blank=True)
    created_at = models.DateTimeField("dibuat pada", auto_now_add=True)

    class Meta:
        verbose_name = "Notifikasi"
        verbose_name_plural = "Notifikasi"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.recipient.username} - {self.title}"


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        User,
        verbose_name="pengguna",
        on_delete=models.CASCADE,
        related_name="notification_preferences",
    )
    email_notifications = models.BooleanField("notifikasi email", default=True)
    enrollment_notifications = models.BooleanField(
        "notifikasi enrollment", default=True
    )
    content_notifications = models.BooleanField("notifikasi konten baru", default=True)
    discussion_notifications = models.BooleanField("notifikasi diskusi", default=True)
    comment_notifications = models.BooleanField("notifikasi komentar", default=True)
    completion_notifications = models.BooleanField(
        "notifikasi penyelesaian", default=True
    )
    announcement_notifications = models.BooleanField(
        "notifikasi pengumuman", default=True
    )

    class Meta:
        verbose_name = "Preferensi Notifikasi"
        verbose_name_plural = "Preferensi Notifikasi"

    def __str__(self):
        return f"{self.user.username} notification preferences"
