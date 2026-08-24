---
id: python-exception-handling
title: Python Exception Handling
category: python_topic
one_liner: Learn how to use try, except, else, and finally blocks to catch and handle errors in Python programs gracefully.
created_at: 2026-08-23T14:57:38Z
updated_at: 2026-08-23T14:57:38Z
turn_count: 1
---

## Summary

Python uses `try` and `except` blocks to handle potential errors, preventing program crashes. Specific exceptions like `ValueError` or `ZeroDivisionError` can be caught, or a general `Exception` can be used as a catch-all. The optional `else` block executes if no exception occurs, while the `finally` block always runs, typically for cleanup operations like closing files.

## Conversation Log

### 2026-08-23T14:57:38Z
**Q:** How do I catch exceptions in Python?
**A (key points):**
- Okay, let's talk about catching exceptions in Python! This is a crucial part of writing robust and user-friendly code, allowing your program to handle unexpected errors gracefully instead of crashing.

In Python, you use the `try`, `except`, `else`, and `finally` blocks to handle exceptions.

### The Core: `try` and `except`

The most basic form involves `try` and `except`.

*   **`try` block**: This is where you put the code that *might* raise an exception.
*   **`except` block**: This is where you put the code that will execute *if* an exception occurs in the `try` block.

**Example 1: Division by Zero**

```python
try:
    numerator = 10
    denominator = 0
    result = numerator / denominator
    print(f"The result is: {result}")
except ZeroDivisionError:
    print("Error: Cannot divide by zero!")

print("Program continues after exception handling.")
```

**Output:**

```
Error: Cannot divide by zero!
Program continues after exception handling.
```

Without the `try-except` block, the program would have crashed with a `ZeroDivisionError`.

### Catching Specific Exceptions

It's good practice to catch specific types of exceptions rather than a general one. This allows you to handle different errors in different ways.

**Example 2: Handling multiple potential errors**

```python
try:
    num1 = int(input("Enter a number: "))
    num2 = int(input("Enter another number: "))
    result = num1 / num2
    print(f"The result is: {result}")
except ValueError:
    print("Error: Invalid input. Please enter whole numbers only.")
except ZeroDivisionError:
    print("Error: You cannot divide by zero!")
except Exception as e: # A general catch-all for other unexpected errors
    print(f"An unexpected error occurred: {e}")

print("Program finished.")
```

**Explanation:**

*   If the user enters text instead of a number, `int()` will raise a `ValueError`, and the first `except ValueError` block will execute.
*   If the user enters `0` for the second number, a `ZeroDivisionError` will be caught.
*   The `except Exception as e:` block is a general catch-all. `Exception` is the base class for most built-in, non-system-exiting exceptions. Using `as e` allows you to capture the exception object itself, which often contains a helpful error message. It's generally placed *after* more specific `except` blocks.

### Catching Multiple Exceptions in One `except` Block

You can catch several specific exceptions with a single `except` block by providing them as a tuple.

```python
try:
    user_input = input("Enter a number: ")
    number = int(user_input)
    result = 10 / number
    print(f"Result: {result}")
except (ValueError, ZeroDivisionError):
    print("Error: Please enter a non-zero whole number.")
```

### The `else` Block

The `else` block is optional and executes *only if* the code inside the `try` block runs without raising any exceptions.

```python
try:
    num1 = int(input("Enter first number: "))
    num2 = int(input("Enter second number: "))
    result = num1 / num2
except (ValueError, ZeroDivisionError):
    print("An error occurred: Please enter valid non-zero numbers.")
else:
    print(f"Division successful! Result: {result}")
    print("No exceptions were raised.")
finally:
    print("This will always execute.")
```

### The `finally` Block

The `finally` block is also optional, but it's very important. The code inside the `finally` block will **always** execute, regardless of whether an exception occurred in the `try` block or not, and regardless of whether it was caught.

This is commonly used for cleanup operations, like closing files, releasing resources, or ensuring a connection is closed.

```python
file = None # Initialize file handle outside try block
try:
    file = open("my_data.txt", "r")
    content = file.read()
    print("File content read successfully.")
    # Simulate another error
    # x = 1 / 0
except FileNotFoundError:
    print("Error: The file 'my_data.txt' was not found.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
finally:
    if file: # Check if the file was actually opened
        file.close()
        print("File closed.")
    print("Cleanup complete.")
```

**Scenario 1: File exists, no other errors**
Output:
```
File content read successfully.
File closed.
Cleanup complete.
```

**Scenario 2: File does not exist**
Output:
```
Error: The file 'my_data.txt' was not found.
Cleanup complete.
```
(Note: `file` remains `None`, so `file.close()` is not called, which is correct.)

**Scenario 3: File exists, but `x = 1 / 0` is uncommented**
Output:
```
File content read successfully.
An unexpected error occurred: division by zero
File closed.
Cleanup complete.
```
(The `finally` block still runs, ensuring the file is closed even though an uncaught error occurred *after* the file operation.)

### Best Practices:

*   **Be Specific**: Catch specific exceptions whenever possible. This makes your error handling more precise and prevents you from accidentally suppressing unexpected errors.
*   **Avoid Bare `except`**: `except:` (without specifying an exception type) will catch *all* exceptions, including system-exiting ones like `SystemExit` and `KeyboardInterrupt`. This can make debugging very difficult and prevent your program from being terminated gracefully. If you need a catch-all, use `except Exception as e:`.
*   **Keep `try` Blocks Small**: Only put the code that might raise an exception inside the `try` block. This makes it easier to pinpoint the source of the error.
*   **Log Errors**: In real-world applications, instead of just printing, you'd often log the exception details to a file or a monitoring system.
*   **Raise Exceptions**: Sometimes, it's appropriate to catch an exception, do some cleanup, and then re-raise it (`raise`) if your function can't fully handle the error. You can also raise your own custom exceptions.

Understanding and effectively using `try-except-else-finally` is a cornerstone of writing robust Python applications!
