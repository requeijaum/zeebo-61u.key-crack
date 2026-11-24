# Pico firmware build. Requires PICO_SDK_PATH (see tools/build_firmware.sh).
cmake_minimum_required(VERSION 3.13)

if(NOT DEFINED ENV{PICO_SDK_PATH})
  message(FATAL_ERROR "PICO_SDK_PATH is not set; run tools/build_firmware.sh")
endif()

include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(badzeesim C CXX ASM)
set(CMAKE_C_STANDARD 11)

pico_sdk_init()

add_executable(badzeesim
  src/main.c
  src/phy.c
  src/host_link.c
  ../core/src/bz_core.c
  ../core/src/bz_stk.c
)

target_include_directories(badzeesim PRIVATE
  include
  ../core/include
)

target_compile_options(badzeesim PRIVATE -Wall -Wextra)

# Firmware identity goes into HELLO_ACK so a run can be pinned to a binary.
execute_process(
  COMMAND git rev-parse --short HEAD
  OUTPUT_VARIABLE BZ_GIT
  OUTPUT_STRIP_TRAILING_WHITESPACE
  ERROR_QUIET
)
if(NOT BZ_GIT)
  set(BZ_GIT "dev")
endif()
target_compile_definitions(badzeesim PRIVATE BZ_FW_HASH="${BZ_GIT}")

target_link_libraries(badzeesim
  pico_stdlib
  pico_stdio_usb
  hardware_gpio
  hardware_timer
)

pico_enable_stdio_usb(badzeesim 1)
pico_enable_stdio_uart(badzeesim 0)
pico_add_extra_outputs(badzeesim)
