# Error Codes
All error codes provided by this extension have a prefix of `T`. Here you'll find a list of all the errors this extension looks for, as well as a description of what they look for.

## `T812`: missing trailing comma
When breaking up a `list`/`tuple`/`dict` over multiple lines, every item should have its own line, and should be followed by a comma. This helps make diffs smaller and more readable. For example, if I start with the following code:

```Python
x = [
    "a"
]
```

and want to add a second item to that list, my diff might look like this:

```Diff
 x = [
-    "a"
+    "a",
+    "b"
]
```

But if all items always have a trailing comma, the diff would look like this:

```Diff
 x = [
     "a",
+    "b",
]
```
