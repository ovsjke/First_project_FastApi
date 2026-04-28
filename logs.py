from database.models import ActionLog

def create_log(
    user_id: int | None,
    method: str,
    path: str,
    status_code: int,
    description: str,
    Schema: ActionLog = ActionLog,
) -> ActionLog:
    '''
    создание логов
    '''
    new_log = Schema(
        user_id=user_id,
        method=method,
        path=path,
        status_code=status_code,
        description=description,
    )
    return new_log