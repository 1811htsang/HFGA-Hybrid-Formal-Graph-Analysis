cmake_minimum_required(VERSION 3.10)
project(ciedpc_test C)

# 0. Ép buộc dùng CLANG nếu muốn tạo Bitcode (Khuyến khích)
set(COMPILER "CLANG" CACHE STRING "Target C compiler: GCC, CLANG")
if(COMPILER STREQUAL "CLANG")
  set(CMAKE_C_COMPILER "clang")
  # Tìm đường dẫn đến llvm-link để gom các file .bc lại
  find_program(LLVM_LINK llvm-link REQUIRED)
else()
  set(CMAKE_C_COMPILER "gcc")
endif()

set(PLATFORM "LINUX" CACHE STRING "Target platform: LINUX, STM32, ESP32")

# 2. File nguồn
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
# 5A. TẠO FILE THỰC THI (Binary thông thường để chạy/debug)
# ---------------------------------------------------------
add_executable(${PROJECT_NAME} ${SOURCES})
target_include_directories(${PROJECT_NAME} PRIVATE
  ../core/inc/ ../common/container/fifo/ ../pal/ ../pal/arch/linux/ ./
)
if(PLATFORM_LIBS)
  target_link_libraries(${PROJECT_NAME} ${PLATFORM_LIBS})
endif()

# ---------------------------------------------------------
# 5B. TẠO FILE BITCODE (.bc) ĐỂ PHÂN TÍCH (Chỉ khi dùng CLANG)
# ---------------------------------------------------------
if(COMPILER STREQUAL "CLANG")
  message(STATUS "Bitcode generation target enabled: ${PROJECT_NAME}.bc")
  
  # Đường dẫn đến thư mục chứa bitcode lẻ
  set(BC_SUBDIR "${CMAKE_CURRENT_BINARY_DIR}/bitcode")
  
  # Tạo thư mục bitcode nếu chưa tồn tại (chạy lúc cấu hình)
  file(MAKE_DIRECTORY ${BC_SUBDIR})

  set(BITCODE_FILES "")
  foreach(SRC ${SOURCES})
    # Lấy tên file nguồn (ví dụ: ciedpc_fsm.c)
    get_filename_component(SRC_NAME ${SRC} NAME)
    
    # Đặt file output vào folder bitcode (ví dụ: build/bitcode/ciedpc_fsm.c.bc)
    set(BC_FILE "${BC_SUBDIR}/${SRC_NAME}.bc")
    
    # Lệnh biên dịch từng file nguồn sang bitcode
    add_custom_command(
      OUTPUT ${BC_FILE}
      # Đảm bảo thư mục tồn tại trước khi ghi file (chạy lúc build)
      COMMAND ${CMAKE_COMMAND} -E make_directory ${BC_SUBDIR}
      COMMAND ${CMAKE_C_COMPILER} -emit-llvm -c -g -O0 
        -DCIEDPC_PLATFORM_LINUX
        -I${CMAKE_CURRENT_SOURCE_DIR}/../core/inc/
        -I${CMAKE_CURRENT_SOURCE_DIR}/../common/container/fifo/
        -I${CMAKE_CURRENT_SOURCE_DIR}/../pal/
        -I${CMAKE_CURRENT_SOURCE_DIR}/../pal/arch/linux/
        ${CMAKE_CURRENT_SOURCE_DIR}/${SRC}
        -o ${BC_FILE}
      DEPENDS ${SRC}
      COMMENT "Generating bitcode for ${SRC_NAME} in bitcode/ folder"
    )
    list(APPEND BITCODE_FILES ${BC_FILE})
  endforeach()

  # Lệnh gom tất cả các file .bc trong folder bitcode thành 1 file duy nhất ở ngoài
  add_custom_target(gen-bitcode
    COMMAND ${LLVM_LINK} ${BITCODE_FILES} -o ${CMAKE_CURRENT_BINARY_DIR}/${PROJECT_NAME}.bc
    DEPENDS ${BITCODE_FILES}
    COMMENT "Linking all intermediate bitcodes into ${PROJECT_NAME}.bc"
  )
endif()