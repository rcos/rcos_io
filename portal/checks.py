from typing import Any, Dict, List, NotRequired, Optional, TypedDict, Union, cast
from portal.models import Semester, User
from collections.abc import Callable
from django.utils import timezone

class FailedCheck(Exception):
    reason: str
    fix: Optional[str]

    def __init__(self, reason: str, fix: Optional[str] = None) -> None:
        self.reason = reason
        self.fix = fix
        super().__init__(reason)

TestFunction = Callable[[User, Optional[Semester]], bool]

class Check:
    test_fn: TestFunction
    dependencies: List["Check"]
    fail_reason: str
    fix: Optional[str] = None
    
    def __init__(self, test_fn: TestFunction, fail_reason: str, fix: Optional[str] = None, dependencies: List["Check"]=[]) -> None:
        self.test_fn = test_fn
        self.fail_reason = fail_reason
        self.fix = fix
        self.dependencies = dependencies
        
    def check(self, user: User, semester: Optional[Semester] = None):
        for dep in self.dependencies:
            dep.check(user, semester)
        if not self.test_fn(user, semester):
            raise FailedCheck(self.fail_reason, self.fix)

UserApprovedCheck = Check(test_fn=lambda user, _: user.is_approved, fail_reason="Not approved", fix="Contact me")
RPIUserCheck = Check(dependencies=[UserApprovedCheck], test_fn=lambda user, _: user.is_rpi, fail_reason="Not RPI")

def c(_: User, semester: Optional[Semester]):
    if not semester:
        return False
    
    now = timezone.now()
    if semester.is_active and (
        semester.enrollment_deadline and now > semester.enrollment_deadline
    ):
        return False

    if not semester.is_active and semester != Semester.get_next():
        return False

    return True

CanEnrollInSemesterCheck = Check(dependencies=[RPIUserCheck], fail_reason="It is passed the enrollment deadline.", test_fn=c)