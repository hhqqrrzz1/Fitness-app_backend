from .auth import router as router_user
from .training import router as router_training
from .muscle_group import router as router_muscle_group
from .exercise import router as router_exercise
from .set import router as router_set
from .permission import router as router_permission
from .dependencies import db_session, current_user