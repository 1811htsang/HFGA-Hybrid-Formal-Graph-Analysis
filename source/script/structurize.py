import re
import json
import argparse

def parse_llvm_analysis(alias_file, stack_file, callgraph_file):
    results = {}

    # --- 1. Parse Call Graph ---
    with open(callgraph_file, 'r') as f:
        content = f.read()
        functions = re.findall(
            r"Call graph node for function: '([^']+)'<<0x[0-9a-f]+>>.*?#uses=\d+(.*?)(?:\n\n|\Z)",
            content,
            re.DOTALL,
        )
        for func_name, body in functions:
            if func_name not in results: results[func_name] = {}
            calls = re.findall(r"calls function '([^']+)'", body)
            results[func_name]['calls'] = list(set(calls))

    # --- 2. Parse Stack Safety ---
    with open(stack_file, 'r') as f:
        content = f.read()
        stack_data = re.findall(r"@(\w+)\s+args uses:.*?allocas uses:\s+(.*?)\s+safe accesses:", content, re.DOTALL)
        for func_name, allocas in stack_data:
            if func_name in results:
                # Trích xuất kích thước stack (ví dụ [8], [136])
                sizes = re.findall(r"\[(\d+)\]", allocas)
                results[func_name]['stack_allocas'] = [int(s) for s in sizes]
                results[func_name]['stack_safe'] = "unsafe" not in allocas

    # --- 3. Parse Alias Sets ---
    with open(alias_file, 'r') as f:
        content = f.read()
        alias_blocks = content.split("Alias sets for function '")
        for block in alias_blocks[1:]:
            lines = block.split("\n")
            func_name = lines[0].replace("':", "").strip()
            if func_name in results:
                alias_list = []
                for line in lines:
                    if "alias" in line:
                        # Rút gọn: lấy loại alias và danh sách con trỏ
                        match = re.search(r"(must alias|may alias).*Memory locations: \((.*?)\)", line)
                        if match:
                            alias_type = match.group(1)
                            pointers = re.findall(r"%(ptr %\d+|%\d+)", match.group(2))
                            alias_list.append({"type": alias_type, "ptrs": pointers})
                results[func_name]['aliases'] = alias_list

    return results

def main():
    parser = argparse.ArgumentParser(
        description="Parse LLVM alias/stack/callgraph outputs into JSON"
    )
    parser.add_argument("alias_file", help="Path to alias analysis output file")
    parser.add_argument("stack_file", help="Path to stack analysis output file")
    parser.add_argument("callgraph_file", help="Path to call graph output file")
    parser.add_argument(
        "-o",
        "--output",
        default="firmware_logic.json",
        help="Output JSON file path (default: firmware_logic.json)",
    )
    args = parser.parse_args()

    data = parse_llvm_analysis(args.alias_file, args.stack_file, args.callgraph_file)
    with open(args.output, 'w') as f:
        json.dump(data, f, indent=4)

    print(f"Da tao file {args.output} gon gang cho Z3!")


if __name__ == "__main__":
    main()