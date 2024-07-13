#
# Copyright (C) 2023, Inria
# GRAPHDECO research group, https://team.inria.fr/graphdeco
# All rights reserved.
#
# This software is free for non-commercial, research and evaluation use
# under the terms of the LICENSE.md file.
#
# For inquiries contact  george.drettakis@inria.fr
#

import os
import logging
from argparse import ArgumentParser
import shutil
from gooey import Gooey

@Gooey
def main():
    # This Python script is based on the shell converter script provided in the MipNerF 360 repository.
    parser = ArgumentParser("Colmap converter")
    #this name shows when writing --help
    parser.add_argument("--no_gpu", action='store_true')
    # The action keyword argument specifies how the command-line arguments should be handled
    # here no_gpu will store True when --no_gpu is passed
    parser.add_argument("--skip_matching", action='store_true')
    # will store True when --skip_matching is passed, by default it is False
    parser.add_argument("--skip_undistortion", action='store_true')
    # will store True when --skip_undistortion is passed, by default it is False
    parser.add_argument("--source_path", "-s", required=True, type=str)
    # expects a folder named input in the source_path
    # source_path
    #   |---input
    parser.add_argument("--camera", default="OPENCV", type=str)
    # but uses PINHOLE model in the end
    # https://github.com/animesh-77/gaussian-splatting/blob/7ab5aed831f2340de09bc5611c6648e57c51f110/scene/dataset_readers.py#L95C1-L95C134
    parser.add_argument("--colmap_executable", default="", type=str)
    parser.add_argument("--skip_resize", action="store_true", default=False)
    parser.add_argument("--magick_executable", default="", type=str)
    args = parser.parse_args()
    # print all the command line arguments
    for arg in vars(args):
        print(f"DISREGARD THIS  {arg}: {getattr(args, arg)}")
    colmap_command = '"{}"'.format(args.colmap_executable) if len(args.colmap_executable) > 0 else "colmap"
    print(f"DISREGARD THIS  {colmap_command}")
    magick_command = '"{}"'.format(args.magick_executable) if len(args.magick_executable) > 0 else "magick"
    print(f"DISREGARD THIS  {magick_command}")
    use_gpu = 1 if not args.no_gpu else 0
    # from TRUE to 1, from FALSE to 0

    if not args.skip_matching:
        # if already matched features are provided, we can skip the matching step
        os.makedirs(args.source_path + "/distorted/sparse", exist_ok=True)
        # till now the source_path tree is
        # source_path
        #   |---input
        #   |---distorted
        #       |---sparse

        ## Feature extraction
        feat_extracton_cmd = colmap_command + " feature_extractor "\
            "--database_path " + args.source_path + "/distorted/database.db \
            --image_path " + args.source_path + "/input \
            --ImageReader.single_camera 1 \
            --ImageReader.camera_model " + args.camera + " \
            --SiftExtraction.use_gpu " + str(use_gpu)
        # COLMAP CLI to extract SIFT features from images
        # COLMAP feature_extractor
        # --database_path: Path to the SQLite database file, will be created
        # --image_path :NOTE name of images directory is input
        # --ImageReader.single_camera 1: Ensures all images have the same camera model
        # --ImageReader.camera_model: Camera model to use for all images, default is OPENCV model
        # because default args.camera is OPENCV
        # --SiftExtraction.use_gpu: Whether to use the GPU for SIFT extraction
        exit_code = os.system(feat_extracton_cmd)
        # feat_extracton_cmd is a simple string!!
        # now the source_path tree is
        # source_path
        #   |---input   
        #   |---distorated
        #       |---database.db
        #       |---sparse
        if exit_code != 0:
        # exit code 0 means successful execution
            logging.error(f"Feature extraction failed with code {exit_code}. Exiting.")
            exit(exit_code)

        ## Feature matching
        feat_matching_cmd = colmap_command + " exhaustive_matcher \
            --database_path " + args.source_path + "/distorted/database.db \
            --SiftMatching.use_gpu " + str(use_gpu)
        # exhausitive matching is used to match features between images
        # database path same as above
        # SiftMatching.use_gpu: Use GPU is used in last step
        # No change in source_path tree structure only database.db is updated
        exit_code = os.system(feat_matching_cmd)
        if exit_code != 0:
            logging.error(f"Feature matching failed with code {exit_code}. Exiting.")
            exit(exit_code)

        ### Bundle adjustment
        # The default Mapper tolerance is unnecessarily large,
        # decreasing it speeds up bundle adjustment steps.
        mapper_cmd = (colmap_command + " mapper \
            --database_path " + args.source_path + "/distorted/database.db \
            --image_path "  + args.source_path + "/input \
            --output_path "  + args.source_path + "/distorted/sparse \
            --Mapper.ba_global_function_tolerance=0.000001")
        # Mapper is the main command to run the bundle adjustment
        # database, image paths same as above
        # output path is where the output will be stored
        # bundle adjustment global function tolerance
        # source_path tree structure
        # source_path
        #   |---input
        #   |---distorated
        #       |---database.db
        #       |---sparse
        #           |---0
        #               |---cameras.bin
        #               |---images.bin
        #               |---points3D.bin
        #               |---project.ini
        #           |---1 and so on. normally we need/get a single consolidated model
        exit_code = os.system(mapper_cmd)
        if exit_code != 0:
            logging.error(f"Mapper failed with code {exit_code}. Exiting.")
            exit(exit_code)
    else:
        print("Skipping feature extraction, matching and bundle adjustment.")
    if not args.skip_undistortion:
        ### Image undistortion
        ## We need to undistort our images into ideal pinhole intrinsics.
        img_undist_cmd = (colmap_command + " image_undistorter \
            --image_path " + args.source_path + "/input \
            --input_path " + args.source_path + "/distorted/sparse/0 \
            --output_path " + args.source_path + "\
            --output_type COLMAP")
        # image_path same as above. image folder name should be /input !!
        # input_path to the sparse point cloud model
        # new folder created for undistorated images in source_path/images
        # output_type COLMAP ???
        # now the source_path tree is
        # source_path
        #   |---input
        #   |---distorated
        #       |---database.db
        #       |---sparse
        #           |---0
        #           |---1 and so on. normally we need/get a single consolidated model
        #   |---images
        #   |---sparse
        #       |---cameras.bin
        #       |---images.bin
        #       |---points3D.bin
        #   |---stereo
        #       |---consistency_graphs
        #       |---depth_maps
        #       |---normal_maps
        #       |---fusion.cfg
        #       |---patch_match.cfg
        #   |---run_colmap-geometric.sh
        #   |---run_colmap-photometric.sh
        # Why are empty stereo folders created??
        exit_code = os.system(img_undist_cmd)
        if exit_code != 0:
            logging.error(f"Mapper failed with code {exit_code}. Exiting.")
            exit(exit_code)

        files = os.listdir(args.source_path + "/sparse")
        os.makedirs(args.source_path + "/sparse/0", exist_ok=True)
        # Copy each file from the source directory to the destination directory
        for file in files:
            if file == '0':
                continue
            source_file = os.path.join(args.source_path, "sparse", file)
            destination_file = os.path.join(args.source_path, "sparse", "0", file)
            shutil.move(source_file, destination_file)
        # now the source_path tree is
        # source_path
        #   |---input
        #   |---distorated
        #       |---database.db
        #       |---sparse
        #           |---0
        #           |---1 and so on. normally we need/get a single consolidated model
        #   |---images
        #   |---sparse
        #       |---0
        #           |---cameras.bin
        #           |---images.bin
        #           |---points3D.bin
        #   |---stereo
        #       |---consistency_graphs
        #       |---depth_maps
        #       |---normal_maps
        #       |---fusion.cfg
        #       |---patch_match.cfg
        #   |---run_colmap-geometric.sh
        #   |---run_colmap-photometric.sh
    else:
        print("Skipping image undistortion.")
    if not args.skip_resize:
        # Only if resize is set True
        print("Copying and resizing...")

        # Resize images.
        os.makedirs(args.source_path + "/images_2", exist_ok=True)
        os.makedirs(args.source_path + "/images_4", exist_ok=True)
        os.makedirs(args.source_path + "/images_8", exist_ok=True)
        # Get the list of files in the source directory
        files = os.listdir(args.source_path + "/images")
        # :NOTE resize only the undistorted images
        # no images folder created during image_undistorter
        # Copy each file from the source directory to the destination directory
        for file in files:
            source_file = os.path.join(args.source_path, "images", file)

            destination_file = os.path.join(args.source_path, "images_2", file)
            shutil.copy2(source_file, destination_file)
            exit_code = os.system(magick_command + " mogrify -resize 50% " + destination_file)
            if exit_code != 0:
                logging.error(f"50% resize failed with code {exit_code}. Exiting.")
                exit(exit_code)

            destination_file = os.path.join(args.source_path, "images_4", file)
            shutil.copy2(source_file, destination_file)
            exit_code = os.system(magick_command + " mogrify -resize 25% " + destination_file)
            if exit_code != 0:
                logging.error(f"25% resize failed with code {exit_code}. Exiting.")
                exit(exit_code)

            destination_file = os.path.join(args.source_path, "images_8", file)
            shutil.copy2(source_file, destination_file)
            exit_code = os.system(magick_command + " mogrify -resize 12.5% " + destination_file)
            if exit_code != 0:
                logging.error(f"12.5% resize failed with code {exit_code}. Exiting.")
                exit(exit_code)
    else:
        print("Skipping resizing.")
    print("Done.")

if __name__ == "__main__":
    main()