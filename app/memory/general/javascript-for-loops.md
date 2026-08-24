---
id: javascript-for-loops
title: JavaScript For Loops
category: general
one_liner: Explains how to write different types of for loops in JavaScript, including traditional, for...of, and for...in loops.
created_at: 2026-08-23T14:57:59Z
updated_at: 2026-08-23T14:57:59Z
turn_count: 1
---

## Summary

The answer details how to write for loops in JavaScript, covering three main types: the traditional C-style `for` loop for iterating a specific number of times or by index, the `for...of` loop for iterating over the values of iterable objects like arrays and strings, and the `for...in` loop for iterating over the enumerable properties (keys) of an object. It also explains the use of `break` and `continue` statements within loops and provides guidance on when to use each loop type.

## Conversation Log

### 2026-08-23T14:57:59Z
**Q:** How do I write a for loop in JavaScript?
**A (key points):**
- Okay, let's look at how to write `for` loops in JavaScript!

JavaScript offers a few different ways to write `for` loops, each suited for slightly different scenarios. The most common ones are:

1.  **The traditional `for` loop (C-style)**: For iterating a specific number of times or over arrays by index.
2.  **`for...of` loop**: For iterating over iterable objects (like arrays, strings, Maps, Sets) to get the *values*.
3.  **`for...in` loop**: For iterating over the *properties* (keys) of an object.

Let's break them down.

---

### 1. The Traditional `for` Loop (C-style)

This is the most flexible `for` loop and is very similar to loops in languages like C, Java, or Python's `range` loop. It has three parts in its declaration:

*   **Initialization**: Executed once before the loop starts. Typically used to declare and initialize a counter variable.
*   **Condition**: Evaluated before each loop iteration. If it's `true`, the loop continues; if `false`, the loop terminates.
*   **Increment/Decrement**: Executed after each loop iteration. Typically used to update the counter variable.

**Syntax:**

```javascript
for (initialization; condition; increment/decrement) {
    // code to be executed in each iteration
}
```

**Examples:**

**a) Looping a specific number of times:**

```javascript
for (let i = 0; i < 5; i++) {
    console.log("Iteration number:", i);
}

// Output:
// Iteration number: 0
// Iteration number: 1
// Iteration number: 2
// Iteration number: 3
// Iteration number: 4
```

**b) Looping through an array by index:**

```javascript
const fruits = ["apple", "banana", "cherry"];

for (let i = 0; i < fruits.length; i++) {
    console.log(`Fruit at index ${i}: ${fruits[i]}`);
}

// Output:
// Fruit at index 0: apple
// Fruit at index 1: banana
// Fruit at index 2: cherry
```

---

### 2. The `for...of` Loop (ES6+)

This loop is designed for iterating directly over the *values* of iterable objects. It's generally preferred for arrays and other iterables because it's cleaner and less prone to off-by-one errors compared to the traditional `for` loop when you only need the values.

**Syntax:**

```javascript
for (variable of iterable) {
    // code to be executed for each value
}
```

**Examples:**

**a) Looping through an array (getting values directly):**

```javascript
const colors = ["red", "green", "blue"];

for (const color of colors) {
    console.log("Color:", color);
}

// Output:
// Color: red
// Color: green
// Color: blue
```

**b) Looping through a string (getting characters):**

```javascript
const myString = "Hello";

for (const char of myString) {
    console.log("Character:", char);
}

// Output:
// Character: H
// Character: e
// Character: l
// Character: l
// Character: o
```

**c) Getting both index and value with `for...of` and `entries()`:**

If you need both the index and the value with `for...of`, you can use the `entries()` method of an array.

```javascript
const items = ["pen", "notebook", "eraser"];

for (const [index, item] of items.entries()) {
    console.log(`Item at index ${index}: ${item}`);
}

// Output:
// Item at index 0: pen
// Item at index 1: notebook
// Item at index 2: eraser
```

---

### 3. The `for...in` Loop

This loop is primarily used for iterating over the *enumerable properties (keys)* of an object. It's generally **not recommended** for iterating over arrays because it can iterate over inherited properties and the order of iteration is not guaranteed. For arrays, use `for` or `for...of`.

**Syntax:**

```javascript
for (variable in object) {
    // code to be executed for each property key
}
```

**Example:**

```javascript
const person = {
    name: "Alice",
    age: 30,
    city: "New York"
};

for (const key in person) {
    console.log(`${key}: ${person[key]}`);
}

// Output:
// name: Alice
// age: 30
// city: New York
```

**Important Note for `for...in`:** When using `for...in` on objects, it's often a good practice to add a `hasOwnProperty` check to ensure you're only dealing with the object's own properties and not inherited ones:

```javascript
for (const key in person) {
    if (person.hasOwnProperty(key)) {
        console.log(`${key}: ${person[key]}`);
    }
}
```

---

### `break` and `continue` Statements

Just like in Python, you can use `break` and `continue` inside JavaScript loops:

*   **`break`**: Immediately terminates the loop.
*   **`continue`**: Skips the rest of the current iteration and moves to the next one.

**Example:**

```javascript
for (let i = 0; i < 10; i++) {
    if (i === 3) {
        console.log("Skipping 3...");
        continue; // Skip to the next iteration
    }
    if (i === 7) {
        console.log("Found 7, breaking loop.");
        break; // Exit the loop entirely
    }
    console.log("Current number:", i);
}

// Output:
// Current number: 0
// Current number: 1
// Current number: 2
// Skipping 3...
// Current number: 4
// Current number: 5
// Current number: 6
// Found 7, breaking loop.
```

---

**Which one to use?**

*   **Traditional `for` loop**: When you need to iterate a specific number of times, need access to the index, or need to iterate backward.
*   **`for...of` loop**: For iterating over the *values* of arrays, strings, Maps, Sets, and other iterable objects. This is generally the cleanest and most modern approach for arrays when you don't need the index.
*   **`for...in` loop**: Primarily for iterating over the *keys* (property names) of plain JavaScript objects.

For most array-related tasks where you just need the elements, `for...of` is usually the best choice.
