# Python test set -- built-in functions

import test.support, unittest
import sys
import pickle
import itertools

# pure Python implementations (3 args only), for comparison
def pyrange(start, stop, step):
    if (start - stop) // step < 0:
        # replace stop with next element in the sequence of integers
        # that are congruent to start modulo step.
        stop += (start - stop) % step
        while start != stop:
            yield start
            start += step

def pyrange_reversed(start, stop, step):
    stop += (start - stop) % step
    return pyrange(stop - step, start - step, -step)


class RangeTest(unittest.TestCase):
    def assert_iterators_equal(self, xs, ys, test_id, limit=None):
        # check that an iterator xs matches the expected results ys,
        # up to a given limit.
        if limit is not None:
            xs = itertools.islice(xs, limit)
            ys = itertools.islice(ys, limit)
        sentinel = object()
        pairs = itertools.zip_longest(xs, ys, fillvalue=sentinel)
        for i, (x, y) in enumerate(pairs):
            if x == y:
                continue
            elif x == sentinel:
                self.fail('{}: iterator ended unexpectedly '
                          'at position {}; expected {}'.format(test_id, i, y))
            elif y == sentinel:
                self.fail('{}: unexpected excess element {} at '
                          'position {}'.format(test_id, x, i))
            else:
                self.fail('{}: wrong element at position {};'
                          'expected {}, got {}'.format(test_id, i, y, x))

    def test_range(self):
        self.assertEqual(list(range(3)), [0, 1, 2])
        self.assertEqual(list(range(1, 5)), [1, 2, 3, 4])
        self.assertEqual(list(range(0)), [])
        self.assertEqual(list(range(-3)), [])
        self.assertEqual(list(range(1, 10, 3)), [1, 4, 7])
        self.assertEqual(list(range(5, -5, -3)), [5, 2, -1, -4])

        a = 10
        b = 100
        c = 50

        self.assertEqual(list(range(a, a+2)), [a, a+1])
        self.assertEqual(list(range(a+2, a, -1)), [a+2, a+1])
        self.assertEqual(list(range(a+4, a, -2)), [a+4, a+2])

        seq = list(range(a, b, c))
        self.assertIn(a, seq)
        self.assertNotIn(b, seq)
        self.assertEqual(len(seq), 2)

        seq = list(range(b, a, -c))
        self.assertIn(b, seq)
        self.assertNotIn(a, seq)
        self.assertEqual(len(seq), 2)

        seq = list(range(-a, -b, -c))
        self.assertIn(-a, seq)
        self.assertNotIn(-b, seq)
        self.assertEqual(len(seq), 2)

        self.assertRaises(TypeError, range)
        self.assertRaises(TypeError, range, 1, 2, 3, 4)
        self.assertRaises(ValueError, range, 1, 2, 0)

        self.assertRaises(TypeError, range, 0.0, 2, 1)
        self.assertRaises(TypeError, range, 1, 2.0, 1)
        self.assertRaises(TypeError, range, 1, 2, 1.0)
        self.assertRaises(TypeError, range, 1e100, 1e101, 1e101)

        self.assertRaises(TypeError, range, 0, "spam")
        self.assertRaises(TypeError, range, 0, 42, "spam")

        self.assertEqual(len(range(0, sys.maxsize, sys.maxsize-1)), 2)

        r = range(-sys.maxsize, sys.maxsize, 2)
        self.assertEqual(len(r), sys.maxsize)

    def test_repr(self):
        self.assertEqual(repr(range(1)), 'range(0, 1)')
        self.assertEqual(repr(range(1, 2)), 'range(1, 2)')
        self.assertEqual(repr(range(1, 2, 3)), 'range(1, 2, 3)')

    def test_pickling(self):
        testcases = [(13,), (0, 11), (-22, 10), (20, 3, -1),
                     (13, 21, 3), (-2, 2, 2)]
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            for t in testcases:
                r = range(*t)
                self.assertEqual(list(pickle.loads(pickle.dumps(r, proto))),
                                 list(r))

    def test_odd_bug(self):
        # This used to raise a "SystemError: NULL result without error"
        # because the range validation step was eating the exception
        # before NULL was returned.
        with self.assertRaises(TypeError):
            range([], 1, -1)

    def test_types(self):
        # Non-integer objects *equal* to any of the range's items are supposed
        # to be contained in the range.
        self.assertIn(1.0, range(3))
        self.assertIn(True, range(3))
        self.assertIn(1+0j, range(3))

        class C1:
            def __eq__(self, other): return True
        self.assertIn(C1(), range(3))

        # Objects are never coerced into other types for comparison.
        class C2:
            def __int__(self): return 1
            def __index__(self): return 1
        self.assertNotIn(C2(), range(3))
        # ..except if explicitly told so.
        self.assertIn(int(C2()), range(3))

        # Check that the range.__contains__ optimization is only
        # used for ints, not for instances of subclasses of int.
        class C3(int):
            def __eq__(self, other): return True
        self.assertIn(C3(11), range(10))
        self.assertIn(C3(11), list(range(10)))

    def test_strided_limits(self):
        r = range(0, 101, 2)
        self.assertIn(0, r)
        self.assertNotIn(1, r)
        self.assertIn(2, r)
        self.assertNotIn(99, r)
        self.assertIn(100, r)
        self.assertNotIn(101, r)

        r = range(0, -20, -1)
        self.assertIn(0, r)
        self.assertIn(-1, r)
        self.assertIn(-19, r)
        self.assertNotIn(-20, r)

        r = range(0, -20, -2)
        self.assertIn(-18, r)
        self.assertNotIn(-19, r)
        self.assertNotIn(-20, r)

    def test_empty(self):
        r = range(0)
        self.assertNotIn(0, r)
        self.assertNotIn(1, r)

        r = range(0, -10)
        self.assertNotIn(0, r)
        self.assertNotIn(-1, r)
        self.assertNotIn(1, r)

    def test_range_iterators(self):
        # exercise 'fast' iterators, that use a rangeiterobject internally.
        # see issue 7298
        limits = [base + jiggle
                  for M in (2**32, 2**64)
                  for base in (-M, -M//2, 0, M//2, M)
                  for jiggle in (-2, -1, 0, 1, 2)]
        test_ranges = [(start, end, step)
                       for start in limits
                       for end in limits
                       for step in (-2**63, -2**31, -2, -1, 1, 2)]

        for start, end, step in test_ranges:
            iter1 = range(start, end, step)
            iter2 = pyrange(start, end, step)
            test_id = "range({}, {}, {})".format(start, end, step)
            # check first 100 entries
            self.assert_iterators_equal(iter1, iter2, test_id, limit=100)

            iter1 = reversed(range(start, end, step))
            iter2 = pyrange_reversed(start, end, step)
            test_id = "reversed(range({}, {}, {}))".format(start, end, step)
            self.assert_iterators_equal(iter1, iter2, test_id, limit=100)

def test_main():
    test.support.run_unittest(RangeTest)

if __name__ == "__main__":
    test_main()
