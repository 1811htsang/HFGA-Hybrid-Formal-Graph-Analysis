#!/bin/bash

# @brief Enter build
echo "[HFGA] Setting up environment for CLANG compiler..."
export CC=/usr/lib64/ccache/clang
export CXX=/usr/lib64/ccache/clang++

# @brief Enter build
echo "[HFGA] Entering build directory..."
cd /home/shanghuang/HFGA/sample/test/build

# @brief Build the project using CMake
echo "[HFGA] Building the project with CLANG..."
cmake -DCOMPILER=CLANG -DPLATFORM=LINUX ..

# @brief Exiting...
echo "[HFGA] Build completed. Exiting..."
exit 0
