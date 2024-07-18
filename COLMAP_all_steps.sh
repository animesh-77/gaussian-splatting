#!/bin/bash


database_path="/cs/student/projects4/ml/2023/asrivast/datasets/handbag_19/visible_model/sparse_only_6_mask/database.db"
image_path="/cs/student/projects4/ml/2023/asrivast/datasets/handbag_19/visible_model/only_6"
mask_path="/cs/student/projects4/ml/2023/asrivast/datasets/handbag_19/visible_model/mask_unrotated"
output_path="/cs/student/projects4/ml/2023/asrivast/datasets/handbag_19/visible_model/sparse_only_6_mask/0"
max_image_size=6400
max_num_features=10000
project_path=$(dirname $database_path)

# if folder of database file does not exists then create it
mkdir -p $(dirname $database_path)

# Check if the database file exists and delete it
if [ -f "$database_path" ]; then
    rm "$database_path"
    echo "Deleted database file: $database_path"
else
    echo "Database file not found: $database_path"
fi


colmap feature_extractor \
    --database_path $database_path \
    --image_path $image_path \
    --SiftExtraction.use_gpu 1 \
    --SiftExtraction.upright 0 \
    --ImageReader.single_camera 0 \
    --SiftExtraction.max_image_size $max_image_size \
    --ImageReader.camera_model PINHOLE \
    --ImageReader.mask_path $mask_path \

Create project.ini file
colmap project_generator \
    --project_path $project_path/project.ini

echo "Project file saved at: $project_path/project.ini"

# make output path if it doesn't exist
mkdir -p $output_path

colmap exhaustive_matcher \
    --database_path $database_path \
    --SiftMatching.use_gpu 1 \
    --TwoViewGeometry.min_num_inliers 100 

colmap mapper \
    --database_path $database_path \
    --image_path $image_path \
    --output_path $output_path \