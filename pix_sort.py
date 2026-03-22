import os
import sys
import shutil
import argparse
import numpy as np
from PIL import Image
from tqdm import tqdm
import torch
from transformers import CLIPProcessor, CLIPModel
import hdbscan
from sklearn.metrics.pairwise import cosine_similarity

# Common photo categories for zero-shot labeling
CATEGORIES = [
    "mountains", "beach", "forest", "city landscape", "people", 
    "faces", "pets", "dogs", "cats", "cars", "food", "receipts", 
    "documents", "memes", "screenshots", "indoor rooms", "wedding",
    "sports", "sky", "art", "flowers", "group photos", "selfies",
    "animals", "wildlife", "architecture", "party"
]

def load_images(input_dir):
    valid_exts = {'.png', '.jpg', '.jpeg', '.webp', '.bmp'}
    image_paths = []
    for root, _, files in os.walk(input_dir):
        for f in files:
            if os.path.splitext(f)[1].lower() in valid_exts:
                image_paths.append(os.path.join(root, f))
    return image_paths

def main():
    parser = argparse.ArgumentParser(description="Sortify - AI Image Organizer")
    parser.add_argument("--input", required=True, help="Directory containing unsorted images")
    parser.add_argument("--output", required=True, help="Directory to output sorted images")
    parser.add_argument("--action", choices=['copy', 'move'], default='copy', help="Action to take on files")
    parser.add_argument("--min_cluster_size", type=int, default=3, help="Minimum images to form a cluster")
    args = parser.parse_args()

    input_dir = args.input
    output_dir = args.output
    action = args.action

    if not os.path.exists(input_dir):
        print(f"Error: Input directory {input_dir} does not exist.")
        sys.exit(1)

    print("Scanning for images...")
    image_paths = load_images(input_dir)
    if not image_paths:
        print("No valid images found in the input directory.")
        sys.exit(0)
    print(f"Found {len(image_paths)} images.")

    print("Loading OpenAI CLIP model...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    
    # In production, cache the model or load silently
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    print("Extracting image embeddings...")
    embeddings = []
    valid_paths = []

    for path in tqdm(image_paths):
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
        except Exception as e:
            print(f"Warning: Failed to process {path}: {e}")

    if not embeddings:
        print("No embeddings could be generated.")
        sys.exit(1)

    X = np.stack(embeddings)

    print("Clustering images with HDBSCAN...")
    clusterer = hdbscan.HDBSCAN(min_cluster_size=args.min_cluster_size, metric='euclidean')
    cluster_labels = clusterer.fit_predict(X)

    unique_clusters = set(cluster_labels)
    num_clusters = len(unique_clusters) - (1 if -1 in unique_clusters else 0)
    print(f"Found {num_clusters} distinct clusters.")

    # Pre-embed the text categories for zero-shot labeling
    print("Computing semantic labels...")
    text_inputs = processor(text=CATEGORIES, return_tensors="pt", padding=True).to(device)
    with torch.no_grad():
        out_text = model.get_text_features(input_ids=text_inputs.input_ids, attention_mask=text_inputs.attention_mask)
        
    if isinstance(out_text, torch.Tensor):
        text_features = out_text
    else:
        text_features = getattr(out_text, 'text_embeds', getattr(out_text, 'pooler_output', out_text))
        
    text_features = text_features.cpu().numpy()

    cluster_names = {}
    os.makedirs(output_dir, exist_ok=True)

    for cluster_id in unique_clusters:
        if cluster_id == -1:
            cluster_names[cluster_id] = "Uncategorized_Misc"
            continue
        
        # Get all embeddings for this cluster
        cluster_indices = [i for i, label in enumerate(cluster_labels) if label == cluster_id]
        cluster_embeddings = X[cluster_indices]
        
        # Compute centroid
        centroid = np.mean(cluster_embeddings, axis=0).reshape(1, -1)
        
        # Cosine similarity against text categories
        similarities = cosine_similarity(centroid, text_features)[0]
        best_match_idx = np.argmax(similarities)
        best_category = CATEGORIES[best_match_idx].title().replace(" ", "_")
        
        # To avoid collisions if multiple clusters pick the same category
        folder_name = f"{best_category}_{cluster_id}"
        cluster_names[cluster_id] = folder_name

    print(f"Organizing files into {output_dir}...")
    for path, cluster_id in tqdm(zip(valid_paths, cluster_labels), total=len(valid_paths)):
        target_folder = os.path.join(output_dir, cluster_names[cluster_id])
        os.makedirs(target_folder, exist_ok=True)
        target_path = os.path.join(target_folder, os.path.basename(path))
        
        # Handle filename collisions
        base, ext = os.path.splitext(target_path)
        counter = 1
        while os.path.exists(target_path):
            target_path = f"{base}_{counter}{ext}"
            counter += 1

        if action == 'copy':
            shutil.copy2(path, target_path)
        else:
            shutil.move(path, target_path)

    print(f"Sortify completed successfully! Images organized into {output_dir}.")

if __name__ == "__main__":
    main()
