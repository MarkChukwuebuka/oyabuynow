from crm.models import ActivityLog
from services.util import CustomRequestUtil


class ActivityLogService(CustomRequestUtil):
    def __init__(self, request):
        super().__init__(request)

    def create(self, activity, note=None):
        return ActivityLog.objects.create(
            user=self.auth_user,
            activity=activity,
            note=note
        )
