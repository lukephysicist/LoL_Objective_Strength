from pydantic import BaseModel
from typing import List
from fastapi import FastAPI
import pandas as pd
from funcs import analyze

from fastapi.middleware.cors import CORSMiddleware
df: pd.DataFrame = pd.read_parquet('predicted.parquet')

# spin up: uvicorn app:app --reload
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FilterParams(BaseModel):
    minMinute: float
    maxMinute: float
    minProb: float
    maxProb: float
    ranks: List[str]


@app.post('/filter-request')
def filter_return_data(params: FilterParams):
    filtered_df = df[(df['minutesElapsed'] >= params.minMinute) &
                     (df['minutesElapsed'] <= params.maxMinute) &
                     (df['pre_pred'] >= params.minProb ) &
                     (df['pre_pred'] <= params.maxProb) &
                     (df['rank'].isin(params.ranks))]
    
    objective_impact = analyze(filtered_df)
    time_hist = filtered_df['minutesElapsed'].tolist()
    thrid_graph = None

    return (objective_impact, time_hist, thrid_graph)