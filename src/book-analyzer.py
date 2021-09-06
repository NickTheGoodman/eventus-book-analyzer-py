import sys

if __name__ == "__main__":
    print("book-analyzer.PY")
    print(sys.argv)

    count = 1
    for line in sys.stdin:
        print(line.rstrip())
        print(count)
        count += 1

