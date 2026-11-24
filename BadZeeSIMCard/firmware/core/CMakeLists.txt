cmake_minimum_required(VERSION 3.20)
project(bz_core C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Debug)
endif()

add_library(bzcore STATIC
  src/bz_core.c
  src/bz_stk.c
)
target_include_directories(bzcore PUBLIC include)
target_compile_options(bzcore PRIVATE -Wall -Wextra -Wpedantic -Werror)
target_compile_options(bzcore PUBLIC -fsanitize=address,undefined -fno-omit-frame-pointer)
target_link_options(bzcore PUBLIC -fsanitize=address,undefined)

add_executable(bz_tests tests/test_core.c)
target_link_libraries(bz_tests PRIVATE bzcore)

enable_testing()
add_test(NAME core COMMAND bz_tests)
