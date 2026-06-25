def check_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

def find_factors(n):
    factors = []
    for i in range(1, n + 1):
        if n % i == 0:
            factors.append(i)
    return factors

number = int(input("Enter a number: "))
if check_prime(number):
    print(f"{number} is a prime number.")
else:
    print(f"{number} is not a prime number.")
print("Factors:", find_factors(number))

