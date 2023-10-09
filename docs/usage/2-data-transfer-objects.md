# Data transfer objects

The user registration DTO can be an instance of either [DataclassDTO][litestar.dto.DataclassDTO], [MsgspecDTO][litestar.dto.msgspec_dto.MsgspecDTO] or [PydanticDTO][litestar.dto.pydantic_dto.PydanticDTO]

## Example

```python
from dataclasses import dataclass

from litestar.contrib.sqlalchemy.dto import SQLAlchemyDTO, SQLAlchemyDTOConfig
from litestar.dto import DataclassDTO

from .models import User


@dataclass
class UserRegistrationSchema:
    email: str
    password: str


class UserRegistrationDTO(DataclassDTO[UserRegistrationSchema]):
    """User registration DTO."""


class UserReadDTO(SQLAlchemyDTO[User]):
    config = SQLAlchemyDTOConfig(exclude={"login_count"})


class UserUpdateDTO(SQLAlchemyDTO[User]):
    config = SQLAlchemyDTOConfig(exclude={"login_count"}, partial=True)
```
