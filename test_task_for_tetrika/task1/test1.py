import unittest
from solution1 import sum_two


class TestSumTwo(unittest.TestCase):
    def test_correct_types(self):
        """Оба аргумента корректные"""
        self.assertEqual(sum_two(1, 2), 3)
        self.assertEqual(sum_two(0, 0), 0)
        self.assertEqual(sum_two(-1, 1), 0)
        self.assertEqual(sum_two(100, 200), 300)

    def test_incorrect_first_arg(self):
        """Первый аргумент некорректный - str"""
        with self.assertRaises(TypeError) as context:
            sum_two("1", 2)
        self.assertIn(
            "Аргумент 'a' должен быть int, а передан str", str(context.exception)
        )

    def test_incorrect_second_arg(self):
        """Второй аргумент некорректный - str"""
        with self.assertRaises(TypeError) as context:
            sum_two(1, "2")
        self.assertIn(
            "Аргумент 'b' должен быть int, а передан str", str(context.exception)
        )

    def test_both_incorrect_args(self):
        """Оба аргумента некорректны - str"""
        with self.assertRaises(TypeError) as context:
            sum_two("1", "2")
        # Проверяем только первый аргумент, так как ошибка возникнет на нем
        self.assertIn(
            "Аргумент 'a' должен быть int, а передан str", str(context.exception)
        )

    def test_float_args(self):
        """Оба аргумента некорректны - float"""
        with self.assertRaises(TypeError) as context:
            sum_two(1.0, 2.2)
        self.assertIn(
            "Аргумент 'a' должен быть int, а передан float", str(context.exception)
        )

    def test_none_args(self):
        """Первый аргумент некорректный - None"""
        with self.assertRaises(TypeError) as context:
            sum_two(None, 2)
        self.assertIn(
            "Аргумент 'a' должен быть int, а передан NoneType", str(context.exception)
        )


if __name__ == "__main__":
    unittest.main()
