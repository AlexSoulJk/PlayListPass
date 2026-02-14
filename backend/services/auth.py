from schemas.auth import UserLoginSchema, UserResponseSchema

class AuthService:
    """
    Здесь лежит бизнес-логика.
    """
    
    @staticmethod
    async def mock_authenticate_user(user_data: UserLoginSchema) -> UserResponseSchema:
        # Имитация похода в базу данных или проверки пароля
        # В реальности тут будет session.execute(select(User)...)
        
        # Эмуляция логики:
        if user_data.password == "secret":
            return UserResponseSchema(
                id=1, 
                email=user_data.email, 
                is_active=True,
                message="Успешная авторизация (Mock)"
            )
        
        
        return UserResponseSchema(
            id=0, 
            email=user_data.email, 
            is_active=False,
            message="Неверный пароль (Mock)"
        )


auth_service = AuthService()