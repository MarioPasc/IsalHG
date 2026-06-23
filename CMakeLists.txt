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
    add_compile_options(-O3 -march=native -DNDEBUG -fno-plt -funroll-loops)
    # Link-time optimisation across translation units. nanobind's helper
    # already enables LTO for the binding shim; this propagates the
    # setting to the rest of the C++ sources too.
    include(CheckIPOSupported)
    check_ipo_supported(RESULT _IPO_OK OUTPUT _IPO_ERR)
    if(_IPO_OK)
        set(CMAKE_INTERPROCEDURAL_OPTIMIZATION ON)
    endif()
endif()

option(ISALHG_ENABLE_SANITIZERS "Enable Address + Undefined sanitizers" OFF)
if(ISALHG_ENABLE_SANITIZERS)
    add_compile_options(-fsanitize=address,undefined -fno-omit-frame-pointer -g -O1)
    add_link_options(-fsanitize=address,undefined)
endif()

# Profile-guided optimisation. Two-stage build:
#  1. CMAKE_ARGS="-DISALHG_PGO_GENERATE=ON" pip install -e ".[dev]"
#  2. Run the training script (scratchpad/cpp_pgo_train.py)
#  3. CMAKE_ARGS="-DISALHG_PGO_USE=ON" pip install -e ".[dev]"
# Profile data persists in ${ISALHG_PGO_DATA}; remove between fresh runs.
option(ISALHG_PGO_GENERATE "Build with -fprofile-generate" OFF)
option(ISALHG_PGO_USE "Build with -fprofile-use" OFF)
set(ISALHG_PGO_DATA "${CMAKE_SOURCE_DIR}/build/pgo-data"
    CACHE PATH "Directory holding GCC PGO .gcda files")
if(ISALHG_PGO_GENERATE)
    file(MAKE_DIRECTORY ${ISALHG_PGO_DATA})
    add_compile_options(-fprofile-generate=${ISALHG_PGO_DATA})
    add_link_options(-fprofile-generate=${ISALHG_PGO_DATA})
endif()
if(ISALHG_PGO_USE)
    add_compile_options(-fprofile-use=${ISALHG_PGO_DATA}
                        -fprofile-correction -Wno-missing-profile)
    add_link_options(-fprofile-use=${ISALHG_PGO_DATA})
endif()

find_package(Python 3.11 REQUIRED COMPONENTS Interpreter Development.Module)
find_package(nanobind CONFIG REQUIRED)

nanobind_add_module(_core
    NB_STATIC
    src/isalhg/core/_native/bindings.cpp
    src/isalhg/core/_native/src/cdll.cpp
    src/isalhg/core/_native/src/token.cpp
    src/isalhg/core/_native/src/sparse_hypergraph.cpp
    src/isalhg/core/_native/src/h2s.cpp
    src/isalhg/core/_native/src/structural_tuples.cpp
    src/isalhg/core/_native/src/wl.cpp
    src/isalhg/core/_native/src/canonical.cpp
    src/isalhg/core/_native/src/thread_pool.cpp
)

find_package(Threads REQUIRED)
target_link_libraries(_core PRIVATE Threads::Threads)

target_include_directories(_core PRIVATE src/isalhg/core/_native/include)

# Install the extension inside the isalhg.core package so the C++
# implementation is importable at ``isalhg.core._core`` — mirroring
# the Python ``_python_*`` references that live in the same package.
install(TARGETS _core LIBRARY DESTINATION isalhg/core)
