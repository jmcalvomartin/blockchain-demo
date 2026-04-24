from __future__ import annotations

from dataclasses import dataclass
from math import isclose
from typing import Optional


@dataclass(frozen=True)
class ECPoint:
    x: Optional[int] = None
    y: Optional[int] = None
    infinity: bool = False

    def __str__(self) -> str:
        if self.infinity:
            return "O"
        return f"({self.x}, {self.y})"


INFINITY = ECPoint(infinity=True)


def format_point(point: ECPoint) -> str:
    return str(point)


def extended_gcd(a: int, b: int) -> tuple[int, int, int]:
    if b == 0:
        return a, 1, 0
    g, x1, y1 = extended_gcd(b, a % b)
    return g, y1, x1 - (a // b) * y1


def mod_inverse(value: int, modulus: int) -> int:
    value %= modulus
    g, x, _ = extended_gcd(value, modulus)
    if g != 1:
        raise ZeroDivisionError(f"No inverse for {value} mod {modulus}")
    return x % modulus


class RealWeierstrassCurve:
    def __init__(self, a: float, b: float) -> None:
        self.a = a
        self.b = b
        self.discriminant = -16 * (4 * a**3 + 27 * b**2)

    def is_nonsingular(self) -> bool:
        return not isclose(self.discriminant, 0.0, abs_tol=1e-10)

    def rhs(self, x: float) -> float:
        return x**3 + self.a * x + self.b

    def contains(self, x: float, y: float) -> bool:
        return isclose(y**2, self.rhs(x), rel_tol=1e-8, abs_tol=1e-8)

    def add_points(self, p: tuple[float, float], q: tuple[float, float]) -> dict:
        x1, y1 = p
        x2, y2 = q

        if isclose(x1, x2, abs_tol=1e-10) and isclose(y1, -y2, abs_tol=1e-10):
            return {
                "mode": "inverse",
                "lambda": None,
                "sum": None,
                "third_intersection": None,
                "message": "La recta es vertical, así que P + (-P) = O.",
            }

        same_point = isclose(x1, x2, abs_tol=1e-10) and isclose(y1, y2, abs_tol=1e-10)
        if same_point:
            if isclose(2 * y1, 0.0, abs_tol=1e-10):
                return {
                    "mode": "tangent_vertical",
                    "lambda": None,
                    "sum": None,
                    "third_intersection": None,
                    "message": "La tangente es vertical, así que 2P = O.",
                }
            slope = (3 * x1**2 + self.a) / (2 * y1)
            mode = "double"
        else:
            slope = (y2 - y1) / (x2 - x1)
            mode = "add"

        x3 = slope**2 - x1 - x2
        y3 = slope * (x1 - x3) - y1
        third_intersection = (x3, -y3)
        return {
            "mode": mode,
            "lambda": slope,
            "sum": (x3, y3),
            "third_intersection": third_intersection,
            "message": "La suma se obtiene al reflejar el tercer punto de intersección respecto al eje x.",
        }


class FiniteWeierstrassCurve:
    def __init__(self, p: int, a: int, b: int) -> None:
        self.p = p
        self.a = a % p
        self.b = b % p

    @property
    def discriminant(self) -> int:
        return (4 * pow(self.a, 3, self.p) + 27 * pow(self.b, 2, self.p)) % self.p

    def is_nonsingular(self) -> bool:
        return self.discriminant % self.p != 0

    def rhs(self, x: int) -> int:
        return (pow(x, 3, self.p) + self.a * x + self.b) % self.p

    def contains(self, point: ECPoint) -> bool:
        if point.infinity:
            return True
        return pow(point.y, 2, self.p) == self.rhs(point.x)

    def negate(self, point: ECPoint) -> ECPoint:
        if point.infinity:
            return point
        return ECPoint(point.x, (-point.y) % self.p)

    def add(self, p1: ECPoint, p2: ECPoint) -> tuple[ECPoint, dict]:
        if p1.infinity:
            return p2, {"case": "identity", "lambda": None, "explanation": "O + Q = Q"}
        if p2.infinity:
            return p1, {"case": "identity", "lambda": None, "explanation": "P + O = P"}
        if p1.x == p2.x and (p1.y + p2.y) % self.p == 0:
            return INFINITY, {"case": "inverse", "lambda": None, "explanation": "P + (-P) = O"}

        if p1 == p2:
            if p1.y % self.p == 0:
                return INFINITY, {"case": "tangent_vertical", "lambda": None, "explanation": "La tangente es vertical, así que 2P = O"}
            numerator = (3 * p1.x * p1.x + self.a) % self.p
            denominator_raw = (2 * p1.y) % self.p
            denominator_inv = mod_inverse(denominator_raw, self.p)
            slope = (numerator * denominator_inv) % self.p
            case = "double"
        else:
            numerator = (p2.y - p1.y) % self.p
            denominator_raw = (p2.x - p1.x) % self.p
            denominator_inv = mod_inverse(denominator_raw, self.p)
            slope = (numerator * denominator_inv) % self.p
            case = "add"

        x3 = (slope * slope - p1.x - p2.x) % self.p
        y3 = (slope * (p1.x - x3) - p1.y) % self.p
        result = ECPoint(x3, y3)
        return result, {
            "case": case,
            "lambda": slope,
            "numerator": numerator,
            "denominator_raw": denominator_raw,
            "denominator_inv": denominator_inv,
            "result": result,
        }

    def scalar_multiply(self, k: int, point: ECPoint) -> tuple[ECPoint, list[str]]:
        result = INFINITY
        addend = point
        trace: list[str] = []
        bit_index = 0
        value = k
        while value > 0:
            if value & 1:
                result, _ = self.add(result, addend)
                trace.append(f"Bit {bit_index}=1: acumulamos {format_point(addend)} -> {format_point(result)}")
            else:
                trace.append(f"Bit {bit_index}=0: no acumulamos")
            addend, _ = self.add(addend, addend)
            trace.append(f"Doblamos para el siguiente bit -> {format_point(addend)}")
            value >>= 1
            bit_index += 1
        return result, trace

    def list_points(self) -> list[ECPoint]:
        points = [INFINITY]
        for x in range(self.p):
            rhs = self.rhs(x)
            for y in range(self.p):
                if (y * y) % self.p == rhs:
                    points.append(ECPoint(x, y))
        return points

    def order(self, point: ECPoint, max_steps: int = 2000) -> int:
        if point.infinity:
            return 1
        current = point
        for index in range(1, max_steps + 1):
            if current.infinity:
                return index
            current, _ = self.add(current, point)
        raise ValueError("Order search exceeded max_steps")

    def multiples(self, point: ECPoint, count: int) -> list[tuple[int, ECPoint]]:
        rows: list[tuple[int, ECPoint]] = []
        current = INFINITY
        for k in range(1, count + 1):
            current, _ = self.add(current, point)
            rows.append((k, current))
            if current.infinity:
                break
        return rows


SECP256R1 = {
    "name": "secp256r1 / NIST P-256",
    "p": 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF,
    "a": 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFC,
    "b": 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B,
    "gx": 0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296,
    "gy": 0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5,
    "n": 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551,
}


def build_p256_curve() -> tuple[FiniteWeierstrassCurve, ECPoint]:
    curve = FiniteWeierstrassCurve(SECP256R1["p"], SECP256R1["a"], SECP256R1["b"])
    generator = ECPoint(SECP256R1["gx"], SECP256R1["gy"])
    return curve, generator


def p256_ecdh_demo(alice_private: int, bob_private: int) -> dict:
    curve, generator = build_p256_curve()
    order = SECP256R1["n"]
    alice_private = alice_private % order or 1
    bob_private = bob_private % order or 1

    alice_public, _ = curve.scalar_multiply(alice_private, generator)
    bob_public, _ = curve.scalar_multiply(bob_private, generator)
    shared_a, _ = curve.scalar_multiply(alice_private, bob_public)
    shared_b, _ = curve.scalar_multiply(bob_private, alice_public)

    return {
        "alice_private": alice_private,
        "bob_private": bob_private,
        "alice_public": alice_public,
        "bob_public": bob_public,
        "shared_a": shared_a,
        "shared_b": shared_b,
    }
