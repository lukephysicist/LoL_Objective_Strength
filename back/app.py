from pydantic import BaseModel
from typing import List
from fastapi import FastAPI
import pandas as pd
from funcs import analyze

from fastapi.middleware.cors import CORSMiddleware

# spin up: uvicorn app:app --reload
app = FastAPI()
df: pd.DataFrame = pd.read_parquet('predicted.parquet')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FilterParams(BaseModel):
    minMinutes: float
    maxMinutes: float
    minProb: float
    maxProb: float
    ranks: List[str]


@app.post('/filter-request')
def filter_return_data(params: FilterParams):
    filtered_df = df[(df['minutesElapsed'] >= params.minMinutes) &
                     (df['minutesElapsed'] <= params.maxMinutes) &
                     (df['pre_pred'] >= params.minProb ) &
                     (df['pre_pred'] <= params.maxProb) &
                     (df['rank'].isin(params.ranks))]
    
    return analyze(filtered_df)
    
