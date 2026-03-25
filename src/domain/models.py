from restaurant import Base, engine
from sqlalchemy import Integer, String, Date, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from datetime import date

#