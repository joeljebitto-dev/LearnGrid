from django.conf import settings
from rest_framework import serializers

from .models import (
    AdminType,
    Batch,
    BatchStatus,
    Department,
    DepartmentStatus,
    Institution,
    InstitutionStatus,
    UserProfile,
    UserProfileStatus,
)


PROFILE_TYPES = ("student", "instructor", "admin")
ORG_SORT_CHOICES = [
    "name",
    "-name",
    "code",
    "-code",
    "status",
    "-status",
    "created_at",
    "-created_at",
    "updated_at",
    "-updated_at",
]


def normalize_code(value: str) -> str:
    code = value.strip().upper()
    if not code:
        raise serializers.ValidationError("Code is required.")
    return code


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = [
            "id",
            "name",
            "code",
            "status",
            "settings",
            "created_at",
            "updated_at",
            "deleted_at",
        ]


class InstitutionCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    code = serializers.CharField(max_length=64)
    status = serializers.ChoiceField(
        choices=InstitutionStatus.choices,
        default=InstitutionStatus.ACTIVE,
    )
    settings = serializers.JSONField(required=False)

    def validate_code(self, value):
        code = normalize_code(value)
        if Institution.objects.filter(code=code).exists():
            raise serializers.ValidationError("Institution code already exists.")
        return code

    def validate(self, attrs):
        attrs["settings"] = attrs.get("settings") or {}
        return attrs


class InstitutionUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, max_length=255)
    code = serializers.CharField(required=False, max_length=64)
    status = serializers.ChoiceField(choices=InstitutionStatus.choices, required=False)
    settings = serializers.JSONField(required=False)

    def validate_code(self, value):
        code = normalize_code(value)
        institution = self.context["institution"]
        if Institution.objects.filter(code=code).exclude(id=institution.id).exists():
            raise serializers.ValidationError("Institution code already exists.")
        return code


class InstitutionSearchSerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True, max_length=255)
    status = serializers.ChoiceField(choices=InstitutionStatus.choices, required=False)
    sort = serializers.ChoiceField(choices=ORG_SORT_CHOICES, default="name", required=False)


class DepartmentSerializer(serializers.ModelSerializer):
    institution_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Department
        fields = [
            "id",
            "institution_id",
            "name",
            "code",
            "status",
            "created_at",
            "updated_at",
            "deleted_at",
        ]


class DepartmentCreateSerializer(serializers.Serializer):
    institution_id = serializers.UUIDField()
    name = serializers.CharField(max_length=255)
    code = serializers.CharField(max_length=64)
    status = serializers.ChoiceField(
        choices=DepartmentStatus.choices,
        default=DepartmentStatus.ACTIVE,
    )

    def validate_code(self, value):
        return normalize_code(value)

    def validate(self, attrs):
        if not Institution.objects.filter(
            id=attrs["institution_id"],
            deleted_at__isnull=True,
        ).exists():
            raise serializers.ValidationError({"institution_id": "Institution was not found."})
        if Department.objects.filter(
            institution_id=attrs["institution_id"],
            code=attrs["code"],
        ).exists():
            raise serializers.ValidationError({"code": "Department code already exists."})
        return attrs


class DepartmentUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, max_length=255)
    code = serializers.CharField(required=False, max_length=64)
    status = serializers.ChoiceField(choices=DepartmentStatus.choices, required=False)

    def validate_code(self, value):
        return normalize_code(value)

    def validate(self, attrs):
        department = self.context["department"]
        code = attrs.get("code")
        if (
            code
            and Department.objects.filter(
                institution=department.institution,
                code=code,
            )
            .exclude(id=department.id)
            .exists()
        ):
            raise serializers.ValidationError({"code": "Department code already exists."})
        return attrs


class DepartmentSearchSerializer(serializers.Serializer):
    institution_id = serializers.UUIDField(required=False)
    q = serializers.CharField(required=False, allow_blank=True, max_length=255)
    status = serializers.ChoiceField(choices=DepartmentStatus.choices, required=False)
    sort = serializers.ChoiceField(choices=ORG_SORT_CHOICES, default="name", required=False)


