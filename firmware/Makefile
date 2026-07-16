CXX ?= c++
CXXFLAGS ?= -std=c++17 -Wall -Wextra -Wpedantic -Werror -O2
SANITIZER_FLAGS = -fsanitize=address,undefined -fno-omit-frame-pointer -O1

INCLUDES = -Icommon/include -Iboards/include -Itests
COMMON_SOURCES = \
	common/src/debounce.cpp \
	common/src/encoder.cpp \
	common/src/navigation.cpp \
	common/src/protocol.cpp \
	common/src/protocol_payloads.cpp \
	common/src/rgb.cpp \
	common/src/safety.cpp \
	common/src/sequence.cpp \
	common/src/state.cpp \
	common/src/touch.cpp
PORT_STUB_SOURCES = \
	ports/esp32s3/bench_port_stub.cpp \
	ports/nrf52840/bench_port_stub.cpp
TEST_SOURCES = tests/test_main.cpp
ALL_SOURCES = $(COMMON_SOURCES) $(PORT_STUB_SOURCES) $(TEST_SOURCES)
TEST_BINARY = build/agent_deck_common_tests
SANITIZER_BINARY = build/agent_deck_common_tests_sanitized
EMBEDDED_CHECK_BINARY = build/agent_deck_common_tests_no_runtime

.PHONY: all test sanitize embedded-check clean

all: test

$(TEST_BINARY): $(ALL_SOURCES)
	@mkdir -p build
	$(CXX) $(CXXFLAGS) $(INCLUDES) $(ALL_SOURCES) -o $(TEST_BINARY)

test: $(TEST_BINARY)
	./$(TEST_BINARY)

sanitize:
	@mkdir -p build
	$(CXX) $(CXXFLAGS) $(SANITIZER_FLAGS) $(INCLUDES) $(ALL_SOURCES) -o $(SANITIZER_BINARY)
	./$(SANITIZER_BINARY)

embedded-check:
	@mkdir -p build
	$(CXX) $(CXXFLAGS) -fno-exceptions -fno-rtti $(INCLUDES) $(ALL_SOURCES) -o $(EMBEDDED_CHECK_BINARY)
	./$(EMBEDDED_CHECK_BINARY)

clean:
	rm -rf build
