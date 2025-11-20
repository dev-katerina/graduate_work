from models.user_auth import UserRole
from fastapi import HTTPException
from models.postgres import User
from functools import wraps


def roles_required(roles_list: list[UserRole]):
    def decorator(function):
        @wraps(function)
        async def wrapper(*args, **kwargs):
            user: User = kwargs.get('request').custom_user

            role_names = [role.name for role in user.roles]
            if not user or not any(role in [x.value for x in roles_list] for role in role_names):

                raise HTTPException(
                    status_code=401,
                    detail="This operation is forbidden for you",
                )
            return await function(*args, **kwargs)
        return wrapper
    return decorator