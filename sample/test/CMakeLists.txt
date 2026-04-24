cmake_minimum_required(VERSION 3.10)
project(ciedpc_test C)

# 0. Lựa chọn compiler
set(COMPILER "CLANG" CACHE STRING "Target C compiler: GCC, CLANG")
if(COMPILER STREQUAL "CLANG")
  set(CMAKE_C_COMPILER "clang")
  find_program(LLVM_LINK llvm-link REQUIRED)
else()
  set(CMAKE_C_COMPILER "gcc")
endif()

set(PLATFORM "LINUX" CACHE STRING "Target platform: LINUX, STM32, ESP32")

# 1. Lấy thông tin KLEE (Cần thiết cho cả 2 bản build nếu có include klee.h)
if(COMPILER STREQUAL "CLANG")
  execute_process(COMMAND klee.env CFLAGS OUTPUT_VARIABLE KLEE_CFLAGS_RAW)
  string(STRIP "${KLEE_CFLAGS_RAW}" KLEE_CFLAGS_RAW)
  # Chuyển chuỗi thành danh sách để CMake hiểu các khoảng trắng
  separate_arguments(KLEE_CFLAGS_LIST NATIVE_COMMAND "${KLEE_CFLAGS_RAW}")
  
  # Trích xuất đường dẫn include để dùng cho target_include_directories
  # Thường là /snap/klee/18/usr/local/include
  set(KLEE_INCLUDE_DIR "/snap/klee/current/usr/local/include") 
endif()



# 2. Danh sách file nguồn
set(CORE_SOURCES
  ../core/src/ciedpc_fsm.c
  ../core/src/ciedpc_tsm.c
  ../core/src/ciedpc_msg.c
  ../core/src/ciedpc_task.c
  ../core/src/ciedpc_timer.c
  ../common/container/fifo/fifo.c
)

if(PLATFORM STREQUAL "LINUX")
  set(PAL_SOURCES ../pal/arch/linux/linux_arch.c)
  set(PLATFORM_LIBS pthread)
  add_definitions(-DCIEDPC_PLATFORM_LINUX)
endif()

set(SOURCES test.c ${CORE_SOURCES} ${PAL_SOURCES})

# ---------------------------------------------------------
# 5A. TẠO FILE THỰC THI (Để chạy simulation bình thường)
# ---------------------------------------------------------
add_executable(${PROJECT_NAME} ${SOURCES})
target_include_directories(${PROJECT_NAME} PRIVATE
  ../core/inc/ ../common/container/fifo/ ../pal/ ../pal/arch/linux/ ./
  ${KLEE_INCLUDE_DIR} # <--- Quan trọng: Để bản native không lỗi khi gặp klee.h
)
if(PLATFORM_LIBS)
  target_link_libraries(${PROJECT_NAME} ${PLATFORM_LIBS})
endif()

# ---------------------------------------------------------
# 5B. TẠO FILE BITCODE (.bc) ĐỂ PHÂN TÍCH KLEE/OPT
# ---------------------------------------------------------
if(COMPILER STREQUAL "CLANG")
  # 1. Lấy thông tin CFLAGS từ klee.env
  execute_process(COMMAND klee.env CFLAGS OUTPUT_VARIABLE KLEE_CFLAGS_RAW)
  string(STRIP "${KLEE_CFLAGS_RAW}" KLEE_CFLAGS_RAW)
  separate_arguments(KLEE_CFLAGS_LIST NATIVE_COMMAND "${KLEE_CFLAGS_RAW}")

  # 2. Định nghĩa thư mục chứa bitcode lẻ
  set(BC_SUBDIR "${CMAKE_CURRENT_BINARY_DIR}/bitcode")
  file(MAKE_DIRECTORY ${BC_SUBDIR})

  set(BITCODE_FILES "")
  foreach(SRC ${SOURCES})
    get_filename_component(SRC_NAME ${SRC} NAME)
    set(BC_FILE "${BC_SUBDIR}/${SRC_NAME}.bc")
    
    add_custom_command(
      OUTPUT ${BC_FILE}
      COMMAND ${CMAKE_COMMAND} -E make_directory ${BC_SUBDIR}
      
      # THÊM -DKLEE_IN_USE VÀO ĐÂY VÀ GIỮ CÁC CỜ QUAN TRỌNG KHÁC
      COMMAND ${CMAKE_C_COMPILER} ${KLEE_CFLAGS_LIST} 
              -DKLEE_IN_USE 
              -emit-llvm -c -g -O0 
              -Xclang -disable-O0-optnone
              -DCIEDPC_PLATFORM_LINUX
              -I${CMAKE_CURRENT_SOURCE_DIR}/../core/inc/
              -I${CMAKE_CURRENT_SOURCE_DIR}/../common/container/fifo/
              -I${CMAKE_CURRENT_SOURCE_DIR}/../pal/
              -I${CMAKE_CURRENT_SOURCE_DIR}/../pal/arch/linux/
              -I${CMAKE_CURRENT_SOURCE_DIR}/.
              ${CMAKE_CURRENT_SOURCE_DIR}/${SRC}
              -o ${BC_FILE}
      DEPENDS ${SRC}
      COMMENT "Generating bitcode for ${SRC_NAME} with KLEE_IN_USE"
    )
    list(APPEND BITCODE_FILES ${BC_FILE})
  endforeach()

  # 3. Gom file .bc
  add_custom_target(gen-bitcode
    COMMAND ${LLVM_LINK} ${BITCODE_FILES} -o ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}.bc
    DEPENDS ${BITCODE_FILES}
    COMMENT "Linking bitcodes with KLEE symbols"
  )
endif()