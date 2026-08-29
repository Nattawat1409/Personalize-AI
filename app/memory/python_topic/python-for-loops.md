---
id: python-for-loops
title: Python For-Loops
category: python_topic
one_liner: Explains the syntax and common uses of for-loops in Python for iterating over sequences and other iterables.
created_at: 2026-08-23T14:57:22Z
updated_at: 2026-08-24T10:18:25Z
turn_count: 3
---

## Summary

This turn explained the fundamentals of Python for-loops, including their basic syntax for iterating over sequences like lists, strings, and dictionaries. It covered using range() for numerical iterations, enumerate() for accessing both index and value, and the control flow statements break and continue to modify loop behavior.

## Conversation Log

### 2026-08-23T14:57:22Z
**Q:** How do I write a for-loop in Python?
**A (key points):**
- Okay, let's dive into `for` loops in Python!

Python's `for` loop is used for iterating over a sequence (like a list, tuple, dictionary, set, or string) or other iterable objects. It's a very powerful and commonly used construct.

Here's the basic syntax and some common examples:

### Basic Syntax

```python
for item in iterable:
    # do something with item
    # This block of code will execute for each item in the iterable
```

*   `for`: The keyword that starts the loop.
*   `item`: A variable name that will take on the value of each element in the `iterable` during each iteration. You can name this variable anything you like (e.g., `num`, `char`, `element`).
*   `in`: The keyword that specifies the `iterable` to loop through.
*   `iterable`: Any object that can return its members one at a time (e.g., a list, string, tuple, range object).
*   `:`: A colon marks the end of the `for` statement.
*   **Indentation**: The code inside the loop must be indented (typically 4 spaces) to indicate that it belongs to the loop.

### Common Examples

#### 1. Looping Through a List

This is one of the most common uses.

```python
my_list = ["apple", "banana", "cherry"]

for fruit in my_list:
    print(f"I like {fruit}")

# Output:
# I like apple
# I like banana
# I like cherry
```

#### 2. Looping Through a String

You can iterate over each character in a string.

```python
my_string = "Python"

for char in my_string:
    print(char)

# Output:
# P
# y
# t
# h
# o
# n
```

#### 3. Looping Using `range()`

The `range()` function is often used to loop a specific number of times.

*   `range(stop)`: Generates numbers from 0 up to (but not including) `stop`.
*   `range(start, stop)`: Generates numbers from `start` up to (but not including) `stop`.
*   `range(start, stop, step)`: Generates numbers from `start` up to (but not including) `stop`, incrementing by `step`.

```python
# Loop 5 times (from 0 to 4)
for i in range(5):
    print(f"Iteration number: {i}")

# Output:
# Iteration number: 0
# Iteration number: 1
# Iteration number: 2
# Iteration number: 3
# Iteration number: 4

# Loop from 2 to 6 (not including 7)
for j in range(2, 7):
    print(f"Number: {j}")

# Output:
# Number: 2
# Number: 3
# Number: 4
# Number: 5
# Number: 6

# Loop from 0 to 10, stepping by 2
for k in range(0, 11, 2):
    print(f"Even number: {k}")

# Output:
# Even number: 0
# Even number: 2
# Even number: 4
# Even number: 6
# Even number: 8
# Even number: 10
```

#### 4. Looping Through a Dictionary

You can iterate over keys, values, or key-value pairs.

```python
my_dict = {"name": "Alice", "age": 30, "city": "New York"}

# Iterate over keys (default)
for key in my_dict:
    print(key)

# Output:
# name
# age
# city

# Iterate over values
for value in my_dict.values():
    print(value)

# Output:
# Alice
# 30
# New York

# Iterate over key-value pairs (items)
for key, value in my_dict.items():
    print(f"{key}: {value}")

# Output:
# name: Alice
# age: 30
# city: New York
```

#### 5. Using `enumerate()` for Index and Value

If you need both the index and the value while looping through a sequence, `enumerate()` is very handy.

```python
colors = ["red", "green", "blue"]

for index, color in enumerate(colors):
    print(f"Color at index {index} is {color}")

# Output:
# Color at index 0 is red
# Color at index 1 is green
# Color at index 2 is blue
```

### `break` and `continue` Statements

*   **`break`**: Immediately terminates the loop.
*   **`continue`**: Skips the rest of the current iteration and moves to the next one.

```python
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

for num in numbers:
    if num == 5:
        print("Found 5, breaking the loop.")
        break  # Exit the loop entirely
    print(f"Current number (before break): {num}")

# Output:
# Current number (before break): 1
# Current number (before break): 2
# Current number (before break): 3
# Current number (before break): 4
# Found 5, breaking the loop.

print("-" * 20)

for num in numbers:
    if num % 2 != 0: # If number is odd
        print(f"Skipping odd number: {num}")
        continue # Skip to the next iteration
    print(f"Current even number: {num}")

# Output:
# Skipping odd number: 1
# Current even number: 2
# Skipping odd number: 3
# Current even number: 4
# Skipping odd number: 5
# Current even number: 6
# Skipping odd number: 7
# Current even number: 8
# Skipping odd number: 9
# Current even number: 10
```

That covers the essentials of writing `for` loops in Python! Let me know if you have a specific scenario in mind or want to explore more advanced uses.

### 2026-08-24T10:12:38Z
**Q:** How do I use Python list comprehensions?
**A (key points):**
- Building on our last chat about Python `for` loops, list comprehensions are a concise way to create lists. They're basically a single line `for` loop inside square brackets.

Here's how you use them:

*   **Basic Syntax:** `[expression for item in iterable]`
    *   `expression`: What you want to do with each `item` (e.g., `item * 2`, `item.upper()`).
    *   `item`: The variable for each element in the `iterable`.
    *   `iterable`: The list, tuple, string, or range you're looping through.

*   **Example (Simple):**
    ```python
    numbers = [1, 2, 3, 4]
    squared_numbers = [n * n for n in numbers]
    # Result: [1, 4, 9, 16]
    ```

*   **With a Condition (if statement):** `[expression for item in iterable if condition]`
    *   You can add an `if` statement to filter items.

*   **Example (With Condition):**
    ```python
    numbers = [1, 2, 3, 4, 5, 6]
    even_numbers = [n for n in numbers if n % 2 == 0]
    # Result: [2, 4, 6]
    ```

*   **Why use them?**
    *   They are often **shorter and more readable** than a traditional `for` loop for simple list creation.
    *   They can be **more efficient** in some cases.

Think of them as a compact way to build a new list based on an existing one, often replacing a multi-line `for` loop.

### 2026-08-24T10:18:25Z
**Q:** How do I use Python list comprehensions?
**A (key points):**
- We've actually covered Python list comprehensions before! To recap, they're a concise way to create lists using a single line of code.

Here's a quick reminder:

*   **Basic Idea:** It's like a `for` loop written inside square brackets `[]`.
*   **Syntax:** `[expression for item in iterable]`
    *   `expression`: What you want to do with each item (e.g., `item * 2`).
    *   `item`: The temporary variable for each element.
    *   `iterable`: The list, string, or range you're looping through.
*   **Example:**
    ```python
    numbers = [1, 2, 3]
    doubled = [n * 2 for n in numbers]
    # Result: [2, 4, 6]
    ```
*   **With a Condition:** You can add an `if` statement to filter items: `[expression for item in iterable if condition]`
    *   Example: `evens = [n for n in numbers if n % 2 == 0]`
*   **Benefit:** They make your code shorter, often more readable, and can be more efficient than a regular `for` loop for list creation.
