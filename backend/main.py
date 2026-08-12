from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import pandas as pd
from pathlib import Path
import tempfile

from models import model_manager
from processing import process_signal, recalculate_with_points

app = FastAPI(title="PD Signal Analysis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "PD Signal Analysis API", "status": "running", "models_loaded": model_manager.is_ready()}

@app.get("/api/models-status")
async def models_status():
    return {
        "ready": model_manager.is_ready(),
        "detector": model_manager.detector_model is not None,
        "segmenter": model_manager.segmenter_model is not None,
        "classifier": model_manager.clf_model is not None,
        "feature_bounds": model_manager.feature_bounds is not None
    }

@app.post("/api/process-signal")
async def process_signal_endpoint(acc_file: UploadFile = File(...), gyro_file: UploadFile = File(...)):
    try:
        if not model_manager.is_ready():
            raise HTTPException(status_code=500, detail="Модели не загружены.")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            acc_path = Path(tmpdir) / "AccelerometerUncalibrated.csv"
            gyro_path = Path(tmpdir) / "GyroscopeUncalibrated.csv"
            
            with open(acc_path, "wb") as f: f.write(await acc_file.read())
            with open(gyro_path, "wb") as f: f.write(await gyro_file.read())
            
            df_acc = pd.read_csv(acc_path)
            df_acc.index = pd.to_datetime(df_acc['time'], unit='ns')
            df_acc.rename(columns={'z': 'acc_z', 'y': 'acc_y', 'x': 'acc_x'}, inplace=True)
            df_acc['time_sec'] = (df_acc.index - df_acc.index[0]).total_seconds()
            
            df_gyro = pd.read_csv(gyro_path)
            df_gyro.index = pd.to_datetime(df_gyro['time'], unit='ns')
            df_gyro.rename(columns={'z': 'gyr_z', 'y': 'gyr_y', 'x': 'gyr_x'}, inplace=True)
            
            df = pd.merge_asof(
                df_acc[['time_sec', 'acc_x', 'acc_y', 'acc_z']],
                df_gyro[['gyr_x', 'gyr_y', 'gyr_z']],
                left_index=True, right_index=True, direction='nearest'
            )
            
            return process_signal(df)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class PointsUpdate(BaseModel):
    points: Dict[str, Optional[float]]

@app.post("/api/recalculate")
async def recalculate_with_new_points(points_data: PointsUpdate):
    try:
        if not model_manager.is_ready():
            raise HTTPException(status_code=400, detail="Модели не загружены")
        
        points = points_data.points
        for key in ['T1', 'T2', 'T3', 'T4', 'T5']:
            if points.get(key) is None:
                raise HTTPException(status_code=400, detail=f"Точка {key} не задана")
        
        return recalculate_with_points(points)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Ошибка пересчёта: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)