# Import all models here so SQLAlchemy registers them before create_all()
from app.db.models.user import User  # noqa: F401
from app.db.models.project import Project  # noqa: F401
from app.db.models.message import Message  # noqa: F401
from app.db.models.status import ProjectStatus  # noqa: F401
from app.db.models.github import GitHubConnection  # noqa: F401
from app.db.models.upload import UploadAnalysis  # noqa: F401
from app.db.models.billing import Subscription, CreditLedger, CreditUsageEvent, BillingEvent  # noqa: F401
