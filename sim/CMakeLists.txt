cmake_minimum_required(VERSION 3.20)
project(verifieds_sim LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Quality-gate flags (from .agent/rules/quality.md)
add_compile_options(
    -Wall -Wextra -Wpedantic
    -Wshadow -Wconversion -Werror
)

# Sanitizers (opt-in; enabled in make verify-sim)
option(ENABLE_SANITIZERS "Enable AddressSanitizer and UBSanitizer" OFF)
if(ENABLE_SANITIZERS)
    add_compile_options(-fsanitize=address,undefined -fno-omit-frame-pointer)
    add_link_options(-fsanitize=address,undefined)
endif()

# ── Source library (no main) ─────────────────────────────────────────────────
add_library(sim_lib INTERFACE)
target_include_directories(sim_lib INTERFACE ${CMAKE_CURRENT_SOURCE_DIR}/src)

# ── Tests ────────────────────────────────────────────────────────────────────
enable_testing()

add_executable(test_smoke tests/test_smoke.cpp)
target_link_libraries(test_smoke PRIVATE sim_lib)
add_test(NAME smoke COMMAND test_smoke)

add_executable(test_structures tests/test_structures.cpp)
target_link_libraries(test_structures PRIVATE sim_lib)
add_test(NAME structures COMMAND test_structures)

add_executable(test_scheduler tests/test_scheduler.cpp)
target_link_libraries(test_scheduler PRIVATE sim_lib)
add_test(NAME scheduler COMMAND test_scheduler)

add_executable(sim_cli src/main.cpp)
target_link_libraries(sim_cli PRIVATE sim_lib)


