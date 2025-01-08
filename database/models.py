from pydantic import BaseModel, Field
from sqlalchemy.orm import Mapped, mapped_column

from database.db import Base


class Battery(Base):
    __tablename__ = "batteries"

    battery_id: Mapped[str] = mapped_column(primary_key=True)
    capacity_kwh: Mapped[float] = mapped_column(nullable=False)
    maximum_power_kw: Mapped[float] = mapped_column(nullable=False)
    state_of_charge: Mapped[int] = mapped_column(
        nullable=False, default=50
    )  # 50% charged when created
    cycles: Mapped[float] = mapped_column(
        nullable=False, default=0.0
    )  # 0 cycles when created

    def to_dict(self):
        return {
            "battery_id": self.battery_id,
            "capacity_kwh": self.capacity_kwh,
            "maximum_power_kw": self.maximum_power_kw,
            "state_of_charge": str(self.state_of_charge) + "%",
            "cycles": self.cycles,
        }


class CreateBattery(BaseModel):
    capacity_kwh: float = Field(..., gt=0, description="Capacity should be greater than 0")
    maximum_power_kw: float = Field(..., gt=0, description="Maximum power should be greater than 0")

class UpdateBattery(BaseModel):
    battery_id: str = Field(..., description="Unique Battery ID")
    power: int = Field(..., description="Kw power, +ve for charge and -ve for discharge")
    duration: int = Field(..., gt=0, description="Duration in minutes")
