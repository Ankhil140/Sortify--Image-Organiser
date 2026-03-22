import os
import sys
import shutil
import numpy as np
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel
import hdbscan
from sklearn.metrics.pairwise import cosine_similarity
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import uuid

app = FastAPI(title="Sortify Web API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading CLIP model on {device}...")
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

CATEGORIES = [
    "mountains", "beach", "forest", "city landscape", "people", 
    "faces", "pets", "dogs", "cats", "cars", "food", "receipts", 
    "documents", "memes", "screenshots", "indoor rooms", "wedding",
    "sports", "sky", "art", "flowers", "group photos", "selfies",
    "animals", "wildlife", "architecture", "party"
]

print("Pre-computing text embeddings for category labels...")
text_inputs = processor(text=CATEGORIES, return_tensors="pt", padding=True).to(device)
with torch.no_grad():
    out_text = model.get_text_features(input_ids=text_inputs.input_ids, attention_mask=text_inputs.attention_mask)

if isinstance(out_text, torch.Tensor):
    text_features = out_text
else:
    text_features = getattr(out_text, 'text_embeds', getattr(out_text, 'pooler_output', out_text))
text_features = text_features.cpu().numpy()

UPLOAD_DIR = "web_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
# Serve uploaded files so frontend can display them
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

@app.post("/api/cluster")
async def cluster_images(files: List[UploadFile] = File(...)):
    session_id = str(uuid.uuid4())[:8]
    session_dir = os.path.join(UPLOAD_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    image_paths = []
    # Save the files locally for PIL to read
    for file in files:
        file_path = os.path.join(session_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        image_paths.append(file_path)

    if not image_paths:
        return {"error": "No files uploaded"}

    embeddings = []
    valid_paths = []
    url_paths = []

    for path in image_paths:
        try:
            image = Image.open(path).convert("RGB")
            inputs = processor(images=image, return_tensors="pt").to(device)
            with torch.no_grad():
                out = model.get_image_features(pixel_values=inputs.pixel_values)
            
            if isinstance(out, torch.Tensor):
                vec = out
            else:
                vec = getattr(out, 'image_embeds', getattr(out, 'pooler_output', out))
                
            embeddings.append(vec.cpu().numpy().flatten())
            valid_paths.append(path)
            # URL path for frontend viewing (assume backend runs on 8080)
            url_paths.append(f"http://localhost:8080/static/{session_id}/{os.path.basename(path)}")
        except Exception as e:
            print(f"Failed to process {path}: {e}")

    if not embeddings:
         return {"error": "No valid images could be processed."}

    X = np.stack(embeddings)
    
    # Run HDBSCAN
    min_size = min(3, len(embeddings))
    if min_size < 2:
        cluster_labels = [-1] * len(embeddings)
    else:
        clusterer = hdbscan.HDBSCAN(min_cluster_size=min_size, metric='euclidean', allow_single_cluster=True)
        cluster_labels = clusterer.fit_predict(X)

    unique_clusters = set(cluster_labels)
    cluster_names = {}
    
    for cluster_id in unique_clusters:
        if cluster_id == -1:
            cluster_names[cluster_id] = "Uncategorized_Misc"
            continue
        cluster_indices = [i for i, label in enumerate(cluster_labels) if label == cluster_id]
        cluster_embeddings = X[cluster_indices]
        centroid = np.mean(cluster_embeddings, axis=0).reshape(1, -1)
        similarities = cosine_similarity(centroid, text_features)[0]
        best_match_idx = np.argmax(similarities)
        best_category = CATEGORIES[best_match_idx].title().replace(" ", "_")
        cluster_names[cluster_id] = f"{best_category}_{cluster_id}"

    results = {}
    for url, cluster_id in zip(url_paths, cluster_labels):
        c_name = cluster_names[cluster_id]
        if c_name not in results:
            results[c_name] = []
        results[c_name].append(url)

    return {"session_id": session_id, "clusters": results}
