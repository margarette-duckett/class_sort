import re
import uuid
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import os
import math

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# Temporary directory for saving files
UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Sanitation section

def sanitize_filename(filename: str) -> str:
    base_name, ext = os.path.splitext(filename)
    
    # Replace spaces with underscores and remove unsafe characters
    safe_base_name = base_name.replace(" ", "_")
    safe_base_name = re.sub(r'[^a-zA-Z0-9_.-]', '', safe_base_name)
    
    # Generate a unique identifier for the sanitized filename
    sanitized_filename = f"{uuid.uuid4().hex}_{safe_base_name}{ext}"
    
    return sanitized_filename

def is_csv(file: UploadFile) -> bool:
    return file.filename.endswith(".csv") and file.content_type == "text/csv"

def validate_num_classes(num_classes: int) -> int:
    if num_classes < 1 or num_classes > 20:
        raise ValueError("The number of classes must be between 1-20.")
    return num_classes

def validate_headers(df: pd.DataFrame):
    required_headers = ["ESOL", "IEP", "GATES", "MAP_score"]
    missing_headers = [header for header in required_headers if header not in df.columns]
    if missing_headers:
        raise ValueError(f"Missing required headers: {', '.join(missing_headers)}")
    
@app.post("/calculate/")
async def calc_map(
    file: UploadFile = File(...)
):
    try:
        if not is_csv(file):
            raise ValueError("Uploaded file must be a CSV")
        
        original_filename = file.filename
        sanitized_filename = sanitize_filename(original_filename)

        input_path = os.path.join(UPLOAD_DIR, sanitized_filename)
        with open(input_path, "wb") as f:
            f.write(await file.read())

        df = pd.read_csv(input_path)

        required_headers = ["math_score", "reading_score"]
        missing_headers = [header for header in required_headers if header not in df.columns]
        if missing_headers:
            raise ValueError(f"Missing required headers: {', '.join(missing_headers)}")
        
        # Ensure "MAP_score" column exist
        if "MAP_score" not in df.columns:
            df["MAP_score"] = None

        df["MAP_score"] = round((df["math_score"].astype(float) + df["reading_score"].astype(float)) / 2)

        output_filename = f"map_{sanitized_filename}"
        output_path = os.path.join(UPLOAD_DIR, output_filename)
        df.to_csv(output_path, index=False)
       
        download_url = f"http://localhost:8000/download/{output_filename}"
        return {"download_url": download_url, "original_filename": original_filename}
    
    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})

        
@app.post("/process/")
async def process_file(
    num_classes: int = Form(...),  
    file: UploadFile = File(...)  
):
    try:
        if not is_csv(file):
            raise ValueError("Uploaded file must be a CSV")
        
        num_classes = validate_num_classes(num_classes)
        original_filename = file.filename
        sanitized_filename = sanitize_filename(original_filename)

        input_path = os.path.join(UPLOAD_DIR, sanitized_filename)
        with open(input_path, "wb") as f:
            f.write(await file.read())

        
        df = pd.read_csv(input_path)
        validate_headers(df)

        # Ensure "assigned_class" column exists
        if "assigned_class" not in df.columns:
            df["assigned_class"] = None

        current = 1

        # Assign SPED students to their own class if any
        if df["IEP"].eq("SPED").any():
            df.loc[df["IEP"] == "SPED", "assigned_class"] = current
            current += 1
            num_classes -= 1

        # Find equal class sizes
        students_remaining = df[df["assigned_class"].isnull()].sort_values("MAP_score", ascending=False)
        count = len(students_remaining)
        class_size = math.ceil(count / num_classes)
        if df["IEP"].eq("SPED").any():
            num_classes += 1

        # Assign GATES students to their class 1st if space remaining assign top preformers
        if df["GATES"].eq("Yes").any():
            gates_students = df[(df["GATES"] == "Yes") & (df["IEP"] != "SPED")]
            gates_size = len(df[df["GATES"] == "Yes"])

            if gates_size > class_size:
                if gates_size >= 30:
                    gates_one_size = round(gates_size / 3)
                    gates_two_size = gates_size - gates_one_size
                    gates_3_size = gates_size - gates_one_size - gates_two_size
                    fill_one = gates_students.head(gates_one_size) 
                    fill_two = gates_students.iloc[gates_one_size:gates_one_size + gates_two_size] 
                    fill_three = gates_students.tail(gates_3_size)
                    df.loc[fill_one.index, "assigned_class"] = current
                    df.loc[fill_two.index, "assigned_class"] = current + 1
                    df.loc[fill_three.index, "assigned_class"] = current + 2
                    students_remaining = df[df["assigned_class"].isnull()].sort_values("MAP_score", ascending=False)

                else:
                    gates_one_size = round(gates_size / 2)
                    gates_two_size = gates_size - gates_one_size
                    fill_one = gates_students.head(gates_one_size)
                    fill_two = gates_students.tail(gates_two_size)
                    df.loc[fill_one.index, "assigned_class"] = current
                    df.loc[fill_two.index, "assigned_class"] = current + 1
                    students_remaining = df[df["assigned_class"].isnull()].sort_values("MAP_score", ascending=False)

            else:
                df.loc[gates_students.index, "assigned_class"] = current
                students_remaining = df[df["assigned_class"].isnull()].sort_values("MAP_score", ascending=False)
                students_to_add = class_size - gates_size
                fill_students = students_remaining.head(students_to_add)
                df.loc[fill_students.index, "assigned_class"] = current
                current += 1
                students_remaining = df[df["assigned_class"].isnull()].sort_values("MAP_score", ascending=False)     
        
            
        # Assign leftover students
        while not students_remaining.empty:
            current_class_size = len(df[df["assigned_class"] == current])
            if current_class_size < class_size:
                fill_students_size = class_size - current_class_size
                fill_students = students_remaining.head(fill_students_size)
                df.loc[fill_students.index, "assigned_class"] = current
                students_remaining = df[df["assigned_class"].isnull()].sort_values("MAP_score", ascending=False)
                current += 1

            else:
                fill_students = students_remaining.head(class_size)
                df.loc[fill_students.index, "assigned_class"] = current
                students_remaining = df[df["assigned_class"].isnull()].sort_values("MAP_score", ascending=False)
                current += 1
                if current > num_classes:
                    current = math.ceil(num_classes / 2)
        
        # Adjust for ESOL
        esol_students = df[(df["ESOL"].notnull()) & (df["IEP"] != "SPED")]
        languages = esol_students["ESOL"].unique()

        for lang in languages:
            cur_lang = esol_students[esol_students["ESOL"] == lang]
            avg_class = cur_lang["assigned_class"].mean()
            avg_class = round(avg_class)
            df.loc[cur_lang.index, "assigned_class"] = avg_class

        df.sort_values("assigned_class", inplace=True)

    
        # Save the sorted data to a new CSV file
        output_filename = f"map_{sanitized_filename}"
        output_path = os.path.join(UPLOAD_DIR, output_filename)
        df.to_csv(output_path, index=False)
       
        download_url = f"http://localhost:8000/download/{output_filename}"
        return {"download_url": download_url, "original_filename": original_filename}


    except ValueError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "Internal Server Error"})
 
@app.get("/download/{filename}")
async def download_file(filename: str):
    sanitize_filename = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(sanitize_filename):
        return JSONResponse(status_code=404, content={"error": "File not found"})
    
    original_filename = filename.split("_", 1)[-1]

    return FileResponse(sanitize_filename, headers={"Content-Disposition": f"attachment; filename={original_filename}"})