import uuid

from django.db import models


class InstitutionStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"
    ARCHIVED = "archived", "Archived"


class DepartmentStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    ARCHIVED = "archived", "Archived"


class BatchStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    ARCHIVED = "archived", "Archived"


class UserProfileStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    INACTIVE = "inactive", "Inactive"
    DEACTIVATED = "deactivated", "Deactivated"


class AdminType(models.TextChoices):
    SUPER_ADMIN = "super_admin", "Super Admin"
    INSTITUTION_ADMIN = "institution_admin", "Institution Admin"


class UserImportJobStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    CANCELLED = "cancelled", "Cancelled"


class Institution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=64, unique=True)
    status = models.CharField(
        max_length=24,
        choices=InstitutionStatus.choices,
        default=InstitutionStatus.ACTIVE,
    )
    settings = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "institutions"
        indexes = [models.Index(fields=["status"], name="idx_institutions_status")]

    def __str__(self) -> str:
        return self.name


class Department(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.ForeignKey(
        Institution,
        on_delete=models.CASCADE,
        related_name="departments",
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=64)
    status = models.CharField(
        max_length=24,
        choices=DepartmentStatus.choices,
        default=DepartmentStatus.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "departments"
        constraints = [
            models.UniqueConstraint(
                fields=["institution", "code"],
                name="uq_departments_inst_code",
            )
        ]
        indexes = [models.Index(fields=["institution", "status"], name="idx_dept_inst_status")]

    def __str__(self) -> str:
        return self.name


class Batch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="batches")
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        related_name="batches",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=24,
        choices=BatchStatus.choices,
        default=BatchStatus.ACTIVE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "batches"
        indexes = [
            models.Index(fields=["institution", "status"], name="idx_batches_inst_status"),
            models.Index(fields=["department"], name="idx_batches_department_id"),
        ]

    def __str__(self) -> str:
        return self.name


class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    auth_account_id = models.UUIDField(unique=True)
    institution = models.ForeignKey(
        Institution,
        on_delete=models.SET_NULL,
        related_name="user_profiles",
        null=True,
        blank=True,
    )
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128)
    display_name = models.CharField(max_length=255, null=True, blank=True)
    avatar_url = models.TextField(null=True, blank=True)
    status = models.CharField(
        max_length=24,
        choices=UserProfileStatus.choices,
        default=UserProfileStatus.ACTIVE,
    )
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "user_profiles"
        indexes = [
            models.Index(fields=["institution", "status"], name="idx_profiles_inst_status"),
            models.Index(fields=["first_name", "last_name"], name="idx_profiles_name"),
        ]

    @property
    def profile_type(self) -> str | None:
        if hasattr(self, "student_profile"):
            return "student"
        if hasattr(self, "instructor_profile"):
            return "instructor"
        if hasattr(self, "admin_profile"):
            return "admin"
        return None

    def __str__(self) -> str:
        return self.display_name or f"{self.first_name} {self.last_name}".strip()


class StudentProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    student_number = models.CharField(max_length=64, unique=True)
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    guardian_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        related_name="guardian_student_profiles",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "student_profiles"
        indexes = [
            models.Index(fields=["batch"], name="idx_student_profiles_batch"),
            models.Index(fields=["department"], name="idx_student_profiles_dept"),
        ]


class InstructorProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="instructor_profile",
    )
    employee_number = models.CharField(max_length=64, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=128, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "instructor_profiles"
        constraints = [
            models.UniqueConstraint(
                fields=["employee_number"],
                condition=models.Q(employee_number__isnull=False),
                name="uq_instructor_employee_number",
            )
        ]
        indexes = [models.Index(fields=["department"], name="idx_instructor_profiles_dept")]


class AdminProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_profile = models.OneToOneField(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="admin_profile",
    )
    admin_type = models.CharField(
        max_length=32,
        choices=AdminType.choices,
        default=AdminType.INSTITUTION_ADMIN,
    )
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "admin_profiles"
        indexes = [
            models.Index(fields=["admin_type"], name="idx_admin_profiles_type"),
            models.Index(fields=["department"], name="idx_admin_profiles_dept"),
        ]


class UserImportJob(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name="import_jobs")
    requested_by_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="requested_import_jobs",
    )
    source_file_asset_id = models.UUIDField(null=True, blank=True)
    status = models.CharField(
        max_length=24,
        choices=UserImportJobStatus.choices,
        default=UserImportJobStatus.QUEUED,
    )
    summary = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_import_jobs"
        indexes = [
            models.Index(fields=["institution", "status"], name="idx_import_jobs_inst_status"),
            models.Index(fields=["requested_by_profile"], name="idx_import_jobs_requested_by"),
        ]
