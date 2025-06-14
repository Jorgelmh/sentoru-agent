from app.utils.util import add_line_numbers_to_diff

# A git diff with a single hunk, using correct unified diff format
SAMPLE_DIFF_SINGLE_HUNK = """diff --git a/file.py b/file.py
index 0000001..0000002 100644
--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 class MyClass:
 -    def my_method(self):
 -        pass
 +    def my_new_method(self):
 +        print("Hello")
 +        pass"""

EXPECTED_OUTPUT_SINGLE_HUNK = """diff --git a/file.py b/file.py
index 0000001..0000002 100644
--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
1    class MyClass:
2    -    def my_method(self):
3    -        pass
4    +    def my_new_method(self):
5    +        print("Hello")
6    +        pass"""

# A git diff with multiple hunks, using correct unified diff format
SAMPLE_DIFF_MULTIPLE_HUNKS = """diff --git a/file.py b/file.py
index 0000001..0000003 100644
--- a/file.py
+++ b/file.py
@@ -1,3 +1,3 @@
 class MyClass:
 -    def my_method(self):
 -        pass
 +    def my_first_method(self):
 +        pass
@@ -8,3 +8,3 @@
     def my_other_method(self):
 -        return True
 +        return False"""

EXPECTED_OUTPUT_MULTIPLE_HUNKS = """diff --git a/file.py b/file.py
index 0000001..0000003 100644
--- a/file.py
+++ b/file.py
@@ -1,3 +1,3 @@
1    class MyClass:
2    -    def my_method(self):
3    -        pass
4    +    def my_first_method(self):
5    +        pass
@@ -8,3 +8,3 @@
1        def my_other_method(self):
2    -        return True
3    +        return False"""


def test_add_line_numbers_to_diff_single_hunk():
    processed_diff = add_line_numbers_to_diff(SAMPLE_DIFF_SINGLE_HUNK)
    assert processed_diff.strip() == EXPECTED_OUTPUT_SINGLE_HUNK.strip()


def test_add_line_numbers_to_diff_multiple_hunks():
    processed_diff = add_line_numbers_to_diff(SAMPLE_DIFF_MULTIPLE_HUNKS)
    assert processed_diff.strip() == EXPECTED_OUTPUT_MULTIPLE_HUNKS.strip()
