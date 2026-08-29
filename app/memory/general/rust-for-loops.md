---
id: rust-for-loops
title: Rust For Loops
category: general
one_liner: Explains the syntax and usage of for loops in the Rust programming language, including iteration over ranges and collections.
created_at: 2026-08-24T18:15:00Z
updated_at: 2026-08-24T18:15:00Z
turn_count: 1
---

## Summary

This turn explained how to write for loops in Rust. It covered basic syntax, iterating over numerical ranges, and looping through vectors. The explanation also highlighted key differences compared to Python's for loops, particularly regarding iteration over iterators and explicit handling of ownership or references.

## Conversation Log

### 2026-08-24T18:15:00Z
**Q:** How do I write a for loop in Rust?
**A (key points):**
- Building on our previous discussions about Python `for` loops, let's look at how to write a `for` loop in Rust.

Rust's `for` loops are primarily used to iterate over anything that implements the `IntoIterator` trait, which usually means iterating over a sequence of items.

Here's how you write them:

*   **Basic Syntax:** `for item in collection.iter() { /* code */ }`
    *   `item`: The variable that takes on the value of each element.
    *   `collection`: The list, array, vector, or range you want to loop through.
    *   `.iter()`: This is common for iterating over references to elements in a collection.

*   **Iterating over a Range:** This is similar to `range()` in Python.
    ```rust
    // Loop from 1 up to (but not including) 5
    for i in 1..5 {
        println!("{}", i); // Prints 1, 2, 3, 4
    }

    // Loop from 1 up to and including 5
    for i in 1..=5 {
        println!("{}", i); // Prints 1, 2, 3, 4, 5
    }
    ```

*   **Iterating over a Vector (like a Python list):**
    ```rust
    let numbers = vec![10, 20, 30];

    // Iterate over references (most common)
    for num_ref in &numbers {
        println!("The number is: {}", num_ref);
    }
    // Output:
    // The number is: 10
    // The number is: 20
    // The number is: 30

    // Iterate and take ownership (if you don't need the original vector afterwards)
    // This consumes the vector.
    for num in numbers {
        println!("Taking ownership of: {}", num);
    }
    ```

*   **Iterating with Index (like `enumerate()` in Python):**
    ```rust
    let fruits = vec!["apple", "banana", "cherry"];

    for (index, fruit) in fruits.iter().enumerate() {
        println!("Fruit at index {} is: {}", index, fruit);
    }
    // Output:
    // Fruit at index 0 is: apple
    // Fruit at index 1 is: banana
    // Fruit at index 2 is: cherry
    ```

**Key Differences from Python:**

*   Rust `for` loops always iterate over an "iterator." You often use methods like `.iter()`, `.into_iter()`, or `.enumerate()` to get the right kind of iterator.
*   Rust doesn't have a direct equivalent of Python's `for item in collection:` that automatically handles ownership/references in the same way. You explicitly choose how you iterate (by reference `&collection`, by value `collection`, or mutably `&mut collection`).
