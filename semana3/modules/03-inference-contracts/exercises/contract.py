from pydantic import BaseModel, Field, field_validator


class WineInputSchema(BaseModel):
    sample_id: str = Field(..., description="Unique identifier of the wine")
    fixed_acidity: float = Field(..., description="Acidity of the wine")
    volatile_acidity: float = Field(..., description="Acidity of the wine")
    citric_acid: float = Field(..., description="Citric acid of the wine")
    residual_sugar: float = Field(..., description="Residual sugar of the wine")
    chlorides: float = Field(..., description="Chlorides of the wine")
    free_sulfur_dioxide: float = Field(..., description="Free sulfur dioxide of the wine")
    total_sulfur_dioxide: float = Field(..., description="Total sulfur dioxide of the wine")
    density: float = Field(..., description="Density of the wine")
    ph: float = Field(..., description="PH of the wine")
    sulphates: float = Field(..., description="Sulphate of the wine")
    alcohol: float = Field(..., description="Percentage alcohol of the wine")