import json
import random
import string

from locust import HttpUser, TaskSet, between, task


class LMSTestSuite(TaskSet):
    def on_start(self):
        """Setup test data and authenticate user"""
        self.base_url = "http://127.0.0.1:8000"
        self.token = None
        self.user_id = None
        self.course_id = None
        self.content_id = None
        self.comment_id = None
        self.discussion_id = None

        # Test user credentials
        self.test_username = "LarissaWylie"
        self.test_password = "RLS71GOH8GF"

        self.authenticate_user()

    def authenticate_user(self):
        """Test 2: User Login Test"""
        response = self.client.post(
            "/api/auth/sign-in",
            json={"username": self.test_username, "password": self.test_password},
        )

        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access")
            self.user_id = data.get("user_id")
            print(f"✅ Login Test PASSED - Token: {self.token[:20]}...")
        else:
            print(f"❌ Login Test FAILED - Status: {response.status_code}")

    @task(1)
    def test_user_registration(self):
        """Test 1: User Registration Test"""
        random_suffix = "".join(random.choices(string.ascii_lowercase, k=6))
        test_user = {
            "username": f"testuser_{random_suffix}",
            "email": f"test_{random_suffix}@example.com",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "User",
        }

        response = self.client.post("/api/auth/register", json=test_user)
        if response.status_code in [200, 201]:
            print("✅ User Registration Test PASSED")
        else:
            print(f"❌ User Registration Test FAILED - Status: {response.status_code}")

    @task(2)
    def test_jwt_token_validation(self):
        """Test 3: JWT Token Validation Test"""
        if not self.token:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.client.get("/api/auth/profile", headers=headers)

        if response.status_code == 200:
            print("✅ JWT Token Validation Test PASSED")
        else:
            print(
                f"❌ JWT Token Validation Test FAILED - Status: {response.status_code}"
            )

    @task(2)
    def test_user_profile_management(self):
        """Test 4: User Profile Management Test"""
        if not self.token:
            return

        headers = {"Authorization": f"Bearer {self.token}"}

        # GET profile
        response = self.client.get("/api/auth/profile", headers=headers)
        if response.status_code == 200:
            print("✅ Get Profile Test PASSED")

            # PUT profile update
            update_data = {"first_name": "Updated Name"}
            response = self.client.put(
                "/api/auth/profile", json=update_data, headers=headers
            )
            if response.status_code == 200:
                print("✅ Update Profile Test PASSED")
            else:
                print(f"❌ Update Profile Test FAILED - Status: {response.status_code}")
        else:
            print(f"❌ Get Profile Test FAILED - Status: {response.status_code}")

    @task(3)
    def test_course_listing(self):
        """Test 7: Course Listing Test"""
        response = self.client.get("/api/courses")
        if response.status_code == 200:
            courses = response.json()
            if courses:
                self.course_id = courses[0].get("id")
                print(f"✅ Course Listing Test PASSED - Found {len(courses)} courses")
            else:
                print("⚠️ Course Listing Test PASSED but no courses found")
        else:
            print(f"❌ Course Listing Test FAILED - Status: {response.status_code}")

    @task(3)
    def test_course_detail(self):
        """Test 8: Course Detail Test"""
        if not self.course_id:
            return

        response = self.client.get(f"/api/courses/{self.course_id}")
        if response.status_code == 200:
            print("✅ Course Detail Test PASSED")
        else:
            print(f"❌ Course Detail Test FAILED - Status: {response.status_code}")

    @task(2)
    def test_my_courses(self):
        """Test 10: My Courses Test"""
        if not self.token:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.client.get("/api/mycourses", headers=headers)

        if response.status_code == 200:
            my_courses = response.json()
            print(f"✅ My Courses Test PASSED - User has {len(my_courses)} courses")

            # Set course_id for further tests
            if my_courses:
                self.course_id = my_courses[0].get("course_id", {}).get("id")
        else:
            print(f"❌ My Courses Test FAILED - Status: {response.status_code}")

    @task(2)
    def test_course_enrollment(self):
        """Test 9: Course Enrollment Test"""
        if not self.token or not self.course_id:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.client.post(
            f"/api/courses/{self.course_id}/enroll", headers=headers
        )

        if response.status_code in [200, 201, 400]:  # 400 might be "already enrolled"
            print("✅ Course Enrollment Test PASSED")
        else:
            print(f"❌ Course Enrollment Test FAILED - Status: {response.status_code}")

    @task(3)
    def test_content_access(self):
        """Test 12: Content Access Test"""
        if not self.token or not self.course_id:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.client.get(
            f"/api/courses/{self.course_id}/contents", headers=headers
        )

        if response.status_code == 200:
            contents = response.json()
            if contents:
                self.content_id = contents[0].get("id")
                print(f"✅ Content Access Test PASSED - Found {len(contents)} contents")
            else:
                print("⚠️ Content Access Test PASSED but no contents found")
        else:
            print(f"❌ Content Access Test FAILED - Status: {response.status_code}")

    @task(2)
    def test_content_progress_tracking(self):
        """Test 13: Content Progress Tracking Test"""
        if not self.token or not self.content_id:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.client.post(
            f"/api/contents/{self.content_id}/complete", headers=headers
        )

        if response.status_code in [200, 201]:
            print("✅ Content Progress Tracking Test PASSED")
        else:
            print(
                f"❌ Content Progress Tracking Test FAILED - Status: {response.status_code}"
            )

    @task(2)
    def test_content_bookmarking(self):
        """Test 14: Content Bookmarking Test"""
        if not self.token or not self.content_id:
            return

        headers = {"Authorization": f"Bearer {self.token}"}

        # Add bookmark
        response = self.client.post(
            f"/api/contents/{self.content_id}/bookmark", headers=headers
        )
        if response.status_code in [200, 201]:
            print("✅ Add Bookmark Test PASSED")

            # Remove bookmark
            response = self.client.delete(
                f"/api/contents/{self.content_id}/bookmark", headers=headers
            )
            if response.status_code == 200:
                print("✅ Remove Bookmark Test PASSED")
            else:
                print(
                    f"❌ Remove Bookmark Test FAILED - Status: {response.status_code}"
                )
        else:
            print(f"❌ Add Bookmark Test FAILED - Status: {response.status_code}")

    @task(2)
    def test_comment_system(self):
        """Test 16: Comment System Test (From original locust_file.py)"""
        if not self.token or not self.content_id:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        comment_data = {"comment": f"Test comment - {random.randint(1000, 9999)}"}

        # Post comment
        response = self.client.post(
            f"/api/contents/{self.content_id}/comments",
            json=comment_data,
            headers=headers,
        )

        if response.status_code in [200, 201]:
            self.comment_id = response.json().get("id")
            print("✅ Post Comment Test PASSED")

            # Get comments
            response = self.client.get(
                f"/api/contents/{self.content_id}/comments", headers=headers
            )
            if response.status_code == 200:
                print("✅ Get Comments Test PASSED")

        else:
            print(f"❌ Comment System Test FAILED - Status: {response.status_code}")

    @task(1)
    def test_comment_deletion(self):
        """Test: Comment Deletion (From original locust_file.py)"""
        if not self.token or not self.comment_id:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.client.delete(
            f"/api/comments/{self.comment_id}", headers=headers
        )

        if response.status_code == 200:
            print("✅ Comment Deletion Test PASSED")
        else:
            print(f"❌ Comment Deletion Test FAILED - Status: {response.status_code}")

    @task(1)
    def test_discussion_thread(self):
        """Test 15: Discussion Thread Test"""
        if not self.token or not self.course_id:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        discussion_data = {
            "title": f"Test Discussion - {random.randint(1000, 9999)}",
            "content": "This is a test discussion thread.",
        }

        response = self.client.post(
            f"/api/courses/{self.course_id}/discussions",
            json=discussion_data,
            headers=headers,
        )

        if response.status_code in [200, 201]:
            self.discussion_id = response.json().get("id")
            print("✅ Discussion Thread Test PASSED")
        else:
            print(f"❌ Discussion Thread Test FAILED - Status: {response.status_code}")

    @task(1)
    def test_notifications(self):
        """Test 18: Notification System Test"""
        if not self.token:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.client.get("/api/notifications", headers=headers)

        if response.status_code == 200:
            notifications = response.json()
            print(
                f"✅ Notifications Test PASSED - Found {len(notifications)} notifications"
            )
        else:
            print(f"❌ Notifications Test FAILED - Status: {response.status_code}")

    @task(1)
    def test_search_and_filter(self):
        """Test 19: Search & Filter Test"""
        search_params = {"search": "python", "category": "programming"}

        response = self.client.get("/api/courses", params=search_params)
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Search & Filter Test PASSED - Found {len(results)} results")
        else:
            print(f"❌ Search & Filter Test FAILED - Status: {response.status_code}")

    def test_logout(self):
        """Test 5: Logout Test"""
        if not self.token:
            return

        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.client.post("/api/auth/logout", headers=headers)

        if response.status_code == 200:
            print("✅ Logout Test PASSED")
            self.token = None
        else:
            print(f"❌ Logout Test FAILED - Status: {response.status_code}")


class LMSUser(HttpUser):
    tasks = [LMSTestSuite]
    wait_time = between(1, 3)
    host = "http://127.0.0.1:8000"
