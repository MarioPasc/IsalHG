cmake_minimum_required(VERSION 3.18)
project(isalhg_native LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT DEFINED CMAKE_BUILD_TYPE OR CMAKE_BUILD_TYPE STREQUAL "")
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

# Default Release flags. Warnings are project-wide; -march=native ties
# the .so to the build host CPU, which is acceptable for a research repo
# where the dev workstation and CI share a CPU family.
add_compile_options(-Wall -Wextra -Wpedantic)
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    add_compile_options(-O3 -march=native -DNDEBUG)
endif()

option(ISALHG_ENABLE_SANITIZERS "Enable Address + Undefined sanitizers" OFF)
if(ISALHG_ENABLE_SANITIZERS)
    add_compile_options(-fsanitize=address,undefined -fno-omit-frame-pointer -g -O1)
    add_link_options(-fsanitize=address,undefined)
endif()

find_package(Python 3.11 REQUIRED COMPONENTS Interpreter Development.Module)
find_package(nanobind CONFIG REQUIRED)

nanobind_add_module(_core
    NB_STATIC
    src/isalhg/_core/bindings.cpp
    src/isalhg/_core/src/cdll.cpp
    src/isalhg/_core/src/token.cpp
    src/isalhg/_core/src/sparse_hypergraph.cpp
    src/isalhg/_core/src/h2s.cpp
    src/isalhg/_core/src/structural_tuples.cpp
    src/isalhg/_core/src/wl.cpp
    src/isalhg/_core/src/canonical.cpp
)

target_include_directories(_core PRIVATE src/isalhg/_core/include)

install(TARGETS _core LIBRARY DESTINATION isalhg)
