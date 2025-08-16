from dataclasses import dataclass


@dataclass
class CodeTemplate:
    name: str
    code: str


templates = [
    CodeTemplate(
        name='For loop with assignment',
        code="""
for i in range(3):
    x = i * 2
""",
    ),
    CodeTemplate(
        name='Function with type annotations',
        code="""
def greet(name: str) -> str:
    return f"Hello, {name}!"
""",
    ),
    CodeTemplate(
        name='Class inheritance and method',
        code="""
class Animal:
    def speak(self):
        pass

class Dog(Animal):
    def speak(self):
        return "Woof!"
""",
    ),
    CodeTemplate(
        name='List comprehension',
        code="""
numbers = [x ** 2 for x in range(10) if x % 2 == 0]
""",
    ),
    CodeTemplate(
        name='Lambda function',
        code="""
add = lambda x, y: x + y
""",
    ),
    CodeTemplate(
        name='Function with decorator',
        code="""
def log(func):
    def wrapper(*args, **kwargs):
        print("Calling", func.__name__)
        return func(*args, **kwargs)
    return wrapper

@log
def foo():
    return "bar"
""",
    ),
    CodeTemplate(
        name='Exception handling',
        code="""
try:
    1 / 0
except ZeroDivisionError as e:
    print("Can't divide by zero!")
finally:
    print("Done")
""",
    ),
    CodeTemplate(
        name='F-string example',
        code="""
value = 42
msg = f"Value is {value}"
""",
    ),
    CodeTemplate(
        name='Match-case (Python 3.10+)',
        code="""
def what_day(day):
    match day:
        case "Monday":
            return 1
        case "Tuesday":
            return 2
        case _:
            return 0
""",
    ),
]
