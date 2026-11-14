import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models.functions import Lower


class Role(models.TextChoices):
    STUDENT = "student", "FIU Student"
    ADMINISTRATION = "administration", "FIU Administration"
    FACILITIES = "facilities", "FIU Facilities Staff"
    IT = "it", "FIU IT Staff"


class AccountManager(BaseUserManager):
    """Email is the login identifier; it is normalised to lowercase on save."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("role", Role.IT)
        if not extra["is_staff"] or not extra["is_superuser"]:
            raise ValueError("Superuser must have is_staff=True and is_superuser=True")
        return self._create_user(email, password, **extra)

    def get_by_natural_key(self, email):
        return self.get(email__iexact=email)


class User(AbstractUser):
    """
    Custom user (Deliverable 2 class model: user_id UUID, email, role).
    Must be set as AUTH_USER_MODEL = "accounts.User" BEFORE the first migrate.
    """

    username = None
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField("email address", max_length=254, unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = AccountManager()

    class Meta:
        db_table = "accounts_user"
        constraints = [
            # Case-insensitive uniqueness: Jane@fiu.edu and jane@fiu.edu are the same account.
            models.UniqueConstraint(Lower("email"), name="accounts_user_email_ci_uniq"),
            models.CheckConstraint(
                condition=models.Q(role__in=[r.value for r in Role]),
                name="accounts_user_role_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["role"], name="accounts_user_role_idx"),
        ]

    def __str__(self):
        return self.email

    @property
    def is_location_manager(self):
        return self.role in {Role.ADMINISTRATION, Role.FACILITIES}