class BatchSerializer(serializers.ModelSerializer):
    institution_id = serializers.UUIDField(read_only=True)
    department_id = serializers.UUIDField(read_only=True, allow_null=True)

    class Meta:
        model = Batch
        fields = [
            "id",
            "institution_id",
            "department_id",
            "name",
            "start_date",
            "end_date",
            "status",
            "created_at",
            "updated_at",
            "deleted_at",
        ]


class BatchCreateSerializer(serializers.Serializer):
    institution_id = serializers.UUIDField()
    department_id = serializers.UUIDField(required=False, allow_null=True)
    name = serializers.CharField(max_length=255)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=BatchStatus.choices, default=BatchStatus.ACTIVE)

    def validate(self, attrs):
        institution_id = attrs["institution_id"]
        if not Institution.objects.filter(id=institution_id, deleted_at__isnull=True).exists():
            raise serializers.ValidationError({"institution_id": "Institution was not found."})

        department_id = attrs.get("department_id")
        if department_id:
            if not Department.objects.filter(
                id=department_id,
                institution_id=institution_id,
                deleted_at__isnull=True,
            ).exists():
                raise serializers.ValidationError(
                    {"department_id": "Department does not belong to the institution."}
                )

        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "End date cannot be before start date."})
        return attrs


class BatchUpdateSerializer(serializers.Serializer):
    department_id = serializers.UUIDField(required=False, allow_null=True)
    name = serializers.CharField(required=False, max_length=255)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=BatchStatus.choices, required=False)

    def validate(self, attrs):
        batch = self.context["batch"]
        department_id = attrs.get("department_id")
        if (
            department_id
            and not Department.objects.filter(
                id=department_id,
                institution=batch.institution,
                deleted_at__isnull=True,
            ).exists()
        ):
            raise serializers.ValidationError(
                {"department_id": "Department does not belong to the institution."}
            )

        start_date = attrs.get("start_date", batch.start_date)
        end_date = attrs.get("end_date", batch.end_date)
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "End date cannot be before start date."})
        return attrs


class BatchSearchSerializer(serializers.Serializer):
    institution_id = serializers.UUIDField(required=False)
    department_id = serializers.UUIDField(required=False)
    q = serializers.CharField(required=False, allow_blank=True, max_length=255)
    status = serializers.ChoiceField(choices=BatchStatus.choices, required=False)
    sort = serializers.ChoiceField(choices=ORG_SORT_CHOICES, default="name", required=False)


class StudentProfilePayloadSerializer(serializers.Serializer):
    student_number = serializers.CharField(max_length=64)
    batch_id = serializers.UUIDField(required=False, allow_null=True)
    department_id = serializers.UUIDField(required=False, allow_null=True)
    guardian_profile_id = serializers.UUIDField(required=False, allow_null=True)


class InstructorProfilePayloadSerializer(serializers.Serializer):
    employee_number = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=64
    )
    department_id = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=128)
    bio = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class AdminProfilePayloadSerializer(serializers.Serializer):
    admin_type = serializers.ChoiceField(
        choices=AdminType.choices, default=AdminType.INSTITUTION_ADMIN
    )
    department_id = serializers.UUIDField(required=False, allow_null=True)


class UserProfileCreateSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone = serializers.RegexField(
        regex=r"^\+?[1-9][0-9]{7,14}$",
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=32,
    )
    temporary_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        min_length=settings.AUTH_PASSWORD_MIN_LENGTH,
        max_length=256,
    )
    profile_type = serializers.ChoiceField(choices=PROFILE_TYPES)
    role_code = serializers.CharField(required=False, allow_blank=True, max_length=64)
    institution_id = serializers.UUIDField(required=False, allow_null=True)
    first_name = serializers.CharField(max_length=128)
    last_name = serializers.CharField(max_length=128)
    display_name = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=255
    )
    avatar_url = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    metadata = serializers.JSONField(required=False)
    student = StudentProfilePayloadSerializer(required=False)
    instructor = InstructorProfilePayloadSerializer(required=False)
    admin = AdminProfilePayloadSerializer(required=False)

    def validate(self, attrs):
        profile_type = attrs["profile_type"]
        if profile_type == "student" and "student" not in attrs:
            raise serializers.ValidationError({"student": "Student profile data is required."})
        if profile_type == "instructor" and "instructor" not in attrs:
            attrs["instructor"] = {}
        if profile_type == "admin" and "admin" not in attrs:
            attrs["admin"] = {"admin_type": AdminType.INSTITUTION_ADMIN}

        institution_id = attrs.get("institution_id")
        if (
            institution_id
            and not Institution.objects.filter(id=institution_id, deleted_at__isnull=True).exists()
        ):
            raise serializers.ValidationError({"institution_id": "Institution was not found."})
        attrs["role_code"] = attrs.get("role_code") or None
        attrs["phone"] = attrs.get("phone") or None
        attrs["display_name"] = attrs.get("display_name") or None
        attrs["avatar_url"] = attrs.get("avatar_url") or None
        attrs["metadata"] = attrs.get("metadata") or {}
        return attrs


class UserProfileUpdateSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    phone = serializers.RegexField(
        regex=r"^\+?[1-9][0-9]{7,14}$",
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=32,
    )
    first_name = serializers.CharField(required=False, max_length=128)
    last_name = serializers.CharField(required=False, max_length=128)
    display_name = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=255
    )
    avatar_url = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    status = serializers.ChoiceField(choices=UserProfileStatus.choices, required=False)
    metadata = serializers.JSONField(required=False)
    student = StudentProfilePayloadSerializer(required=False, partial=True)
    instructor = InstructorProfilePayloadSerializer(required=False, partial=True)
    admin = AdminProfilePayloadSerializer(required=False, partial=True)


class ProfileSearchSerializer(serializers.Serializer):
    institution_id = serializers.UUIDField(required=False)
    q = serializers.CharField(required=False, allow_blank=True, max_length=255)
    profile_type = serializers.ChoiceField(choices=PROFILE_TYPES, required=False)
    status = serializers.ChoiceField(choices=UserProfileStatus.choices, required=False)
    department_id = serializers.UUIDField(required=False)
    batch_id = serializers.UUIDField(required=False)
    sort = serializers.ChoiceField(
        choices=[
            "first_name",
            "-first_name",
            "last_name",
            "-last_name",
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
        ],
        default="last_name",
        required=False,
    )


def profile_type_for(profile: UserProfile) -> str | None:
    return profile.profile_type


def role_specific_payload(profile: UserProfile) -> dict:
    if hasattr(profile, "student_profile"):
        student = profile.student_profile
        return {
            "student_number": student.student_number,
            "batch_id": str(student.batch_id) if student.batch_id else None,
            "department_id": str(student.department_id) if student.department_id else None,
            "guardian_profile_id": (
                str(student.guardian_profile_id) if student.guardian_profile_id else None
            ),
        }
    if hasattr(profile, "instructor_profile"):
        instructor = profile.instructor_profile
        return {
            "employee_number": instructor.employee_number,
            "department_id": str(instructor.department_id) if instructor.department_id else None,
            "title": instructor.title,
            "bio": instructor.bio,
        }
    if hasattr(profile, "admin_profile"):
        admin = profile.admin_profile
        return {
            "admin_type": admin.admin_type,
            "department_id": str(admin.department_id) if admin.department_id else None,
        }
    return {}


class UserProfileSerializer(serializers.ModelSerializer):
    institution_id = serializers.UUIDField(source="institution.id", read_only=True)
    profile_type = serializers.SerializerMethodField()
    role_profile = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "auth_account_id",
            "institution_id",
            "first_name",
            "last_name",
            "display_name",
            "avatar_url",
            "status",
            "metadata",
            "profile_type",
            "role_profile",
            "created_at",
            "updated_at",
            "deleted_at",
        ]

    def get_profile_type(self, obj):
        return profile_type_for(obj)

    def get_role_profile(self, obj):
        return role_specific_payload(obj)
