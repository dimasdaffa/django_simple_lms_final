# Django Simple LMS - Learning Management System

![Django](https://img.shields.io/badge/Django-5.1.6-green.svg)
![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg)
![API](https://img.shields.io/badge/API-Django%20Ninja-red.svg)

## 📋 Deskripsi

Django Simple LMS adalah sistem manajemen pembelajaran (Learning Management System) yang dibangun dengan Django dan Django Ninja. Sistem ini menyediakan fitur-fitur lengkap untuk mengelola kursus, konten pembelajaran, user management, dan berbagai fitur advanced lainnya.

## 🚀 Teknologi Stack

- **Backend**: Django 5.1.6
- **API Framework**: Django Ninja 1.3.0
- **Authentication**: JWT (django-ninja-simple-jwt)
- **Database**: MySQL 8.0+
- **Image Processing**: Pillow 11.1.0
- **Load Testing**: Locust 2.32.10

## 📊 Fitur dan Point System

### 🎯 **FITUR UTAMA (+17 Points Total)**

#### **FITUR 1: User Registration (+1 Point)**
- ✅ Endpoint registrasi user baru
- ✅ Validasi duplikasi username dan email
- ✅ Hash password untuk keamanan
- **Endpoint**: `POST /api/v1/register`

#### **FITUR 2: Comment Moderation (+1 Point)**
- ✅ Moderasi komentar dengan approval system
- ✅ Approve/reject komentar
- **Endpoint**: `PUT /api/v1/comments/{comment_id}/moderate`

#### **FITUR 3: Content Scheduling (+1 Point)**
- ✅ Penjadwalan rilis konten otomatis
- ✅ Set release time untuk konten
- **Endpoint**: `PUT /api/v1/contents/{content_id}/schedule`

#### **FITUR 4: Course Enrollment (+1 Point)**
- ✅ Enrollment user ke kursus
- ✅ Validasi enrollment limits
- **Endpoint**: `POST /api/v1/courses/{course_id}/enroll`

#### **FITUR 5: Batch Enrollment (+1 Point)**
- ✅ Enrollment massal multiple students
- ✅ Validasi slot tersedia
- ✅ Bulk operations untuk efisiensi
- **Endpoint**: `POST /api/v1/courses/{course_id}/batch-enroll`

#### **FITUR 6: User Activity Dashboard (+1 Point)**
- ✅ Dashboard aktivitas user
- ✅ Statistik enrollment dan engagement
- ✅ Recent activities tracking
- **Endpoint**: `GET /api/v1/user/dashboard`

#### **FITUR 7: Course Analytics (+1 Point)**
- ✅ Analytics dan statistik kursus
- ✅ Engagement scoring
- ✅ Enrollment trends
- **Endpoint**: `GET /api/v1/courses/{course_id}/analytics`

#### **FITUR 8: Profile Management (+2 Points)**
- ✅ **GET Profile (+1 Point)**: Tampilkan profil user dengan statistik
- ✅ **PUT Profile (+1 Point)**: Edit profil user dengan validasi
- **Endpoints**: 
  - `GET /api/v1/user/profile`
  - `PUT /api/v1/user/profile`

#### **FITUR 9: Content Approval Workflow (+2 Points)**
- ✅ **Publish Content (+1 Point)**: Workflow persetujuan konten
- ✅ **Unpublish Content (+1 Point)**: Workflow penghapusan publikasi
- **Endpoints**:
  - `PUT /api/v1/contents/{content_id}/publish`
  - `PUT /api/v1/contents/{content_id}/unpublish`

#### **FITUR 10: Content Completion Tracking (+3 Points)**
- ✅ **Mark Complete (+1 Point)**: Mark konten sebagai completed
- ✅ **Progress Tracking (+1 Point)**: Get progress course
- ✅ **Unmark Complete (+1 Point)**: Remove completion mark
- **Endpoints**:
  - `POST /api/v1/contents/{content_id}/complete`
  - `GET /api/v1/courses/{course_id}/progress`
  - `DELETE /api/v1/contents/{content_id}/complete`

#### **FITUR 11: Content Bookmarking (+3 Points)**
- ✅ **Add Bookmark (+1 Point)**: Save content favorit
- ✅ **Get Bookmarks (+1 Point)**: Retrieve saved content
- ✅ **Remove Bookmark (+1 Point)**: Unsave content
- **Endpoints**:
  - `POST /api/v1/contents/{content_id}/bookmark`
  - `GET /api/v1/user/bookmarks`
  - `DELETE /api/v1/contents/{content_id}/bookmark`



---
