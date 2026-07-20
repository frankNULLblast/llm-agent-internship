def greet(name: str) -> str:
    if not name.strip():
        raise ValueError("姓名不能为空白")
    return f"Hello, {name}!"


if __name__ == "__main__":
    print(greet("student"))
